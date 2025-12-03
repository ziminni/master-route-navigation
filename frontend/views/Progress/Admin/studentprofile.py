# frontend/views/Progress/Admin/studentprofile.py
import threading
import traceback
import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QProgressBar, QFrame, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont, QColor, QCursor


class StudentProfileWidget(QWidget):
    # Signals for thread-safe UI updates
    data_loaded = pyqtSignal(dict)
    show_error = pyqtSignal(str)
    show_not_found = pyqtSignal()
    show_unknown = pyqtSignal()

    def __init__(self, student_id, admin_name=None, go_back_callback=None, token=None, api_base="http://127.0.0.1:8000"):
        super().__init__()
        self.student_id = str(student_id).strip() if student_id else ""
        self.admin_name = admin_name
        self.go_back_callback = go_back_callback
        self.token = token or ""
        self.api_base = (api_base or "http://127.0.0.1:8000").rstrip("/")

        self.student_data = {}
        self.notes_data = []

        self.setObjectName("studentProfileWidget")
        self.init_ui()
        
        # Connect signals
        self.data_loaded.connect(self._update_ui_with_data)
        self.show_error.connect(self._show_error_message)
        self.show_not_found.connect(self._show_not_found_message)
        self.show_unknown.connect(self._show_unknown_user)

        # Ensure no invalid API request is made
        if self.student_id:
            self.load_student()
        else:
            self._show_unknown_user()

    def _headers(self):
        token = (self.token or "").strip()
        if not token:
            return {}
        if token.startswith("Bearer ") or token.startswith("Token "):
            token = token.split(" ", 1)[1]
        return {"Authorization": f"Bearer {token}"}


    def init_ui(self):
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

        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(15)

        # Avatar with better styling
        avatar = QLabel()
        avatar.setFixedSize(80, 80)
        avatar.setObjectName("studentAvatar")
        avatar.setStyleSheet("""
            QLabel#studentAvatar {
                background-color: #e9ecef;
                border-radius: 40px;
                border: 2px solid #155724;
                font-size: 24px;
                color: #155724;
                qproperty-alignment: AlignCenter;
            }
        """)
        avatar.setText("Img")  # Default avatar
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

        back_button = QPushButton("← Go Back")
        back_button.setObjectName("goBackButton")
        back_button.setFixedSize(120, 32)
        back_button.clicked.connect(self.handle_back)
        header_layout.addWidget(back_button)
        main_layout.addWidget(header_frame)

        # Grades section
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

        self.grade_table.setMinimumHeight(150)  # Set a decent minimum height
        self.grade_table.setMaximumHeight(500)  # Set a maximum to prevent excessive growth
        
        self.grade_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                gridline-color: #f1f1f1;
            }
            QTableWidget::item {
                padding: 10px;  /* Increased padding for better readability */
                border-bottom: 1px solid #f1f1f1;
            }
            QTableWidget::item:selected {
            }
            QHeaderView::section {
                padding: 12px 8px;  /* Increased header padding */
                border: none;
                border-bottom: 2px solid #dee2e6;
                font-weight: bold;
                font-family: "Poppins";
                font-size: 11px;
            }
            QHeaderView::section:hover {
            }
        """)
        
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
        self.grade_table.setColumnWidth(4, 100)  # Midterm (slightly wider)
        self.grade_table.setColumnWidth(5, 100)  # Finals (slightly wider)
        
        main_layout.addWidget(self.grade_table)

        # Progress section
        progress_frame = QFrame()
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setSpacing(10)
        progress_layout.setContentsMargins(0, 0, 0, 0)

        progress_label = QLabel("Degree Progress")
        progress_label.setFont(QFont("Poppins", 13, 75))
        main_layout.addWidget(progress_label)

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
                    height: 24px;  /* Slightly taller progress bars */
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

        # Create a frame for the notes section
        notes_frame = QFrame()
        notes_frame.setObjectName("notesFrame")
        notes_frame.setStyleSheet("""
            QFrame#notesFrame {
                border: none;
                background-color: transparent;
                min-height: 350px;
            }
        """)
        notes_layout = QVBoxLayout(notes_frame)
        notes_layout.setContentsMargins(0, 0, 0, 0)

        notes_scroll = QScrollArea()
        notes_scroll.setWidgetResizable(True)
        notes_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        notes_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        notes_scroll.setObjectName("facultyNotesScroll")
        notes_scroll.setMinimumHeight(350)
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

        main_layout.addWidget(notes_frame)
        main_layout.addStretch()

    def _show_unknown_user(self):
        self.name_label.setText("Student Not Found")
        self.id_label.setText(f"ID: {self.student_id}")
        self.course_label.setText("Course: Unknown")
        
        # Clear tables and progress bars
        self.grade_table.setRowCount(0)
        self._adjust_table_height()  # ✅ Call adjust height for empty state
        for bar in self.progress_bars.values():
            bar.setValue(0)
        
        # Show error in notes
        self._display_error_notes("Student profile not found or doesn't exist.")

    def _display_error_notes(self, message):
        """Display an error message in the notes section"""
        for i in reversed(range(self.notes_layout.count())):
            widget = self.notes_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        label = QLabel(message)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #dc3545; font-weight: bold; padding: 20px; font-size: 14px;")
        self.notes_layout.addWidget(label)
        self.notes_layout.addStretch()

    def load_student(self):
        url = f"{self.api_base}/api/progress/admin/student/{self.student_id}/profile/"

        def fetch():
            try:
                print(f"DEBUG: Fetching student profile from {url}")
                r = requests.get(url, headers=self._headers(), timeout=10)
                print(f"DEBUG: Response status: {r.status_code}")
                
                if r.status_code == 200:
                    data = r.json()
                    print(f"DEBUG: Received profile data")
                    
                    if isinstance(data, dict):
                        # Emit signal with data
                        self.data_loaded.emit(data)
                        return
                    else:
                        print(f"DEBUG: Unexpected response format: {type(data)}")
                        self.show_unknown.emit()
                elif r.status_code == 404:
                    print(f"DEBUG: Student not found (404)")
                    self.show_not_found.emit()
                else:
                    print(f"DEBUG: API error {r.status_code}: {r.text}")
                    self.show_unknown.emit()
                    
            except Exception as e:
                print(f"❌ Exception loading student: {e}")
                traceback.print_exc()
                self.show_error.emit(str(e))

        threading.Thread(target=fetch, daemon=True).start()

    @pyqtSlot(dict)
    def _update_ui_with_data(self, student_data):
        """Update UI with student data (runs on main thread)"""
        # Use try-except to handle potential object deletion
        try:
            s = student_data or {}
            
            print(f"DEBUG: Processing profile data on main thread")
            print(f"DEBUG: Full student data keys: {s.keys()}")
            
            # Extract name
            name = s.get("student_name") or s.get("name") or ""
            self.name_label.setText(name or "Unknown Student")
            
            # ID display
            student_id = s.get("student_id") or self.student_id
            self.id_label.setText(f"ID: {student_id}")
            
            # Course display
            course = s.get("course") or s.get("program") or ""
            self.course_label.setText(f"Course: {course}")

            # Populate grades
            grades = s.get("grades", [])
            print(f"DEBUG: Found {len(grades)} grades")
            self.populate_grades(grades)
            
            # Populate progress
            progress = s.get("progress", {})
            print(f"DEBUG: Progress data: {progress}")
            self._populate_progress(progress)
            
            # Populate notes
            notes = s.get("notes", [])
            print(f"DEBUG: Found {len(notes)} notes")
            self.notes_data = notes
            
            # Try to display notes, catch any errors
            self._display_notes()
            
        except RuntimeError as e:
            print(f"WARNING: Widget or layout was deleted, skipping UI update: {e}")
        except Exception as e:
            print(f"ERROR in _update_ui_with_data: {e}")
            traceback.print_exc()

    @pyqtSlot(str)
    def _show_error_message(self, error_msg):
        """Show error message (runs on main thread)"""
        QMessageBox.critical(self, "Error", f"Failed to load student profile: {error_msg}")
        self._show_unknown_user()

    @pyqtSlot()
    def _show_not_found_message(self):
        """Show student not found message (runs on main thread)"""
        QMessageBox.warning(self, "Not Found", f"Student with ID '{self.student_id}' not found.")
        self._show_unknown_user()

    def populate_grades(self, grades):
        self.grade_table.setRowCount(0)
        
        if not grades:
            # Show empty message
            self.grade_table.setRowCount(1)
            self.grade_table.setSpan(0, 0, 1, 6)
            empty_item = QTableWidgetItem("No grade records found")
            empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_item.setForeground(QColor("#6c757d"))
            empty_item.setFont(QFont("Poppins", 11))
            self.grade_table.setItem(0, 0, empty_item)
            self._adjust_table_height()
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
                item.setFont(QFont("Poppins", 10))
                
                # Highlight failed grades (assuming > 3.0 is failing)
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
        self._adjust_table_height()  # ✅ Adjust height after populating

    def _adjust_table_height(self):
        """Adjust table height based on number of rows - Enhanced Version"""
        row_count = self.grade_table.rowCount()

        if row_count == 0:
            # Empty state - show just header
            self.grade_table.setMinimumHeight(80)
            return
            
        # Calculate header height
        header_height = self.grade_table.horizontalHeader().height()
        
        # Calculate total row height
        total_row_height = 0
        for row in range(row_count):
            total_row_height += self.grade_table.rowHeight(row)
        
        # Add some padding and header
        total_height = header_height + total_row_height + 40  # Extra padding
        
        # Limit maximum height to prevent excessive scrolling
        max_height = 500
        if total_height > max_height:
            total_height = max_height
            # Enable vertical scrolling when content exceeds max height
            self.grade_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        else:
            # Disable scrollbar when all content fits
            self.grade_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.grade_table.setMinimumHeight(total_height)
        self.grade_table.setMaximumHeight(max_height)
        
        # Ensure the widget updates its layout
        self.updateGeometry()

    def _populate_progress(self, progress):
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

    def _display_notes(self):
        """Display faculty notes matching the design from facultynotes.py"""
        try:
            # Clear existing notes
            for i in reversed(range(self.notes_layout.count())):
                widget = self.notes_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()
        except RuntimeError as e:
            print(f"ERROR: Cannot clear notes: {e}")
            return

        print(f"DEBUG _display_notes: Processing {len(self.notes_data)} notes")
        
        if not self.notes_data:
            label = QLabel("No faculty notes available.")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("color: #6c757d; font-style: italic; padding: 30px;")
            self.notes_layout.addWidget(label)
            self.notes_layout.addStretch()
            return

        # Display notes in chronological order (oldest first)
        for note in self.notes_data:
            try:
                # Extract note data with fallbacks
                faculty = note.get("faculty", "Unknown")
                subject = note.get("subject", "General")
                message = note.get("message", "")
                
                # Format date
                date = note.get("date", "")
                if date:
                    formatted_date = date
                else:
                    formatted_date = "Unknown date"

                # Card Container (borderless - exact match from facultynotes.py)
                note_card = QFrame()
                note_card.setObjectName("noteCard")
                card_layout = QVBoxLayout(note_card)
                card_layout.setContentsMargins(0, 0, 0, 0)
                card_layout.setSpacing(0)

                # Header (subject + faculty) - exact match from facultynotes.py
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

                # Collapsible message body - exact match from facultynotes.py
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
                msg_layout.setContentsMargins(20, 12, 20, 12)
                msg_layout.setSpacing(8)

                # Message label with word wrap - exact match from facultynotes.py
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

                # Bottom bar (date) - exact match from facultynotes.py
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
                msg_layout.addLayout(bottom_bar)
                card_layout.addWidget(message_body)

                # Toggle visibility when header clicked
                header_btn.clicked.connect(lambda checked, body=message_body: body.setVisible(checked))

                self.notes_layout.addWidget(note_card)
                
            except Exception as e:
                print(f"ERROR creating note card: {e}")
                continue

        self.notes_layout.addStretch()
        print("DEBUG: Finished adding all notes")

    def handle_back(self):
        if callable(self.go_back_callback):
            self.go_back_callback()