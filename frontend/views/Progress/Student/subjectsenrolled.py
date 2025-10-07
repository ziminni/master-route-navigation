import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, QFileSystemWatcher
from PyQt6.QtGui import QColor, QBrush, QFont


class SubjectsEnrolledWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.subjects_data = {}
        self.current_semester = None
        self.file_watcher = QFileSystemWatcher(self)

        # JSON path
        self.file_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "student_enrolledSubjects.json"
        )

        self.init_ui()
        self.load_subjects_from_file()

        # Watch file for changes
        if os.path.exists(self.file_path):
            self.file_watcher.addPath(self.file_path)
            self.file_watcher.fileChanged.connect(self.on_file_changed)

    # ---------------------------------------------------------
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 0)
        layout.setSpacing(0)

        # Create table
        self.table = QTableWidget()
        self.table.setObjectName("gradesTable")  # Match QSS
        headers = ["No.", "Subject Code", "Description", "Units", "Schedule", "Room", "Instructor"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        # Table configuration
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setWordWrap(True)

        # Column widths: 0 = stretch
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
    def load_subjects_from_file(self):
        """Load all subjects from JSON"""
        if not os.path.exists(self.file_path):
            print(f"⚠️ File not found: {self.file_path}")
            return

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Handle both structures: with or without 'semesters'
            self.subjects_data = data.get("semesters", data)
            self.semester_list = list(self.subjects_data.keys())

            # Default to the latest semester
            if self.semester_list:
                self.current_semester = self.semester_list[-1]
                self.load_semester_data(self.current_semester)

        except Exception as e:
            print(f"❌ Error reading enrolledSubjects.json: {e}")

    # ---------------------------------------------------------
    def load_semester_data(self, semester):
        """Load and display subjects for a specific semester"""
        semester_data = self.subjects_data.get(semester, {})
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
        print(f"📘 Loaded {len(subjects)} subjects for {semester}")

    # ---------------------------------------------------------
    def set_semester(self, semester):
        """Used by GradesWidget combo to update subjects"""
        self.current_semester = semester
        self.load_semester_data(semester)

    # ---------------------------------------------------------
    def on_file_changed(self, path):
        """Reload table when JSON changes"""
        print(f"🔄 Detected change in {path}, reloading...")
        self.load_subjects_from_file()
        if os.path.exists(self.file_path) and self.file_path not in self.file_watcher.files():
            self.file_watcher.addPath(self.file_path)

    # ---------------------------------------------------------
    def add_subject_entry(self, number, code, description, units, schedule, room, instructor):
        row = self.table.rowCount()
        self.table.insertRow(row)

        values = [number, code, description, units, schedule, room, instructor]
        for col, val in enumerate(values):
            item = QTableWidgetItem(val)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            font = QFont("Poppins", 9)
            item.setFont(font)

            # Grey out empty cells
            if val.strip() == "":
                item.setForeground(QBrush(QColor("#888888")))

            self.table.setItem(row, col, item)

    # ---------------------------------------------------------
    def clear_subjects(self):
        self.table.setRowCount(0)