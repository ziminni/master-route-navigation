from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QSpinBox, QComboBox, QPushButton,
    QTextEdit, QLabel, QGroupBox, QScrollArea,
    QWidget, QTimeEdit, QFrame
)
from PyQt6.QtCore import Qt, QTime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ScheduleWidget(QWidget):
    """
    Widget for a single schedule entry.
    
    Contains day, start time, end time, and remove button.
    """
    
    DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    def __init__(self, parent=None, on_remove=None):
        """
        Initialize schedule widget.
        
        Args:
            parent: Parent widget
            on_remove: Callback function when remove button clicked
        """
        super().__init__(parent)
        self.on_remove = on_remove
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI for this schedule entry."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 5, 0, 5)
        
        # Day selector
        self.day_combo = QComboBox()
        self.day_combo.addItems(self.DAYS)
        self.day_combo.setMinimumWidth(120)
        layout.addWidget(self.day_combo)
        
        # Start time (7 AM to 7 PM)
        self.start_time = QTimeEdit()
        self.start_time.setDisplayFormat("hh:mm AP")
        self.start_time.setTime(QTime(9, 0)) # Default 9:00 AM
        self.start_time.setMinimumTime(QTime(7, 0))  # 7:00 AM minimum
        self.start_time.setMaximumTime(QTime(18, 0))  # 6:00 PM maximum (to allow 1-hour class until 7 PM)
        self.start_time.setMinimumWidth(130)
        layout.addWidget(QLabel("from"))
        layout.addWidget(self.start_time)

        # End time (8 AM to 7 PM)
        self.end_time = QTimeEdit()
        self.end_time.setDisplayFormat("hh:mm AP")
        self.end_time.setTime(QTime(10, 30))  # Default 10:30 AM
        self.end_time.setMinimumTime(QTime(8, 0))  # 8:00 AM minimum (start + 1 hour)
        self.end_time.setMaximumTime(QTime(19, 0))  # 7:00 PM maximum
        self.end_time.setMinimumWidth(130)
        layout.addWidget(QLabel("to"))
        layout.addWidget(self.end_time)

        self.start_time.timeChanged.connect(self._validate_time_range)
        self.end_time.timeChanged.connect(self._validate_time_range)

        # Remove button
        self.remove_btn = QPushButton("✕")
        self.remove_btn.setFixedSize(35, 35)
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 16px;
                margin: 0px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.remove_btn.clicked.connect(self.remove_clicked)
        layout.addWidget(self.remove_btn)
        
        layout.addStretch()
        self.setLayout(layout)

    def _validate_time_range(self):
        """
        Validate that end time is at least 1 hour after start time.
        Adjusts end time if necessary.
        """
        start = self.start_time.time()
        end = self.end_time.time()

        # Calculate minimum end time (start + 1 hour)
        min_end_time = start.addSecs(3600)  # 3600 seconds = 1 hour

        # If end time is before the minimum, adjust it
        if end < min_end_time:
            self.end_time.setTime(min_end_time)

        # Ensure end time doesn't exceed 7 PM
        max_time = QTime(19, 0)  # 7:00 PM
        if self.end_time.time() > max_time:
            self.end_time.setTime(max_time)
            # If this forces start time to be too late, adjust start time
            if self.start_time.time().addSecs(3600) > max_time:
                self.start_time.setTime(QTime(18, 0))  # 6:00 PM
    
    def remove_clicked(self):
        """Handle remove button click."""
        if self.on_remove:
            self.on_remove(self)
    
    def get_schedule_data(self) -> Dict:
        """
        Get schedule data from this widget.
        
        Returns:
            Dict: Schedule data with day, start_time, end_time
        """
        start = self.start_time.time()
        end = self.end_time.time()

        if end.secsTo(start) >= -3600:  # Less than 1 hour duration
            # just in case
            logger.warning("Invalid schedule duration detected")
        
        return {
            'day': self.day_combo.currentText(),
            'start_time': start.toString("hh:mm AP"),
            'end_time': end.toString("hh:mm AP")
        }
    
    def set_schedule_data(self, schedule: Dict):
        """
        Set schedule data in this widget.
        
        Args:
            schedule: Schedule dictionary to populate
        """
        # Set day
        day_index = self.day_combo.findText(schedule.get('day', 'Monday'))
        if day_index >= 0:
            self.day_combo.setCurrentIndex(day_index)
        
        # Set times
        start_str = schedule.get('start_time', '09:00 AM')
        start_time = QTime.fromString(start_str, "hh:mm AP")
        if start_time.isValid():
            self.start_time.setTime(start_time)
        
        end_str = schedule.get('end_time', '10:30 AM')
        end_time = QTime.fromString(end_str, "hh:mm AP")
        if end_time.isValid():
            self.end_time.setTime(end_time)


