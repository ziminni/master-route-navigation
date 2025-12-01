# frontend/views/Progress/Student/facultynotes.py
import threading
import traceback
import requests

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame,
    QPushButton, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont, QCursor


class FacultyNotesWidget(QWidget):
    """Faculty Notes – polished UI with collapsible notes and modern styling."""
    notes_loaded = pyqtSignal(list)   # emits list of notes
    notify = pyqtSignal(str, str)     # emits (title, message)

    def __init__(self, token=None, api_base="http://127.0.0.1:8000", role="student"):
        super().__init__()
        self.token = token or ""
        self.api_base = api_base.rstrip("/")
        self.role = role
        self.notes_data = []
        self.current_semester = None

        self.setObjectName("facultyNotesWidget")
        self.init_ui()

        # connect signals
        self.notes_loaded.connect(self._on_notes_loaded_slot)
        self.notify.connect(self._show_notify_slot)

    # ---------------------------------------------
    def set_token(self, token):
        self.token = token or ""
        if self.token:
            self.load_notes_async()

    def set_role(self, role):
        self.role = role or "student"

    # ---------------------------------------------
    def init_ui(self):
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
        self.container = QWidget()
        self.notes_layout = QVBoxLayout(self.container)
        self.notes_layout.setContentsMargins(0, 0, 0, 0)
        self.notes_layout.setSpacing(0)
        scroll.setWidget(self.container)

    # ---------------------------------------------
    def _build_headers(self):
        token = (self.token or "").strip()
        if not token:
            return {}
        if token.startswith("Bearer ") or token.startswith("Token "):
            token = token.split(" ", 1)[1]
        return {"Authorization": f"Bearer {token}"}

    # ---------------------------------------------
    def load_notes_async(self):
        """Load faculty notes for the student"""
        url = f"{self.api_base}/api/progress/student/messages/"
        headers = self._build_headers()

        def fetch():
            try:
                r = requests.get(url, headers=headers, timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    # Backend returns list of messages
                    if isinstance(data, list):
                        self.notes_loaded.emit(data)
                    else:
                        self.notes_loaded.emit([])
                else:
                    self.notes_loaded.emit([])
            except Exception:
                traceback.print_exc()
                self.notes_loaded.emit([])

        threading.Thread(target=fetch, daemon=True).start()

    @pyqtSlot(list)
    def _on_notes_loaded_slot(self, notes):
        """Display faculty notes in the old UI format"""
        self.notes_data = notes or []
        self.populate_notes()

    # ---------------------------------------------------------
    def populate_notes(self):
        self.clear_notes()

        if not self.notes_data:
            label = QLabel("No faculty notes available.")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("color: #6c757d; font-style: italic; padding: 30px;")
            self.notes_layout.addWidget(label)
            self.notes_layout.addStretch()
            return

        # Display notes in reverse order (newest first)
        for note in reversed(self.notes_data):
            # Extract note data with fallbacks
            faculty = note.get("faculty_name", note.get("faculty", "Unknown"))
            
            # Get subject/course from grade_simple or directly
            subject = "General"
            if isinstance(note.get("grade_simple"), dict):
                subject = note.get("grade_simple", {}).get("course_code", "General")
            elif note.get("subject"):
                subject = note.get("subject")
            
            message = note.get("message", "")
            
            # Format date
            date = note.get("date_sent", "")
            if date and isinstance(date, str):
                # Try to parse and format date
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    formatted_date = dt.strftime("%b %d, %Y %I:%M %p")
                except:
                    formatted_date = date
            else:
                formatted_date = "Unknown date"

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
            header_btn.setStyleSheet("""
                QPushButton#noteHeaderBtn {
                    text-align: left;
                    padding: 12px 15px;
                    border: none;
                    font-family: "Poppins";
                    font-size: 11px;
                    font-weight: bold;
                    border-radius: 8px 8px 0 0;
                }
                QPushButton#noteHeaderBtn:checked {
                    border-bottom: 1px solid #dee2e6;
                }
                QPushButton#noteHeaderBtn:hover {
                }
            """)
            card_layout.addWidget(header_btn)

            # Collapsible message body
            message_body = QFrame()
            message_body.setVisible(False)
            message_body.setObjectName("noteMessageBody")
            message_body.setStyleSheet("""
                QFrame#noteMessageBody {
                    background-color: white;
                    border-radius: 0 0 8px 8px;
                    padding: 0;
                }
            """)
            msg_layout = QVBoxLayout(message_body)
            msg_layout.setContentsMargins(15, 12, 15, 12)
            msg_layout.setSpacing(8)

            # Message label with word wrap
            msg_label = QLabel(message)
            msg_label.setWordWrap(True)
            msg_label.setFont(QFont("Poppins", 10))
            msg_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            msg_label.setObjectName("noteMessageLabel")
            msg_label.setStyleSheet("""
                QLabel#noteMessageLabel {
                    color: #222;
                    font-size: 12px;
                    font-family: "Poppins";
                    text-align: left;
                    line-height: 1.4;
                }
            """)
            msg_layout.addWidget(msg_label)

            # Bottom bar (date + delete button)
            bottom_bar = QHBoxLayout()
            bottom_bar.setContentsMargins(0, 10, 0, 0)

            date_label = QLabel(formatted_date)
            date_label.setFont(QFont("Poppins", 9))
            date_label.setObjectName("noteFooterLabel")
            date_label.setStyleSheet("""
                QLabel#noteFooterLabel {
                    color: #666;
                    font-size: 11px;
                    font-family: "Poppins";
                }
            """)
            bottom_bar.addWidget(date_label)

            bottom_bar.addStretch()

            # Add delete button for all users (student can delete their own notes)
            note_id = note.get("id")
            if note_id:  # Only show delete if we have a valid note ID
                delete_btn = QPushButton("Delete")
                delete_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                delete_btn.setObjectName("deleteNoteButton")
                delete_btn.setStyleSheet("""
                    QPushButton#deleteNoteButton {
                        background-color: #dc3545;
                        color: white;
                        border: none;
                        padding: 4px 12px;
                        border-radius: 4px;
                        font-size: 11px;
                    }
                    QPushButton#deleteNoteButton:hover {
                        background-color: #c82333;
                    }
                """)
                # Connect delete button to delete function
                delete_btn.clicked.connect(lambda checked, nid=note_id: self.confirm_delete_note(nid))
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

    # ---------------------------------------------
    def confirm_delete_note(self, note_id):
        """Show confirmation dialog before deleting note"""
        if not note_id:
            return
        
        reply = QMessageBox.question(
            self, 
            "Delete Note", 
            "Are you sure you want to delete this note?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_note(note_id)

    # ---------------------------------------------
    def delete_note(self, note_id):
        """Delete a note (students can delete notes sent to them)"""
        if not note_id:
            return
        
        url = f"{self.api_base}/api/progress/student/messages/{note_id}/delete/"
        headers = self._build_headers()

        def delete():
            try:
                r = requests.delete(url, headers=headers, timeout=15)
                if r.status_code == 204:
                    self.notify.emit("Success", "Note deleted successfully.")
                    # Reload notes after deletion
                    self.load_notes_async()
                elif r.status_code == 403:
                    self.notify.emit("Error", "You don't have permission to delete this note.")
                else:
                    self.notify.emit("Error", f"Failed to delete note. Status: {r.status_code}")
            except Exception as e:
                traceback.print_exc()
                self.notify.emit("Error", f"Failed to delete note: {str(e)}")

        threading.Thread(target=delete, daemon=True).start()

    # ---------------------------------------------
    @pyqtSlot(str, str)
    def _show_notify_slot(self, title, msg):
        QMessageBox.information(self, title, msg)

    # ---------------------------------------------
    def set_semester(self, semester):
        """Semester change - reload notes if needed"""
        self.current_semester = semester
        if self.token:
            self.load_notes_async()