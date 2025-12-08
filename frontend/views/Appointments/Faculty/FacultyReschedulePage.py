from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QWidget, QMessageBox
import logging
from datetime import datetime
from ..api_client import APIClient

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class FacultyReschedulePage_ui(QWidget):
    back = QtCore.pyqtSignal()
    reschedule_completed = QtCore.pyqtSignal()  # New signal to notify when reschedule is done

    def __init__(self, username, roles, primary_role, token, selected_appointment_id, parent=None):
        super().__init__(parent)
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        self.crud = APIClient(token)
        self.faculty_id = self._get_faculty_id()
        self.selected_appointment_id = selected_appointment_id  # To be set externally
        print(f"Test: {self.selected_appointment_id}")
        self.available_days = set()  # Store available days for highlighting
        self.slot_buttons = []  # Initialize slot_buttons here
        self.selected_slot_entry_id = None
        self.selected_start_time = None
        self.selected_end_time = None
        self.selected_date = None
        self.original_appointment_data = None  # Store original appointment data
        
        self._setupFacultyReschedulePage()
        self.retranslateUi()
        self._load_appointment_details()
        self._loadAvailableSlots()  # Load available slots for calendar highlighting
        self.setFixedSize(1000, 550)

    def get_student_name(self, student_id):
            students = self.crud.get_students()
            print(f"Students list: {students}")
            for student in students:
                print(f"{student}")
                print("Hello Lord!")
                if int(student["id"]) == int(student_id):
                    return student['full_name']

    def _is_past_appointment(self, selected_date, start_time):
        """Check if the selected appointment date and time is in the past"""
        try:
            # Combine date and time into a datetime object
            appointment_datetime_str = f"{selected_date} {start_time}"
            
            # Parse the appointment datetime
            if ':' in start_time:
                time_parts = start_time.split(':')
                if len(time_parts) == 2:  # If only HH:MM, add seconds
                    start_time = start_time + ':00'
                appointment_datetime_str = f"{selected_date} {start_time}"
            
            appointment_datetime = datetime.strptime(appointment_datetime_str, "%Y-%m-%d %H:%M:%S")
            current_datetime = datetime.now()
            
            # Return True if appointment datetime is in the past
            return appointment_datetime < current_datetime
            
        except Exception as e:
            print(f"Error checking appointment datetime: {e}")
            return False

    def _get_faculty_id(self):
        faculty_list = self.crud.get_faculties()
        logging.debug(f"Faculty list: {faculty_list}")
        for faculty in faculty_list:
            if faculty["user"]["first_name"] == self.username:
                logging.debug(f"Found faculty: {faculty['user']['first_name']} with ID: {faculty['id']}")
                return faculty["id"]
        logging.warning(f"No faculty found for username: {self.username}, using fallback ID: 1")
        return 1

    def _load_appointment_details(self):
        """Load and display details of the selected appointment."""
        if not self.selected_appointment_id:
            logging.warning("No selected appointment ID")
            return
        
        appointments = self.crud.get_faculty_appointments()
        self.original_appointment_data = next((a for a in appointments if a["id"] == self.selected_appointment_id), None)
        print(self.original_appointment_data)
        self.label_29.setText(self.get_student_name(self.original_appointment_data['student']) if self.original_appointment_data else "Student Name")
        if self.original_appointment_data:
            logging.debug(f"Loaded appointment: {self.original_appointment_data}")
            # Update UI with appointment details
            original_date = self.original_appointment_data.get('appointment_date', 'N/A')
            original_time = self.original_appointment_data.get('start_time', 'N/A')
            original_end_time = self.original_appointment_data.get('end_time', 'N/A')
            
            # Format the date for display
            try:
                date_obj = datetime.strptime(original_date, '%Y-%m-%d')
                formatted_date = date_obj.strftime('%B %d, %Y')
            except:
                formatted_date = original_date
            
            self.subtitle.setText(f"Reschedule Appointment - {formatted_date} {original_time} to {original_end_time}")
            
            # Set the current appointment date as initially selected in calendar
            try:
                date_obj = datetime.strptime(original_date, '%Y-%m-%d')
                qt_date = QtCore.QDate(date_obj.year, date_obj.month, date_obj.day)
                self.calendarWidget.setSelectedDate(qt_date)
                self._updateAvailableSlots()  # Load slots for the original date
            except:
                pass

    def _loadAvailableSlots(self):
        """Load availability rules for the faculty to extract available days for calendar highlighting"""
        try:
            # Get availability rules for the faculty
            availability_rules = self.crud.get_availability_rules(faculty_id=self.faculty_id)
            
            if availability_rules:
                self.availability_rules = availability_rules
                # Extract available days from availability rules for calendar highlighting
                self._extractAvailableDays()
            else:
                logging.warning(f"No availability rules found for faculty ID: {self.faculty_id}")
                self.availability_rules = []
                
        except Exception as e:
            print(f"Error loading availability rules: {e}")
            logging.error(f"Failed to load availability rules: {str(e)}")
            self.availability_rules = []

    def _extractAvailableDays(self):
        """Extract available days from availability rules for calendar highlighting"""
        self.available_days.clear()
        
        if not hasattr(self, 'availability_rules') or not self.availability_rules:
            return
            
        # Map day names from your availability rules to numbers (Monday=1, Sunday=7)
        day_mapping = {
            "MON": 1, "TUE": 2, "WED": 3, 
            "THU": 4, "FRI": 5, "SAT": 6, "SUN": 7
        }
        
        for rule in self.availability_rules:
            day_name = rule.get('day_of_week', '')
            if day_name in day_mapping:
                self.available_days.add(day_mapping[day_name])
        
        logging.debug(f"Available days for faculty: {self.available_days}")
        
        # Update calendar highlighting
        self._updateCalendarHighlighting()

    def _updateCalendarHighlighting(self):
        """Update calendar to highlight available days"""
        if not self.available_days:
            return
            
        # Create a text char format for available days
        available_format = QtGui.QTextCharFormat()
        available_format.setBackground(QtGui.QBrush(QtGui.QColor("#FFF9C4")))  # Light yellow
        available_format.setForeground(QtGui.QBrush(QtGui.QColor("#000000")))  # Black text
        
        # Apply the format to available days
        for day_number in self.available_days:
            self.calendarWidget.setWeekdayTextFormat(
                QtCore.Qt.DayOfWeek(day_number), 
                available_format
            )

    def _setupFacultyReschedulePage(self):
        self.setObjectName("facultyreschedule")
        reschedule_layout = QtWidgets.QVBoxLayout(self)
        reschedule_layout.setContentsMargins(10, 10, 10, 10)
        reschedule_layout.setSpacing(10)

        header_widget = QtWidgets.QWidget()
        header_layout = QtWidgets.QHBoxLayout(header_widget)
        header_layout.setContentsMargins(30, 0, 30, 0)

        self.FacultyListPage = QtWidgets.QLabel()
        font = QtGui.QFont("Poppins", 24)
        self.FacultyListPage.setFont(font)
        self.FacultyListPage.setStyleSheet("QLabel { color: #084924; }")
        header_layout.addWidget(self.FacultyListPage)
        header_layout.addStretch(1)

        self.backButton = QtWidgets.QPushButton("<- Back")
        self.backButton.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #084924, stop:1 #0a5a2f);
                color: white;
                border: none;
                border-radius: 8px;
                font: 600 11pt 'Poppins';
                padding: 8px 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0a5a2f, stop:1 #0c6b3a);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #06381b, stop:1 #084924);
            }
        """)
        self.backButton.setFixedSize(100, 40)
        self.backButton.clicked.connect(self.back.emit)
        header_layout.addWidget(self.backButton)

        reschedule_layout.addWidget(header_widget)

        self.widget_3 = QtWidgets.QWidget()
        self.widget_3.setStyleSheet("QWidget#widget_3 { background-color: #FFFFFF; border-radius: 20px; }")
        widget_layout = QtWidgets.QVBoxLayout(self.widget_3)
        widget_layout.setContentsMargins(10, 0, 10, 0)
        widget_layout.setSpacing(5)

        self.nameheader = QtWidgets.QFrame()
        self.nameheader.setStyleSheet("QFrame#nameheader { background: #ffffff; border-radius: 12px; }")
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 3)
        shadow.setColor(QtGui.QColor(0, 0, 0, 60))
        self.nameheader.setGraphicsEffect(shadow)
        nameheader_layout = QtWidgets.QHBoxLayout(self.nameheader)
        nameheader_layout.setContentsMargins(20, 0, 20, 0)
        nameheader_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.label_32 = QtWidgets.QLabel()
        self.label_32.setFixedSize(50, 50)
        self.label_32.setStyleSheet("QLabel { background: #4285F4; border-radius: 25px; border: 2px solid white; }")
        print(f"Original appointment data: {self.original_appointment_data}")
        self.label_29 = QtWidgets.QLabel()
        font = QtGui.QFont("Poppins", 18, QtGui.QFont.Weight.Bold)
        self.label_29.setFont(font)
        self.label_29.setStyleSheet("color: #084924;")
        nameheader_layout.addWidget(self.label_32)
        nameheader_layout.addWidget(self.label_29, 1)

        center_layout = QtWidgets.QHBoxLayout()
        center_layout.addStretch()
        center_layout.addWidget(self.nameheader)
        center_layout.addStretch()
        widget_layout.addLayout(center_layout)

        self.subtitle = QtWidgets.QLabel("Select Date & Time")
        subtitle_font = QtGui.QFont("Poppins", 14, QtGui.QFont.Weight.Medium)
        self.subtitle.setFont(subtitle_font)
        self.subtitle.setStyleSheet("color: #084924;")
        self.subtitle.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        widget_layout.addWidget(self.subtitle)

        content_widget = QtWidgets.QWidget()
        content_layout = QtWidgets.QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(20)

        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        calendar_header = QtWidgets.QWidget()
        calendar_header_layout = QtWidgets.QHBoxLayout(calendar_header)
        self.label_30 = QtWidgets.QLabel()
        font = QtGui.QFont("Poppins", 16, QtGui.QFont.Weight.Bold)
        self.label_30.setFont(font)
        self.label_30.setStyleSheet("QLabel { color: #084924; }")
        calendar_header_layout.addWidget(self.label_30)
        calendar_header_layout.addStretch(1)
        left_layout.addWidget(calendar_header)

        month_header = QtWidgets.QLabel()
        font = QtGui.QFont("Poppins", 14, QtGui.QFont.Weight.Bold)
        month_header.setFont(font)
        month_header.setStyleSheet("QLabel { color: #084924; }")
        month_header.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        month_header.setText(datetime.now().strftime("%B %Y"))
        left_layout.addWidget(month_header)

        days_widget = QtWidgets.QWidget()
        days_layout = QtWidgets.QHBoxLayout(days_widget)
        days_layout.setContentsMargins(0, 0, 0, 0)
        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for day in days:
            day_label = QtWidgets.QLabel(day)
            day_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            day_label.setStyleSheet("QLabel { color: #666666; font: 600 10pt 'Poppins'; padding: 8px 0px; }")
            days_layout.addWidget(day_label)
        left_layout.addWidget(days_widget)

        self.calendarCard = QtWidgets.QWidget()
        self.calendarCard.setStyleSheet("QWidget#calendarCard { background: #ffffff; border-radius: 12px; border: 1px solid #e0e0e0; }")
        calendar_layout = QtWidgets.QVBoxLayout(self.calendarCard)
        calendar_layout.setContentsMargins(10, 10, 10, 10)
        self.calendarWidget = QtWidgets.QCalendarWidget()
        self.calendarWidget.setVerticalHeaderFormat(QtWidgets.QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendarWidget.setHorizontalHeaderFormat(QtWidgets.QCalendarWidget.HorizontalHeaderFormat.NoHorizontalHeader)
        self.calendarWidget.setSelectedDate(QtCore.QDate.currentDate())
        
        # Set minimum date to today to prevent selecting past dates
        self.calendarWidget.setMinimumDate(QtCore.QDate.currentDate())
        
        self.calendarWidget.setStyleSheet("""
            QCalendarWidget { 
                background: #ffffff; 
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                font: 10pt 'Poppins';
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar { 
                background: transparent; 
                border: none; 
                margin: 10px; 
            }
            QCalendarWidget QToolButton { 
                background: transparent; 
                color: #084924; 
                font: bold 12pt 'Poppins'; 
                border: none; 
                padding: 5px; 
            }
            QCalendarWidget QToolButton:hover { 
                color: #0a5a2f; 
            }
            QCalendarWidget QToolButton#qt_calendar_prevmonth { 
                qproperty-icon: url(:/assets/arrow_left.png); 
                icon-size: 16px; 
            }
            QCalendarWidget QToolButton#qt_calendar_nextmonth { 
                qproperty-icon: url(:/assets/arrow_right.png); 
                icon-size: 16px; 
            }
            QCalendarWidget QToolButton#qt_calendar_monthbutton,
            QCalendarWidget QToolButton#qt_calendar_yearbutton {
                font: bold 12pt 'Poppins';
                color: #084924;
            }
            QCalendarWidget QTableView {
                selection-background-color: transparent;
                selection-color: black;
            }
            QCalendarWidget QHeaderView::section {
                background: transparent;
                color: #084924;
                font: 600 10pt 'Poppins';
                border: none;
                padding: 6px 0;
            }
            QCalendarWidget QAbstractItemView:enabled { 
                color: #084924; 
                font: 10pt 'Poppins';
                background: white;
                selection-background-color: #084924; 
                selection-color: white; 
                border-radius: 20px;
                outline: none;
            }
            QCalendarWidget QAbstractItemView:disabled { 
                color: #cccccc; 
            }
        """)
        calendar_layout.addWidget(self.calendarWidget)
        left_layout.addWidget(self.calendarCard, 1)

        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)

        self.label_31 = QtWidgets.QLabel("Available Slots")
        font = QtGui.QFont("Poppins", 16, QtGui.QFont.Weight.Bold)
        self.label_31.setFont(font)
        self.label_31.setStyleSheet("color: #084924;")
        right_layout.addWidget(self.label_31)

        self.availableSlot = QtWidgets.QFrame()
        self.availableSlot.setStyleSheet("""
            QFrame#availableSlot { 
                background: #ffffff; 
                border: 1px solid #e0e0e0; 
                border-radius: 10px;
            }
        """)
        self.availableSlot.setObjectName("availableSlot")
        available_layout = QtWidgets.QVBoxLayout(self.availableSlot)
        available_layout.setContentsMargins(15, 15, 15, 15)
        available_layout.setSpacing(10)

        # Initial message
        self.initial_message = QtWidgets.QLabel("Select a date to view available slots")
        self.initial_message.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.initial_message.setStyleSheet("""
            QLabel {
                font: 12pt 'Poppins';
                color: #666666;
                background: #f8f9fa;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        available_layout.addWidget(self.initial_message)

        self.button_4 = QtWidgets.QPushButton("Reschedule")
        self.button_4.setFixedHeight(50)
        self.button_4.setFont(QtGui.QFont("Poppins", 14, QtGui.QFont.Weight.Bold))
        self.button_4.setStyleSheet("""
            QPushButton { 
                background-color: #084924; 
                border-radius: 8px; 
                color: white; 
                font: 600 14pt 'Poppins'; 
            }
            QPushButton:hover { 
                background-color: #0a5a2f; 
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.button_4.clicked.connect(self._openRescheduleDialog)
        self.button_4.setEnabled(False)
        available_layout.addWidget(self.button_4)

        right_layout.addWidget(self.availableSlot, 1)
        content_layout.addWidget(left_widget, 1)
        content_layout.addWidget(right_widget, 1)
        widget_layout.addWidget(content_widget, 1)
        reschedule_layout.addWidget(self.widget_3, 1)
        
        # Connect calendar selection change
        self.calendarWidget.selectionChanged.connect(self._updateAvailableSlots)

    def resizeEvent(self, event):
        """Adjust slot buttons and calendar size dynamically."""
        # Only resize if there are slot buttons
        if hasattr(self, 'slot_buttons') and self.slot_buttons:
            width = self.availableSlot.width()
            num_slots = max(1, len(self.slot_buttons))
            for btn in self.slot_buttons:
                btn.setFixedWidth(int(width / min(num_slots, 3)) - 12)
        
        # Set minimum calendar size
        self.calendarWidget.setMinimumSize(int(self.widget_3.width() * 0.45), 300)
        super().resizeEvent(event)

    def _updateAvailableSlots(self):
        """Update available slots when date is selected"""
        date = self.calendarWidget.selectedDate()
        selected_date_str = date.toString('yyyy-MM-dd')
        self.selected_date = selected_date_str
        
        # Clear existing slot buttons
        for btn in self.slot_buttons:
            btn.deleteLater()
        self.slot_buttons.clear()
        
        # Clear the available slot area except the button
        layout = self.availableSlot.layout()
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if widget and widget != self.button_4 and widget != self.initial_message:
                widget.deleteLater()
        
        # Hide initial message
        self.initial_message.hide()
        
        # Get available schedule for the selected date using the API endpoint
        available_schedule = self.crud.get_faculty_available_schedule(self.faculty_id, selected_date_str)
        
        if not available_schedule:
            logging.warning(f"No available schedule found for faculty {self.faculty_id} on {selected_date_str}")
            no_slots_label = QtWidgets.QLabel("No available time slots")
            no_slots_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            no_slots_label.setStyleSheet("""
                QLabel {
                    font: 12pt 'Poppins';
                    color: #666666;
                    background: #f8f9fa;
                    border-radius: 8px;
                    padding: 20px;
                }
            """)
            layout.insertWidget(0, no_slots_label)
            self.button_4.setEnabled(False)
            return
        
        if len(available_schedule) == 0:
            no_slots_label = QtWidgets.QLabel(f"No available slots for {date.toString('dddd')}")
            no_slots_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            no_slots_label.setStyleSheet("""
                QLabel {
                    font: 12pt 'Poppins';
                    color: #666666;
                    background: #f8f9fa;
                    border-radius: 8px;
                    padding: 20px;
                }
            """)
            layout.insertWidget(0, no_slots_label)
            self.button_4.setEnabled(False)
            return
        
        # Create scroll area for slots
        slots_scroll = QtWidgets.QScrollArea()
        slots_scroll.setWidgetResizable(True)
        slots_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        slots_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        slots_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #f0f0f0;
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 4px;
                min-height: 20px;
            }
        """)
        
        slots_container = QtWidgets.QWidget()
        slots_layout = QtWidgets.QVBoxLayout(slots_container)
        slots_layout.setContentsMargins(5, 5, 5, 5)
        slots_layout.setSpacing(8)
        
        # Create buttons for each available time slot
        for i, slot in enumerate(available_schedule):
            start_time = slot.get('start', '').split('T')[1][:5] if 'T' in str(slot.get('start', '')) else str(slot.get('start', ''))[:5]
            end_time = slot.get('end', '').split('T')[1][:5] if 'T' in str(slot.get('end', '')) else str(slot.get('end', ''))[:5]
            time_text = f"{start_time} - {end_time}"
            
            btn = QtWidgets.QPushButton(time_text)
            btn.setFixedHeight(45)
            btn.setCheckable(True)
            
            # Check if this slot is in the past
            is_past = self._is_past_appointment(selected_date_str, start_time)
            
            if is_past:
                # Slot is in the past - disable it
                btn.setEnabled(False)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ffcdd2;
                        color: #b71c1c;
                        border: 2px solid #f44336;
                        border-radius: 8px;
                        padding: 10px 20px;
                        font: 600 11pt 'Poppins';
                    }
                """)
                btn.setToolTip("This time slot has already passed")
            else:
                # Slot is available
                btn.setStyleSheet(self.slot_style(default=True))
                btn.clicked.connect(lambda checked, b=btn, s=start_time, e=end_time: self.select_slot(b, start_time=s, end_time=e))
                btn.setToolTip("Click to select this time slot")
            
            # Store time information
            btn.setProperty("start_time", start_time)
            btn.setProperty("end_time", end_time)
            btn.setProperty("slot_index", i)
            
            slots_layout.addWidget(btn)
            self.slot_buttons.append(btn)
        
        slots_layout.addStretch(1)
        slots_scroll.setWidget(slots_container)
        layout.insertWidget(0, slots_scroll)
        
        # Enable the first available (non-past) slot by default
        available_buttons = [btn for btn in self.slot_buttons if btn.isEnabled()]
        if available_buttons:
            available_buttons[0].setChecked(True)
            available_buttons[0].setStyleSheet(self.slot_style(selected=True))
            self.selected_start_time = available_buttons[0].property("start_time")
            self.selected_end_time = available_buttons[0].property("end_time")
            self.button_4.setEnabled(True)
            
            # Find the corresponding schedule entry for the selected time
            self._find_schedule_entry_for_time(selected_date_str, self.selected_start_time)
        else:
            self.button_4.setEnabled(False)
            self.selected_slot_entry_id = None
            self.selected_start_time = None
            self.selected_end_time = None
            if self.slot_buttons:  # If there are slots but all are in the past
                past_slots_label = QtWidgets.QLabel("All time slots for this date have passed")
                past_slots_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                past_slots_label.setStyleSheet("""
                    QLabel {
                        font: 12pt 'Poppins';
                        color: #d32f2f;
                        background: #ffebee;
                        border-radius: 8px;
                        padding: 20px;
                    }
                """)
                layout.insertWidget(0, past_slots_label)

    def _find_schedule_entry_for_time(self, date_str, start_time):
        """Find the schedule entry ID for the selected time"""
        # Since we don't have direct schedule entry IDs from available_schedule,
        # we need to find it based on the time and date
        # This is a simplified approach - you may need to adjust based on your actual data structure
        
        # Get availability rules for the day of week
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        day_of_week_num = date_obj.weekday()
        day_mapping_num_to_str = {0: 'MON', 1: 'TUE', 2: 'WED', 3: 'THU', 4: 'FRI', 5: 'SAT', 6: 'SUN'}
        day_of_week = day_mapping_num_to_str.get(day_of_week_num, '')
        
        if hasattr(self, 'availability_rules') and self.availability_rules:
            for rule in self.availability_rules:
                if rule.get('day_of_week') == day_of_week:
                    # For now, we'll use the rule ID as schedule_entry_id
                    # You may need to adjust this based on your actual data model
                    self.selected_slot_entry_id = rule.get('id')
                    logging.debug(f"Found schedule entry ID {self.selected_slot_entry_id} for {day_of_week} at {start_time}")
                    break
        
        if not self.selected_slot_entry_id:
            logging.warning(f"Could not find schedule entry for {date_str} at {start_time}")
            # Try to get it from the appointment data if it exists
            if self.original_appointment_data:
                self.selected_slot_entry_id = self.original_appointment_data.get('appointment_schedule_entry_id')
                logging.debug(f"Using original appointment schedule entry ID: {self.selected_slot_entry_id}")

    def slot_style(self, default=False, selected=False):
        """Style for slot buttons."""
        if selected:
            return """
            QPushButton { 
                background-color: #084924; 
                color: white; 
                border: 2px solid #084924; 
                border-radius: 8px; 
                padding: 10px 20px; 
                font: 600 11pt 'Poppins'; 
            }
            QPushButton:hover {
                background-color: #0a5a2f;
            }
            QPushButton:disabled {
                background-color: #bfbfbf;
                color: #6f6f6f;
                border: 2px solid #a0a0a0;
            }
            """
        else:
            return """
            QPushButton { 
                background-color: #ffffff; 
                color: #333333; 
                border: 2px solid #084924; 
                border-radius: 8px; 
                padding: 10px 20px; 
                font: 600 11pt 'Poppins'; 
            }
            QPushButton:hover { 
                background-color: #f0f7f3; 
            }
            QPushButton:pressed { 
                background-color: #e0f0e8; 
            }
            QPushButton:disabled {
                background-color: #bfbfbf;
                color: #6f6f6f;
                border: 2px solid #a0a0a0;
            }
            """

    def select_slot(self, button, start_time=None, end_time=None):
        """Handle slot button selection."""
        # Only allow selection of enabled buttons
        if not button.isEnabled():
            return
            
        for btn in self.slot_buttons:
            if btn.isEnabled():  # Only reset style for enabled buttons
                btn.setChecked(False)
                btn.setStyleSheet(self.slot_style(default=True))
        button.setChecked(True)
        button.setStyleSheet(self.slot_style(selected=True))
        self.selected_start_time = button.property("start_time")
        self.selected_end_time = button.property("end_time")
        self.button_4.setEnabled(True)
        
        # Find the schedule entry for the selected time
        date_str = self.calendarWidget.selectedDate().toString('yyyy-MM-dd')
        self._find_schedule_entry_for_time(date_str, self.selected_start_time)

    def _openRescheduleDialog(self):
        """Open dialog to confirm rescheduling."""
        if not self.selected_appointment_id:
            logging.warning("No selected appointment ID for rescheduling")
            QMessageBox.warning(self, "Warning", "No appointment selected for rescheduling.")
            return
        
        if not self.selected_slot_entry_id or not self.selected_date or not self.selected_start_time or not self.selected_end_time:
            logging.warning("No slot or date selected for rescheduling")
            QMessageBox.warning(self, "Warning", "Please select a date and time slot.")
            return
        
        # Check if the selected slot is in the past
        if self._is_past_appointment(self.selected_date, self.selected_start_time):
            QMessageBox.warning(
                self, 
                "Invalid Time Slot", 
                "You cannot reschedule to a past date and time. "
                "Please select a future time slot."
            )
            return
        
        # Find the selected button for display
        selected_slot_btn = next((btn for btn in self.slot_buttons if btn.isChecked()), None)
        if not selected_slot_btn:
            QMessageBox.warning(self, "Warning", "Please select a time slot.")
            return
        
        selected_slot = selected_slot_btn.text()
        
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Reschedule Appointment")
        dlg.setModal(True)
        dlg.setFixedSize(500, 280)
        dlg.setStyleSheet("QDialog { background-color: white; border-radius: 12px; }")
        
        root = QtWidgets.QVBoxLayout(dlg)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(20)

        # Original appointment details
        original_date = self.original_appointment_data.get('appointment_date', 'N/A')
        original_time = f"{self.original_appointment_data.get('start_time', 'N/A')} to {self.original_appointment_data.get('end_time', 'N/A')}"
        
        # Format the dates
        try:
            date_obj = datetime.strptime(original_date, '%Y-%m-%d')
            formatted_original_date = date_obj.strftime('%B %d, %Y')
        except:
            formatted_original_date = original_date
            
        try:
            new_date_obj = datetime.strptime(self.selected_date, '%Y-%m-%d')
            formatted_new_date = new_date_obj.strftime('%B %d, %Y')
        except:
            formatted_new_date = self.selected_date

        # Create a more detailed confirmation message
        title = QtWidgets.QLabel("Reschedule Appointment")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("QLabel { color: #084924; font: bold 16pt 'Poppins'; }")
        root.addWidget(title)

        # Original appointment info
        original_info = QtWidgets.QLabel(f"Original: {formatted_original_date} {original_time}")
        original_info.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        original_info.setStyleSheet("QLabel { color: #666666; font: 11pt 'Poppins'; }")
        root.addWidget(original_info)

        # Arrow icon
        arrow_label = QtWidgets.QLabel("↓")
        arrow_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        arrow_label.setStyleSheet("QLabel { color: #084924; font: bold 20pt 'Poppins'; }")
        root.addWidget(arrow_label)

        # New appointment info
        new_info = QtWidgets.QLabel(f"New: {formatted_new_date} {selected_slot}")
        new_info.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        new_info.setStyleSheet("QLabel { color: #084924; font: 11pt 'Poppins'; }")
        root.addWidget(new_info)

        warning_label = QtWidgets.QLabel("Note: Rescheduling will set the appointment status to 'Pending' for faculty approval.")
        warning_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet("QLabel { color: #d32f2f; font: 10pt 'Poppins'; }")
        root.addWidget(warning_label)

        root.addStretch(1)

        btn_row = QtWidgets.QHBoxLayout()
        btn_cancel = QtWidgets.QPushButton("Cancel")
        btn_confirm = QtWidgets.QPushButton("Confirm Reschedule")
        
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: #e0e0e0;
                border-radius: 6px;
                padding: 10px 20px;
                font: 600 11pt 'Poppins';
                color: #2b2b2b;
            }
            QPushButton:hover {
                background: #d0d0d0;
            }
        """)
        
        btn_confirm.setStyleSheet("""
            QPushButton {
                background: #084924;
                border-radius: 6px;
                padding: 10px 20px;
                font: 600 11pt 'Poppins';
                color: white;
            }
            QPushButton:hover {
                background: #0a5a2f;
            }
        """)
        
        btn_cancel.clicked.connect(dlg.reject)
        
        def _confirm_clicked():
            try:
                # Final check to ensure the selected appointment isn't in the past
                if self._is_past_appointment(self.selected_date, self.selected_start_time):
                    QMessageBox.warning(
                        dlg,
                        "Invalid Time Slot",
                        "This appointment time has already passed. Please select a future time slot."
                    )
                    return
                
                # Prepare reschedule data for API
                # Format: YYYY-MM-DDTHH:MM:SS
                start_datetime_str = f"{self.selected_date}T{self.selected_start_time}:00"
                end_datetime_str = f"{self.selected_date}T{self.selected_end_time}:00"
                
                # CRITICAL FIX: Do NOT include 'status' field in the update_data
                # The Django view will automatically set it to 'pending' when rescheduling
                update_data = {
                    "start_at": start_datetime_str,
                    "end_at": end_datetime_str,
                    # Include appointment_schedule_entry_id if your serializer needs it
                    "appointment_schedule_entry_id": self.selected_slot_entry_id,
                    # Do NOT include "status" field here - let Django handle it
                }
                
                # Make the API call to reschedule
                logging.debug(f"Attempting to reschedule appointment {self.selected_appointment_id} with data: {update_data}")
                result = self.crud.update_appointment(self.selected_appointment_id, update_data)
                
                if result:
                    logging.info(f"Appointment {self.selected_appointment_id} rescheduled successfully")
                    self._showSuccessDialog("Appointment rescheduled successfully!\nStatus set to Pending for faculty approval.")
                    dlg.accept()
                    # Emit signal to notify parent that reschedule is complete
                    self.reschedule_completed.emit()
                    self.back.emit()  # Go back to previous page
                else:
                    logging.error(f"Failed to reschedule appointment {self.selected_appointment_id}")
                    QMessageBox.warning(dlg, "Error", "Failed to reschedule appointment. Please try again.")
                    
            except Exception as e:
                logging.error(f"Error rescheduling appointment: {str(e)}")
                QMessageBox.warning(dlg, "Error", f"Failed to reschedule appointment: {str(e)}")
        
        btn_confirm.clicked.connect(_confirm_clicked)
        
        btn_row.addWidget(btn_cancel)
        btn_row.addStretch(1)
        btn_row.addWidget(btn_confirm)
        root.addLayout(btn_row)
        
        dlg.exec()

    def _showSuccessDialog(self, message="Operation completed successfully!"):
        """Show success dialog after rescheduling."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Success")
        dialog.setModal(True)
        dialog.setFixedSize(450, 300)
        dialog.setStyleSheet("QDialog { background-color: white; border-radius: 10px; }")
        
        layout = QtWidgets.QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        icon_label = QtWidgets.QLabel()
        icon_label.setFixedSize(64, 64)
        icon_label.setStyleSheet("""
            QLabel {
                background-color: #4CAF50;
                border-radius: 32px;
                color: white;
                font: bold 24pt 'Poppins';
                qproperty-alignment: AlignCenter;
            }
        """)
        icon_label.setText("✓")
        layout.addWidget(icon_label, 0, QtCore.Qt.AlignmentFlag.AlignCenter)
        
        message_label = QtWidgets.QLabel(message)
        message_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        message_label.setStyleSheet("QLabel { color: #084924; font: 600 14pt 'Poppins'; }")
        layout.addWidget(message_label)
        
        ok_button = QtWidgets.QPushButton("OK")
        ok_button.setFixedHeight(40)
        ok_button.setStyleSheet("""
            QPushButton { 
                background-color: #084924; 
                color: white; 
                border-radius: 8px; 
                font: 600 12pt 'Poppins'; 
            }
            QPushButton:hover { 
                background-color: #0a5a2f; 
            }
        """)
        ok_button.clicked.connect(dialog.accept)
        layout.addWidget(ok_button)
        
        dialog.exec()

    def retranslateUi(self):
        """Set text for UI elements."""
        self.FacultyListPage.setText("Reschedule Appointment")
        self.label_30.setText("Pick a Date")
        self.label_31.setText("Available Slots")
        self.button_4.setText("Reschedule")