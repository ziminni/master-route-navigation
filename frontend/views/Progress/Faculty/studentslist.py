# frontend/views/Progress/Faculty/studentslist.py
import threading
import traceback
import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont, QColor

from .base import FacultyAPIClient
from .studentprofile import StudentProfileWidget


class StudentsListWidget(QWidget):  # ✅ Only inherit from QWidget, not FacultyAPIClient
    """Displays students in a specific section for Faculty"""
    
    students_loaded = pyqtSignal(list)  # Signal when students data is loaded
    
    def __init__(self, section_name, faculty_name=None, go_back_callback=None, 
                 parent_stack=None, token=None, api_base="http://127.0.0.1:8000"):
        super().__init__()  # ✅ Only call QWidget.__init__
        
        self.section_name = section_name
        self.faculty_name = faculty_name
        self.go_back_callback = go_back_callback
        self.parent_stack = parent_stack
        self.students_data = []
        
        # ✅ Create API client as composition (not inheritance)
        self.api_client = FacultyAPIClient(token, api_base)
        
        # Connect API client signals
        self.api_client.api_error.connect(self._on_api_error)
        self.api_client.show_message.connect(self._on_show_message)
        
        # Connect local signals
        self.students_loaded.connect(self._on_students_loaded)

        self.setObjectName("studentsListWidget")
        self.init_ui()
        self.load_students_from_api()

        self.table.cellClicked.connect(self.on_cell_clicked)

    # ---------------------------------------------------------
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 20, 50, 20)
        layout.setSpacing(10)

        # Header bar
        header_layout = QHBoxLayout()
        title = QLabel(f"Students in {self.section_name}")
        title.setFont(QFont("Poppins", 14, 75))
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
    def load_students_from_api(self):
        """Load students for this section from backend API - FACULTY SPECIFIC"""
        endpoint = f"/api/progress/faculty/section/{self.section_name}/students/"
        
        def handle_response(data):
            if isinstance(data, dict) and "students" in data:
                self.students_loaded.emit(data.get("students", []))
            elif isinstance(data, dict) and "detail" in data:
                # Error response
                self.api_client.api_error.emit(data["detail"])
                self.students_loaded.emit([])
            else:
                self.students_loaded.emit([])
        
        self.api_client.api_get(endpoint, callback=handle_response)

    @pyqtSlot(list)
    def _on_students_loaded(self, students_list):
        """Handle loaded students data"""
        self.students_data = students_list or []
        self.populate_table()

    @pyqtSlot(str)
    def _on_api_error(self, error_msg):
        """Handle API errors"""
        QMessageBox.warning(self, "Error", error_msg)
        self.populate_table()  # Show empty table

    @pyqtSlot(str, str)
    def _on_show_message(self, title, message):
        """Show message dialog"""
        QMessageBox.information(self, title, message)

    # ---------------------------------------------------------
    def populate_table(self):
        """Display students in the table"""
        self.table.setRowCount(0)
        
        if not self.students_data:
            # Show empty message
            self.table.setRowCount(1)
            self.table.setSpan(0, 0, 1, 7)
            empty_item = QTableWidgetItem("No students found in this section")
            empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_item.setForeground(QColor("#6c757d"))
            self.table.setItem(0, 0, empty_item)
            return

        print(f"DEBUG [Faculty]: Populating table with {len(self.students_data)} students")
        for i, student in enumerate(self.students_data, start=1):
            self.table.insertRow(self.table.rowCount())
            
            # Extract data with fallbacks
            student_id = student.get("student_id") or student.get("id") or ""
            name = student.get("name") or student.get("student_name") or ""
            grade = student.get("grade", "")
            remarks = student.get("remarks", "")
            gwa = student.get("gwa", "")
            missing_req = student.get("missing_requirement", "")
            
            values = [
                str(i),
                student_id,
                name,
                str(grade),
                str(remarks),
                str(gwa),
                str(missing_req)
            ]
            
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # Clickable visual for student id/name
                if col in [1, 2]:
                    item.setForeground(QColor("#155724"))
                    font = item.font()
                    font.setUnderline(True)
                    item.setFont(font)
                    item.setToolTip("Click to open profile")

                # Mark failed remarks in red
                if col == 4 and str(val).strip().upper() == "FAILED":
                    item.setForeground(QColor("#ff0000"))
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                    
                # Highlight low grades
                if col == 3:
                    try:
                        grade_val = float(val)
                        if grade_val > 3.0:
                            item.setForeground(QColor("#ff0000"))
                            font = item.font()
                            font.setBold(True)
                            item.setFont(font)
                    except ValueError:
                        pass

                self.table.setItem(i - 1, col, item)

        self.table.resizeRowsToContents()

    # ---------------------------------------------------------
    def on_cell_clicked(self, row, column):
        """Handle click events on student ID or name"""
        if column not in [1, 2]:
            return

        # Check if we're showing the "no students" message
        if self.table.rowCount() == 1 and self.table.item(0, 0) and "No students" in self.table.item(0, 0).text():
            return

        try:
            student = self.students_data[row]
        except (IndexError, KeyError) as e:
            print(f"❌ Error accessing student data: {e}")
            QMessageBox.warning(self, "Error", "Could not access student data.")
            return

        # Get student ID
        student_id = student.get("student_id") or student.get("id") or ""
        
        if not student_id:
            print("❌ No student ID found")
            QMessageBox.warning(self, "Error", "No student ID available for this student.")
            return

        print(f"DEBUG [Faculty]: Opening profile for student ID: {student_id}")
        profile_page = StudentProfileWidget(
            student_id=student_id,
            faculty_name=self.faculty_name,
            token=self.api_client.token,  # ✅ Use api_client's token
            parent_stack=self.parent_stack,
            go_back_callback=self.show_self,
            api_base=self.api_client.api_base  # ✅ Use api_client's api_base
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