class CreateClassDialog(QDialog):
    """
    Dialog for creating a new class.
    
    Supports multiple schedules with dynamic add/remove functionality.
    
    Attributes:
        code_edit: Class code input
        title_edit: Class title input
        units_spin: Units selection
        section_combo: Section selection
        schedules_container: Container for schedule widgets
        schedule_widgets: List of ScheduleWidget instances
        room_edit: Room input
        instructor_edit: Instructor input
        type_combo: Class type selection
    """
    
    TYPES = ['Lecture', 'Laboratory']
    
    def __init__(self, parent=None, sections: Optional[List[Dict]] = None, class_data: Optional[Dict] = None):
        """
        Initialize the create class dialog.
        
        Args:
            parent: Parent widget
            sections: List of available sections for selection
            class_data: Existing class data for editing (None for create mode)
        """
        super().__init__(parent)
        self.sections = sections or []
        self.schedule_widgets: List[ScheduleWidget] = []

        # Store whether we're in edit mode
        self.is_edit_mode = class_data is not None
        self.class_data = class_data

        # Set window title based on mode
        title_text = "Edit Class" if self.is_edit_mode else "Create Class"
        self.setWindowTitle(title_text)
        
        self.setWindowTitle("Create Class")
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)
        self.setup_ui()

        # Add initial schedule or populate from existing data
        if self.is_edit_mode and class_data:
            self._populate_fields(class_data)
        else:
            # Add initial empty schedule for create mode
            self.add_schedule()
        
        logger.debug("CreateClassDialog initialized")
    
    def setup_ui(self):
        """Set up the user interface."""
        # Apply global stylesheet
        self.setStyleSheet("""
            QLabel {
                color: #2d2d2d;
                font-size: 14px;
            }
            QLineEdit, QComboBox, QSpinBox, QTimeEdit {
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 6px 10px;
                background-color: #f9f9f9;
                min-height: 30px;
                font-size: 14px;
            }
            QComboBox QAbstractItemView {
                font-size: 14px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
                height: 5px;
            }
            QPushButton {
                background-color: #1e5631;
                color: white;
                padding: 8px 18px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
                border: none;
                min-width: 100px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #2d5a3d;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #1e5631;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #1e5631;
                min-height: 30px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #2d5a3d;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar:horizontal {
                border: none;
                background: #f0f0f0;
                height: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #1e5631;
                min-width: 30px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #2d5a3d;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(5)

        # Title - dynamic based on mode
        title_text = "Edit Class" if self.is_edit_mode else "Create Class"
        title_label = QLabel(title_text)
        from PyQt6.QtGui import QFont
        title_label.setFont(QFont("Segoe UI", 18, QFont.Weight.DemiBold))
        title_label.setStyleSheet("color: #1e5631; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # Scrollable area for form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Basic Information Group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout()

        self.section_combo = QComboBox()
        self.populate_sections()
        basic_layout.addRow("Section*:", self.section_combo)

        self.code_combo = QComboBox()
        self.code_combo.setPlaceholderText("Select a course")
        basic_layout.addRow("Class Code*:", self.code_combo)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Auto-filled based on course code")
        self.title_edit.setReadOnly(True)
        self.title_edit.setStyleSheet("background-color: #e9ecef;")
        basic_layout.addRow("Class Title*:", self.title_edit)

        self.units_spin = QSpinBox()
        self.units_spin.setRange(1, 6)
        self.units_spin.setValue(3)
        self.units_spin.setSuffix(" units") if self.units_spin.value() > 1 else self.units_spin.setSuffix(" unit")
        self.units_spin.setReadOnly(True)
        self.units_spin.setStyleSheet("background-color: #e9ecef;")
        self.units_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        basic_layout.addRow("Units*:", self.units_spin)
        

        
        basic_group.setLayout(basic_layout)
        scroll_layout.addWidget(basic_group)
        
        # Schedule Group
        schedule_group = QGroupBox("Schedule")
        schedule_layout = QVBoxLayout()
        
        schedule_header = QHBoxLayout()
        schedule_label = QLabel("Class Schedule (add multiple time slots)")
        schedule_header.addWidget(schedule_label)
        schedule_header.addStretch()
        
        self.add_schedule_btn = QPushButton("+ Add Schedule")
        self.add_schedule_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 5px 15px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.add_schedule_btn.clicked.connect(self.add_schedule)
        schedule_header.addWidget(self.add_schedule_btn)
        
        schedule_layout.addLayout(schedule_header)
        
        # Container for schedule widgets
        self.schedules_container = QVBoxLayout()
        schedule_layout.addLayout(self.schedules_container)
        
        schedule_group.setLayout(schedule_layout)
        scroll_layout.addWidget(schedule_group)
        
        # Location & Instructor Group
        location_group = QGroupBox("Other Details")
        location_layout = QFormLayout()
        
        self.room_edit = QLineEdit()
        self.room_edit.setPlaceholderText("e.g., CISC Lab 1, Room 301")
        location_layout.addRow("Room*:", self.room_edit)

        # Instructor dropdown with search capability
        self.instructor_combo = QComboBox()
        self.instructor_combo.setEditable(True)  # Allows typing to search
        self.instructor_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)  # Prevent adding new items
        self.instructor_combo.setPlaceholderText("Type to search or select faculty")
        self.populate_instructors()
        location_layout.addRow("Instructor*:", self.instructor_combo)

        self.type_combo = QComboBox()
        self.type_combo.addItems(self.TYPES)
        location_layout.addRow("Type*:", self.type_combo)
        
        location_group.setLayout(location_layout)
        scroll_layout.addWidget(location_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        button_text = "Update Class" if self.is_edit_mode else "Create Class"
        self.create_btn = QPushButton(button_text)
        self.create_btn.setDefault(True)
        self.create_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e5631;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        self.draft_btn = QPushButton("Draft Class")
        self.draft_btn.setDefault(True)
        self.draft_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #1e5631;
                        color: white;
                        padding: 8px 20px;
                        border: none;
                        border-radius: 4px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.draft_btn)
        button_layout.addWidget(self.create_btn)

        # Connect signals for dynamic course code dropdown
        self.section_combo.currentIndexChanged.connect(self._handle_section_changed)
        self.code_combo.currentIndexChanged.connect(self._handle_code_changed)

        # Trigger initial population if section is already selected
        if self.section_combo.count() > 0:
            self._handle_section_changed(0)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        
        # Connect signals to action buttons
        self.create_btn.clicked.connect(self.validate_and_accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.draft_btn.clicked.connect(self.handle_draft)
    
    def populate_sections(self):
        """Populate section dropdown with available sections."""
        self.section_combo.clear()
        
        if not self.sections:
            self.section_combo.addItem("No sections available")
            self.section_combo.setEnabled(False)
            return
        
        for section in self.sections:
            # Generate section name in format: BSIT-3B
            section_name = self._generate_section_display_name(section)

            # Get section type (Lecture, Laboratory, Hybrid)
            section_type = section.get('type', 'Lecture')

            # Format: BSIT-3B (Lecture)
            display_text =  f"{section_name} ({section_type})"
            self.section_combo.addItem(display_text, section['id'])

    def _generate_section_display_name(self, section: Dict) -> str:
        """
        Generate formatted section name from section data.

        Args:
            section: Section dictionary containing program, year, and section

        Returns:
            Formatted section name (e.g., "BSIT-3B")
        """
        program = section.get('program', '')
        year = section.get('year', '')
        section_letter = section.get('section', '')

        # Generate program acronym (e.g., "BS Information Technology" -> "BSIT")
        program_acronym = ''
        if program:
            words = program.split()
            for word in words:
                # If word is all caps (like "BS", "IT"), take the whole thing
                if word.isupper():
                    program_acronym += word
                else:
                    # Otherwise take first letter if it's uppercase
                    if word and word[0].isupper():
                        program_acronym += word[0]

        # Extract year number (e.g., "3rd" -> "3")
        year_num = ''
        if year:
            year_num = ''.join(filter(str.isdigit, year))

        # Combine: PROGRAM-YEARSECTION (e.g., "BSIT-3B")
        if program_acronym and year_num and section_letter:
            return f"{program_acronym}-{year_num}{section_letter}"
        elif section_letter:
            # Fallback to just the section letter
            return section_letter
        else:
            return "Unknown"

    def populate_instructors(self):
        """Populate instructor dropdown with available faculty."""
        self.instructor_combo.clear()
        self.instructor_combo.addItem("-- Select an instructor --", None)

        for faculty_member in self.faculty:
            # Format: ID - Name
            display_text = f"{faculty_member['id']} - {faculty_member['name']}"
            self.instructor_combo.addItem(display_text, faculty_member)
    
    def add_schedule(self):
        """Add a new schedule widget to the form."""
        schedule_widget = ScheduleWidget(
            parent=self,
            on_remove=self.remove_schedule
        )
        
        self.schedule_widgets.append(schedule_widget)
        self.schedules_container.addWidget(schedule_widget)
        
        logger.debug(f"Added schedule widget (total: {len(self.schedule_widgets)})")
    
    def remove_schedule(self, widget: ScheduleWidget):
        """
        Remove a schedule widget from the form.
        
        Args:
            widget: ScheduleWidget to remove
        """
        if len(self.schedule_widgets) <= 1:
            # Don't allow removing the last schedule
            logger.warning("Cannot remove last schedule")
            return
        
        if widget in self.schedule_widgets:
            self.schedule_widgets.remove(widget)
            self.schedules_container.removeWidget(widget)
            widget.deleteLater()
            
            logger.debug(f"Removed schedule widget (remaining: {len(self.schedule_widgets)})")

    def _check_duplicate_schedules(self) -> tuple[bool, Optional[str]]:
        """
        Check if there are duplicate schedules within this class.

        Returns:
            tuple: (has_duplicates: bool, error_message: Optional[str])
        """
        schedules = []
        for widget in self.schedule_widgets:
            schedule = widget.get_schedule_data()
            schedules.append(schedule)

        # Check for duplicates
        seen = set()
        duplicates = []

        for schedule in schedules:
            # Create a hashable key from schedule data
            schedule_key = (
                schedule['day'],
                schedule['start_time'],
                schedule['end_time']
            )

            if schedule_key in seen:
                duplicate_str = f"{schedule['day']} {schedule['start_time']} - {schedule['end_time']}"
                if duplicate_str not in duplicates:
                    duplicates.append(duplicate_str)
            else:
                seen.add(schedule_key)

        if duplicates:
            error_msg = (
                    "Duplicate schedules detected:\n\n" +
                    "\n".join(f"• {dup}" for dup in duplicates) +
                    "\n\nPlease remove duplicate schedule entries."
            )
            return True, error_msg

        return False, None

    def _populate_fields(self, class_data: Dict) -> None:
        """
        Populate form fields with existing class data for editing.

        Args:
            class_data: Dictionary containing class information
        """
        try:
            # Populate basic information
            if 'code' in class_data:
                # Find and select the matching course in dropdown
                code_to_find = str(class_data['code'])
                for i in range(self.code_combo.count()):
                    course = self.code_combo.itemData(i)
                    if course and course.get('code') == code_to_find:
                        self.code_combo.setCurrentIndex(i)
                        break

            # Populate section
            if 'section_id' in class_data:
                section_id = class_data['section_id']
                for i in range(self.section_combo.count()):
                    if self.section_combo.itemData(i) == section_id:
                        self.section_combo.setCurrentIndex(i)
                        break

            # Populate schedules
            if 'schedules' in class_data and class_data['schedules']:
                schedules = class_data['schedules']

                # Add schedule widgets for each schedule in data
                for schedule in schedules:
                    schedule_widget = ScheduleWidget(
                        parent=self,
                        on_remove=self.remove_schedule
                    )
                    schedule_widget.set_schedule_data(schedule)

                    self.schedule_widgets.append(schedule_widget)
                    self.schedules_container.addWidget(schedule_widget)

                logger.debug(f"Populated {len(schedules)} schedule(s)")
            else:
                # No schedules in data, add one empty schedule
                self.add_schedule()

            # Populate location & instructor
            if 'room' in class_data:
                self.room_edit.setText(str(class_data['room']))

            if 'instructor' in class_data:
                instructor_name = str(class_data['instructor'])

                # Try to find matching faculty by name
                found = False
                for i in range(self.instructor_combo.count()):
                    faculty_data = self.instructor_combo.itemData(i)
                    if faculty_data and faculty_data.get('name') == instructor_name:
                        self.instructor_combo.setCurrentIndex(i)
                        found = True
                        break

            if 'type' in class_data:
                index = self.type_combo.findText(class_data['type'])
                if index >= 0:
                    self.type_combo.setCurrentIndex(index)

            logger.info(f"Populated form fields for class: {class_data.get('code', 'Unknown')}")

        except Exception as e:
            logger.exception(f"Error populating class fields: {e}")

    def handle_draft(self):
        """Handle draft button clicked."""
        pass
    
    def validate_and_accept(self):
        """Validate input and accept dialog if valid."""
        # Check required fields
        if self.code_combo.currentData() is None:
            self.code_combo.setFocus()
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Validation Error", "Please select a course code.")
            return
        
        if not self.title_edit.text().strip():
            self.title_edit.setFocus()
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Validation Error", "Please select a course code to auto-fill the title.")
            return
        
        if not self.room_edit.text().strip():
            self.room_edit.setFocus()
            self.room_edit.setStyleSheet("border: 2px solid red;")
            return
        
        instructor_text = self.instructor_combo.currentText().strip()
        if not instructor_text or instructor_text == "-- Select an instructor --":
            self.instructor_combo.setFocus()
            self.instructor_combo.setStyleSheet("border: 2px solid red;")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Validation Error", "Please select an instructor.")
            return
        
        if not self.sections:
            logger.warning("No sections available. Please create a section first.")
            return

        # Check for duplicate schedules
        has_duplicates, error_message = self._check_duplicate_schedules()
        if has_duplicates:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Duplicate Schedules",
                error_message,
                QMessageBox.StandardButton.Ok
            )
            return
        
        # Reset styling
        self.room_edit.setStyleSheet("")
        self.instructor_combo.setStyleSheet("")
        
        self.accept()
    
    def get_data(self) -> Dict:
        """
        Get class data from form including all schedules.
        
        Returns:
            Dict: Complete class data with schedules list
        """
        # Get selected section ID
        section_id = self.section_combo.currentData()
        if section_id is None:
            section_id = -1  # Fallback

        # Get course code from selected course
        course_data = self.code_combo.currentData()
        code = course_data['code'] if course_data else ""
        
        # Collect all schedules
        schedules = []
        for widget in self.schedule_widgets:
            schedules.append(widget.get_schedule_data())

        instructor_text = self.instructor_combo.currentText().strip()
        instructor_name = instructor_text

        # If format is "ID - Name", extract just the name
        if ' - ' in instructor_text:
            parts = instructor_text.split(' - ', 1)
            if len(parts) == 2:
                instructor_name = parts[1].strip()

        data = {
            'code': code,
            'title': self.title_edit.text().strip(),
            'units': self.units_spin.value(),
            'section_id': section_id,
            'schedules': schedules,
            'room': self.room_edit.text().strip(),
            'instructor': instructor_name,
            'type': self.type_combo.currentText()
        }

        # If editing, preserve the class ID
        if self.is_edit_mode and self.class_data and 'id' in self.class_data:
            data['id'] = self.class_data['id']
        
        logger.debug(f"Class data collected: {data['code']} with {len(schedules)} schedules")
        return data
    
    def set_sections(self, sections: List[Dict]):
        """
        Update available sections.
        
        Args:
            sections: List of section dictionaries
        """
        self.sections = sections
        self.populate_sections()

    def _get_selected_section_data(self) -> Optional[Dict]:
        """
        Get the full section data for the currently selected section.

        Returns:
            Section dictionary or None
        """
        section_id = self.section_combo.currentData()
        if section_id is None:
            return None

        for section in self.sections:
            if section.get('id') == section_id:
                return section
        return None

    def _filter_courses_by_section(self, year: str, track: str) -> List[Dict]:
        """
        Filter courses based on section year and track.

        Args:
            year: Year level (e.g., "1st", "2nd", "N/A (Petition)")
            track: Track name (e.g., "Software Development", "N/A")

        Returns:
            List of course dictionaries
        """
        filtered_courses = []
        semester = "First Semester"  # Hardcoded for now

        if year == "N/A (Petition)":
            # Add all courses from all years for current semester
            for yr in ["1st", "2nd", "3rd", "4th"]:
                if yr in self.bsit_curriculum and semester in self.bsit_curriculum[yr]:
                    filtered_courses.extend(self.bsit_curriculum[yr][semester])

            # Add all electives from all tracks
            if "Electives" in self.bsit_curriculum:
                for track_name in self.bsit_curriculum["Electives"]:
                    filtered_courses.extend(self.bsit_curriculum["Electives"][track_name])
        else:
            # Add courses for specific year and semester
            if year in self.bsit_curriculum and semester in self.bsit_curriculum[year]:
                filtered_courses = self.bsit_curriculum[year][semester].copy()

            # Add track-specific electives if applicable (for 3rd and 4th year)
            if (year == "4th" or year == "3rd")  and track != "N/A":
                track_key = track + " Track"
                if "Electives" in self.bsit_curriculum and track_key in self.bsit_curriculum["Electives"]:
                    filtered_courses.extend(self.bsit_curriculum["Electives"][track_key])

        logger.debug(f"Filtered {len(filtered_courses)} courses for year={year}, track={track}")
        return filtered_courses

    def _populate_course_dropdown(self, courses: List[Dict]) -> None:
        """
        Populate code dropdown with filtered courses.

        Args:
            courses: List of course dictionaries
        """
        self.code_combo.clear()
        self.code_combo.addItem("-- Select a course --", None)

        for course in courses:
            display_text = f"{course['code']} - {course['title']}"
            self.code_combo.addItem(display_text, course)

        logger.debug(f"Populated code dropdown with {len(courses)} courses")

    def _handle_section_changed(self, index: int) -> None:
        """
        Handle section dropdown change to filter available courses.

        Args:
            index: Selected index in section dropdown
        """
        # Clear course selection and auto-filled fields
        self.code_combo.clear()
        self.title_edit.clear()
        self.units_spin.setValue(3)

        section_data = self._get_selected_section_data()
        if not section_data:
            self.code_combo.addItem("-- No section selected --", None)
            self.code_combo.setEnabled(False)
            return

        # Enable code dropdown
        self.code_combo.setEnabled(True)

        # Extract year and track
        year = section_data.get('year', '1st')
        track = section_data.get('track', 'N/A')

        logger.info(f"Section changed: year={year}, track={track}")

        # Filter and populate courses
        filtered_courses = self._filter_courses_by_section(year, track)
        self._populate_course_dropdown(filtered_courses)

    def _handle_code_changed(self, index: int) -> None:
        """
        Handle course code dropdown change to auto-fill title and units.

        Args:
            index: Selected index in code dropdown
        """
        course_data = self.code_combo.currentData()

        if course_data is None:
            # Placeholder or no selection
            self.title_edit.clear()
            self.units_spin.setValue(3)
            return

        # Auto-fill title and units from course data
        self.title_edit.setText(course_data['title'])
        self.units_spin.setValue(course_data['units'])

        logger.debug(f"Course selected: {course_data['code']} - {course_data['title']}")

    # Hard coded data for simplicity and demo only, will improve later

    faculty = [
        {"id": "789789789", "name": "Kim Jong Un"},
        {"id": "2019-00001", "name": "Juan Dela Cruz"},
        {"id": "2019-00002", "name": "Maria Santos"},
        {"id": "2020-00003", "name": "Pedro Reyes"},
        {"id": "2020-00004", "name": "Ana Garcia"},
        {"id": "2021-00005", "name": "Jose Rizal"}
    ]

    bsit_curriculum = {
        "1st": {
            "First Semester": [
                {"code": "GEC 11", "title": "Understanding the Self", "units": 3},
                {"code": "GEC 14", "title": "Mathematics in the Modern World", "units": 3},
                {"code": "GEC 15", "title": "Purposive Communication", "units": 3},
                {"code": "GEC 16", "title": "Art Appreciation", "units": 3},
                {"code": "PE 31", "title": "Movement Enhancement (PATH-FIT I)", "units": 2},
                {"code": "NSTP 1", "title": "National Service Training Program I", "units": 3},
                {"code": "ITCC 41", "title": "Introduction to Computing", "units": 3},
                {"code": "ITCC 43", "title": "Computer Programming 1", "units": 3}
            ],
            "Second Semester": [
                {"code": "GEC 12", "title": "Readings in Philippine History", "units": 3},
                {"code": "GEC 13", "title": "The Contemporary World", "units": 3},
                {"code": "GEC 18", "title": "Ethics", "units": 3},
                {"code": "GEC 19", "title": "The Life and Works of Jose Rizal", "units": 3},
                {"code": "GEE 16", "title": "The Entrepreneurial Mind", "units": 3},
                {"code": "PE 32", "title": "Fitness Exercise (PATH-FIT II)", "units": 2},
                {"code": "NSTP 2", "title": "National Service Training Program II", "units": 3},
                {"code": "ITCC 42", "title": "Computer Programming 2", "units": 3},
                {"code": "ITCC 44", "title": "Discrete Structures", "units": 3}
            ]
        },

        "2nd": {
            "First Semester": [
                {"code": "ITCC 45", "title": "Computer Programming 3 (OOP)", "units": 3},
                {"code": "ITCC 47", "title": "Data Structures and Algorithms", "units": 3},
                {"code": "IT 51", "title": "Computer Architecture", "units": 3},
                {"code": "IT 57", "title": "Fundamentals of Networking", "units": 3},
                {"code": "IT 59", "title": "Web Systems and Technologies 1", "units": 3},
                {"code": "GEC 17", "title": "Science, Technology and Society", "units": 3},
                {"code": "GEE 11", "title": "Environmental Science", "units": 3},
                {"code": "PE 33", "title": "Physical Activities Towards Health and Fitness III", "units": 2}
            ],
            "Second Semester": [
                {"code": "ITCC 46", "title": "Information Management", "units": 3},
                {"code": "ITCC 48", "title": "Application Development and Emerging Technologies", "units": 3},
                {"code": "IT 52", "title": "Operating Systems", "units": 3},
                {"code": "IT 58", "title": "Routing and Switching", "units": 3},
                {"code": "IT 60", "title": "Web Systems and Technologies 2", "units": 3},
                {"code": "STAT 22", "title": "Elementary Statistics and Probability", "units": 3},
                {"code": "GEE 15", "title": "Gender and Society", "units": 3},
                {"code": "PE 34", "title": "Physical Activities Towards Health and Fitness IV", "units": 2}
            ]
        },

        "3rd": {
            "First Semester": [
                {"code": "IT 65", "title": "Software Engineering", "units": 3},
                {"code": "IT 57", "title": "Introduction to Human Computer Interaction", "units": 3},
                {"code": "IT 61", "title": "Fundamentals of Database Systems", "units": 3},
                {"code": "IT 63", "title": "Multimedia Technologies", "units": 3},
                {"code": "IT 95", "title": "Research Methods for IT", "units": 3},
                {"code": "IT 62", "title": "Systems Administration and Maintenance", "units": 3}
            ],
            "Second Semester": [
                {"code": "IT 58", "title": "Emerging Technologies in HCI", "units": 3},
                {"code": "IT 56", "title": "Systems Integration and Architecture", "units": 3},
                {"code": "IT 99", "title": "Technopreneurship", "units": 1},
                {"code": "IT 100.1", "title": "IT Capstone Project and Research 1", "units": 3},
                {"code": "IT 62", "title": "IT Trips and Seminar", "units": 1},

            ]
        },

        "4th": {
            "First Semester": [
                {"code": "IT 67", "title": "Information Assurance and Security 2", "units": 3},
                {"code": "IT 69", "title": "Professional Elective 1", "units": 3},
                {"code": "IT 71", "title": "Professional Elective 2", "units": 3},
                {"code": "IT 100.2", "title": "IT Capstone Project and Research 2", "units": 3}
            ],
            "Second Semester": [
                {"code": "IT 98", "title": "Practicum (486 Hours)", "units": 6}
            ]
        },

        "Electives": {
            "Software Development Track": [
                {"code": "ITSD 81", "title": "Desktop Application Development", "units": 3},
                {"code": "ITSD 82", "title": "Mobile Application Development 1", "units": 3},
                {"code": "ITSD 83", "title": "Web Software Tools", "units": 3},
                {"code": "ITSD 84", "title": "Mobile Application Development 2", "units": 3},
                {"code": "ITSD 85", "title": "Special Topics in Software Development", "units": 3}
            ],
            "Data Network Track": [
                {"code": "ITDN 81", "title": "Scaling Networks", "units": 3},
                {"code": "ITDN 82", "title": "Connecting Networks", "units": 3},
                {"code": "ITDN 83", "title": "Network Security", "units": 3},
                {"code": "ITDN 84", "title": "Internet of Things", "units": 3},
                {"code": "ITDN 85", "title": "Special Topics in Networking", "units": 3}
            ],
            "Information Management Track": [
                {"code": "ITIM 81", "title": "Programming for Data Science and AI", "units": 3},
                {"code": "ITIM 82", "title": "Data Mining", "units": 3},
                {"code": "ITIM 83", "title": "Big Data Analytics", "units": 3},
                {"code": "ITIM 84", "title": "Intelligent Systems", "units": 3},
                {"code": "ITIM 85", "title": "Special Topics in Information Management", "units": 3}
            ]
        }
    }
