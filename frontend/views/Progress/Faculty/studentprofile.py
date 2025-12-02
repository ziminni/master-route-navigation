import os
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QProgressBar, QTextEdit, QFrame, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, QFileSystemWatcher
from PyQt6.QtGui import QFont, QColor


class StudentProfileWidget(QWidget):
    """
    Faculty view of a specific student's profile.
    Displays student info, grades, progress, and allows faculty to send notes.
    """

    def __init__(self, student_id, faculty_name, go_back_callback=None):
        super().__init__()
        self.student_id = student_id
        self.faculty_name = faculty_name
        self.go_back_callback = go_back_callback

        # JSON paths
        base_dir = os.path.dirname(os.path.dirname(__file__))
        self.profile_file = os.path.join(base_dir, "data", "faculty_studentProfile.json")
        self.notes_file = os.path.join(base_dir, "data", "student_facultyNotes.json")

        # File watcher for dynamic note updates
        self.file_watcher = QFileSystemWatcher(self)
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
        self.name_label.setFont(QFont("Poppins", 16, 75))  # 75 = Bold weight for Python 3.9.11 compatibility
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
        grade_label.setFont(QFont("Poppins", 13, 75))  # 75 = Bold weight for Python 3.9.11 compatibility
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
            lbl.setFont(QFont("Poppins", 10, 75))  # 75 = Bold weight for Python 3.9.11 compatibility
            bar.setObjectName("progressBar")
            bar.setTextVisible(True)
            progress_layout.addWidget(lbl)
            progress_layout.addWidget(bar)

        main_layout.addWidget(progress_frame)

        # ============================
        # FACULTY NOTES SECTION
        # ============================
        notes_label = QLabel("Faculty Notes")
        notes_label.setFont(QFont("Poppins", 13, 75))  # 75 = Bold weight for Python 3.9.11 compatibility
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

        # ============================
        # SEND MESSAGE AREA
        # ============================
        send_frame = QFrame()
        send_frame.setObjectName("sendFrame")
        send_layout = QVBoxLayout(send_frame)
        send_layout.setContentsMargins(20, 15, 20, 15)
        send_layout.setSpacing(6)

        # Subject line
        self.subject_label = QLabel("Subject: Data Structures")
        self.subject_label.setObjectName("subjectLabel")
        send_layout.addWidget(self.subject_label)

        # Input + button
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.message_input = QTextEdit()
        self.message_input.setObjectName("messageInput")
        self.message_input.setPlaceholderText("Write a note or feedback for this student...")
        self.message_input.setFixedHeight(60)

        self.send_button = QPushButton("Send")
        self.send_button.setObjectName("sendNoteButton")
        self.send_button.setFixedSize(90, 36)
        self.send_button.clicked.connect(self.send_message)

        input_row.addWidget(self.message_input)
        input_row.addWidget(self.send_button)
        send_layout.addLayout(input_row)
        main_layout.addWidget(send_frame)

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
            print(f"⚠️ Notes file not found: {self.notes_file}")
            return

        try:
            with open(self.notes_file, "r", encoding="utf-8") as f:
                all_notes = json.load(f)

            self.notes_data = [n for n in all_notes if n.get("receiver") == self.student_id]
            self.display_notes()

        except Exception as e:
            print(f"❌ Error reading notes: {e}")

    # ---------------------------------------------------------
    def display_notes(self):
        for i in reversed(range(self.notes_layout.count())):
            widget = self.notes_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

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
    def send_message(self):
        message = self.message_input.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "Empty Message", "Please enter a message before sending.")
            return

        new_note = {
            "subject": "Data Structures",
            "faculty": self.faculty_name,
            "receiver": self.student_id,
            "message": message,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

        try:
            if os.path.exists(self.notes_file):
                with open(self.notes_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = []

            data.append(new_note)
            with open(self.notes_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

            self.message_input.clear()
            self.load_faculty_notes()
            print(f"📨 Note sent to {self.student_id}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save note: {e}")

    # ---------------------------------------------------------
    def reload_notes(self, path):
        self.load_faculty_notes()

    # ---------------------------------------------------------
    def handle_back(self):
        if callable(self.go_back_callback):
            self.go_back_callback()