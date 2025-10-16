from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QMessageBox, QComboBox, QLineEdit, QTextEdit, QDateEdit, 
    QTimeEdit, QCheckBox, QFrame, QGridLayout, QScrollArea, QCalendarWidget
    
)
from PyQt6.QtCore import Qt, QDate, QTime


class AddEvent(QWidget):
    def __init__(self, username, roles, primary_role, token, parent=None):
        super().__init__(parent)
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token

        # Reference to MainCalendar (set by MainCalendar after initialization)
        self.main_calendar = None

        # API configuration
        self.api_base = "http://127.0.0.1:8000/api/"
        self.activities_url = self.api_base + "activities/"
        self.headers = {"Authorization": f"Bearer {self.token}"}

        # Navigation callbacks
        self.navigate_back_to_activities = None

        self.setWindowTitle("Add Event")
        self.resize(1200, 700)

        # Main layout
        root = QVBoxLayout(self)

        # Top controls (navigation buttons)
        self.setup_controls(root)

        # Main content area - the form
        self.setup_form_content(root)

    def setup_controls(self, root):
        """Setup navigation controls"""
        controls = QHBoxLayout()
        
        # Title
        title_label = QLabel("Add New Event")
        title_label.setStyleSheet("font-weight: bold; color: #084924; font-size: 18px;")
        controls.addWidget(title_label)
        controls.addStretch()
        
        # Back button
        self.btn_back = QPushButton("← Back to Activities")
        self.btn_back.setStyleSheet("""
            QPushButton {
                background-color: #FDC601;
                color: #084924;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #e6b400;
                border: 2px solid #084924;
            }
        """)
        self.btn_back.clicked.connect(self.back_to_activities)
        controls.addWidget(self.btn_back)
        
        root.addLayout(controls)

    def setup_form_content(self, root):
        """Setup the main form content area with scroll capability"""
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #f0f0f0;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #084924;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #FDC601;
            }
        """)
        
        # Create scroll widget container
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background-color: transparent;")
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(10, 10, 10, 10)
        
        # Form container
        form_container = QFrame()
        form_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #084924;
                border-radius: 8px;
            }
        """)
        
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(30, 30, 30, 30)
        form_layout.setSpacing(20)

        # Event form fields
        self.setup_event_form(form_layout)
        
        # User type selection
        self.setup_user_selection(form_layout)
        
        # Action buttons
        self.setup_action_buttons(form_layout)
        
        # Add form to scroll layout
        scroll_layout.addWidget(form_container)
        scroll_layout.addStretch()
        
        # Set scroll widget
        scroll_area.setWidget(scroll_widget)
        
        root.addWidget(scroll_area)

    def customize_calendar(self, calendar):
        """Customize the calendar widget appearance and behavior"""
        # Set minimum size for calendar
        calendar.setMinimumSize(400, 350)
        
        # Style the calendar
        calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: white;
                border: 2px solid #084924;
                border-radius: 8px;
            }
            
            /* Navigation bar */
            QCalendarWidget QToolButton {
                background-color: #084924;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                margin: 3px;
                font-weight: bold;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #FDC601;
                color: #084924;
            }
            QCalendarWidget QToolButton::menu-indicator {
                image: none;
            }
            
            /* Month/Year selection */
            QCalendarWidget QMenu {
                background-color: white;
                border: 1px solid #084924;
            }
            QCalendarWidget QSpinBox {
                background-color: white;
                border: 1px solid #084924;
                border-radius: 4px;
                padding: 5px;
                font-weight: bold;
                color: #084924;
            }
            
            /* Header (days of week) */
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #084924;
            }
            QCalendarWidget QAbstractItemView:enabled {
                background-color: white;
                selection-background-color: #FDC601;
                selection-color: #084924;
                font-size: 13px;
            }
            
            /* Day cells */
            QCalendarWidget QAbstractItemView {
                gridline-color: #e0e0e0;
                alternate-background-color: #f8f9fa;
            }
            
            /* Selected date */
            QCalendarWidget QAbstractItemView:enabled {
                color: #084924;
            }
            QCalendarWidget QAbstractItemView:disabled {
                color: #cccccc;
            }
        """)
        
        # Set grid to be visible
        calendar.setGridVisible(True)
        
        # Set first day of week to Sunday (optional)
        calendar.setFirstDayOfWeek(Qt.DayOfWeek.Sunday)

    def setup_event_form(self, form_layout):
        """Setup the event form fields with 12-hour time format and FIXED calendar"""
        # Form fields container
        fields_container = QFrame()
        fields_container.setStyleSheet("""
            QFrame {
                border: 2px solid #ddd;
                border-radius: 6px;
                background-color: #f9f9f9;
                padding: 20px;
            }
        """)
        
        grid_layout = QGridLayout(fields_container)
        grid_layout.setSpacing(20)
        grid_layout.setContentsMargins(20, 20, 20, 20)
        grid_layout.setVerticalSpacing(25)
        grid_layout.setHorizontalSpacing(20)
        
        # Set column stretch
        grid_layout.setColumnStretch(0, 0)
        grid_layout.setColumnStretch(1, 2)
        grid_layout.setColumnStretch(2, 0)
        grid_layout.setColumnStretch(3, 2)
        
        # Set minimum column widths
        grid_layout.setColumnMinimumWidth(0, 130)
        grid_layout.setColumnMinimumWidth(1, 200)
        grid_layout.setColumnMinimumWidth(2, 130)
        grid_layout.setColumnMinimumWidth(3, 200)
        
        # Styling
        input_style = """
            QLineEdit, QComboBox, QDateEdit, QTimeEdit, QTextEdit {
                border: 1px solid #ccc;
                border-radius: 6px;
                padding: 12px;
                background-color: white;
                font-size: 14px;
                min-height: 40px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTimeEdit:focus, QTextEdit:focus {
                border-color: #FDC601;
                border-width: 2px;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            QDateEdit::drop-down {
                border: none;
                width: 25px;
                subcontrol-origin: padding;
                subcontrol-position: center right;
            }
            QDateEdit::down-arrow {
                image: none;
                border: 2px solid #084924;
                width: 8px;
                height: 8px;
                border-left: 0;
                border-top: 0;
                margin-right: 5px;
            }
        """
        
        label_style = """
            font-weight: bold; 
            color: #084924; 
            font-size: 14px; 
            padding-bottom: 5px;
        """
        
        # Row 0: Event Title and Description
        row = 0
        label_title = QLabel("Event Title")
        label_title.setStyleSheet(label_style)
        grid_layout.addWidget(label_title, row, 0, Qt.AlignmentFlag.AlignTop)
        
        self.input_event_title = QLineEdit()
        self.input_event_title.setPlaceholderText("Input Event Title Here")
        self.input_event_title.setStyleSheet(input_style)
        grid_layout.addWidget(self.input_event_title, row, 1)
        
        label_desc = QLabel("Description")
        label_desc.setStyleSheet(label_style)
        grid_layout.addWidget(label_desc, row, 2, Qt.AlignmentFlag.AlignTop)
        
        self.input_description = QTextEdit()
        self.input_description.setPlaceholderText("(Optional)")
        self.input_description.setMaximumHeight(100)
        self.input_description.setMinimumHeight(100)
        self.input_description.setStyleSheet(input_style)
        grid_layout.addWidget(self.input_description, row, 3)
        
        # Row 1: Event Type and Location
        row = 1
        label_type = QLabel("Event Type")
        label_type.setStyleSheet(label_style)
        grid_layout.addWidget(label_type, row, 0, Qt.AlignmentFlag.AlignTop)
        
        self.combo_event_type = QComboBox()
        self.combo_event_type.addItems([
            "Select Event Type",
            "Academic",
            "Organizational",
            "Deadline",
            "Holiday"
        ])
        self.combo_event_type.setStyleSheet(input_style)
        grid_layout.addWidget(self.combo_event_type, row, 1)
        
        label_location = QLabel("Location/Venue")
        label_location.setStyleSheet(label_style)
        grid_layout.addWidget(label_location, row, 2, Qt.AlignmentFlag.AlignTop)
        
        self.input_location = QLineEdit()
        self.input_location.setPlaceholderText("(Optional)")
        self.input_location.setStyleSheet(input_style)
        grid_layout.addWidget(self.input_location, row, 3)
        
        # Row 2: Start Date and Start Time
        row = 2
        label_start_date = QLabel("Start Date")
        label_start_date.setStyleSheet(label_style)
        grid_layout.addWidget(label_start_date, row, 0, Qt.AlignmentFlag.AlignTop)
        
        self.date_start = QDateEdit()
        self.date_start.setDate(QDate.currentDate())
        self.date_start.setCalendarPopup(True)
        self.date_start.setDisplayFormat("MM/dd/yyyy")
        self.date_start.setStyleSheet(input_style)
        
        # Get and customize the calendar widget
        start_calendar = self.date_start.calendarWidget()
        if start_calendar is None:
            start_calendar = QCalendarWidget()
            self.date_start.setCalendarWidget(start_calendar)
        self.customize_calendar(start_calendar)
        
        grid_layout.addWidget(self.date_start, row, 1)
        
        label_start_time = QLabel("Start Time")
        label_start_time.setStyleSheet(label_style)
        grid_layout.addWidget(label_start_time, row, 2, Qt.AlignmentFlag.AlignTop)
        
        # Start time with AM/PM
        start_time_widget = QWidget()
        start_time_layout = QHBoxLayout(start_time_widget)
        start_time_layout.setContentsMargins(0, 0, 0, 0)
        start_time_layout.setSpacing(5)
        
        self.time_start = QTimeEdit()
        self.time_start.setTime(QTime(9, 0))
        self.time_start.setDisplayFormat("h:mm")
        self.time_start.setTimeRange(QTime(1, 0), QTime(12, 59))
        self.time_start.setStyleSheet(input_style)
        start_time_layout.addWidget(self.time_start, 1)
        
        ampm_style = """
            QPushButton {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #FDC601;
                color: #084924;
                font-weight: bold;
            }
        """
        
        self.btn_start_am = QPushButton("AM")
        self.btn_start_am.setCheckable(True)
        self.btn_start_am.setChecked(True)
        self.btn_start_am.setFixedSize(40, 35)
        self.btn_start_am.setStyleSheet(ampm_style)
        self.btn_start_am.clicked.connect(lambda: self.set_am_pm(self.btn_start_am, self.btn_start_pm))
        
        self.btn_start_pm = QPushButton("PM")
        self.btn_start_pm.setCheckable(True)
        self.btn_start_pm.setFixedSize(40, 35)
        self.btn_start_pm.setStyleSheet(ampm_style)
        self.btn_start_pm.clicked.connect(lambda: self.set_am_pm(self.btn_start_pm, self.btn_start_am))
        
        start_time_layout.addWidget(self.btn_start_am)
        start_time_layout.addWidget(self.btn_start_pm)
        grid_layout.addWidget(start_time_widget, row, 3)
        
        # Row 3: End Date and End Time
        row = 3
        label_end_date = QLabel("End Date")
        label_end_date.setStyleSheet(label_style)
        grid_layout.addWidget(label_end_date, row, 0, Qt.AlignmentFlag.AlignTop)
        
        self.date_end = QDateEdit()
        self.date_end.setDate(QDate.currentDate())
        self.date_end.setCalendarPopup(True)
        self.date_end.setDisplayFormat("MM/dd/yyyy")
        self.date_end.setStyleSheet(input_style)
        
        # Get and customize the end date calendar widget
        end_calendar = self.date_end.calendarWidget()
        if end_calendar is None:
            end_calendar = QCalendarWidget()
            self.date_end.setCalendarWidget(end_calendar)
        self.customize_calendar(end_calendar)
        
        grid_layout.addWidget(self.date_end, row, 1)
        
        label_end_time = QLabel("End Time")
        label_end_time.setStyleSheet(label_style)
        grid_layout.addWidget(label_end_time, row, 2, Qt.AlignmentFlag.AlignTop)
        
        # End time with AM/PM
        end_time_widget = QWidget()
        end_time_layout = QHBoxLayout(end_time_widget)
        end_time_layout.setContentsMargins(0, 0, 0, 0)
        end_time_layout.setSpacing(5)
        
        self.time_end = QTimeEdit()
        self.time_end.setTime(QTime(5, 0))
        self.time_end.setDisplayFormat("h:mm")
        self.time_end.setTimeRange(QTime(1, 0), QTime(12, 59))
        self.time_end.setStyleSheet(input_style)
        end_time_layout.addWidget(self.time_end, 1)
        
        self.btn_end_am = QPushButton("AM")
        self.btn_end_am.setCheckable(True)
        self.btn_end_am.setFixedSize(40, 35)
        self.btn_end_am.setStyleSheet(ampm_style)
        self.btn_end_am.clicked.connect(lambda: self.set_am_pm(self.btn_end_am, self.btn_end_pm))
        
        self.btn_end_pm = QPushButton("PM")
        self.btn_end_pm.setCheckable(True)
        self.btn_end_pm.setChecked(True)
        self.btn_end_pm.setFixedSize(40, 35)
        self.btn_end_pm.setStyleSheet(ampm_style)
        self.btn_end_pm.clicked.connect(lambda: self.set_am_pm(self.btn_end_pm, self.btn_end_am))
        
        end_time_layout.addWidget(self.btn_end_am)
        end_time_layout.addWidget(self.btn_end_pm)
        grid_layout.addWidget(end_time_widget, row, 3)
        
        form_layout.addWidget(fields_container)

    def setup_user_selection(self, form_layout):
        """Setup user type selection checkboxes"""
        user_container = QFrame()
        user_container.setStyleSheet("""
            QFrame {
                border: 2px solid #ddd;
                border-radius: 6px;
                background-color: #f9f9f9;
                padding: 20px;
            }
        """)
        
        user_layout = QVBoxLayout(user_container)
        user_layout.setSpacing(15)
        
        title = QLabel("Target Audience")
        title.setStyleSheet("font-weight: bold; color: #084924; font-size: 16px; padding-bottom: 10px;")
        user_layout.addWidget(title)
        
        checkboxes_layout = QHBoxLayout()
        checkboxes_layout.setSpacing(25)
        
        checkbox_style = """
            QCheckBox {
                font-size: 14px;
                color: #084924;
                spacing: 12px;
                padding: 8px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #ccc;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #084924;
                border-radius: 3px;
                background-color: #FDC601;
            }
        """
        
        self.check_students = QCheckBox("Students")
        self.check_students.setStyleSheet(checkbox_style)
        checkboxes_layout.addWidget(self.check_students)
        
        self.check_faculty = QCheckBox("Faculty")
        self.check_faculty.setStyleSheet(checkbox_style)
        checkboxes_layout.addWidget(self.check_faculty)
        
        self.check_org_officer = QCheckBox("Organization Officer")
        self.check_org_officer.setStyleSheet(checkbox_style)
        checkboxes_layout.addWidget(self.check_org_officer)
        
        self.check_all = QCheckBox("All")
        self.check_all.setStyleSheet(checkbox_style)
        self.check_all.stateChanged.connect(self.toggle_all_users)
        checkboxes_layout.addWidget(self.check_all)
        
        checkboxes_layout.addStretch()
        user_layout.addLayout(checkboxes_layout)
        
        form_layout.addWidget(user_container)

    def setup_action_buttons(self, form_layout):
        """Setup save and cancel buttons"""
        # Add some spacing before buttons
        form_layout.addSpacing(10)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setFixedSize(120, 50)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #666;
                border: 1px solid #ccc;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border: 2px solid #999;
            }
        """)
        self.btn_cancel.clicked.connect(self.cancel_event)
        buttons_layout.addWidget(self.btn_cancel)
        
        # Add spacing between buttons
        buttons_layout.addSpacing(15)
        
        self.btn_save = QPushButton("Save Event")
        self.btn_save.setFixedSize(140, 50)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #084924;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0a5228;
            }
            QPushButton:pressed {
                background-color: #063318;
            }
        """)
        self.btn_save.clicked.connect(self.save_event)
        buttons_layout.addWidget(self.btn_save)
        
        form_layout.addLayout(buttons_layout)

    # Event handlers
    def set_am_pm(self, selected_btn, other_btn):
        """Handle AM/PM button selection"""
        selected_btn.setChecked(True)
        other_btn.setChecked(False)

    def toggle_all_users(self):
        """Handle the 'All' checkbox"""
        is_checked = self.check_all.isChecked()
        self.check_students.setChecked(is_checked)
        self.check_faculty.setChecked(is_checked)
        self.check_org_officer.setChecked(is_checked)

    def back_to_activities(self):
        """Navigate back to activities"""
        if self.navigate_back_to_activities:
            self.navigate_back_to_activities()
        else:
            self._info("Navigation not configured")

    def save_event(self):
        """Handle save event action - saves to JSON through MainCalendar"""
        # Validate inputs
        event_title = self.input_event_title.text().strip()
        event_type = self.combo_event_type.currentText()
        
        if not event_title:
            self._error("Please enter an event title.")
            return
            
        if event_type == "Select Event Type":
            self._error("Please select an event type.")
            return
        
        # Get start date and time
        start_date = self.date_start.date()
        start_time = self.time_start.time()
        
        # Convert to 24-hour format based on AM/PM selection
        start_hour = start_time.hour()
        if self.btn_start_pm.isChecked() and start_hour != 12:
            start_hour += 12
        elif self.btn_start_am.isChecked() and start_hour == 12:
            start_hour = 0
        
        # Format start date/time
        start_time_str = QTime(start_hour, start_time.minute()).toString("h:mm AP")
        date_time_str = f"{start_date.toString('M/d/yyyy')}\n{start_time_str}"
        
        # Get location (optional)
        location = self.input_location.text().strip() if self.input_location.text().strip() else "N/A"
        
        # Create event data matching the JSON format
        event_data = {
            "date_time": date_time_str,
            "event": event_title,
            "type": event_type,
            "location": location,
            "status": "Upcoming"  # Default status for new events
        }
        
        # Save through MainCalendar
        if self.main_calendar:
            if self.main_calendar.add_new_event(event_data):
                QMessageBox.information(self, "Success", f"Event '{event_title}' has been saved successfully!")
                self.clear_form()
                # Navigate back to activities
                if self.navigate_back_to_activities:
                    self.navigate_back_to_activities()
            else:
                self._error("Failed to save event. Please try again.")
        else:
            self._error("Cannot save event: MainCalendar reference not set.")

    def cancel_event(self):
        """Handle cancel action"""
        self.clear_form()
        if self.navigate_back_to_activities:
            self.navigate_back_to_activities()

    def clear_form(self):
        """Clear all form fields"""
        self.input_event_title.clear()
        self.input_description.clear()
        self.input_location.clear()
        self.combo_event_type.setCurrentIndex(0)
        self.date_start.setDate(QDate.currentDate())
        self.date_end.setDate(QDate.currentDate())
        self.time_start.setTime(QTime(9, 0))
        self.time_end.setTime(QTime(5, 0))
        self.btn_start_am.setChecked(True)
        self.btn_start_pm.setChecked(False)
        self.btn_end_am.setChecked(False)
        self.btn_end_pm.setChecked(True)
        self.check_students.setChecked(False)
        self.check_faculty.setChecked(False)
        self.check_org_officer.setChecked(False)
        self.check_all.setChecked(False)

    def _info(self, msg):
        QMessageBox.information(self, "Info", str(msg))

    def _error(self, msg):
        QMessageBox.critical(self, "Error", str(msg))