import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, QFileSystemWatcher
from PyQt6.QtGui import QFont, QColor
from .studentprofile import StudentProfileWidget  # ✅ import profile page


class StudentsListWidget(QWidget):
    """
    Displays the list of students in a specific section (for Faculty).
    Clicking a student's name or ID opens their profile.
    """

    def __init__(self, section_name, faculty_name=None, go_back_callback=None, parent_stack=None):
        super().__init__()
        self.section_name = section_name
        self.faculty_name = faculty_name
        self.go_back_callback = go_back_callback
        self.parent_stack = parent_stack  # ✅ stacked widget reference for navigation
        self.students_data = []
        self.file_watcher = QFileSystemWatcher(self)

        # JSON file path
        self.data_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "faculty_studentsList.json"
        )

        self.setObjectName("studentsListWidget")
        self.init_ui()
        self.load_students_from_json()

        # Watch file for updates
        if os.path.exists(self.data_path):
            self.file_watcher.addPath(self.data_path)
            self.file_watcher.fileChanged.connect(self.on_file_changed)

        # ✅ Connect to the correct handler
        self.table.cellClicked.connect(self.on_cell_clicked)

    # ---------------------------------------------------------
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 20, 50, 20)
        layout.setSpacing(10)

        # Header bar
        header_layout = QHBoxLayout()
        title = QLabel(self.section_name)
        title.setFont(QFont("Poppins", 14, 75))  # 75 = Bold weight for Python 3.9.11 compatibility
        title.setStyleSheet("color: #155724;")

        header_layout.addWidget(title)
        header_layout.addStretch()

        # Go Back button
        back_button = QPushButton("← Go Back")
        back_button.setObjectName("goBackButton")
        back_button.setFixedSize(120, 32)
        back_button.clicked.connect(self.handle_back)
        header_layout.addWidget(back_button)

        layout.addLayout(header_layout)

        # Table setup
        self.table = QTableWidget()
        self.table.setObjectName("gradesTable")
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "No.", "Student ID", "Name", "Grade", "Remarks", "GWA", "Missing Requirement"
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setWordWrap(True)

        # Column width policy
        widths = [60, 130, 0, 80, 100, 80, 0]
        header = self.table.horizontalHeader()
        for i, w in enumerate(widths):
            if w == 0:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
                self.table.setColumnWidth(i, w)

        layout.addWidget(self.table)
        self.setLayout(layout)

    # ---------------------------------------------------------
    def load_students_from_json(self):
        """Load student data for this section"""
        if not os.path.exists(self.data_path):
            print(f"⚠️ File not found: {self.data_path}")
            return

        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.students_data = data.get(self.section_name, [])
            self.populate_table()

        except Exception as e:
            print(f"❌ Error reading faculty_studentsList.json: {e}")

    # ---------------------------------------------------------
    def populate_table(self):
        """Display students in the table"""
        self.table.setRowCount(0)
        for i, student in enumerate(self.students_data, start=1):
            self.table.insertRow(self.table.rowCount())

            values = [
                str(i),
                student.get("student_id", ""),
                student.get("name", ""),
                str(student.get("grade", "")),
                student.get("remarks", ""),
                str(student.get("gwa", "")),
                student.get("missing_requirement", ""),
            ]

            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # Highlight clickable fields (ID & Name)
                if col in [1, 2]:
                    item.setForeground(QColor("#155724"))
                    font = item.font()
                    font.setUnderline(True)
                    item.setFont(font)
                    item.setToolTip("Click to open profile")

                # Mark failed grades
                if col == 4 and val.strip().upper() == "FAILED":
                    item.setForeground(QColor("#ff0000"))
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)

                self.table.setItem(i - 1, col, item)

        self.table.resizeRowsToContents()
        print(f"📘 Loaded {len(self.students_data)} students for {self.section_name}")

    # ---------------------------------------------------------
    def on_cell_clicked(self, row, column):
        """Handle click events on student ID or name"""
        if column not in [1, 2]:
            return

        student = self.students_data[row]
        student_id = student.get("student_id", "")
        print(f"👤 Opening profile for {student_id}")

        # Create Student Profile page
        profile_page = StudentProfileWidget(
            student_id=student_id,
            faculty_name=self.faculty_name,
            go_back_callback=self.show_self
        )

        if self.parent_stack:
            self.parent_stack.addWidget(profile_page)
            self.parent_stack.setCurrentWidget(profile_page)

    # ---------------------------------------------------------
    def show_self(self):
        """Return to student list (used when back button in profile pressed)"""
        if self.parent_stack:
            self.parent_stack.setCurrentWidget(self)

    # ---------------------------------------------------------
    def handle_back(self):
        """Go back to previous page"""
        if callable(self.go_back_callback):
            self.go_back_callback()

    # ---------------------------------------------------------
    def on_file_changed(self, path):
        """Reload when JSON changes"""
        print(f"🔄 Detected change in {path}, reloading student list...")
        self.load_students_from_json()

        # Re-add watcher
        if os.path.exists(self.data_path):
            if self.data_path not in self.file_watcher.files():
                self.file_watcher.addPath(self.data_path)