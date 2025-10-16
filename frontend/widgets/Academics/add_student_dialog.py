from PyQt6 import uic
from PyQt6.QtWidgets import (QDialog, QMessageBox, QTableWidgetItem, 
                                QListWidgetItem, QHBoxLayout, QPushButton, QWidget)
from PyQt6.QtCore import Qt

# Add import for BulkUploadDialog at the top with proper error handling
try:
    from bulk_upload_dialog import BulkUploadDialog
    BULK_UPLOAD_AVAILABLE = True
except ImportError:
    try:
        from frontend.widgets.Academics.bulk_upload_dialog import BulkUploadDialog
        BULK_UPLOAD_AVAILABLE = True
    except ImportError:
        try:
            from widgets.Academics.bulk_upload_dialog import BulkUploadDialog
            BULK_UPLOAD_AVAILABLE = True
        except ImportError:
            BULK_UPLOAD_AVAILABLE = False
            print("BulkUploadDialog not found - bulk upload feature disabled")

class AddStudentDialog(QDialog):
    """
    Independent Add Student Dialog - Matches provided UI design
    
    Flow:
    1. User types ID or name in search box
    2. Suggestions appear below search bar (autocomplete style)
    3. Click "+" button next to suggestion to add to table
    4. Students appear in the table ready to enroll
    5. Click "Enroll" to save all students
    """
    
    # ==================== DUMMY DATABASE ====================
    # Simulates database of all students in the school
    STUDENT_DATABASE = [
        {"id": "2022301", "name": "Castro, Carlos Fidel", "year": "3"},
        {"id": "20223011108", "name": "Castro, Carlos Fidel", "year": "3"},
        {"id": "20223011223", "name": "Buntoyan, Earlyd", "year": "2"},
        {"id": "20223010045", "name": "Dela Cruz, Juan", "year": "1"},
        {"id": "20223010156", "name": "Santos, Maria", "year": "2"},
        {"id": "20223010267", "name": "Reyes, Pedro", "year": "3"},
        {"id": "20223010378", "name": "Garcia, Ana", "year": "1"},
        {"id": "20223010489", "name": "Mendoza, Jose", "year": "4"},
        {"id": "20223010590", "name": "Lee, Mark", "year": "2"},
        {"id": "20223010691", "name": "Raj, Lara", "year": "3"},
        {"id": "20223010792", "name": "Smith, Jane", "year": "1"},
    ]
    
    # Simulates enrolled students table in database
    ENROLLED_STUDENTS = []
    
    def __init__(self):
        """Initialize the dialog"""
        super().__init__()

        import os
        from PyQt6 import uic

        # Try multiple possible paths for the UI file
        possible_paths = [
            os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "ui", "Academics", "Enrollment", "add_student_dialog.ui")),
            os.path.normpath(os.path.join(os.path.dirname(__file__), "ui", "Academics", "Enrollment", "add_student_dialog.ui")),
            os.path.normpath(os.path.join(os.path.dirname(__file__), "add_student_dialog.ui")),
            "frontend/ui/Academics/Enrollment/add_student_dialog.ui",
            "ui/Academics/Enrollment/add_student_dialog.ui",
            "ui/Academics/Enrollment/add_student_dialog.ui",
        ]
        
        ui_path = None
        for path in possible_paths:
            if os.path.exists(path):
                ui_path = path
                print(f"Found UI file at: {ui_path}")
                break
        
        if ui_path is None:
            # Create a basic dialog programmatically if UI file not found
            print("UI file not found, creating basic dialog programmatically")
            self.setup_basic_dialog()
            return
        
        try:
            uic.loadUi(ui_path, self)
        except Exception as e:
            print(f"Error loading UI file: {e}")
            # Fallback to basic dialog
            self.setup_basic_dialog()
            return

        self.students_to_enroll = []
        self.suggestion_widgets = []

        # Setup components
        self._setup_table()
        self._connect_signals()
        self._hide_suggestions()
        self._update_count_label()

    def setup_basic_dialog(self):
        """Setup a basic dialog programmatically if UI file is not found"""
        from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QTableWidget, QTableWidgetItem
        
        self.setWindowTitle("Add Students")
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # Search area
        search_layout = QHBoxLayout()
        self.searchLineEdit = QLineEdit()
        self.searchLineEdit.setPlaceholderText("Search students by ID or name...")
        search_layout.addWidget(self.searchLineEdit)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.cancelButton = QPushButton("Cancel")
        self.enrollButton = QPushButton("Enroll")
        button_layout.addWidget(self.cancelButton)
        button_layout.addWidget(self.enrollButton)
        
        # Table
        self.studentsTable = QTableWidget()
        self.studentsTable.setColumnCount(4)
        self.studentsTable.setHorizontalHeaderLabels(["No", "ID Number", "Full Name", "Year Level"])
        
        # Count label
        self.countLabel = QLabel("0 student(s) to enroll")
        
        layout.addLayout(search_layout)
        layout.addWidget(self.studentsTable)
        layout.addWidget(self.countLabel)
        layout.addLayout(button_layout)
        
        # Store references for compatibility
        self.suggestionsContainer = None
        self.suggestionsList = None
        self.bulkButton = None
        
        # Initialize
        self.students_to_enroll = []
        self.suggestion_widgets = []
        
        # Connect basic signals
        self.searchLineEdit.textChanged.connect(self._on_search_changed)
        self.cancelButton.clicked.connect(self.reject)
        self.enrollButton.clicked.connect(self._on_enroll)
    
    # ==================== SETUP ====================
    
    def _setup_table(self):
        """Configure table properties"""
        self.studentsTable.setColumnWidth(0, 50)   # No
        self.studentsTable.setColumnWidth(1, 150)  # ID Number
        self.studentsTable.setColumnWidth(2, 250)  # Full Name
        self.studentsTable.setColumnWidth(3, 100)  # Year Level
        
        # Disable editing
        self.studentsTable.setEditTriggers(
            self.studentsTable.EditTrigger.NoEditTriggers
        )
    
    def _connect_signals(self):
        """Connect all signal handlers"""
        # Search as user types
        self.searchLineEdit.textChanged.connect(self._on_search_changed)
        self.searchLineEdit.returnPressed.connect(self._on_search_enter)
        
        # Buttons
        self.bulkButton.clicked.connect(self._on_bulk_add)
        self.cancelButton.clicked.connect(self.reject)
        self.enrollButton.clicked.connect(self._on_enroll)
        
        # Double click on suggestion
        self.suggestionsList.itemDoubleClicked.connect(self._on_suggestion_double_click)
    
    # ==================== BULK ADD ====================
    
    def _on_bulk_add(self):
        """Handle bulk add functionality - opens bulk upload dialog"""
        if not BULK_UPLOAD_AVAILABLE:
            QMessageBox.warning(
                self,
                "Feature Not Available",
                "Bulk upload feature is not available.\n\n"
                "Please ensure bulk_upload_dialog.py is in the correct directory."
            )
            return
        
        try:
            # Open bulk upload dialog
            dialog = BulkUploadDialog()
            result = dialog.exec()
            
            if result == QDialog.DialogCode.Accepted:
                # Get uploaded students
                bulk_students = dialog.get_students()
                
                if bulk_students:
                    # Add all students to enrollment table
                    added_count = 0
                    duplicate_count = 0
                    
                    for student in bulk_students:
                        # Check if already in list
                        if not any(s['id'] == student['id'] for s in self.students_to_enroll):
                            # Convert student format to match our database
                            formatted_student = {
                                'id': student['id'],
                                'name': student['name'],
                                'year': student['year']
                            }
                            self.students_to_enroll.append(formatted_student)
                            added_count += 1
                        else:
                            duplicate_count += 1
                    
                    # Refresh table
                    self._refresh_table()
                    
                    # Show summary
                    msg = f"Added {added_count} student(s) to enrollment list."
                    if duplicate_count > 0:
                        msg += f"\n{duplicate_count} duplicate(s) skipped."
                    
                    QMessageBox.information(self, "Bulk Upload Complete", msg)
                else:
                    QMessageBox.information(
                        self,
                        "No Students Found",
                        "No valid students found in the CSV file."
                    )
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while processing bulk upload:\n{str(e)}"
            )
    
    # ... rest of the methods remain the same ...
    # ==================== SEARCH & SUGGESTIONS ====================
    
    def _on_search_changed(self, text):
        """Handle search text changes - show suggestions as user types"""
        search_term = text.strip()
        
        # Clear previous suggestions
        self._clear_suggestions()
        
        # If empty, hide suggestions
        if not search_term:
            self._hide_suggestions()
            return
        
        # Search database
        results = self._search_database(search_term)
        
        # Show suggestions
        if results:
            self._show_suggestions(results)
        else:
            self._hide_suggestions()
    
    def _search_database(self, search_term):
        """Search database by ID or name"""
        search_term = search_term.lower()
        results = []
        
        for student in self.STUDENT_DATABASE:
            # Check if already in enrollment table
            if any(s['id'] == student['id'] for s in self.students_to_enroll):
                continue
            
            # Search by ID or name
            if (search_term in student['id'].lower() or 
                search_term in student['name'].lower()):
                results.append(student)
                
                # Limit to 5 suggestions
                if len(results) >= 5:
                    break
        
        return results
    
    def _show_suggestions(self, students):
        """Display search suggestions with + buttons"""
        self._clear_suggestions()
        
        for student in students:
            # Create suggestion item with custom widget
            item = QListWidgetItem()
            self.suggestionsList.addItem(item)
            
            # Create custom widget for the item
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(10, 5, 10, 5)
            
            # Student info label
            from PyQt6.QtWidgets import QLabel
            info_label = QLabel(f"{student['id']}    {student['name']}")
            info_label.setStyleSheet("color: #333; font-size: 10pt;")
            layout.addWidget(info_label)
            
            layout.addStretch()
            
            # Plus button
            plus_btn = QPushButton("+")
            plus_btn.setProperty("class", "plusButton")
            plus_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    color: #4CAF50;
                    font-size: 18pt;
                    font-weight: bold;
                    padding: 5px;
                    min-width: 30px;
                    max-width: 30px;
                }
                QPushButton:hover {
                    background-color: #E8F5E9;
                    border-radius: 4px;
                }
            """)
            plus_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            plus_btn.clicked.connect(lambda checked, s=student: self._add_student_to_table(s))
            layout.addWidget(plus_btn)
            
            widget.setLayout(layout)
            
            # Set the widget for the item
            item.setSizeHint(widget.sizeHint())
            self.suggestionsList.setItemWidget(item, widget)
            
            self.suggestion_widgets.append(widget)
        
        # Show suggestions container
        self.suggestionsContainer.setVisible(True)
        
        # Adjust height based on number of items
        item_height = 45
        list_height = min(len(students) * item_height, 150)
        self.suggestionsList.setFixedHeight(list_height)
        self.suggestionsContainer.setFixedHeight(list_height)
    
    def _hide_suggestions(self):
        """Hide suggestions container"""
        self.suggestionsContainer.setVisible(False)
        self.suggestionsContainer.setFixedHeight(0)
    
    def _clear_suggestions(self):
        """Clear all suggestions"""
        self.suggestionsList.clear()
        self.suggestion_widgets.clear()
    
    def _on_suggestion_double_click(self, item):
        """Handle double click on suggestion - same as clicking +"""
        row = self.suggestionsList.row(item)
        if row >= 0 and row < len(self.STUDENT_DATABASE):
            # Find the student from the current search
            search_term = self.searchLineEdit.text().strip()
            results = self._search_database(search_term)
            if row < len(results):
                self._add_student_to_table(results[row])
    
    def _on_search_enter(self):
        """Handle Enter key in search box - add first suggestion"""
        if self.suggestionsList.count() > 0:
            search_term = self.searchLineEdit.text().strip()
            results = self._search_database(search_term)
            if results:
                self._add_student_to_table(results[0])
    
    # ==================== ADD TO TABLE ====================
    
    def _add_student_to_table(self, student):
        """Add student to enrollment table"""
        # Check if already added
        if any(s['id'] == student['id'] for s in self.students_to_enroll):
            return
        
        # Add to list
        self.students_to_enroll.append(student)
        
        # Refresh table
        self._refresh_table()
        
        # Clear search and hide suggestions
        self.searchLineEdit.clear()
        self._hide_suggestions()
    
    def _refresh_table(self):
        """Refresh the enrollment table"""
        # Clear table
        self.studentsTable.setRowCount(0)
        
        # Populate with students
        for i, student in enumerate(self.students_to_enroll):
            row = self.studentsTable.rowCount()
            self.studentsTable.insertRow(row)
            
            # No
            no_item = QTableWidgetItem(str(i + 1))
            no_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.studentsTable.setItem(row, 0, no_item)
            
            # ID Number
            id_item = QTableWidgetItem(student["id"])
            self.studentsTable.setItem(row, 1, id_item)
            
            # Full Name
            name_item = QTableWidgetItem(student["name"])
            self.studentsTable.setItem(row, 2, name_item)
            
            # Year Level
            year_item = QTableWidgetItem(student["year"])
            year_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.studentsTable.setItem(row, 3, year_item)
        
        # Update count
        self._update_count_label()
    
    def _update_count_label(self):
        """Update count label and enable/disable enroll button"""
        count = len(self.students_to_enroll)
        self.countLabel.setText(f"{count} student(s) to enroll")
        self.enrollButton.setEnabled(count > 0)
    
    # ==================== REMOVE FROM TABLE ====================
    
    def keyPressEvent(self, event):
        """Handle Delete key to remove selected student"""
        if event.key() == Qt.Key.Key_Delete:
            selected_row = self.studentsTable.currentRow()
            if selected_row >= 0:
                # Remove from list
                del self.students_to_enroll[selected_row]
                # Refresh table
                self._refresh_table()
        else:
            super().keyPressEvent(event)
    
    # ==================== ENROLL ====================
    
    def _on_enroll(self):
        """Enroll all students in the table"""
        if not self.students_to_enroll:
            return
        
        # Create summary
        names = [s['name'] for s in self.students_to_enroll]
        summary = "\n".join([f"• {name}" for name in names])
        
        # Confirm
        reply = QMessageBox.question(
            self,
            "Confirm Enrollment",
            f"Enroll {len(self.students_to_enroll)} student(s)?\n\n{summary}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Save to "database"
            for student in self.students_to_enroll:
                if not any(s['id'] == student['id'] for s in self.ENROLLED_STUDENTS):
                    self.ENROLLED_STUDENTS.append(student.copy())
            
            # Success message
            QMessageBox.information(
                self,
                "Success",
                f"Successfully enrolled {len(self.students_to_enroll)} student(s)!"
            )
            
            # Close dialog
            self.accept()
    
    # ==================== PUBLIC METHODS ====================
    
    def get_enrolled_students(self):
        """Get students enrolled in this session"""
        return self.students_to_enroll.copy()
    
    @classmethod
    def get_all_enrolled_students(cls):
        """Get all enrolled students from database"""
        return cls.ENROLLED_STUDENTS.copy()


# ==================== TESTING ====================

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel
    
    def show_dialog():
        dialog = AddStudentDialog()
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            enrolled = dialog.get_enrolled_students()
            
            if enrolled:
                print("\n=== Enrolled Students ===")
                for s in enrolled:
                    print(f"ID: {s['id']}, Name: {s['name']}, Year: {s['year']}")
                
                status_label.setText(f"Enrolled {len(enrolled)} student(s)")
        else:
            status_label.setText("Cancelled")
    
    def show_database():
        all_enrolled = AddStudentDialog.get_all_enrolled_students()
        
        if all_enrolled:
            msg = f"Total enrolled: {len(all_enrolled)}\n\n"
            for i, s in enumerate(all_enrolled, 1):
                msg += f"{i}. {s['name']} ({s['id']})\n"
            
            QMessageBox.information(None, "Enrolled Database", msg)
        else:
            QMessageBox.information(None, "Enrolled Database", "No students enrolled.")
    
    app = QApplication(sys.argv)
    
    window = QWidget()
    layout = QVBoxLayout()
    
    title = QLabel("Add Student Dialog - Test")
    title.setStyleSheet("font-size: 14pt; font-weight: bold; margin: 10px;")
    layout.addWidget(title)
    
    btn_open = QPushButton("Open Add Student Dialog")
    btn_open.clicked.connect(show_dialog)
    btn_open.setMinimumHeight(50)
    layout.addWidget(btn_open)
    
    btn_view = QPushButton("View Enrolled Database")
    btn_view.clicked.connect(show_database)
    btn_view.setMinimumHeight(50)
    layout.addWidget(btn_view)
    
    status_label = QLabel("Ready")
    status_label.setStyleSheet("color: #666; margin: 10px;")
    layout.addWidget(status_label)
    
    window.setLayout(layout)
    window.setWindowTitle("Test - Add Student Dialog")
    window.resize(450, 220)
    window.show()
    
    sys.exit(app.exec())