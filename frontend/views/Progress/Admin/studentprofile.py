import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QProgressBar, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QFileSystemWatcher
from PyQt6.QtGui import QFont, QColor


class StudentProfileWidget(QWidget):
    """
    Admin read-only view of a specific student's profile.
    Displays student info, grades, and degree progress.
    (Faculty-only send-message UI removed for Admin.)
    """

    def __init__(self, student_id, admin_name=None, go_back_callback=None):
        super().__init__()
        self.student_id = student_id
        self.admin_name = admin_name
        self.go_back_callback = go_back_callback

        # JSON paths (same faculty files)
        base_dir = os.path.dirname(os.path.dirname(__file__))
        self.profile_file = os.path.join(base_dir, "data", "faculty_studentProfile.json")
        self.notes_file = os.path.join(base_dir, "data", "student_facultyNotes.json")

        # File watcher for dynamic note updates (read-only for admin)
        self.file_watcher = QFileSystemWatcher(self)
        if os.path.exists(self.notes_file):
            self.file_watcher.addPath(self.notes_file)
            self.file_watcher.fileChanged.connect(self.reload_notes)

        self.student_data = {}
        self.notes_data = []

        self.setObjectName("studentProfileWidget")
        self.init_ui()
        self.load_student_data()
        self.load_faculty_notes()

    # ---------------------------------------------------------
    def init_ui(self):
        # === Scrollable root ===
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("studentProfileScroll")
        outer_layout.addWidget(scroll_area)

        content_widget = QWidget()
        scroll_area.setWidget(content_widget)

        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(50, 20, 50, 20)
        main_layout.setSpacing(15)

        # ============================
        # HEADER SECTION
        # ============================
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(15)

        avatar = QLabel()
        avatar.setFixedSize(80, 80)
        avatar.setObjectName("studentAvatar")
        header_layout.addWidget(avatar)

        self.name_label = QLabel("Unknown")
        self.name_label.setFont(QFont("Poppins", 16, 75))
        self.id_label = QLabel("2023000001")
        self.course_label = QLabel("BS Information Technology")

        info_layout = QVBoxLayout()
        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.id_label)
        info_layout.addWidget(self.course_label)
        header_layout.addLayout(info_layout)
        header_layout.addStretch()

        back_button = QPushButton("← Go Back")
        back_button.setObjectName("goBackButton")
        back_button.setFixedSize(120, 32)
        back_button.clicked.connect(self.handle_back)
        header_layout.addWidget(back_button)
        main_layout.addWidget(header_frame)

        # ============================
        # GRADES TABLE
        # ============================
        grade_label = QLabel("Student Grade")
        grade_label.setFont(QFont("Poppins", 13, 75))
        main_layout.addWidget(grade_label)

        self.grade_table = QTableWidget()
        self.grade_table.setObjectName("gradesTable")
        self.grade_table.setColumnCount(6)
        self.grade_table.setHorizontalHeaderLabels([
            "No.", "Subject Code", "Description", "Units", "Midterm", "Finals"
        ])
        self.grade_table.verticalHeader().setVisible(False)
        self.grade_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.grade_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.grade_table.setAlternatingRowColors(True)

        header = self.grade_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        main_layout.addWidget(self.grade_table)

        # ============================
        # DEGREE PROGRESS
        # ============================
        progress_frame = QFrame()
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setSpacing(10)
        progress_layout.setContentsMargins(0, 0, 0, 0)

        self.progress_bars = {
            "Core Courses": QProgressBar(),
            "Electives": QProgressBar(),
            "Capstone Project": QProgressBar(),
            "Internship": QProgressBar(),
            "General Education": QProgressBar()
        }

        for label, bar in self.progress_bars.items():
            lbl = QLabel(label)
            lbl.setFont(QFont("Poppins", 10, 75))
            bar.setObjectName("progressBar")
            bar.setTextVisible(True)
            progress_layout.addWidget(lbl)
            progress_layout.addWidget(bar)

        main_layout.addWidget(progress_frame)

        # ============================
        # FACULTY NOTES SECTION (READ-ONLY)
        # ============================
        notes_label = QLabel("Faculty Notes (Read-only)")
        notes_label.setFont(QFont("Poppins", 13, 75))
        main_layout.addWidget(notes_label)

        notes_scroll = QScrollArea()
        notes_scroll.setWidgetResizable(True)
        notes_scroll.setObjectName("facultyNotesScroll")

        self.notes_container = QWidget()
        self.notes_layout = QVBoxLayout(self.notes_container)
        self.notes_layout.setContentsMargins(10, 10, 10, 10)
        self.notes_layout.setSpacing(8)
        notes_scroll.setWidget(self.notes_container)
        main_layout.addWidget(notes_scroll)

    # ---------------------------------------------------------
    def load_student_data(self):
        if not os.path.exists(self.profile_file):
            print(f"⚠️ Missing profile file: {self.profile_file}")
            return

        try:
            with open(self.profile_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            student = data.get(self.student_id, {})
            self.student_data = student

            self.name_label.setText(student.get("name", "Unknown"))
            self.id_label.setText(str(student.get("student_id", self.student_id)))
            self.course_label.setText(student.get("course", "BS Information Technology"))

            grades = student.get("grades", [])
            self.populate_grades(grades)

            progress = student.get("progress", {})
            for key, bar in self.progress_bars.items():
                bar.setValue(progress.get(key, 0))

        except Exception as e:
            print(f"❌ Error loading student profile: {e}")

    # ---------------------------------------------------------
    def populate_grades(self, grades):
        self.grade_table.setRowCount(0)
        for i, g in enumerate(grades, start=1):
            self.grade_table.insertRow(self.grade_table.rowCount())
            items = [
                str(i),
                g.get("subject_code", ""),
                g.get("description", ""),
                str(g.get("units", "")),
                str(g.get("midterm", "")),
                str(g.get("finals", "")),
            ]
            for col, val in enumerate(items):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.grade_table.setItem(i - 1, col, item)

    # ---------------------------------------------------------
    def load_faculty_notes(self):
        if not os.path.exists(self.notes_file):
            # no notes file is fine — admin will just see none
            self.notes_data = []
            self.display_notes()
            return

        try:
            with open(self.notes_file, "r", encoding="utf-8") as f:
                all_notes = json.load(f)

            # notes JSON structure may be a list or a dict per your existing file.
            # We'll support both: flatten to list of notes where receiver matches student_id
            notes_list = []
            if isinstance(all_notes, dict):
                # if keys are semesters or receiver lists
                # attempt to flatten values
                for val in all_notes.values():
                    if isinstance(val, list):
                        notes_list.extend(val)
            elif isinstance(all_notes, list):
                notes_list = all_notes

            # filter notes for this student
            self.notes_data = [n for n in notes_list if n.get("receiver") == self.student_id]
            self.display_notes()

        except Exception as e:
            print(f"❌ Error reading notes: {e}")

    # ---------------------------------------------------------
    def display_notes(self):
        for i in reversed(range(self.notes_layout.count())):
            widget = self.notes_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        if not self.notes_data:
            label = QLabel("No faculty notes available.")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.notes_layout.addWidget(label)
            self.notes_layout.addStretch()
            return

        for note in reversed(self.notes_data):
            msg_frame = QFrame()
            msg_frame.setObjectName("noteFrame")
            msg_layout = QVBoxLayout(msg_frame)
            msg_layout.setContentsMargins(10, 6, 10, 6)

            sender = note.get("faculty", "Unknown")
            subject = note.get("subject", "No Subject")
            message = note.get("message", "")
            date = note.get("date", "")

            sender_label = QLabel(f"{subject} • {sender}")
            sender_label.setObjectName("noteSender")
            msg_label = QLabel(message)
            msg_label.setWordWrap(True)
            date_label = QLabel(date)
            date_label.setObjectName("noteDate")

            msg_layout.addWidget(sender_label)
            msg_layout.addWidget(msg_label)
            msg_layout.addWidget(date_label)
            self.notes_layout.addWidget(msg_frame)

        self.notes_layout.addStretch()

    # ---------------------------------------------------------
    def reload_notes(self, path):
        self.load_faculty_notes()

    # ---------------------------------------------------------
    def handle_back(self):
        if callable(self.go_back_callback):
            self.go_back_callback()