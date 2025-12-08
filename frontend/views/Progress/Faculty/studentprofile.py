# frontend/views/Progress/Faculty/studentprofile.py
import threading
import traceback
import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QProgressBar, QTextEdit, QFrame, QScrollArea, 
    QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtGui import QFont, QColor, QCursor

from .base import FacultyAPIClient


class StudentProfileWidget(QWidget):
    """
    Faculty view of a specific student's profile with API integration.
    Allows faculty to view grades, progress, and send notes to students.
    """
    
    profile_loaded = pyqtSignal(dict)  # Signal when profile data is loaded
    note_sent = pyqtSignal()  # ✅ Signal for when note is sent
    
    def __init__(self, student_id, faculty_name=None, go_back_callback=None, 
                 parent_stack=None, token=None, api_base="http://127.0.0.1:8000"):
        super().__init__()
        
        self.student_id = str(student_id).strip() if student_id else ""
        self.faculty_name = faculty_name
        self.go_back_callback = go_back_callback
        self.parent_stack = parent_stack
        
        self.student_data = {}
        self.notes_data = []
        self.grades_list = []  # Store grades for subject dropdown
        
        self.api_client = FacultyAPIClient(token, api_base)
        
        # Connect API client signals
        self.api_client.api_error.connect(self._on_api_error)
        self.api_client.show_message.connect(self._on_show_message)
        
        # Connect local signals
        self.profile_loaded.connect(self._on_profile_loaded)
        self.note_sent.connect(self._on_note_sent)  # ✅ Connect the signal

        self.setObjectName("studentProfileWidget")
        self.init_ui()
        
        # Load data - ONLY load profile, notes come with it
        if self.student_id:
            self.load_student_profile()
        else:
            self._show_unknown_user()

    # ---------------------------------------------------------
    def init_ui(self):
        # Scrollable root
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

        # Avatar
        avatar = QLabel()
        avatar.setFixedSize(80, 80)
        avatar.setObjectName("studentAvatar")
        avatar.setStyleSheet("""
            QLabel#studentAvatar {
                border-radius: 40px;
                border: 2px solid #155724;
                font-size: 24px;
                qproperty-alignment: AlignCenter;
            }
        """)
        avatar.setText("👨‍🎓")  # Default avatar
        header_layout.addWidget(avatar)

        # Student info
        self.name_label = QLabel("Loading...")
        self.name_label.setFont(QFont("Poppins", 16, 75))
        self.id_label = QLabel(f"ID: {self.student_id}")
        self.id_label.setFont(QFont("Poppins", 12))
        self.course_label = QLabel("Course: Loading...")
        self.course_label.setFont(QFont("Poppins", 12))

        info_layout = QVBoxLayout()
        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.id_label)
        info_layout.addWidget(self.course_label)
        header_layout.addLayout(info_layout)
        header_layout.addStretch()

        # Back button
        back_button = QPushButton("← Go Back")
        back_button.setObjectName("goBackButton")
        back_button.setFixedSize(120, 32)
        back_button.clicked.connect(self.handle_back)
        header_layout.addWidget(back_button)
        main_layout.addWidget(header_frame)

        # ============================
        # GRADES SECTION
        # ============================
        grade_label = QLabel("Student Grades")
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
        
        # ✅ Fix: Set minimum height for the table to make it visible
        # self.grade_table.setMinimumHeight(200)  # Minimum 200px height
        # self.grade_table.setMaximumHeight(400)  # Maximum 400px height
        
        self.grade_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f1f1f1;
            }
            QTableWidget::item:selected {
                background-color: #e9ecef;
            }
            QHeaderView::section {
                padding: 10px;
                border: none;
                border-bottom: 2px solid #dee2e6;
                font-weight: bold;
            }
        """)
        
        # ✅ Fix: Set proper header resize modes
        header = self.grade_table.horizontalHeader()
        header.setDefaultSectionSize(120)  # Default column width
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # No. column fixed
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Subject Code stretches
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Description stretches
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Units fixed
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Midterm fixed
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Finals fixed
        
        # Set specific widths for fixed columns
        self.grade_table.setColumnWidth(0, 50)   # No.
        self.grade_table.setColumnWidth(3, 70)   # Units
        self.grade_table.setColumnWidth(4, 80)   # Midterm
        self.grade_table.setColumnWidth(5, 80)   # Finals
        
        main_layout.addWidget(self.grade_table)

        # ============================
        # DEGREE PROGRESS
        # ============================
        progress_label = QLabel("Degree Progress")
        progress_label.setFont(QFont("Poppins", 13, 75))
        main_layout.addWidget(progress_label)

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
            container = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setFont(QFont("Poppins", 10, 75))
            lbl.setFixedWidth(150)
            bar.setObjectName("progressBar")
            bar.setTextVisible(True)
            bar.setFormat("%p%")
            bar.setValue(0)
            bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #dee2e6;
                    border-radius: 3px;
                    text-align: center;
                    height: 20px;
                }
                QProgressBar::chunk {
                    background-color: #28a745;
                    border-radius: 3px;
                }
            """)
            container.addWidget(lbl)
            container.addWidget(bar)
            progress_layout.addLayout(container)

        main_layout.addWidget(progress_frame)

        # ============================
        # FACULTY NOTES SECTION
        # ============================
        notes_label = QLabel("Faculty Notes")
        notes_label.setFont(QFont("Poppins", 13, 75))
        main_layout.addWidget(notes_label)

        notes_frame = QFrame()
        notes_frame.setObjectName("notesFrame")
        notes_frame.setStyleSheet("""
            QFrame#notesFrame {
                border: none;
                background-color: transparent;
                min-height: 200px;
            }
        """)
        notes_layout = QVBoxLayout(notes_frame)
        notes_layout.setContentsMargins(0, 0, 0, 0)

        notes_scroll = QScrollArea()
        notes_scroll.setWidgetResizable(True)
        notes_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        notes_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        notes_scroll.setObjectName("facultyNotesScroll")
        notes_scroll.setMinimumHeight(200)
        notes_scroll.setStyleSheet("""
            QScrollArea#facultyNotesScroll {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #f8f9fa;
                width: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #ced4da;
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #adb5bd;
            }
        """)
        notes_layout.addWidget(notes_scroll)

        # Scroll Content Container
        self.notes_container = QWidget()
        self.notes_layout = QVBoxLayout(self.notes_container)
        self.notes_layout.setContentsMargins(0, 0, 0, 0)
        self.notes_layout.setSpacing(0)
        notes_scroll.setWidget(self.notes_container)
        notes_layout.addWidget(notes_scroll)

        main_layout.addWidget(notes_frame)

        # ============================
        # SEND MESSAGE AREA
        # ============================
        send_frame = QFrame()
        send_frame.setObjectName("sendFrame")
        send_frame.setStyleSheet("""
            QFrame#sendFrame {
                border-radius: 8px;
                border: 1px solid #dee2e6;
            }
        """)
        send_layout = QVBoxLayout(send_frame)
        send_layout.setContentsMargins(20, 15, 20, 15)
        send_layout.setSpacing(10)

        # Subject dropdown
        subject_label = QLabel("Select Subject:")
        subject_label.setFont(QFont("Poppins", 10, 75))
        send_layout.addWidget(subject_label)

        self.subject_combo = QComboBox()
        self.subject_combo.setObjectName("subjectCombo")
        self.subject_combo.setStyleSheet("""
            QComboBox#subjectCombo {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 6px 10px;
                font-family: "Poppins";
                font-size: 12px;
                min-height: 28px;
            }
            QComboBox#subjectCombo:hover {
            }
            QComboBox#subjectCombo:focus {
                outline: none;
            }
            QComboBox#subjectCombo::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox#subjectCombo::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #495057;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 1px solid #ced4da;
                border-radius: 4px;
                selection-background-color: #e9ecef;
                selection-color: #212529;
                font-family: "Poppins";
                font-size: 12px;
            }
        """)
        self.subject_combo.addItem("General Feedback")  # Default
        send_layout.addWidget(self.subject_combo)

        # Message input
        input_label = QLabel("Your Message:")
        input_label.setFont(QFont("Poppins", 10, 75))
        send_layout.addWidget(input_label)
        
        self.message_input = QTextEdit()
        self.message_input.setObjectName("messageInput")
        self.message_input.setPlaceholderText("Write a note or feedback for this student...")
        self.message_input.setFixedHeight(80)
        self.message_input.setStyleSheet("""
            QTextEdit#messageInput {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px;
                font-family: "Poppins";
                font-size: 12px;
                background-color: white;
            }
        """)
        send_layout.addWidget(self.message_input)

        # Send button
        self.send_button = QPushButton("Send Message")
        self.send_button.setObjectName("sendNoteButton")
        self.send_button.setFixedHeight(40)
        self.send_button.setStyleSheet("""
            QPushButton#sendNoteButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-family: "Poppins";
            }
            QPushButton#sendNoteButton:hover {
                background-color: #218838;
            }
            QPushButton#sendNoteButton:pressed {
                background-color: #1e7e34;
            }
        """)
        self.send_button.clicked.connect(self.send_faculty_note)
        send_layout.addWidget(self.send_button)

        main_layout.addWidget(send_frame)
        main_layout.addStretch()

    # ---------------------------------------------------------
    def load_student_profile(self):
        """Load student profile from backend API - FACULTY SPECIFIC"""
        endpoint = f"/api/progress/faculty/student/{self.student_id}/profile/"
        
        def handle_response(data):
            self.profile_loaded.emit(data)
        
        self.api_client.api_get(endpoint, callback=handle_response)

    @pyqtSlot(dict)
    def _on_profile_loaded(self, student_data):
        """Handle loaded student profile"""
        print(f"DEBUG [Faculty]: Profile loaded: {student_data.keys() if isinstance(student_data, dict) else 'No data'}")
        
        self.student_data = student_data or {}
        
        if "detail" in self.student_data:
            # Error response
            error_msg = self.student_data["detail"]
            print(f"DEBUG [Faculty]: Error in profile: {error_msg}")
            self.api_client.api_error.emit(error_msg)
            return
        
        # Update UI
        name = self.student_data.get("student_name") or self.student_data.get("name") or "Unknown"
        self.name_label.setText(name)
        
        student_id = self.student_data.get("student_id") or self.student_id
        self.id_label.setText(f"ID: {student_id}")
        
        course = self.student_data.get("course") or self.student_data.get("program") or "Unknown"
        self.course_label.setText(f"Course: {course}")

        # Populate grades
        grades = self.student_data.get("grades", [])
        print(f"DEBUG [Faculty]: Found {len(grades)} grades")
        self.grades_list = grades
        self.populate_grades(grades)
        
        # Populate subject dropdown
        self.populate_subject_combo(grades)
        
        # Populate progress
        progress = self.student_data.get("progress", {})
        print(f"DEBUG [Faculty]: Progress data: {progress}")
        self.populate_progress(progress)
        
        # Get notes from the profile response
        notes = self.student_data.get("notes", [])
        print(f"DEBUG [Faculty]: Found {len(notes)} notes in profile response")
        self.notes_data = notes
        
        # Display notes
        self.display_notes()
        
        # After populating grades, adjust table height
        self._adjust_table_height()

    # def _adjust_table_height(self):
    #     """Adjust table height based on number of rows"""
    #     row_count = self.grade_table.rowCount()
    #     if row_count == 0:
    #         self.grade_table.setMinimumHeight(60)  # Just header
    #     else:
    #         # Calculate height: header + rows (each ~40px)
    #         height = 40 + (row_count * 40)
    #         # Set reasonable limits
    #         height = max(100, min(400, height))
    #         self.grade_table.setMinimumHeight(height)
    
    def _adjust_table_height(self):
        """Ensure table has reasonable minimum height"""
        row_count = self.grade_table.rowCount()

        if row_count == 0:
            # Just show header for empty state
            self.grade_table.setMinimumHeight(50)
            return
            
        # Auto-size rows to content
        self.grade_table.resizeRowsToContents()
        
        # Calculate total height needed
        total_height = self.grade_table.horizontalHeader().height()
        for row in range(row_count):
            total_height += self.grade_table.rowHeight(row)
        
        # Add some padding (10px top/bottom)
        total_height += 70
        
        # Set minimum to ensure all content is visible
        self.grade_table.setMinimumHeight(total_height)
        
        # Also update the scroll area if needed
        self.updateGeometry()

    @pyqtSlot(str)
    def _on_api_error(self, error_msg):
        """Handle API errors"""
        print(f"ERROR [Faculty]: API error: {error_msg}")
        QMessageBox.warning(self, "Error", error_msg)

    @pyqtSlot(str, str)
    def _on_show_message(self, title, message):
        """Show message dialog"""
        QMessageBox.information(self, title, message)

    # ---------------------------------------------------------
    def populate_grades(self, grades):
        """Populate grades table"""
        self.grade_table.setRowCount(0)
        
        if not grades:
            # Show empty message
            self.grade_table.setRowCount(1)
            self.grade_table.setSpan(0, 0, 1, 6)
            empty_item = QTableWidgetItem("No grade records found")
            empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_item.setForeground(QColor("#6c757d"))
            self.grade_table.setItem(0, 0, empty_item)
            return

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
                
                # Highlight failed grades
                if col in [4, 5]:  # Midterm and Finals columns
                    try:
                        grade_val = float(val)
                        if grade_val > 3.0:
                            item.setForeground(QColor("#dc3545"))
                            font = item.font()
                            font.setBold(True)
                            item.setFont(font)
                        elif grade_val <= 1.5:
                            item.setForeground(QColor("#28a745"))
                    except ValueError:
                        pass
                
                self.grade_table.setItem(i - 1, col, item)
        
        self.grade_table.resizeRowsToContents()

    # ---------------------------------------------------------
    def populate_subject_combo(self, grades):
        """Populate subject dropdown with student's subjects"""
        self.subject_combo.clear()
        self.subject_combo.addItem("General Feedback")  # Default
        
        for grade in grades:
            subject_code = grade.get("subject_code", "")
            subject_desc = grade.get("description", "")
            if subject_code:
                display_text = f"{subject_code}"
                if subject_desc:
                    display_text += f" - {subject_desc[:30]}..."
                self.subject_combo.addItem(display_text)

    # ---------------------------------------------------------
    def populate_progress(self, progress):
        """Populate progress bars"""
        if not progress:
            progress = {
                "Core Courses": 0,
                "Electives": 0,
                "Capstone Project": 0,
                "Internship": 0,
                "General Education": 0
            }
        
        for key, bar in self.progress_bars.items():
            try:
                value = progress.get(key)
                if value is None:
                    # Try different key formats
                    for alt_key in [key.lower(), key.replace(" ", "_").lower(), key.replace(" ", "").lower()]:
                        if alt_key in progress:
                            value = progress[alt_key]
                            break
                
                if value is not None:
                    value = max(0, min(100, int(value)))
                    bar.setValue(value)
                else:
                    bar.setValue(0)
            except (ValueError, TypeError) as e:
                print(f"Error setting progress for {key}: {e}")
                bar.setValue(0)

    # ---------------------------------------------------------
    def display_notes(self):
        """Display faculty notes"""
        # Clear existing notes
        for i in reversed(range(self.notes_layout.count())):
            widget = self.notes_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        print(f"DEBUG [Faculty]: Displaying {len(self.notes_data)} notes")
        
        if not self.notes_data:
            label = QLabel("No faculty notes available.")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("color: #6c757d; font-style: italic; padding: 30px;")
            self.notes_layout.addWidget(label)
            self.notes_layout.addStretch()
            return

        # Display notes in chronological order (newest first - most common UX)
        for note in self.notes_data:
            try:
                # Extract note data with fallbacks - match backend response format
                faculty = note.get("faculty", note.get("faculty_name", "Unknown"))
                subject = note.get("subject", "General Feedback")
                message = note.get("message", "")
                
                # Format date - check different possible date fields
                date = note.get("date_sent") or note.get("date") or note.get("created_at") or ""
                if date and isinstance(date, str):
                    try:
                        from datetime import datetime
                        # Handle ISO format date
                        dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
                        formatted_date = dt.strftime("%b %d, %Y %I:%M %p")
                    except:
                        formatted_date = date
                else:
                    formatted_date = "Unknown date"

                # Card Container
                note_card = QFrame()
                note_card.setObjectName("noteCard")
                note_card.setStyleSheet("""
                    QFrame#noteCard {
                        border: 1px solid #dee2e6;
                        border-radius: 8px;
                        margin: 5px 0px;
                    }
                """)
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

                # Message label
                msg_label = QLabel(message)
                msg_label.setWordWrap(True)
                msg_label.setFont(QFont("Poppins", 10))
                msg_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
                msg_label.setObjectName("noteMessageLabel")
                msg_label.setStyleSheet("""
                    QLabel#noteMessageLabel {
                        font-size: 12px;
                        font-family: "Poppins";
                        text-align: left;
                        line-height: 1.4;
                    }
                """)
                msg_layout.addWidget(msg_label)

                # Bottom bar (date)
                bottom_bar = QHBoxLayout()
                bottom_bar.setContentsMargins(0, 10, 0, 0)

                date_label = QLabel(formatted_date)
                date_label.setFont(QFont("Poppins", 9))
                date_label.setObjectName("noteFooterLabel")
                date_label.setStyleSheet("""
                    QLabel#noteFooterLabel {
                        color: #6c757d;
                        font-size: 11px;
                        font-family: "Poppins";
                        font-style: italic;
                    }
                """)
                bottom_bar.addWidget(date_label)
                bottom_bar.addStretch()
                msg_layout.addLayout(bottom_bar)
                card_layout.addWidget(message_body)

                # Toggle visibility when header clicked
                header_btn.clicked.connect(lambda checked, body=message_body: body.setVisible(checked))

                self.notes_layout.addWidget(note_card)
                
            except Exception as e:
                print(f"ERROR creating note card: {e}")
                continue

        self.notes_layout.addStretch()

    # ---------------------------------------------------------
    def send_faculty_note(self):
        """Send faculty note to student via API - FACULTY SPECIFIC"""
        message = self.message_input.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "Warning", "Please enter a message before sending.")
            return
        
        # Get selected subject and find grade_id
        subject_text = self.subject_combo.currentText()
        grade_id = None
        
        if subject_text != "General Feedback":
            # Extract subject code from dropdown text
            subject_code = subject_text.split(" - ")[0] if " - " in subject_text else subject_text
            
            # Find matching grade in grades list
            for grade in self.grades_list:
                if grade.get("subject_code", "") == subject_code:
                    grade_id = grade.get("id")  # This should be grade_id from backend
                    break
        
        # Try to get the user_id from student_data (backend now returns user_id)
        student_identifier = self.student_id  # Default to institutional ID
        
        # Check if we have user_id in the student data
        if self.student_data:
            # Try user_id first (numeric ID)
            if "user_id" in self.student_data:
                student_identifier = self.student_data.get("user_id")
            # Try id field
            elif "id" in self.student_data and isinstance(self.student_data.get("id"), int):
                student_identifier = self.student_data.get("id")
        
        print(f"DEBUG [Faculty]: Student identifier to send: {student_identifier} (type: {type(student_identifier)})")
        print(f"DEBUG [Faculty]: Grade ID: {grade_id}")
        print(f"DEBUG [Faculty]: Message: '{message}'")
        
        # Prepare API payload
        note_data = {
            "student": str(student_identifier),  # Ensure it's a string
            "message": message
        }
        
        # Only add grade if it's not None
        if grade_id is not None:
            note_data["grade"] = grade_id
        
        print(f"DEBUG [Faculty]: Full note data: {note_data}")
        
        # Send via FACULTY-specific API
        endpoint = "/api/progress/faculty/feedback/send/"
        
        def handle_response(response_data):
            print(f"DEBUG [Faculty]: Note sent successfully: {response_data}")
            # ✅ Emit signal for thread-safe UI update
            self.note_sent.emit()
        
        self.api_client.api_post(endpoint, note_data, callback=handle_response)

    @pyqtSlot()
    def _on_note_sent(self):
        """Handle note sent - runs in main thread"""
        try:
            # Clear the message input
            self.message_input.clear()
            
            # Show success message
            # QMessageBox.information(self, "Success", "Message sent to student successfully.")
            
            # ✅ Force immediate reload with visual feedback
            self._show_loading_message("Refreshing notes...")
            
            # Reload profile after a short delay
            QTimer.singleShot(100, self.load_student_profile)
            
        except Exception as e:
            print(f"Error in _on_note_sent: {e}")
            # Even if UI update fails, note was sent successfully

    def _show_loading_message(self, message):
        """Show loading message in notes section"""
        # Clear existing notes
        for i in reversed(range(self.notes_layout.count())):
            widget = self.notes_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # Show loading message
        label = QLabel(message)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #6c757d; font-style: italic; padding: 30px;")
        self.notes_layout.addWidget(label)
        self.notes_layout.addStretch()

    # ---------------------------------------------------------
    def _show_unknown_user(self):
        """Show unknown user state"""
        self.name_label.setText("Student Not Found")
        self.id_label.setText(f"ID: {self.student_id}")
        self.course_label.setText("Course: Unknown")
        
        # Clear tables and progress bars
        self.grade_table.setRowCount(0)
        self._adjust_table_height()
        for bar in self.progress_bars.values():
            bar.setValue(0)
        
        # Show error in notes
        self._display_error_notes("Student profile not found.")

    def _display_error_notes(self, message):
        """Display error message in notes section"""
        for i in reversed(range(self.notes_layout.count())):
            widget = self.notes_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        label = QLabel(message)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #dc3545; font-weight: bold; padding: 20px; font-size: 14px;")
        self.notes_layout.addWidget(label)
        self.notes_layout.addStretch()

    # ---------------------------------------------------------
    def handle_back(self):
        """Go back to previous page"""
        if self.parent_stack and callable(self.go_back_callback):
            # Remove this widget from stack
            self.parent_stack.removeWidget(self)
            # Call the callback to show previous page
            self.go_back_callback()
        elif callable(self.go_back_callback):
            self.go_back_callback()