import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QStackedWidget, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from .gwastatistics import GwaStatisticsWidget
from .degreeprogress import DegreeProgressWidget
from .subjectsenrolled import SubjectsEnrolledWidget
from .facultynotes import FacultyNotesWidget


class GradesWidget(QWidget):
    """
    Main Student Progress page combining:
    Grades, GWA STATISTICS, SUBJECTS ENROLLED, DEGREE PROGRESS, FACULTY NOTES.
    """
    def __init__(self, user_role="student"):
        super().__init__()
        self.user_role = user_role
        self.current_semester = None

        # Load only from student_grades.json
        self.grades_data = self.load_grades_from_json()
        self.semester_list = list(self.grades_data.keys()) if self.grades_data else []

        self.setObjectName("gradesWidget")
        self.init_ui()

    # ---------------------------------------------------------
    def load_grades_from_json(self):
        """Load all grades and available semesters from student_grades.json"""
        progress_dir = os.path.dirname(os.path.dirname(__file__))
        data_path = os.path.join(progress_dir, "data", "student_grades.json")
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Support both { "semesters": {...} } or direct dict
                if isinstance(data, dict):
                    return data.get("semesters", data)
        except Exception as e:
            print(f"❌ Error loading student_grades.json: {e}")
        return {}

    # ---------------------------------------------------------
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 0, 10, 10)
        main_layout.setSpacing(10)

        # Header
        header_label = QLabel("Academic Progress Tracker")
        header_label.setFont(QFont("Poppins", 14, 75))  # 75 = Bold weight for Python 3.9.11 compatibility
        main_layout.addWidget(header_label)

        # Tabs
        tab_layout = QHBoxLayout()
        self.tab_names = [
            "GRADES", "GWA STATISTICS", "SUBJECTS ENROLLED", "DEGREE PROGRESS", "FACULTY NOTES"
        ]
        self.tab_buttons = []

        for i, name in enumerate(self.tab_names):
            btn = QPushButton(name)
            btn.setObjectName("tabButton")
            btn.setProperty("active", i == 0)
            btn.clicked.connect(lambda checked, index=i: self.switch_tab(index))
            self.tab_buttons.append(btn)
            tab_layout.addWidget(btn)

        tab_layout.addStretch()
        main_layout.addLayout(tab_layout)

        # Semester Combo - smaller and aligned to the right
        combo_layout = QHBoxLayout()
        combo_layout.addStretch()  # Push combo to the right
        self.semester_combo = QComboBox()
        self.semester_combo.setObjectName("semesterCombo")
        self.semester_combo.setFixedWidth(200)  # Make it smaller
        if self.semester_list:
            self.semester_combo.addItems(self.semester_list)
            self.current_semester = self.semester_list[0]
        self.semester_combo.currentTextChanged.connect(self.on_semester_changed)
        combo_layout.addWidget(self.semester_combo)
        main_layout.addLayout(combo_layout)

        # --- StackedWidget (pages) ---
        self.stacked_widget = QStackedWidget()

        # GRADES PAGE
        self.grades_page = QWidget()
        self.grades_page.setObjectName("gradesPage")
        grades_layout = QVBoxLayout(self.grades_page)
        grades_layout.setContentsMargins(0, 0, 0, 0)

        # Grades Table
        self.grades_table = QTableWidget()
        self.grades_table.setObjectName("gradesTable")
        self.grades_table.setColumnCount(8)
        self.grades_table.setHorizontalHeaderLabels([
            "No.", "Subject Code", "Description", "Units",
            "Midterm", "Finals", "Re-Exam", "Remarks"
        ])
        self.grades_table.verticalHeader().setVisible(False)
        self.grades_table.setAlternatingRowColors(True)
        self.grades_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.grades_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.grades_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.grades_table.setWordWrap(True)

        # Column width policy (0 means stretch)
        widths = [50, 120, 0, 60, 80, 80, 80, 100]
        header = self.grades_table.horizontalHeader()
        for i, w in enumerate(widths):
            if w == 0:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
                self.grades_table.setColumnWidth(i, w)

        grades_layout.addWidget(self.grades_table)

        # Add widgets to stack
        self.stacked_widget.addWidget(self.grades_page)
        self.gwa_widget = GwaStatisticsWidget()
        self.subjects_widget = SubjectsEnrolledWidget()
        self.degree_widget = DegreeProgressWidget()
        self.faculty_widget = FacultyNotesWidget()

        self.stacked_widget.addWidget(self.gwa_widget)
        self.stacked_widget.addWidget(self.subjects_widget)
        self.stacked_widget.addWidget(self.degree_widget)
        self.stacked_widget.addWidget(self.faculty_widget)

        main_layout.addWidget(self.stacked_widget)

        # Default tab
        self.stacked_widget.setCurrentIndex(0)
        if self.current_semester:
            self.populate_table(self.current_semester)

            # Sync initial semester with other widgets
            self.subjects_widget.set_semester(self.current_semester)
            self.degree_widget.set_semester(self.current_semester)
            if hasattr(self.faculty_widget, "set_semester"):
                self.faculty_widget.set_semester(self.current_semester)

    # ---------------------------------------------------------
    def switch_tab(self, index):
        for i, btn in enumerate(self.tab_buttons):
            btn.setProperty("active", i == index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.stacked_widget.setCurrentIndex(index)
        
        # Hide combo box when on GWA STATISTICS tab (index 1)
        if index == 1:  # GWA STATISTICS
            self.semester_combo.hide()
        else:
            self.semester_combo.show()

    # ---------------------------------------------------------
    def on_semester_changed(self, semester):
        if not semester:
            return
        self.current_semester = semester
        self.populate_table(semester)

        # 🔁 Sync semester with other widgets
        if hasattr(self, "subjects_widget") and self.subjects_widget:
            self.subjects_widget.set_semester(semester)
        if hasattr(self, "degree_widget") and self.degree_widget:
            self.degree_widget.set_semester(semester)
        if hasattr(self, "faculty_widget") and self.faculty_widget:
            if hasattr(self.faculty_widget, "set_semester"):
                self.faculty_widget.set_semester(semester)

    # ---------------------------------------------------------
    def populate_table(self, semester):
        sem_obj = self.grades_data.get(semester, {})
        grades_list = sem_obj.get("grades", []) if isinstance(sem_obj, dict) else []
        self.grades_table.setRowCount(0)

        for idx, record in enumerate(grades_list, start=1):
            row = self.grades_table.rowCount()
            self.grades_table.insertRow(row)

            # No. column
            no_item = QTableWidgetItem(str(idx))
            no_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grades_table.setItem(row, 0, no_item)

            # Subject code
            sc_item = QTableWidgetItem(record.get("subject_code", ""))
            sc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grades_table.setItem(row, 1, sc_item)

            # Description
            desc_item = QTableWidgetItem(record.get("description", ""))
            desc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grades_table.setItem(row, 2, desc_item)

            # Units
            units_item = QTableWidgetItem(str(record.get("units", "")))
            units_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grades_table.setItem(row, 3, units_item)

            # Midterm
            mid_item = QTableWidgetItem(str(record.get("midterm", "")))
            mid_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grades_table.setItem(row, 4, mid_item)

            # Finals
            fin_item = QTableWidgetItem(str(record.get("finals", "")))
            fin_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grades_table.setItem(row, 5, fin_item)

            # Re-exam
            re_item = QTableWidgetItem(str(record.get("re_exam", "")))
            re_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grades_table.setItem(row, 6, re_item)

            # Remarks (with FAILED styling)
            remarks = str(record.get("remarks", ""))
            remarks_item = QTableWidgetItem(remarks)
            remarks_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            if remarks.strip().upper() == "FAILED":
                remarks_item.setForeground(QColor("#ff0000"))
                fnt = remarks_item.font()
                fnt.setBold(True)
                remarks_item.setFont(fnt)

            self.grades_table.setItem(row, 7, remarks_item)

        self.grades_table.resizeRowsToContents()
        print(f"📘 Loaded {len(grades_list)} subjects for {semester}")