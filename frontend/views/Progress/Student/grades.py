# frontend/views/Progress/Student/grades.py
import threading
import traceback
import requests

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QStackedWidget, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont, QColor

from .gwastatistics import GwaStatisticsWidget
from .degreeprogress import DegreeProgressWidget
from .subjectsenrolled import SubjectsEnrolledWidget
from .facultynotes import FacultyNotesWidget


class GradesWidget(QWidget):
    """
    Thread-safe GradesWidget: background fetch emits 'grades_loaded' signal.
    """
    grades_loaded = pyqtSignal(dict)  # emits the raw backend response dict

    def __init__(self, username=None, user_role="student", token=None, api_base="http://127.0.0.1:8000"):
        super().__init__()
        self.username = username
        self.user_role = user_role
        self.token = token or ""
        self.api_base = api_base.rstrip("/")
        self.current_semester = None

        self.grades_data = {}
        self.semester_list = []

        self.setObjectName("gradesWidget")
        self.init_ui()

        # connect signal and start fetch
        self.grades_loaded.connect(self._on_grades_response_slot)
        self.load_grades_from_backend_async()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 0, 10, 10)
        main_layout.setSpacing(10)

        header_label = QLabel("Academic Progress Tracker")
        header_label.setFont(QFont("Poppins", 14, 75))
        main_layout.addWidget(header_label)

        tab_layout = QHBoxLayout()
        self.tab_names = ["GRADES", "GWA STATISTICS", "SUBJECTS ENROLLED", "DEGREE PROGRESS", "FACULTY NOTES"]
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

        combo_layout = QHBoxLayout()
        combo_layout.addStretch()
        self.semester_combo = QComboBox()
        self.semester_combo.setObjectName("semesterCombo")
        self.semester_combo.setFixedWidth(240)
        self.semester_combo.currentTextChanged.connect(self.on_semester_changed)
        combo_layout.addWidget(self.semester_combo)
        main_layout.addLayout(combo_layout)

        self.stacked_widget = QStackedWidget()

        # Grades page
        self.grades_page = QWidget()
        self.grades_page.setObjectName("gradesPage")
        grades_layout = QVBoxLayout(self.grades_page)
        grades_layout.setContentsMargins(0, 0, 0, 0)

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

        widths = [50, 120, 0, 60, 80, 80, 80, 100]
        header = self.grades_table.horizontalHeader()
        for i, w in enumerate(widths):
            if w == 0:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
                self.grades_table.setColumnWidth(i, w)

        grades_layout.addWidget(self.grades_table)
        self.stacked_widget.addWidget(self.grades_page)

        # Other pages/widgets
        self.gwa_widget = GwaStatisticsWidget(token=self.token, api_base=self.api_base)
        self.subjects_widget = SubjectsEnrolledWidget(token=self.token, api_base=self.api_base)
        self.degree_widget = DegreeProgressWidget(token=self.token, api_base=self.api_base)
        
        # Faculty notes widget - pass the role parameter
        self.faculty_widget = FacultyNotesWidget(token=self.token, api_base=self.api_base, role=self.user_role)

        self.stacked_widget.addWidget(self.gwa_widget)
        self.stacked_widget.addWidget(self.subjects_widget)
        self.stacked_widget.addWidget(self.degree_widget)
        self.stacked_widget.addWidget(self.faculty_widget)

        main_layout.addWidget(self.stacked_widget)
        self.stacked_widget.setCurrentIndex(0)

        # Connect subjects loaded signal if available
        if hasattr(self.subjects_widget, 'subjects_loaded_done'):
            self.subjects_widget.subjects_loaded_done.connect(self._on_subjects_loaded_done)

    def switch_tab(self, index):
        for i, btn in enumerate(self.tab_buttons):
            btn.setProperty("active", i == index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.stacked_widget.setCurrentIndex(index)
        self.semester_combo.setVisible(index != 1)  # Hide for GWA tab

    def _build_headers(self):
        token = (self.token or "").strip()
        if not token:
            return {}
        if token.startswith("Bearer ") or token.startswith("Token "):
            return {"Authorization": token}
        if len(token) > 40:
            return {"Authorization": f"Bearer {token}"}
        return {"Authorization": f"Token {token}"}

    def load_grades_from_backend_async(self):
        url = f"{self.api_base}/api/progress/student/grades/"
        headers = self._build_headers()

        def fetch():
            try:
                r = requests.get(url, headers=headers, timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    self.grades_loaded.emit(data)
                else:
                    self.grades_loaded.emit({})
            except Exception:
                traceback.print_exc()
                self.grades_loaded.emit({})

        threading.Thread(target=fetch, daemon=True).start()

    @pyqtSlot(dict)
    def _on_grades_response_slot(self, data):
        """
        Parse backend payload into internal format and update UI (main thread).
        """
        formatted = {}
        
        # Backend returns {"academic_years": [...]}
        if isinstance(data, dict) and "academic_years" in data:
            for year in data.get("academic_years", []):
                sy = year.get("school_year", "")
                for sem in year.get("semesters", []):
                    sem_name = sem.get("name", "")
                    key = f"{sy} – {sem_name}" if sy else sem_name
                    formatted[key] = {"grades": sem.get("courses", [])}
        # Fallback for other formats
        elif isinstance(data, dict) and "semesters" in data:
            formatted = data.get("semesters", {})
        
        # Set internal state
        self.grades_data = formatted
        self.semester_list = list(self.grades_data.keys())
        self._on_grades_loaded()

    def _on_grades_loaded(self):
        self.semester_combo.blockSignals(True)
        self.semester_combo.clear()

        if self.semester_list:
            self.semester_combo.addItems(self.semester_list)
            self.current_semester = self.semester_list[0]
            self.semester_combo.setCurrentIndex(0)
            self.populate_table(self.current_semester)

            # Propagate semester to child widgets
            self._refresh_child_widgets(self.current_semester)

        self.semester_combo.blockSignals(False)

    @pyqtSlot()
    def _on_subjects_loaded_done(self):
        """Called when subjects widget finishes loading"""
        if self.current_semester:
            self._refresh_child_widgets(self.current_semester)

    def on_semester_changed(self, semester):
        if not semester:
            return
        self.current_semester = semester
        self.populate_table(semester)

        # Tell children their semester changed
        self._refresh_child_widgets(semester)

    def populate_table(self, semester):
        sem_obj = self.grades_data.get(semester, {})
        grades_list = sem_obj.get("grades", [])
        self.grades_table.setRowCount(0)

        for idx, record in enumerate(grades_list, start=1):
            row = self.grades_table.rowCount()
            self.grades_table.insertRow(row)

            # Extract fields with fallbacks
            def _get_field(rec, *keys):
                for k in keys:
                    val = rec.get(k)
                    if val is not None and val != "":
                        return val
                return ""

            midterm = _get_field(record, "midterm", "midterm_grade")
            finals = _get_field(record, "finals", "final_term_grade", "final_grade")
            re_exam = _get_field(record, "re_exam", "reExam")
            remarks = _get_field(record, "remarks", "status", "")

            # If fields are dicts, extract nested values
            def _normalize_field(val):
                if isinstance(val, dict):
                    return val.get("finals") or val.get("midterm") or val.get("grade") or ""
                return val

            midterm = _normalize_field(midterm)
            finals = _normalize_field(finals)
            re_exam = _normalize_field(re_exam)

            items = [
                str(idx),
                record.get("subject_code", ""),
                record.get("description", ""),
                str(record.get("units", "")),
                str(midterm),
                str(finals),
                str(re_exam),
                str(remarks).upper()
            ]

            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Highlight failed grades
                if col == 7 and text.strip().upper() == "FAILED":
                    item.setForeground(QColor("#ff0000"))
                    fnt = item.font()
                    fnt.setBold(True)
                    item.setFont(fnt)
                
                self.grades_table.setItem(row, col, item)

        self.grades_table.resizeRowsToContents()

    def _refresh_child_widgets(self, semester):
        """
        Notify child widgets about semester change
        """
        # GWA widget
        if hasattr(self.gwa_widget, 'set_semester'):
            self.gwa_widget.set_semester(semester)

        # Subjects widget
        if hasattr(self.subjects_widget, 'set_semester'):
            self.subjects_widget.set_semester(semester)

        # Degree Progress widget
        if hasattr(self.degree_widget, 'set_semester'):
            self.degree_widget.set_semester(semester)

        # Faculty Notes widget
        if hasattr(self.faculty_widget, 'set_semester'):
            self.faculty_widget.set_semester(semester)