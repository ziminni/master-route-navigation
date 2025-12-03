from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMessageBox, QDialog, QScrollArea, QTextEdit, QComboBox, QFileDialog
from PyQt6.QtCore import QDate, QDateTime
import requests
import json
import os
import shutil
import time
import logging
from datetime import datetime
from ..api_client import APIClient

class StudentRequestPage_ui(QWidget):
    back = QtCore.pyqtSignal()
    backrefreshdata = QtCore.pyqtSignal()
    
    def __init__(self, username, roles, primary_role, token, parent=None):
        super().__init__(parent)
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        self.appointment_crud = APIClient(token=token)
        self.selected_faculty = None
        self.selected_date = None
        self.selected_slot = None
        self.slot_buttons = []
        self.slots_container = None
        self.available_days = set()
        self.setFixedSize(1000, 550)
        self._setupStudentRequestPage()
        self.retranslateUi()

    def _is_past_appointment(self, selected_date, start_time_str):
        """Check if the selected appointment date and time is in the past"""
        try:
            # Parse start time string (can be HH:MM or HH:MM:SS or full datetime with Z)
            if 'T' in start_time_str:
                # It's a full datetime string like '2025-12-08T09:30:00Z'
                try:
                    # Try parsing with Z timezone
                    if start_time_str.endswith('Z'):
                        dt_str = start_time_str.replace('Z', '')
                        appointment_datetime = datetime.fromisoformat(dt_str)
                    else:
                        appointment_datetime = datetime.fromisoformat(start_time_str)
                except ValueError:
                    # Fallback: try parsing as string without timezone
                    date_part = start_time_str.split('T')[0]
                    time_part = start_time_str.split('T')[1].split('.')[0]  # Remove milliseconds if present
                    time_parts = time_part.split(':')
                    hour = int(time_parts[0])
                    minute = int(time_parts[1]) if len(time_parts) > 1 else 0
                    
                    date_parts = date_part.split('-')
                    year = int(date_parts[0])
                    month = int(date_parts[1])
                    day = int(date_parts[2])
                    
                    appointment_datetime = datetime(year, month, day, hour, minute)
            else:
                # It's just a time string like '09:30'
                time_parts = start_time_str.split(':')
                hour = int(time_parts[0])
                minute = int(time_parts[1]) if len(time_parts) > 1 else 0
                
                date_parts = selected_date.split('-')
                year = int(date_parts[0])
                month = int(date_parts[1])
                day = int(date_parts[2])
                
                appointment_datetime = datetime(year, month, day, hour, minute)
            
            current_datetime = datetime.now()
            
            return appointment_datetime < current_datetime
            
        except Exception as e:
            logging.error(f"Error checking appointment datetime: {e}")
            return True

    def set_faculty_data(self, faculty_data):
        """Set the faculty data when navigating from browse page"""
        print(f"DEBUG: set_faculty_data called with: {faculty_data}")
        self.selected_faculty = faculty_data
        self._updateFacultyInfo()
        self._updateCalendarForToday()

    def _updateFacultyInfo(self):
        """Update the UI with faculty information"""
        if self.selected_faculty:
            print(f"DEBUG: Updating faculty info with: {self.selected_faculty}")
            
            # Extract user info from faculty data
            user_info = self.selected_faculty.get('user', {})
            
            # Handle different possible faculty data structures
            if isinstance(user_info, dict):
                faculty_name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
                if not faculty_name:
                    faculty_name = user_info.get('username', 'Unknown Faculty')
            else:
                # If user_info is not a dict, try to get name directly
                faculty_name = self.selected_faculty.get('name', 'Unknown Faculty')
            
            print(f"DEBUG: Faculty name: {faculty_name}")
            
            self.label_29.setText(faculty_name)
            self.label_30.setText(f"Select Date & Time with {faculty_name}")
            
            # Update month header
            current_date = datetime.now()
            self.month_header.setText(current_date.strftime("%B %Y"))
        else:
            print("DEBUG: No faculty data available")
            self.label_29.setText("Select a Faculty")
            self.label_30.setText("Select Date & Time")

    def _updateCalendarForToday(self):
        """Set calendar to today's date and load available slots"""
        if not self.selected_faculty:
            print("DEBUG: Cannot update calendar - no faculty selected")
            return
            
        today = QDate.currentDate()
        self.calendarWidget.setSelectedDate(today)
        self.selected_date = today.toString('yyyy-MM-dd')
        print(f"DEBUG: Setting initial date to: {self.selected_date}")
        self._loadAvailableSlotsForDate(self.selected_date)

    def _loadAvailableSlotsForDate(self, date_str):
        """Load available slots for the selected date"""
        print(f"DEBUG: _loadAvailableSlotsForDate called with date: {date_str}")
        
        if not self.selected_faculty:
            print("DEBUG: No faculty selected, cannot load slots")
            self._showNoFacultySelectedMessage()
            return
        
        try:
            faculty_id = self.selected_faculty.get('id')
            if not faculty_id:
                print("ERROR: Faculty data has no 'id' field")
                print(f"DEBUG: Faculty data: {self.selected_faculty}")
                self._showErrorMessage("Invalid faculty data: missing ID")
                return
            
            print(f"DEBUG: Fetching slots for faculty ID: {faculty_id}, date: {date_str}")
            
            # Call API to get available slots
            available_slots = self.appointment_crud.get_faculty_available_schedule(faculty_id, date_str)
            print(f"DEBUG: API returned slots: {available_slots}")
            
            # Clear existing slot buttons
            for btn in self.slot_buttons:
                if btn:
                    btn.deleteLater()
            self.slot_buttons.clear()
            
            # Clear slots container
            if hasattr(self, "slots_container") and self.slots_container is not None:
                self.slots_container.deleteLater()
                self.slots_container = None
            
            # Clear the availableSlot widget
            self._clearAvailableSlotWidget()
            
            if available_slots and isinstance(available_slots, list) and len(available_slots) > 0:
                print(f"DEBUG: Found {len(available_slots)} available slots")
                self._displayAvailableSlots(available_slots, date_str)
            else:
                print("DEBUG: No available slots found")
                self._showNoSlotsMessage()
                
        except Exception as e:
            logging.error(f"Error loading available slots: {e}")
            print(f"ERROR: Exception in _loadAvailableSlotsForDate: {str(e)}")
            self._showErrorMessage(f"Error loading available slots: {str(e)}")

    def _clearAvailableSlotWidget(self):
        """Clear the available slot widget"""
        # Get the layout of availableSlot
        available_layout = self.availableSlot.layout()
        if available_layout:
            # Remove all widgets except the last one (which is the button_4)
            while available_layout.count() > 1:
                item = available_layout.takeAt(0)
                if item and item.widget():
                    item.widget().deleteLater()

    def _displayAvailableSlots(self, available_slots, date_str):
        """Display available slots in the UI"""
        try:
            # Create new slots container
            self.slots_container = QtWidgets.QWidget()
            self.slots_layout = QtWidgets.QVBoxLayout(self.slots_container)
            self.slots_layout.setContentsMargins(5, 5, 5, 5)
            self.slots_layout.setSpacing(8)
            
            # Create scroll area
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
            slots_scroll.setWidget(self.slots_container)
            
            # Clear existing content in availableSlot and add scroll area
            available_layout = self.availableSlot.layout()
            if available_layout:
                # Remove existing content (except button_4)
                while available_layout.count() > 0:
                    item = available_layout.takeAt(0)
                    if item and item.widget():
                        if item.widget() != self.button_4:
                            item.widget().deleteLater()
                
                # Add scroll area at the beginning
                available_layout.insertWidget(0, slots_scroll)
            
            # Create slot buttons for each available time
            for slot in available_slots:
                if not isinstance(slot, dict):
                    print(f"WARNING: Slot is not a dictionary: {slot}")
                    continue
                    
                start_time = slot.get('start')
                end_time = slot.get('end')
                
                if not start_time or not end_time:
                    print(f"WARNING: Slot missing start or end time: {slot}")
                    continue
                
                print(f"DEBUG: Processing slot: {start_time} - {end_time}")
                
                # Parse datetime strings
                time_text = ""
                slot_start_time = ""
                
                try:
                    # Handle different time formats
                    if 'T' in start_time:
                        # Try parsing ISO format (with or without Z)
                        start_time_clean = start_time.replace('Z', '')
                        end_time_clean = end_time.replace('Z', '')
                        
                        # Parse using Python datetime
                        try:
                            start_dt = datetime.fromisoformat(start_time_clean)
                            end_dt = datetime.fromisoformat(end_time_clean)
                            
                            # Format for display
                            start_formatted = start_dt.strftime('%I:%M %p')
                            end_formatted = end_dt.strftime('%I:%M %p')
                            time_text = f"{start_formatted} - {end_formatted}"
                            slot_start_time = start_dt.strftime("%H:%M")
                        except ValueError:
                            # Fallback: try QDateTime parsing
                            try:
                                start_dt = QDateTime.fromString(start_time, "yyyy-MM-ddTHH:mm:ss")
                                end_dt = QDateTime.fromString(end_time, "yyyy-MM-ddTHH:mm:ss")
                                if start_dt.isValid() and end_dt.isValid():
                                    time_text = f"{start_dt.toString('hh:mm AP')} - {end_dt.toString('hh:mm AP')}"
                                    slot_start_time = start_dt.toString("HH:mm")
                                else:
                                    # If QDateTime fails, use string splitting
                                    start_time_only = start_time.split('T')[1].split('.')[0]
                                    end_time_only = end_time.split('T')[1].split('.')[0]
                                    time_text = f"{start_time_only} - {end_time_only}"
                                    slot_start_time = start_time_only
                            except:
                                start_time_only = start_time.split('T')[1].split('.')[0]
                                end_time_only = end_time.split('T')[1].split('.')[0]
                                time_text = f"{start_time_only} - {end_time_only}"
                                slot_start_time = start_time_only
                    else:
                        # Simple time format
                        time_text = f"{start_time} - {end_time}"
                        slot_start_time = start_time
                        
                except Exception as e:
                    print(f"ERROR parsing time format: {e}")
                    # Fallback to raw strings
                    if 'T' in start_time:
                        start_time_only = start_time.split('T')[1].split('.')[0] if 'T' in start_time else start_time
                        end_time_only = end_time.split('T')[1].split('.')[0] if 'T' in end_time else end_time
                        time_text = f"{start_time_only} - {end_time_only}"
                        slot_start_time = start_time_only
                    else:
                        time_text = f"{start_time} - {end_time}"
                        slot_start_time = start_time
                
                # Create button
                btn = QtWidgets.QPushButton(time_text)
                btn.setFixedHeight(45)
                btn.setCheckable(True)
                btn.setProperty("start_time", slot_start_time)
                
                # Check if slot is in the past
                is_past = self._is_past_appointment(date_str, start_time)
                
                if is_past:
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
                    btn.setStyleSheet(self.slot_style(default=True))
                    # Use lambda with default arguments to capture current values
                    btn.clicked.connect(lambda checked, b=btn, s=slot.copy(): self.select_slot(b, s))
                
                self.slots_layout.addWidget(btn)
                self.slot_buttons.append(btn)
            
            self.slots_layout.addStretch(1)
            
            # Enable first available slot by default
            available_buttons = [btn for btn in self.slot_buttons if btn.isEnabled()]
            if available_buttons:
                available_buttons[0].setChecked(True)
                available_buttons[0].setStyleSheet(self.slot_style(selected=True))
                self.selected_slot = available_slots[0]
                if hasattr(self, 'button_4'):
                    self.button_4.setEnabled(True)
                print(f"DEBUG: Selected first slot: {self.selected_slot}")
            else:
                self.selected_slot = None
                if hasattr(self, 'button_4'):
                    self.button_4.setEnabled(False)
                
                # Show no available slots message
                no_available_label = QtWidgets.QLabel("No available time slots for this date")
                no_available_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                no_available_label.setStyleSheet("""
                    QLabel {
                        font: 12pt 'Poppins';
                        color: #666666;
                        background: #f8f9fa;
                        border-radius: 8px;
                        padding: 20px;
                    }
                """)
                self.slots_layout.insertWidget(0, no_available_label)
                
        except Exception as e:
            logging.error(f"Error displaying available slots: {e}")
            print(f"ERROR: Exception in _displayAvailableSlots: {str(e)}")
            self._showErrorMessage(f"Error displaying slots: {str(e)}")

    def _showNoFacultySelectedMessage(self):
        """Show message when no faculty is selected"""
        no_faculty_label = QtWidgets.QLabel("No faculty selected.\nPlease go back and select a faculty.")
        no_faculty_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        no_faculty_label.setStyleSheet("""
            QLabel {
                font: 12pt 'Poppins';
                color: #666666;
                background: #f8f9fa;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        no_faculty_label.setWordWrap(True)
        
        self._clearAvailableSlotWidget()
        available_layout = self.availableSlot.layout()
        if available_layout:
            available_layout.insertWidget(0, no_faculty_label)
        
        if hasattr(self, 'button_4'):
            self.button_4.setEnabled(False)

    def _showNoSlotsMessage(self):
        """Show message when no slots are available"""
        no_slots_label = QtWidgets.QLabel("No available time slots\nfor this faculty on this date")
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
        no_slots_label.setWordWrap(True)
        
        self._clearAvailableSlotWidget()
        available_layout = self.availableSlot.layout()
        if available_layout:
            available_layout.insertWidget(0, no_slots_label)
        
        self.selected_slot = None
        if hasattr(self, 'button_4'):
            self.button_4.setEnabled(False)

    def _showErrorMessage(self, message):
        """Show error message"""
        error_label = QtWidgets.QLabel(f"Error: {message}")
        error_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("""
            QLabel {
                font: 12pt 'Poppins';
                color: #d32f2f;
                background: #ffebee;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        error_label.setWordWrap(True)
        
        self._clearAvailableSlotWidget()
        available_layout = self.availableSlot.layout()
        if available_layout:
            available_layout.insertWidget(0, error_label)
        
        self.selected_slot = None
        if hasattr(self, 'button_4'):
            self.button_4.setEnabled(False)

    def _check_existing_appointments(self, start_time_str):
        """Check if student already has an appointment at this time"""
        try:
            appointments = self.appointment_crud.get_student_appointments()
            if not appointments:
                return False
            
            # Parse selected appointment time
            if 'T' in start_time_str:
                # Clean the time string
                clean_time_str = start_time_str.replace('Z', '')
                try:
                    selected_dt = datetime.fromisoformat(clean_time_str)
                except ValueError:
                    # Fallback to string parsing
                    date_part = start_time_str.split('T')[0]
                    time_part = start_time_str.split('T')[1].split('.')[0]
                    selected_dt = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M:%S")
            else:
                selected_dt = datetime.strptime(f"{self.selected_date} {start_time_str}", "%Y-%m-%d %H:%M")
            
            for appointment in appointments:
                if appointment.get('status') in ['PENDING', 'APPROVED']:
                    appt_start = appointment.get('start_at')
                    if appt_start:
                        if 'T' in appt_start:
                            clean_appt_start = appt_start.replace('Z', '')
                            try:
                                appt_dt = datetime.fromisoformat(clean_appt_start)
                            except ValueError:
                                date_part = appt_start.split('T')[0]
                                time_part = appt_start.split('T')[1].split('.')[0]
                                appt_dt = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M:%S")
                        else:
                            appt_dt = datetime.strptime(appt_start, "%Y-%m-%d %H:%M:%S")
                        
                        # Check if this is the same time
                        if appt_dt == selected_dt:
                            return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error checking existing appointments: {e}")
            print(f"ERROR in _check_existing_appointments: {e}")
            return False

    def _setupStudentRequestPage(self):
        self.setObjectName("facultyreschedule")
        
        reschedule_layout = QtWidgets.QVBoxLayout(self)
        reschedule_layout.setContentsMargins(0, 0, 0, 0)
        reschedule_layout.setSpacing(10)
        
        # Header section
        header_widget = QtWidgets.QWidget()
        header_layout = QtWidgets.QHBoxLayout(header_widget)
        header_layout.setContentsMargins(30, 0, 30, 0)
        
        self.FacultyListPage = QtWidgets.QLabel()
        font = QtGui.QFont()
        font.setFamily("Poppins")
        font.setPointSize(24)
        self.FacultyListPage.setFont(font)
        self.FacultyListPage.setStyleSheet("QLabel { color: #084924; }")
        self.FacultyListPage.setObjectName("FacultyListPage")
        
        header_layout.addWidget(self.FacultyListPage)
        header_layout.addStretch(1)

        self.backbutton = QtWidgets.QPushButton("<- Back")
        self.backbutton.clicked.connect(self._handleBackButton)
        self.backbutton.setStyleSheet("""
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
        self.backbutton.setFixedSize(100, 40)
        header_layout.addWidget(self.backbutton)
        
        reschedule_layout.addWidget(header_widget)
        
        # Main content widget
        self.widget_3 = QtWidgets.QWidget()
        self.widget_3.setStyleSheet("QWidget#widget_3 { background-color: #FFFFFF; border-radius: 20px; }")
        self.widget_3.setObjectName("widget_3")
        
        widget_layout = QtWidgets.QVBoxLayout(self.widget_3)
        widget_layout.setContentsMargins(10, 0, 10, 0)
        widget_layout.setSpacing(5)
        
        # Faculty name header
        self.nameheader = QtWidgets.QFrame()
        self.nameheader.setContentsMargins(30, 0, 30, 0)
        self.nameheader.setStyleSheet("""
            QFrame#nameheader {
                background: #ffffff;
                border-radius: 12px;
            }
        """)
        self.nameheader.setObjectName("nameheader")
        self.nameheader.setFixedHeight(80)
        
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 3)
        shadow.setColor(QtGui.QColor(0, 0, 0, 60))
        self.nameheader.setGraphicsEffect(shadow)

        nameheader_layout = QtWidgets.QHBoxLayout(self.nameheader)
        nameheader_layout.setContentsMargins(20, 0, 20, 0)
        nameheader_layout.setSpacing(12)
        nameheader_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.label_32 = QtWidgets.QLabel()
        self.label_32.setFixedSize(50, 50)
        self.label_32.setStyleSheet("""
            QLabel {
                background: #4285F4;
                border-radius: 25px;
                border: 2px solid white;
            }
        """)
        
        self.label_29 = QtWidgets.QLabel("Select a Faculty")
        font = QtGui.QFont("Poppins", 18, QtGui.QFont.Weight.Bold)
        self.label_29.setFont(font)
        self.label_29.setStyleSheet("color: #084924;")
        self.label_29.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)

        nameheader_layout.addWidget(self.label_32)
        nameheader_layout.addWidget(self.label_29, 1)

        center_layout = QtWidgets.QHBoxLayout()
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.addStretch()
        center_layout.addWidget(self.nameheader)
        center_layout.addStretch()

        widget_layout.addLayout(center_layout)

        # Subtitle
        self.subtitle = QtWidgets.QLabel("Select Date & Time")
        subtitle_font = QtGui.QFont("Poppins", 14, QtGui.QFont.Weight.Medium)
        self.subtitle.setFont(subtitle_font)
        self.subtitle.setStyleSheet("color: #084924;")
        self.subtitle.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        widget_layout.addWidget(self.subtitle)

        # Content area with calendar and slots
        content_widget = QtWidgets.QWidget()
        content_layout = QtWidgets.QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(20)
        
        # Left side - Calendar
        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        calendar_header = QtWidgets.QWidget()
        calendar_header_layout = QtWidgets.QHBoxLayout(calendar_header)
        calendar_header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.label_30 = QtWidgets.QLabel()
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.label_30.setFont(font)
        self.label_30.setStyleSheet("QLabel#label_30 { color: #084924; }")
        self.label_30.setObjectName("label_30")
        
        calendar_header_layout.addWidget(self.label_30)
        calendar_header_layout.addStretch(1)
        
        left_layout.addWidget(calendar_header)
        
        self.month_header = QtWidgets.QLabel()
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.month_header.setFont(font)
        self.month_header.setStyleSheet("QLabel { color: #084924; background: transparent; }")
        self.month_header.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.month_header.setText(datetime.now().strftime("%B %Y"))
        left_layout.addWidget(self.month_header)
        
        # Calendar widget
        self.calendarCard = QtWidgets.QWidget()
        self.calendarCard.setStyleSheet("""
            QWidget#calendarCard {
                background: #ffffff;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
        """)
        self.calendarCard.setObjectName("calendarCard")

        calendar_layout = QtWidgets.QVBoxLayout(self.calendarCard)
        calendar_layout.setContentsMargins(10, 10, 10, 10)
        
        self.calendarWidget = QtWidgets.QCalendarWidget()
        self.calendarWidget.setVerticalHeaderFormat(QtWidgets.QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendarWidget.setHorizontalHeaderFormat(QtWidgets.QCalendarWidget.HorizontalHeaderFormat.NoHorizontalHeader)
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
        self.calendarWidget.selectionChanged.connect(self._onDateSelected)
        self.calendarWidget.setMinimumDate(QtCore.QDate.currentDate())
        
        calendar_layout.addWidget(self.calendarWidget)
        left_layout.addWidget(self.calendarCard, 1)
        
        # Right side - Available slots
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
        self.initial_message = QtWidgets.QLabel("Please select a faculty first")
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

        # Request button
        self.button_4 = QtWidgets.QPushButton("Request Appointment")
        self.button_4.setFixedHeight(50)
        self.button_4.setContentsMargins(0, 20, 0, 0)
        self.button_4.clicked.connect(self._showRequestDialog)
        self.button_4.setFont(QtGui.QFont("Poppins", 14, QtGui.QFont.Weight.Bold))
        self.button_4.setStyleSheet("""
            QPushButton {
                background-color: #084924;
                border-radius: 8px;
                color: white;
                font: 600 14pt 'Poppins';
            }
            QPushButton:hover { background-color: #0a5a2f; }
            QPushButton:pressed { background-color: #06381b; }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.button_4.setEnabled(False)
        available_layout.addWidget(self.button_4)

        right_layout.addWidget(self.availableSlot, 1)

        content_layout.addWidget(left_widget, 1)
        content_layout.addWidget(right_widget, 1)

        widget_layout.addWidget(content_widget, 1)
        reschedule_layout.addWidget(self.widget_3, 1)

    def _handleBackButton(self):
        """Handle back button click"""
        self.back.emit()
        self.backrefreshdata.emit()

    def _onDateSelected(self):
        """Handle date selection from calendar"""
        print("DEBUG: _onDateSelected called")
        
        # # Remove initial message if it exists
        # if hasattr(self, 'initial_message') and self.initial_message:
        #     self.initial_message.hide()
        
        self.selected_date = self.calendarWidget.selectedDate().toString('yyyy-MM-dd')
        print(f"DEBUG: Selected date: {self.selected_date}")
        
        # Update month header
        selected_qdate = self.calendarWidget.selectedDate()
        self.month_header.setText(selected_qdate.toString("MMMM yyyy"))
        
        self._loadAvailableSlotsForDate(self.selected_date)

    def slot_style(self, default=False, selected=False):
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

    def select_slot(self, button, slot_data):
        """Handle slot selection"""
        print(f"DEBUG: select_slot called with slot_data: {slot_data}")
        
        if not button.isEnabled():
            return
            
        for btn in self.slot_buttons:
            if btn.isEnabled():
                btn.setChecked(False)
                btn.setStyleSheet(self.slot_style(default=True))
        
        button.setChecked(True)
        button.setStyleSheet(self.slot_style(selected=True))
        self.selected_slot = slot_data
        
        if hasattr(self, 'button_4') and self.button_4:
            self.button_4.setEnabled(True)
            print(f"DEBUG: Button enabled, selected_slot: {self.selected_slot}")
            self._showRequestDialog()

    def _showRequestDialog(self):
        """Show request dialog to collect appointment details"""
        print(f"DEBUG: _showRequestDialog called")
        print(f"DEBUG: selected_faculty: {self.selected_faculty}")
        print(f"DEBUG: selected_slot: {self.selected_slot}")
        print(f"DEBUG: selected_date: {self.selected_date}")
        
        if not self.selected_faculty:
            QMessageBox.warning(self, "Warning", "Please select a faculty first.")
            return
            
        if not self.selected_slot:
            QMessageBox.warning(self, "Warning", "Please select a time slot.")
            return
            
        if not self.selected_date:
            QMessageBox.warning(self, "Warning", "Please select a date.")
            return

        # Check if slot is in the past
        start_time = self.selected_slot.get('start', '')
        
        if self._is_past_appointment(self.selected_date, start_time):
            QMessageBox.warning(
                self, 
                "Invalid Time Slot", 
                "You cannot request an appointment for a past date and time. "
                "Please select a future time slot."
            )
            return

        # Check for existing appointments
        if self._check_existing_appointments(start_time):
            QMessageBox.warning(
                self, 
                "Already Booked", 
                "You already have a pending or approved appointment for this time. "
                "Please choose a different time."
            )
            return

        self._showAppointmentDetailsDialog()

    def _showAppointmentDetailsDialog(self):
        """Show dialog with appointment details, purpose form, and document upload"""
        dialog = QtWidgets.QDialog()
        dialog.setWindowTitle("Appointment Request")
        dialog.setModal(True)
        dialog.setFixedSize(550, 700)
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
                border-radius: 12px;
            }
        """)
        
        # Create scroll area
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: white;
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
        
        # Main content widget
        content_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(content_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title_label = QtWidgets.QLabel("Appointment Request Details")
        title_label.setStyleSheet("""
            QLabel {
                color: #084924;
                font: 600 18pt 'Poppins';
            }
        """)
        title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Appointment Summary
        summary_group = QtWidgets.QGroupBox("Appointment Summary")
        summary_group.setStyleSheet("""
            QGroupBox {
                font: 600 12pt 'Poppins';
                color: #084924;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
            }
        """)
        
        summary_layout = QtWidgets.QFormLayout(summary_group)
        summary_layout.setVerticalSpacing(8)
        summary_layout.setHorizontalSpacing(20)
        
        # Get faculty name
        user_info = self.selected_faculty.get('user', {})
        faculty_name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
        if not faculty_name:
            faculty_name = user_info.get('username', 'Unknown Faculty')
        
        # Format time
        start_time = self.selected_slot.get('start', '')
        end_time = self.selected_slot.get('end', '')

        print(f"DEBUG: Raw start_time = '{start_time}'")
        print(f"DEBUG: Raw end_time = '{end_time}'")

        time_display = ""
        if 'T' in start_time:
            try:
                # Clean the time strings
                start_time_clean = start_time.replace('Z', '')
                end_time_clean = end_time.replace('Z', '')
                
                # Parse using Python datetime
                start_dt = datetime.fromisoformat(start_time_clean)
                end_dt = datetime.fromisoformat(end_time_clean)
                
                # Format for display
                start_formatted = start_dt.strftime('%I:%M %p')
                end_formatted = end_dt.strftime('%I:%M %p')
                time_display = f"{start_formatted} - {end_formatted}"
                
                print(f"DEBUG: Parsed successfully: {time_display}")
            except ValueError as e:
                print(f"DEBUG: Error parsing with fromisoformat: {e}")
                # Fallback: extract time part directly
                try:
                    start_time_only = start_time.split('T')[1].split('.')[0]
                    end_time_only = end_time.split('T')[1].split('.')[0]
                    
                    # Convert to AM/PM format
                    start_hour = int(start_time_only.split(':')[0])
                    start_minute = int(start_time_only.split(':')[1])
                    end_hour = int(end_time_only.split(':')[0])
                    end_minute = int(end_time_only.split(':')[1])
                    
                    start_period = "AM" if start_hour < 12 else "PM"
                    end_period = "AM" if end_hour < 12 else "PM"
                    
                    start_hour_12 = start_hour if start_hour <= 12 else start_hour - 12
                    end_hour_12 = end_hour if end_hour <= 12 else end_hour - 12
                    
                    time_display = f"{start_hour_12}:{start_minute:02d} {start_period} - {end_hour_12}:{end_minute:02d} {end_period}"
                except:
                    time_display = f"{start_time} - {end_time}"
        else:
            time_display = f"{start_time} - {end_time}"

        print(f"DEBUG: Result time_display = '{time_display}'")
        
        summary_data = [
            ("Faculty:", faculty_name),
            ("Date:", self.selected_date),
            ("Time:", time_display),
        ]
        
        for label, value in summary_data:
            label_widget = QtWidgets.QLabel(label)
            label_widget.setStyleSheet("QLabel { font: 600 11pt 'Poppins'; color: #333; }")
            value_widget = QtWidgets.QLabel(value)
            value_widget.setStyleSheet("QLabel { font: 11pt 'Poppins'; color: #666; }")
            summary_layout.addRow(label_widget, value_widget)
        
        layout.addWidget(summary_group)
        
        # Appointment Purpose
        reason_group = QtWidgets.QGroupBox("Appointment Purpose *")
        reason_group.setStyleSheet("""
            QGroupBox {
                font: 600 12pt 'Poppins';
                color: #084924;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }
        """)
        
        reason_layout = QtWidgets.QVBoxLayout(reason_group)
        
        self.reason_text_edit = QtWidgets.QTextEdit()
        self.reason_text_edit.setPlaceholderText("Please describe the purpose of your appointment in detail...")
        self.reason_text_edit.setFixedHeight(120)
        self.reason_text_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px;
                font: 11pt 'Poppins';
                background-color: #fafafa;
            }
            QTextEdit:focus {
                border: 1px solid #084924;
                background-color: white;
            }
        """)
        reason_layout.addWidget(self.reason_text_edit)
        layout.addWidget(reason_group)
        
        # Meeting Location
        location_group = QtWidgets.QGroupBox("Meeting Location")
        location_group.setStyleSheet("""
            QGroupBox {
                font: 600 12pt 'Poppins';
                color: #084924;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }
        """)
        
        location_layout = QtWidgets.QVBoxLayout(location_group)
        
        self.location_combo = QtWidgets.QComboBox()
        self.location_combo.addItems([
            "Faculty Office",
            "Online Meeting",
            "Classroom",
            "Laboratory",
            "Library",
            "Conference Room",
            "Other (specify in purpose)"
        ])
        self.location_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px;
                font: 11pt 'Poppins';
                background-color: #fafafa;
            }
            QComboBox:focus {
                border: 1px solid #084924;
            }
        """)
        location_layout.addWidget(self.location_combo)
        layout.addWidget(location_group)
        
        # Document Upload Section
        documents_group = QtWidgets.QGroupBox("Supporting Documents (Optional)")
        documents_group.setStyleSheet("""
            QGroupBox {
                font: 600 12pt 'Poppins';
                color: #084924;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }
        """)
        
        documents_layout = QtWidgets.QVBoxLayout(documents_group)
        
        # Upload instructions
        instructions_label = QtWidgets.QLabel(
            "You can upload supporting documents such as:\n"
            "• Project proposals\n• Research papers\n• Assignment files"
        )
        instructions_label.setStyleSheet("""
            QLabel {
                font: 10pt 'Poppins';
                color: #666666;
                background-color: #f8f9fa;
                padding: 10px;
                border-radius: 6px;
                line-height: 1.4;
            }
        """)
        instructions_label.setWordWrap(True)
        documents_layout.addWidget(instructions_label)
        
        # File format info
        format_label = QtWidgets.QLabel("Supported formats: Images (PNG, JPG, JPEG), PDF, Documents (DOC, DOCX)")
        format_label.setStyleSheet("QLabel { font: 9pt 'Poppins'; color: #888888; margin-top: 5px; }")
        documents_layout.addWidget(format_label)
        
        # Upload button
        upload_button_layout = QtWidgets.QHBoxLayout()
        
        self.upload_button = QtWidgets.QPushButton("Choose Files")
        self.upload_button.setFixedSize(120, 40)
        self.upload_button.setStyleSheet("""
            QPushButton {
                background-color: #2F80ED;
                color: white;
                border-radius: 8px;
                font: 600 11pt 'Poppins';
                border: none;
            }
            QPushButton:hover {
                background-color: #2a75e0;
            }
            QPushButton:pressed {
                background-color: #1e6ac8;
            }
        """)
        self.upload_button.clicked.connect(lambda: self._handleFileUpload(dialog))
        
        self.clear_files_button = QtWidgets.QPushButton("Clear All")
        self.clear_files_button.setFixedSize(100, 40)
        self.clear_files_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border-radius: 8px;
                font: 600 11pt 'Poppins';
                border: none;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.clear_files_button.clicked.connect(lambda: self._clearUploadedFiles(dialog))
        self.clear_files_button.setEnabled(False)
        
        upload_button_layout.addWidget(self.upload_button)
        upload_button_layout.addWidget(self.clear_files_button)
        upload_button_layout.addStretch(1)
        
        documents_layout.addLayout(upload_button_layout)
        
        # Uploaded files list
        self.uploaded_files_widget = QtWidgets.QWidget()
        self.uploaded_files_layout = QtWidgets.QVBoxLayout(self.uploaded_files_widget)
        self.uploaded_files_layout.setContentsMargins(0, 10, 0, 0)
        self.uploaded_files_layout.setSpacing(5)
        
        documents_layout.addWidget(self.uploaded_files_widget)
        
        # Store uploaded files for this dialog
        self.uploaded_files = []
        
        layout.addWidget(documents_group)
        layout.addStretch(1)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        cancel_button = QtWidgets.QPushButton("Cancel")
        cancel_button.setFixedSize(120, 40)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border-radius: 8px;
                font: 600 12pt 'Poppins';
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        cancel_button.clicked.connect(dialog.reject)
        
        submit_button = QtWidgets.QPushButton("Submit Request")
        submit_button.setFixedSize(140, 40)
        submit_button.setStyleSheet("""
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
        submit_button.clicked.connect(lambda: self._handleSubmitRequest(dialog))
        
        button_layout.addStretch(1)
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(submit_button)
        
        layout.addLayout(button_layout)
        
        # Set up scroll area
        scroll_area.setWidget(content_widget)
        
        # Main dialog layout
        main_layout = QtWidgets.QVBoxLayout(dialog)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        
        dialog.exec()

    def _handleFileUpload(self, dialog):
        """Handle file upload button click"""
        file_dialog = QtWidgets.QFileDialog()
        file_paths, _ = file_dialog.getOpenFileNames(
            dialog,
            "Select Supporting Documents",
            "",
            "All Supported Files (*.png *.jpg *.jpeg *.pdf *.doc *.docx);;"
            "Images (*.png *.jpg *.jpeg);;"
            "PDF Files (*.pdf);;"
            "Word Documents (*.doc *.docx);;"
            "All Files (*)"
        )
        
        if file_paths:
            for file_path in file_paths:
                if file_path:
                    self._addUploadedFile(file_path, dialog)

    def _addUploadedFile(self, file_path, dialog):
        """Add an uploaded file to the list"""
        try:
            file_name = os.path.basename(file_path)
            file_size = self._get_file_size(file_path)
            
            # Create file item widget
            file_item = QtWidgets.QWidget()
            file_item.setFixedHeight(50)
            file_item.setStyleSheet("""
                QWidget {
                    background-color: #f8f9fa;
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                    margin: 2px 0px;
                }
            """)
            
            file_layout = QtWidgets.QHBoxLayout(file_item)
            file_layout.setContentsMargins(10, 5, 10, 5)
            file_layout.setSpacing(10)
            
            # File icon
            icon_label = QtWidgets.QLabel()
            icon_label.setFixedSize(24, 24)
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                icon_label.setStyleSheet("QLabel { background-color: #4CAF50; border-radius: 4px; }")
                icon_label.setText("🖼️")
            elif file_path.lower().endswith('.pdf'):
                icon_label.setStyleSheet("QLabel { background-color: #F44336; border-radius: 4px; }")
                icon_label.setText("📄")
            elif file_path.lower().endswith(('.doc', '.docx')):
                icon_label.setStyleSheet("QLabel { background-color: #2196F3; border-radius: 4px; }")
                icon_label.setText("📝")
            else:
                icon_label.setStyleSheet("QLabel { background-color: #9E9E9E; border-radius: 4px; }")
                icon_label.setText("📎")
            
            icon_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            icon_label.setStyleSheet(icon_label.styleSheet() + " QLabel { color: white; font: 12pt; }")
            
            # File info
            file_info_widget = QtWidgets.QWidget()
            file_info_layout = QtWidgets.QVBoxLayout(file_info_widget)
            file_info_layout.setContentsMargins(0, 0, 0, 0)
            file_info_layout.setSpacing(2)
            
            file_name_label = QtWidgets.QLabel(file_name)
            file_name_label.setStyleSheet("QLabel { font: 600 10pt 'Poppins'; color: #333; }")
            file_name_label.setWordWrap(True)
            file_name_label.setMaximumWidth(300)
            
            file_size_label = QtWidgets.QLabel(file_size)
            file_size_label.setStyleSheet("QLabel { font: 9pt 'Poppins'; color: #666; }")
            
            file_info_layout.addWidget(file_name_label)
            file_info_layout.addWidget(file_size_label)
            
            # Remove button
            remove_button = QtWidgets.QPushButton("×")
            remove_button.setFixedSize(24, 24)
            remove_button.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border-radius: 12px;
                    font: bold 10pt 'Poppins';
                    border: none;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """)
            remove_button.clicked.connect(lambda: self._removeUploadedFile(file_item, file_path, dialog))
            
            file_layout.addWidget(icon_label)
            file_layout.addWidget(file_info_widget, 1)
            file_layout.addWidget(remove_button)
            
            # Add to uploaded files list
            self.uploaded_files_layout.addWidget(file_item)
            self.uploaded_files.append(file_path)
            
            # Enable clear all button
            self.clear_files_button.setEnabled(True)
            
        except Exception as e:
            logging.error(f"Error adding uploaded file: {e}")
            QtWidgets.QMessageBox.warning(
                dialog,
                "Upload Error",
                f"Failed to add file: {str(e)}"
            )

    def _removeUploadedFile(self, file_item, file_path, dialog):
        """Remove an uploaded file from the list"""
        try:
            self.uploaded_files_layout.removeWidget(file_item)
            file_item.deleteLater()
            
            if file_path in self.uploaded_files:
                self.uploaded_files.remove(file_path)
            
            if not self.uploaded_files:
                self.clear_files_button.setEnabled(False)
                
        except Exception as e:
            logging.error(f"Error removing uploaded file: {e}")

    def _clearUploadedFiles(self, dialog):
        """Clear all uploaded files"""
        try:
            for i in reversed(range(self.uploaded_files_layout.count())):
                item = self.uploaded_files_layout.itemAt(i)
                if item.widget():
                    item.widget().deleteLater()
            
            self.uploaded_files.clear()
            self.clear_files_button.setEnabled(False)
            
        except Exception as e:
            logging.error(f"Error clearing uploaded files: {e}")

    def _get_file_size(self, file_path):
        """Get human-readable file size"""
        try:
            size = os.path.getsize(file_path)
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size/1024:.1f} KB"
            else:
                return f"{size/(1024*1024):.1f} MB"
        except:
            return "Unknown size"

    def _handleSubmitRequest(self, dialog):
        """Handle the appointment request submission"""
        reason_text = self.reason_text_edit.toPlainText().strip()
        location = self.location_combo.currentText()
        
        if not reason_text:
            QtWidgets.QMessageBox.warning(
                dialog,
                "Missing Information",
                "Please enter the purpose of your appointment before submitting."
            )
            return
        
        try:
            # Prepare appointment data
            appointment_data = {
                
                "faculty": self.selected_faculty['id'],
                "start_at": self.selected_slot['start'],
                "end_at": self.selected_slot['end'],
                "reason": reason_text,
                
            }
            
            # Create appointment
            result = self.appointment_crud.create_appointment(appointment_data)
            
            if result:
                dialog.accept()
                self._showSuccessDialog()
            else:
                QtWidgets.QMessageBox.warning(dialog, "Error", "Failed to create appointment request.")
                
        except Exception as e:
            logging.error(f"Error creating appointment: {e}")
            QtWidgets.QMessageBox.warning(dialog, "Error", f"Failed to create appointment: {str(e)}")

    def _showSuccessDialog(self):
        """Show success dialog"""
        dialog = QtWidgets.QDialog()
        dialog.setWindowTitle("Success")
        dialog.setModal(True)
        dialog.setFixedSize(400, 250)
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
                border-radius: 10px;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Success icon
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
        
        message_label = QtWidgets.QLabel("Appointment Request Submitted!")
        message_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        message_label.setStyleSheet("""
            QLabel {
                color: #084924;
                font: 600 16pt 'Poppins';
            }
        """)
        layout.addWidget(message_label)
        
        info_label = QtWidgets.QLabel("Your request is pending faculty approval.\nYou will be notified once it's processed.")
        info_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("QLabel { font: 11pt 'Poppins'; color: #666; }")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
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
        ok_button.clicked.connect(self.back)
        
        layout.addWidget(ok_button)
        
        dialog.exec()

    def retranslateUi(self):
        self.label_29.setText("Select a Faculty")
        self.label_30.setText("Select Date & Time")
        self.label_31.setText("Available Slots")
        self.button_4.setText("Request Appointment")
        self.FacultyListPage.setText("Request Appointment")