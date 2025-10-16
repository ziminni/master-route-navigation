import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QScrollArea, QGridLayout, QFrame, QStackedWidget
)
from PyQt6.QtCore import Qt, QFileSystemWatcher
from PyQt6.QtGui import QPixmap, QFont

from .studentslist import StudentsListWidget  # ✅ import
from .studentprofile import StudentProfileWidget  # ✅ import


class SectionsWidget(QWidget):
    """
    Faculty Progress page – displays list of sections per year level.
    Each section card shows:
        • Section name
        • Number of students
        • Optional image
        • 'View Students' button (opens StudentsListWidget)
    """

    def __init__(self, user_role="faculty", username=""):
        super().__init__()
        self.user_role = user_role
        self.username = username  # ✅ Faculty username (from login)
        self.sections_data = {}
        self.current_year = None

        # JSON watcher setup
        self.file_watcher = QFileSystemWatcher(self)
        self.sections_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "faculty_sections.json"
        )

        # --- Main Layout ---
        self.setObjectName("sectionsWidget")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # QStackedWidget (for switching pages)
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        # Build main sections page
        self.sections_page = QWidget()
        self.sections_layout = QVBoxLayout(self.sections_page)
        self.sections_layout.setContentsMargins(20, 20, 20, 20)
        self.sections_layout.setSpacing(15)

        # Header
        header_label = QLabel("Sections")
        header_label.setFont(QFont("Poppins", 14, 75))  # 75 = Bold weight for Python 3.9.11 compatibility
        self.sections_layout.addWidget(header_label)

        # Dropdown (same style as Student)
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)

        self.year_combo = QComboBox()
        self.year_combo.setObjectName("semesterCombo")
        self.year_combo.currentTextChanged.connect(self.on_year_changed)

        top_layout.addStretch()
        top_layout.addWidget(self.year_combo)
        self.sections_layout.addLayout(top_layout)

        # Scroll area for section cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setObjectName("facultyNotesScroll")

        self.scroll_content = QWidget()
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setContentsMargins(0, 10, 0, 10)
        self.grid_layout.setHorizontalSpacing(20)
        self.grid_layout.setVerticalSpacing(20)

        self.scroll_area.setWidget(self.scroll_content)
        self.sections_layout.addWidget(self.scroll_area)

        # Add to stack
        self.stack.addWidget(self.sections_page)

        # --- Load JSON data ---
        self.load_sections_from_json()

        # Add file watcher
        if os.path.exists(self.sections_file):
            self.file_watcher.addPath(self.sections_file)
            self.file_watcher.fileChanged.connect(self.on_file_changed)

        self.setLayout(main_layout)

    # ---------------------------------------------------------
    def load_sections_from_json(self):
        """Load section data from JSON file"""
        if not os.path.exists(self.sections_file):
            print(f"⚠️ File not found: {self.sections_file}")
            return

        try:
            with open(self.sections_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.sections_data = data.get("year_levels", {})

            # Populate dropdown
            self.year_combo.blockSignals(True)
            self.year_combo.clear()
            self.year_combo.addItems(self.sections_data.keys())
            self.year_combo.blockSignals(False)

            if not self.current_year and self.sections_data:
                self.current_year = list(self.sections_data.keys())[0]
                self.year_combo.setCurrentText(self.current_year)

            # Load cards
            self.populate_sections(self.current_year)

        except Exception as e:
            print(f"❌ Error reading faculty_sections.json: {e}")

    # ---------------------------------------------------------
    def populate_sections(self, year_level):
        """Populate section cards for the selected year"""
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        if not year_level or year_level not in self.sections_data:
            return

        sections = self.sections_data[year_level]

        for index, section in enumerate(sections):
            card = self.create_section_card(section)
            row, col = divmod(index, 4)
            self.grid_layout.addWidget(card, row, col)

    # ---------------------------------------------------------
    def create_section_card(self, section):
        """Create a single section card"""
        frame = QFrame()
        frame.setObjectName("sectionCard")
        frame.setFixedSize(220, 260)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Image
        image_label = QLabel()
        image_label.setFixedHeight(120)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_path = section.get("image", "")

        if os.path.exists(image_path):
            pixmap = QPixmap(image_path).scaled(
                220, 120,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            image_label.setPixmap(pixmap)
        else:
            image_label.setStyleSheet(
                "background-color: #dce0dd; border-top-left-radius: 6px; border-top-right-radius: 6px;"
            )
            image_label.setText("No Image")
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(image_label)

        # Info
        info_frame = QFrame()
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(10, 10, 10, 10)
        info_layout.setSpacing(5)

        section_name = section.get("section_name", "Unknown")
        section_label = QLabel(section_name)
        section_label.setFont(QFont("Poppins", 11, 75))  # 75 = Bold weight for Python 3.9.11 compatibility
        students_label = QLabel(f"{section.get('students', 0)} STUDENTS")
        students_label.setFont(QFont("Poppins", 9))
        students_label.setStyleSheet("color: #555;")

        info_layout.addWidget(section_label)
        info_layout.addWidget(students_label)
        info_layout.addStretch()
        layout.addWidget(info_frame)

        # View Students Button
        btn = QPushButton("View Students")
        btn.setObjectName("viewStudentsButton")
        btn.setFixedHeight(36)
        btn.clicked.connect(lambda: self.open_students_list(section_name))
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignBottom)

        return frame

    # ---------------------------------------------------------
    def open_students_list(self, section_name):
        """Switch to StudentsListWidget for the given section"""
        print(f"📖 Opening Students List for {section_name}")

        # ✅ Pass parent stack and username
        students_page = StudentsListWidget(
            section_name=section_name,
            faculty_name=self.username if hasattr(self, "username") else "Faculty",
            go_back_callback=self.show_sections_page,
            parent_stack=self.stack
        )

        self.stack.addWidget(students_page)
        self.stack.setCurrentWidget(students_page)

    # ---------------------------------------------------------
    def show_sections_page(self):
        """Go back to the main Sections page"""
        print("↩️ Returning to Sections page")
        self.stack.setCurrentWidget(self.sections_page)

    # ---------------------------------------------------------
    def on_year_changed(self, year):
        """Triggered when year dropdown changes"""
        self.current_year = year
        self.populate_sections(year)

    # ---------------------------------------------------------
    def on_file_changed(self, path):
        """Triggered when JSON file changes"""
        print(f"🔄 Detected change in {path}, reloading sections...")
        self.load_sections_from_json()

        # Re-add watcher if needed
        if os.path.exists(self.sections_file):
            if self.sections_file not in self.file_watcher.files():
                self.file_watcher.addPath(self.sections_file)