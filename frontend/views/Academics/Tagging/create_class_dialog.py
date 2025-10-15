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
        
        # Start time
        self.start_time = QTimeEdit()
        self.start_time.setDisplayFormat("hh:mm AP")
        self.start_time.setTime(QTime(9, 0))  # Default 9:00 AM
        self.start_time.setMinimumWidth(100)
        layout.addWidget(QLabel("from"))
        layout.addWidget(self.start_time)
        
        # End time
        self.end_time = QTimeEdit()
        self.end_time.setDisplayFormat("hh:mm AP")
        self.end_time.setTime(QTime(10, 30))  # Default 10:30 AM
        self.end_time.setMinimumWidth(100)
        layout.addWidget(QLabel("to"))
        layout.addWidget(self.end_time)
        
        # Remove button
        self.remove_btn = QPushButton("✕")
        self.remove_btn.setFixedSize(30, 30)
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.remove_btn.clicked.connect(self.remove_clicked)
        layout.addWidget(self.remove_btn)
        
        layout.addStretch()
        self.setLayout(layout)
    
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
        main_layout = QVBoxLayout()
        
        # Title - dynamic based on mode
        title_text = "Edit Class" if self.is_edit_mode else "Create New Class"
        title_label = QLabel(title_text)
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
        
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("e.g., IT57, CS101")
        self.code_edit.setMaxLength(10)
        basic_layout.addRow("Class Code*:", self.code_edit)
        
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("e.g., Database Management Systems")
        basic_layout.addRow("Class Title*:", self.title_edit)
        
        self.units_spin = QSpinBox()
        self.units_spin.setRange(1, 6)
        self.units_spin.setValue(3)
        self.units_spin.setSuffix(" units")
        basic_layout.addRow("Units*:", self.units_spin)
        
        self.section_combo = QComboBox()
        self.populate_sections()
        basic_layout.addRow("Section*:", self.section_combo)
        
        basic_group.setLayout(basic_layout)
        scroll_layout.addWidget(basic_group)
        
        # Schedule Group
        schedule_group = QGroupBox("Schedule")
        schedule_layout = QVBoxLayout()
        
        schedule_header = QHBoxLayout()
        schedule_label = QLabel("Class Schedule (add multiple time slots)")
        schedule_label.setStyleSheet("font-weight: bold;")
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
        location_group = QGroupBox("Location & Instructor")
        location_layout = QFormLayout()
        
        self.room_edit = QLineEdit()
        self.room_edit.setPlaceholderText("e.g., CISC Lab 1, Room 301")
        location_layout.addRow("Room*:", self.room_edit)
        
        self.instructor_edit = QLineEdit()
        self.instructor_edit.setPlaceholderText("e.g., Juan Dela Cruz")
        location_layout.addRow("Instructor*:", self.instructor_edit)
        
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
                background-color: #4CAF50;
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
                background-color: #f0f0f0;
            }
        """)

        self.draft_btn = QPushButton("Draft Class")
        self.draft_btn.setDefault(True)
        self.draft_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
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
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        
        # Connect signals
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
            display_text = f"{section['section']} - {section['program']} ({section['year']})"
            self.section_combo.addItem(display_text, section['id'])
    
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

    def _populate_fields(self, class_data: Dict) -> None:
        """
        Populate form fields with existing class data for editing.

        Args:
            class_data: Dictionary containing class information
        """
        try:
            # Populate basic information
            if 'code' in class_data:
                self.code_edit.setText(str(class_data['code']))

            if 'title' in class_data:
                self.title_edit.setText(str(class_data['title']))

            if 'units' in class_data:
                self.units_spin.setValue(int(class_data['units']))

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
                self.instructor_edit.setText(str(class_data['instructor']))

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
        if not self.code_edit.text().strip():
            self.code_edit.setFocus()
            self.code_edit.setStyleSheet("border: 2px solid red;")
            return
        
        if not self.title_edit.text().strip():
            self.title_edit.setFocus()
            self.title_edit.setStyleSheet("border: 2px solid red;")
            return
        
        if not self.room_edit.text().strip():
            self.room_edit.setFocus()
            self.room_edit.setStyleSheet("border: 2px solid red;")
            return
        
        if not self.instructor_edit.text().strip():
            self.instructor_edit.setFocus()
            self.instructor_edit.setStyleSheet("border: 2px solid red;")
            return
        
        if not self.sections:
            logger.warning("No sections available. Please create a section first.")
            return
        
        # Reset styling
        self.code_edit.setStyleSheet("")
        self.title_edit.setStyleSheet("")
        self.room_edit.setStyleSheet("")
        self.instructor_edit.setStyleSheet("")
        
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
        
        # Collect all schedules
        schedules = []
        for widget in self.schedule_widgets:
            schedules.append(widget.get_schedule_data())
        
        data = {
            'code': self.code_edit.text().strip().upper(),
            'title': self.title_edit.text().strip(),
            'units': self.units_spin.value(),
            'section_id': section_id,
            'schedules': schedules,
            'room': self.room_edit.text().strip(),
            'instructor': self.instructor_edit.text().strip(),
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