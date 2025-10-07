import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QStackedWidget, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from .gwastatistics import GwaStatisticsWidget
from .degreeprogress import DegreeProgressWidget
from .subjectsenrolled import SubjectsEnrolledWidget


class GradesWidget(QWidget):
    """
    Main Student Progress page combining the tabs:
    Grades, GWA Statistics, Subjects Enrolled, Degree Progress.
    """
    def __init__(self, user_role="student"):
        super().__init__()
        self.user_role = user_role
        self.current_semester = None

        # load data
        self.semester_list = self.load_semesters_from_json()
        self.grades_data = self.load_grades_from_json()

        self.init_ui()
        self.load_styles()

    # ---------------------------------------------------------
    def load_semesters_from_json(self):
        """Load list of semesters from /views/Progress/data/semesters.json"""
        progress_dir = os.path.dirname(os.path.dirname(__file__))
        data_path = os.path.join(progress_dir, "data", "semesters.json")
        if not os.path.exists(data_path):
            print(f"⚠️ semesters.json not found at {data_path}")
            return []
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                if isinstance(data, dict) and "semesters" in data:
                    return data["semesters"]
                return []
        except Exception as e:
            print(f"❌ Error loading semesters.json: {e}")
            return []

    # ---------------------------------------------------------
    def load_grades_from_json(self):
        """Load all grades from /views/Progress/data/grades.json"""
        progress_dir = os.path.dirname(os.path.dirname(__file__))
        data_path = os.path.join(progress_dir, "data", "grades.json")
        if not os.path.exists(data_path):
            print(f"⚠️ grades.json not found at {data_path}")
            return {}
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "semesters" in data:
                    return data["semesters"]
                return data
        except Exception as e:
            print(f"❌ Error loading grades.json: {e}")
            return {}

    # ---------------------------------------------------------
    def init_ui(self):
        self.setObjectName("gradesWidget")  # 🔹 matches your QSS
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 0, 10, 10)
        main_layout.setSpacing(10)

        # header
        header_label = QLabel("Academic Progress Tracker")
        header_label.setFont(QFont("Poppins", 14, QFont.Weight.Bold))
        main_layout.addWidget(header_label)

        # -----------------------
        # Tab buttons
        # -----------------------
        self.tab_names = [
            "GRADES", "GWA STATISTICS", "SUBJECTS ENROLLED", "DEGREE PROGRESS"
        ]
        self.tab_buttons = []
        tab_layout = QHBoxLayout()

        for i, name in enumerate(self.tab_names):
            btn = QPushButton(name)
            btn.setObjectName("tabButton")  # 🔹 apply tabButton style
            btn.setProperty("active", i == 0)
            btn.clicked.connect(lambda checked, index=i: self.switch_tab(index))
            self.tab_buttons.append(btn)
            tab_layout.addWidget(btn)

        tab_layout.addStretch()
        main_layout.addLayout(tab_layout)

        # -----------------------
        # Semester combo
        # -----------------------
        self.semester_combo = QComboBox()
        self.semester_combo.setObjectName("semesterCombo")  # 🔹 match QSS
        if self.semester_list:
            self.semester_combo.addItems(self.semester_list)
            self.semester_combo.setCurrentIndex(0)
            self.current_semester = self.semester_list[0]
        self.semester_combo.currentTextChanged.connect(self.on_semester_changed)
        main_layout.addWidget(self.semester_combo)

        # -----------------------
        # Stacked pages
        # -----------------------
        self.stacked_widget = QStackedWidget()

        # Grades Table
        self.grades_table = QTableWidget()
        self.grades_table.setObjectName("gradesTable")  # 🔹 match QSS
        self.grades_table.setColumnCount(7)
        self.grades_table.setHorizontalHeaderLabels([
            "Subject Code", "Description", "Units",
            "Midterm", "Finals", "Re-Exam", "Remarks"
        ])
        self.grades_table.setAlternatingRowColors(True)
        self.grades_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.grades_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.grades_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        gwa_widget = GwaStatisticsWidget()
        subjects_widget = SubjectsEnrolledWidget()
        degree_widget = DegreeProgressWidget()

        self.widgets = [
            self.grades_table,
            gwa_widget,
            subjects_widget,
            degree_widget,
        ]

        for w in self.widgets:
            self.stacked_widget.addWidget(w)
        main_layout.addWidget(self.stacked_widget)

        # default visible tab: GRADES
        self.stacked_widget.setCurrentIndex(0)
        if self.current_semester:
            self.populate_table(self.current_semester)
        else:
            self.grades_table.setRowCount(0)

    # ---------------------------------------------------------
    def switch_tab(self, index):
        for i, btn in enumerate(self.tab_buttons):
            btn.setProperty("active", i == index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        if 0 <= index < len(self.widgets):
            self.stacked_widget.setCurrentWidget(self.widgets[index])

    # ---------------------------------------------------------
    def on_semester_changed(self, semester):
        if not semester:
            return
        self.current_semester = semester
        self.populate_table(semester)

    # ---------------------------------------------------------
    def populate_table(self, semester):
        """Fill the grades table with subjects for the given semester"""
        sem_obj = self.grades_data.get(semester, {})
        grades_list = sem_obj.get("grades", []) if isinstance(sem_obj, dict) else []
        if not grades_list:
            self.grades_table.setRowCount(0)
            return

        self.grades_table.setRowCount(len(grades_list))
        for row, record in enumerate(grades_list):
            self.grades_table.setItem(row, 0, QTableWidgetItem(str(record.get("subject_code", ""))))
            self.grades_table.setItem(row, 1, QTableWidgetItem(str(record.get("description", ""))))
            self.grades_table.setItem(row, 2, QTableWidgetItem(str(record.get("units", ""))))
            self.grades_table.setItem(row, 3, QTableWidgetItem(str(record.get("midterm", ""))))
            self.grades_table.setItem(row, 4, QTableWidgetItem(str(record.get("finals", ""))))
            self.grades_table.setItem(row, 5, QTableWidgetItem(str(record.get("re_exam", ""))))
            remarks_item = QTableWidgetItem(str(record.get("remarks", "")))

            # mark failed rows visually
            if record.get("remarks", "").upper() == "FAILED":
                remarks_item.setData(Qt.ItemDataRole.UserRole, "FAILED")

            self.grades_table.setItem(row, 6, remarks_item)

        self.grades_table.resizeColumnsToContents()
        print(f"📘 Loaded {len(grades_list)} subjects for {semester}")

    # ---------------------------------------------------------
    def load_styles(self):
        """Load the shared QSS stylesheet for Progress module."""
        try:
            styles_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "Styles", "styles.qss"
            )
            if os.path.exists(styles_path):
                with open(styles_path, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
                print(f"✅ Loaded Progress styles from {styles_path}")
            else:
                print(f"⚠️ Stylesheet not found at {styles_path}")
        except Exception as e:
            print(f"❌ Error loading styles: {e}")