# frontend/views/Progress/Admin/sections.py
import threading
import traceback
import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QScrollArea, QGridLayout, QFrame, QStackedWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont

from .studentslist import StudentsListWidget


class SectionsWidget(QWidget):
    """
    Admin Progress page – fetches sections by year-level from backend API.
    """

    def __init__(self, username=None, user_role=None, token=None,
                 api_base="http://127.0.0.1:8000"):
        super().__init__()
        self.username = username
        self.user_role = user_role
        self.token = token or ""
        self.api_base = api_base.rstrip("/")
        self.sections_data = {}        # {"1st Year": [...], "2nd Year": [...]} from backend
        self.current_year = None

        # UI setup
        self.setObjectName("adminSectionsWidget")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        self.sections_page = QWidget()
        self.sections_layout = QVBoxLayout(self.sections_page)
        self.sections_layout.setContentsMargins(20, 20, 20, 20)
        self.sections_layout.setSpacing(15)

        header_label = QLabel("Sections (Admin)")
        header_label.setFont(QFont("Poppins", 14, 75))
        self.sections_layout.addWidget(header_label)

        top = QHBoxLayout()
        self.year_combo = QComboBox()
        self.year_combo.setObjectName("semesterCombo")
        self.year_combo.currentTextChanged.connect(self.on_year_changed)
        top.addStretch()
        top.addWidget(self.year_combo)
        self.sections_layout.addLayout(top)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.scroll_content = QWidget()
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setContentsMargins(0, 10, 0, 10)
        self.grid_layout.setHorizontalSpacing(20)
        self.grid_layout.setVerticalSpacing(20)

        self.scroll_area.setWidget(self.scroll_content)
        self.sections_layout.addWidget(self.scroll_area)

        self.stack.addWidget(self.sections_page)

        # FETCH API
        self.load_sections()

        self.setLayout(main_layout)

    def _headers(self):
        token = (self.token or "").strip()
        if not token:
            return {}
        if token.startswith("Bearer ") or token.startswith("Token "):
            token = token.split(" ", 1)[1]
        return {"Authorization": f"Bearer {token}"}

    # ---------------------------------------------------------
    def load_sections(self):
        """Fetch section list grouped by year-level from backend"""
        url = f"{self.api_base}/api/progress/admin/sections/"

        def fetch():
            try:
                print(f"DEBUG: Fetching sections from {url}")
                r = requests.get(url, headers=self._headers(), timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    print(f"DEBUG: Sections API response: {data}")
                    
                    if isinstance(data, dict):
                        if "year_levels" in data:
                            self.sections_data = data.get("year_levels", {})
                            print(f"DEBUG: Loaded sections data: {list(self.sections_data.keys())}")
                        elif "sections" in data:
                            self.sections_data = {"All Years": data.get("sections", [])}
                        else:
                            self.sections_data = data
                    else:
                        self.sections_data = {"All Years": []}
                else:
                    print(f"❌ API error {r.status_code}: {r.text}")
                    self.sections_data = {}
            except Exception as e:
                print(f"❌ Exception fetching sections: {e}")
                traceback.print_exc()
                self.sections_data = {}

            self.populate_years()

        threading.Thread(target=fetch, daemon=True).start()

    # ---------------------------------------------------------
    def populate_years(self):
        # defensive: ensure keys is a list
        if isinstance(self.sections_data, dict):
            years = list(self.sections_data.keys())
        elif isinstance(self.sections_data, list):
            years = ["All Years"]
            self.sections_data = {"All Years": self.sections_data}
        else:
            years = []
            self.sections_data = {}

        self.year_combo.blockSignals(True)
        self.year_combo.clear()
        if years:
            self.year_combo.addItems(years)
        else:
            self.year_combo.addItem("No Sections Available")
        self.year_combo.blockSignals(False)

        if years and not self.current_year:
            self.current_year = years[0]
            self.year_combo.setCurrentText(self.current_year)
            self.populate_sections(self.current_year)
        else:
            # Clear sections display
            self.clear_sections_display()

    # ---------------------------------------------------------
    def clear_sections_display(self):
        """Clear all section cards"""
        for i in reversed(range(self.grid_layout.count())):
            w = self.grid_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

    # ---------------------------------------------------------
    def populate_sections(self, year_level):
        # clear previous widgets
        self.clear_sections_display()

        if not year_level or year_level not in self.sections_data:
            # Show message if no sections
            no_sections_label = QLabel(f"No sections found for {year_level}")
            no_sections_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(no_sections_label, 0, 0)
            return

        sections = self.sections_data[year_level]
        if not isinstance(sections, list):
            sections = []

        if not sections:
            # Show empty message
            empty_label = QLabel(f"No sections in {year_level}")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(empty_label, 0, 0)
            return

        print(f"DEBUG: Displaying {len(sections)} sections for {year_level}")
        for index, section in enumerate(sections):
            card = self.create_section_card(section)
            row, col = divmod(index, 4)
            self.grid_layout.addWidget(card, row, col)

    # ---------------------------------------------------------
    def create_section_card(self, section):
        frame = QFrame()
        frame.setObjectName("sectionCard")
        frame.setFixedSize(220, 260)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(6, 6, 6, 6)

        img_label = QLabel()
        img_label.setFixedHeight(120)
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Handle image field
        img_path = ""
        for field in ["image", "image_path", "img_url", "photo"]:
            if field in section:
                img_path = section[field]
                break
        
        try:
            if img_path and isinstance(img_path, str) and img_path.strip():
                pixmap = QPixmap(img_path).scaled(
                    220, 120,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                img_label.setPixmap(pixmap)
            else:
                img_label.setText("📚")
                img_label.setStyleSheet("font-size: 48px; color: #555;")
        except Exception:
            img_label.setText("📚")
            img_label.setStyleSheet("font-size: 48px; color: #555;")

        layout.addWidget(img_label)

        info = QVBoxLayout()
        
        # Get section name
        section_name = ""
        for field in ["section_name", "name", "title", "code"]:
            if field in section:
                section_name = section[field]
                break
        
        name = QLabel(section_name or "Unknown Section")
        name.setFont(QFont("Poppins", 11, 75))
        name.setWordWrap(True)
        
        student_count = section.get("students", section.get("student_count", 0))
        count = QLabel(f"{student_count} STUDENTS")
        count.setFont(QFont("Poppins", 9))
        
        info.addWidget(name)
        info.addWidget(count)
        info_frame = QFrame()
        info_frame.setLayout(info)
        layout.addWidget(info_frame)

        btn = QPushButton("View Students")
        btn.setObjectName("viewStudentsButton")
        btn.setFixedHeight(36)
        btn.clicked.connect(lambda: self.open_students(section_name or "Unknown"))
        layout.addWidget(btn)

        return frame

    def open_students(self, section_name):
        print(f"DEBUG: Opening students for section: {section_name}")
        students_page = StudentsListWidget(
            section_name=section_name,
            admin_name=self.username,
            token=self.token,
            parent_stack=self.stack,
            go_back_callback=self.show_sections,
            api_base=self.api_base
        )
        self.stack.addWidget(students_page)
        self.stack.setCurrentWidget(students_page)

    def show_sections(self):
        self.stack.setCurrentWidget(self.sections_page)

    def on_year_changed(self, year):
        self.current_year = year
        self.populate_sections(year)