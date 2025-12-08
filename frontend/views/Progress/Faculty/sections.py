# frontend/views/Progress/Faculty/sections.py
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QScrollArea, QGridLayout, QFrame, QStackedWidget, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QPixmap, QFont

from .base import FacultyAPIClient
from .studentslist import StudentsListWidget


class SectionsWidget(QWidget):
    """
    Faculty Progress page – displays list of sections assigned to the faculty.
    Fetches from backend API: GET /api/progress/faculty/sections/
    """
    
    sections_loaded = pyqtSignal(dict)  # Signal when sections data is loaded
    api_error_signal = pyqtSignal(str)  # Signal for API errors
    show_message_signal = pyqtSignal(str, str)  # Signal for messages
    
    def __init__(self, username=None, user_role="faculty", token=None, 
                 api_base="http://127.0.0.1:8000"):
        super().__init__()
        
        self.username = username
        self.user_role = user_role
        self.sections_data = {}
        self.current_year = None
        
        # Create API client as a separate object (COMPOSITION)
        self.api_client = FacultyAPIClient(token, api_base)
        
        # Connect API client signals to local slots
        self.api_client.api_error.connect(self._on_api_error)
        self.api_client.show_message.connect(self._on_show_message)

        # Connect local signals
        self.sections_loaded.connect(self._on_sections_loaded)

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
        header_label = QLabel("My Sections")
        header_label.setFont(QFont("Poppins", 14, 75))
        self.sections_layout.addWidget(header_label)

        # Dropdown for year levels
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
        self.scroll_area.setObjectName("facultySectionsScroll")

        self.scroll_content = QWidget()
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setContentsMargins(0, 10, 0, 10)
        self.grid_layout.setHorizontalSpacing(20)
        self.grid_layout.setVerticalSpacing(20)

        self.scroll_area.setWidget(self.scroll_content)
        self.sections_layout.addWidget(self.scroll_area)

        # Add to stack
        self.stack.addWidget(self.sections_page)

        # --- Load sections from API ---
        self.load_sections_from_api()

        self.setLayout(main_layout)

    # ---------------------------------------------------------
    def load_sections_from_api(self):
        """Load section data from backend API - FACULTY SPECIFIC"""
        endpoint = "/api/progress/faculty/sections/"  # Faculty-specific endpoint
        
        def handle_response(data):
            self.sections_loaded.emit(data)
        
        self.api_client.api_get(endpoint, callback=handle_response)

    @pyqtSlot(dict)
    def _on_sections_loaded(self, data):
        """Handle loaded sections data"""
        print(f"DEBUG [Faculty]: Sections data received: {data.keys() if isinstance(data, dict) else 'Not dict'}")
        
        if isinstance(data, dict) and "year_levels" in data:
            self.sections_data = data.get("year_levels", {})
        elif isinstance(data, dict) and "sections" in data:
            # Alternative format: {"sections": [...]}
            self.sections_data = {"All Years": data.get("sections", [])}
        elif isinstance(data, dict) and "detail" in data:
            # Error response
            error_msg = data.get("detail", "Unknown error")
            self.api_error_signal.emit(error_msg)
            self.sections_data = {}
        else:
            self.sections_data = {}
            print(f"WARNING [Faculty]: Unexpected sections data format: {data}")

        # Populate dropdown
        self.year_combo.blockSignals(True)
        self.year_combo.clear()
        
        if self.sections_data:
            years = list(self.sections_data.keys())
            self.year_combo.addItems(years)
            
            if not self.current_year and years:
                self.current_year = years[0]
                self.year_combo.setCurrentText(self.current_year)
                self.populate_sections(self.current_year)
        else:
            self.year_combo.addItem("No Sections Available")
            self.clear_sections_display()
            
        self.year_combo.blockSignals(False)

    @pyqtSlot(str)
    def _on_api_error(self, error_msg):
        """Handle API errors from API client"""
        print(f"❌ API Error [Faculty]: {error_msg}")
        self.show_message_signal.emit("Error", error_msg)
        self.clear_sections_display()

    @pyqtSlot(str, str)
    def _on_show_message(self, title, message):
        """Show message dialog from API client"""
        self.show_message_signal.emit(title, message)

    @pyqtSlot(str, str)
    def _on_show_message_signal(self, title, message):
        """Handle show message signal"""
        QMessageBox.information(self, title, message)

    # ---------------------------------------------------------
    def clear_sections_display(self):
        """Clear all section cards"""
        for i in reversed(range(self.grid_layout.count())):
            w = self.grid_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

    # ---------------------------------------------------------
    def populate_sections(self, year_level):
        """Populate section cards for the selected year"""
        self.clear_sections_display()

        if not year_level or year_level not in self.sections_data:
            # Show message if no sections
            no_sections_label = QLabel(f"No sections found for {year_level}")
            no_sections_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_sections_label.setStyleSheet("color: #6c757d; font-style: italic; padding: 30px;")
            self.grid_layout.addWidget(no_sections_label, 0, 0)
            return

        sections = self.sections_data[year_level]
        if not isinstance(sections, list):
            sections = []

        if not sections:
            # Show empty message
            empty_label = QLabel(f"No sections in {year_level}")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #6c757d; font-style: italic; padding: 30px;")
            self.grid_layout.addWidget(empty_label, 0, 0)
            return

        print(f"DEBUG [Faculty]: Displaying {len(sections)} sections for {year_level}")
        for index, section in enumerate(sections):
            card = self.create_section_card(section)
            row, col = divmod(index, 4)
            self.grid_layout.addWidget(card, row, col)

    # ---------------------------------------------------------
    def create_section_card(self, section):
        """Create a single section card"""
        frame = QFrame()
        frame.setObjectName("sectionCard")
        frame.setMinimumSize(200, 240)
        frame.setMaximumSize(240, 280)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        # Image/Icon area
        img_label = QLabel()
        img_label.setFixedHeight(120)
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Try to get image from section data
        img_path = ""
        for field in ["image", "image_path", "img_url", "photo"]:
            if field in section and section[field]:
                img_path = section[field]
                break
        
        try:
            if img_path and isinstance(img_path, str) and img_path.strip():
                pixmap = QPixmap(img_path).scaled(
                    200, 120,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                img_label.setPixmap(pixmap)
            else:
                # Default section icon
                img_label.setText("📚")
                img_label.setStyleSheet("font-size: 48px; color: #495057; background-color: #e9ecef; border-radius: 8px;")
        except Exception:
            img_label.setText("📚")
            img_label.setStyleSheet("font-size: 48px; color: #495057; background-color: #e9ecef; border-radius: 8px;")
        
        layout.addWidget(img_label)

        # Section info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        # Get section name
        section_name = ""
        for field in ["section_name", "name", "title", "code"]:
            if field in section:
                section_name = section[field]
                break
        
        name_label = QLabel(section_name or "Unknown Section")
        name_label.setFont(QFont("Poppins", 11, 75))
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        student_count = section.get("students", section.get("student_count", 0))
        count_label = QLabel(f"{student_count} STUDENTS")
        count_label.setFont(QFont("Poppins", 9))
        count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        count_label.setStyleSheet("color: #6c757d;")
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(count_label)
        layout.addLayout(info_layout)

        # View Students Button
        btn = QPushButton("View Students")
        btn.setObjectName("viewStudentsButton")
        btn.setFixedHeight(36)
        btn.clicked.connect(lambda: self.open_students_list(section_name or "Unknown"))
        layout.addWidget(btn)

        return frame

    # ---------------------------------------------------------
    def open_students_list(self, section_name):
        """Switch to StudentsListWidget for the given section"""
        print(f"📖 Opening Students List for {section_name}")
        
        students_page = StudentsListWidget(
            section_name=section_name,
            faculty_name=self.username,
            token=self.api_client.token,
            parent_stack=self.stack,
            go_back_callback=self.show_sections_page,
            api_base=self.api_client.api_base
        )
        
        self.stack.addWidget(students_page)
        self.stack.setCurrentWidget(students_page)

    # ---------------------------------------------------------
    def show_sections_page(self):
        """Go back to the main Sections page"""
        self.stack.setCurrentWidget(self.sections_page)

    # ---------------------------------------------------------
    def on_year_changed(self, year):
        """Triggered when year dropdown changes"""
        self.current_year = year
        self.populate_sections(year)