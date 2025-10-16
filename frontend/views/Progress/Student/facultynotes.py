import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame,
    QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QCursor


class FacultyNotesWidget(QWidget):
    """Faculty Notes – polished UI with collapsible notes and modern styling."""
    def __init__(self):
        super().__init__()
        self.setObjectName("facultyNotesWidget")
        self.notes_data = self.load_notes_from_json()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 0, 10, 10)
        main_layout.setSpacing(10)

        header_label = QLabel("Faculty Notes")
        header_label.setFont(QFont("Poppins", 14, 75))  # 75 = Bold weight for Python 3.9.11 compatibility
        header_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(header_label)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setObjectName("facultyNotesScroll")
        main_layout.addWidget(scroll)

        # Scroll Content Container
        container = QWidget()
        self.notes_layout = QVBoxLayout(container)
        self.notes_layout.setContentsMargins(0, 0, 0, 0)
        self.notes_layout.setSpacing(0)
        scroll.setWidget(container)

        self.populate_notes()

    # ---------------------------------------------------------
    def load_notes_from_json(self):
        progress_dir = os.path.dirname(os.path.dirname(__file__))
        data_path = os.path.join(progress_dir, "data", "student_facultyNotes.json")
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading student_facultyNotes.json: {e}")
            return {}

    # ---------------------------------------------------------
    def populate_notes(self):
        self.clear_notes()

        if not self.notes_data:
            label = QLabel("No faculty notes available.")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.notes_layout.addWidget(label)
            return

        for semester, notes in self.notes_data.items():
            for note in notes:
                subject = note.get("subject", "Unknown Subject")
                faculty = note.get("faculty", "")
                message = note.get("message", "")
                date = note.get("date", "")

                # Card Container (borderless)
                note_card = QFrame()
                note_card.setObjectName("noteCard")
                card_layout = QVBoxLayout(note_card)
                card_layout.setContentsMargins(0, 0, 0, 0)
                card_layout.setSpacing(0)

                # Header (subject + faculty)
                header_btn = QPushButton(f"{subject} – {faculty}")
                header_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                header_btn.setCheckable(True)
                header_btn.setChecked(False)
                header_btn.setObjectName("noteHeaderBtn")
                card_layout.addWidget(header_btn)

                # Collapsible message body
                message_body = QFrame()
                message_body.setVisible(False)
                message_body.setObjectName("noteMessageBody")
                msg_layout = QVBoxLayout(message_body)
                msg_layout.setContentsMargins(20, 12, 20, 12)
                msg_layout.setSpacing(8)

                msg_label = QLabel(message)
                msg_label.setWordWrap(True)
                msg_label.setFont(QFont("Poppins", 10))
                msg_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
                msg_label.setObjectName("noteMessageLabel")
                msg_layout.addWidget(msg_label)

                # Bottom bar (date + delete)
                bottom_bar = QHBoxLayout()
                bottom_bar.setContentsMargins(0, 10, 0, 0)

                date_label = QLabel(date)
                date_label.setFont(QFont("Poppins", 9))
                date_label.setObjectName("noteFooterLabel")
                bottom_bar.addWidget(date_label)

                bottom_bar.addStretch()

                delete_btn = QPushButton("Delete")
                delete_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                delete_btn.setObjectName("deleteNoteButton")
                bottom_bar.addWidget(delete_btn)

                msg_layout.addLayout(bottom_bar)
                card_layout.addWidget(message_body)

                # Toggle visibility when header clicked
                header_btn.clicked.connect(lambda checked, body=message_body: body.setVisible(checked))

                self.notes_layout.addWidget(note_card)

        self.notes_layout.addStretch()

    # ---------------------------------------------------------
    def clear_notes(self):
        while self.notes_layout.count():
            child = self.notes_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()