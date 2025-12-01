# frontend/views/Progress/Student/subjectsenrolled.py
import threading
import traceback
import requests

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QBrush, QFont


class SubjectsEnrolledWidget(QWidget):
    """
    Thread-safe SubjectsEnrolledWidget. Worker emits 'subjects_loaded' (payload)
    and 'subjects_loaded_done' when finished loading so parent can react.
    """
    subjects_loaded = pyqtSignal(dict)       # emits backend payload dict
    subjects_loaded_done = pyqtSignal()      # signals that loading & initial set up are done

    def __init__(self, token=None, api_base="http://127.0.0.1:8000"):
        super().__init__()
        self.token = token or ""
        self.api_base = api_base.rstrip("/")

        self.subjects_data = {}
        self.semester_list = []
        self.current_semester = None

        self.init_ui()

        # connect signal then start worker
        self.subjects_loaded.connect(self._on_subjects_loaded_slot)
        self.load_subjects_from_backend_async()

    # ---------------------------------------------------------
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 0)
        layout.setSpacing(0)

        self.table = QTableWidget()
        self.table.setObjectName("gradesTable")
        headers = ["No.", "Subject Code", "Description", "Units", "Schedule", "Room", "Instructor"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setWordWrap(True)

        widths = [50, 120, 0, 60, 0, 120, 0]
        header = self.table.horizontalHeader()
        for i, w in enumerate(widths):
            if w == 0:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
                self.table.setColumnWidth(i, w)

        layout.addWidget(self.table)

    # ---------------------------------------------------------
    def _build_headers(self):
        token = (self.token or "").strip()
        if not token:
            return {}
        if token.startswith("Bearer ") or token.startswith("Token "):
            return {"Authorization": token}
        if len(token) > 40:
            return {"Authorization": f"Bearer {token}"}
        return {"Authorization": f"Token {token}"}

    # ---------------------------------------------------------
    def load_subjects_from_backend_async(self):
        """GET /api/progress/student/subjects/"""
        url = f"{self.api_base}/api/progress/student/subjects/"
        headers = self._build_headers()

        def fetch():
            try:
                r = requests.get(url, headers=headers, timeout=15)
                try:
                    data = r.json() if r.status_code == 200 else r.json()
                except Exception:
                    data = {}
                # emit to main thread with payload
                self.subjects_loaded.emit(data if isinstance(data, dict) else {})
            except Exception:
                traceback.print_exc()
                self.subjects_loaded.emit({})

        threading.Thread(target=fetch, daemon=True).start()

    # ---------------------------------------------------------
    @pyqtSlot(dict)
    def _on_subjects_loaded_slot(self, data):
        # Normalize payload
        if isinstance(data, dict) and "semesters" in data:
            self.subjects_data = data.get("semesters", {}) or {}
        else:
            self.subjects_data = {}

        self.semester_list = list(self.subjects_data.keys())
        if self.semester_list:
            # default to first semester immediately so UI is populated
            self.current_semester = self.semester_list[0]
            self.load_semester_data(self.current_semester)

        # notify parent / listeners that subjects have loaded and initial semester set
        self.subjects_loaded_done.emit()

    # ---------------------------------------------------------
    def load_semester_data(self, semester):
        if not semester:
            return

        resolved = self._resolve_semester_key(semester)
        semester_data = self.subjects_data.get(resolved, {}) if resolved else {}

        subjects = semester_data.get("subjects", [])

        self.clear_subjects()

        for i, subj in enumerate(subjects, start=1):
            self.add_subject_entry(
                str(i),
                subj.get("subject_code", ""),
                subj.get("description", ""),
                str(subj.get("units", "")),
                subj.get("schedule", ""),
                subj.get("room", ""),
                subj.get("instructor", "")
            )

        self.table.resizeRowsToContents()

    
    # ---------------------------------------------------------
    def _resolve_semester_key(self, semester):
        # exact match
        if semester in self.subjects_data:
            return semester

        # backend subjects format uses "YYYY-YYYY first", while grades uses "YYYY-YYYY – first"
        # remove dash if needed
        cleaned = semester.replace(" – ", " ").replace("–", " ")
        for key in self.subjects_data.keys():
            key_clean = key.replace(" – ", " ").replace("–", " ")
            if key_clean.strip().lower() == cleaned.strip().lower():
                return key

        # fallback: try suffix/prefix contains
        for key in self.subjects_data.keys():
            if key in semester or semester in key:
                return key

        return None


    # ---------------------------------------------------------
    def set_semester(self, semester):
        self.current_semester = semester
        self.load_semester_data(semester)

    # ---------------------------------------------------------
    def add_subject_entry(self, number, code, description, units, schedule, room, instructor):
        row = self.table.rowCount()
        self.table.insertRow(row)

        values = [number, code, description, units, schedule, room, instructor]
        for col, val in enumerate(values):
            item = QTableWidgetItem(val)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setFont(QFont("Poppins", 9))

            if str(val).strip() == "":
                item.setForeground(QBrush(QColor("#888888")))

            self.table.setItem(row, col, item)

    # ---------------------------------------------------------
    def clear_subjects(self):
        self.table.setRowCount(0)
