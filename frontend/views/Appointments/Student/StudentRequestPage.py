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
        self.slot_buttons = []
        self.slots_container = None
        self.available_days = set()
        self.setFixedSize(1000, 550)
        self._setupStudentRequestPage()
        self.retranslateUi()

    def _is_past_appointment(self, selected_date, start_time_str):
        """Check if the selected appointment date and time is in the past"""
        try:
            # Parse start time string (HH:MM or HH:MM:SS)
            if ':' in start_time_str:
                time_parts = start_time_str.split(':')
                hour = int(time_parts[0])
                minute = int(time_parts[1])
            else:
                hour = 0
                minute = 0
            
            # Create datetime object
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
        self.selected_faculty = faculty_data
        self._updateFacultyInfo()
        self._updateCalendarForToday()
        self._onDateSelected()

    def _updateFacultyInfo(self):
        """Update the UI with faculty information"""
        if self.selected_faculty:
            user_info = self.selected_faculty.get('user', {})
            faculty_name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
            if not faculty_name:
                faculty_name = user_info.get('username', 'Unknown Faculty')
            
            self.label_29.setText(faculty_name)
            self.label_30.setText(f"Select Date & Time with {faculty_name}")
            current_date = datetime.now()
            self.month_header.setText(current_date.strftime("%B %Y"))

    def _updateCalendarForToday(self):
        """Set calendar to today's date and load available slots"""
        today = QDate.currentDate()
        self.calendarWidget.setSelectedDate(today)
        self.selected_date = today.toString('yyyy-MM-dd')
        self._loadAvailableSlotsForDate(self.selected_date)

    def _loadAvailableSlotsForDate(self, date_str):
        """Load available slots for the selected date"""
        if not self.selected_faculty:
            return
        
        try:
            faculty_id = self.selected_faculty['id']
            available_slots = self.appointment_crud.get_faculty_available_schedule(faculty_id, date_str)
            
            # Clear existing slot buttons
            for btn in self.slot_buttons:
                btn.deleteLater()
            self.slot_buttons.clear()
            
            # Clear slots container
            if hasattr(self, "slots_container") and self.slots_container is not None:
                self.slots_container.deleteLater()
                self.slots_container = None
            
            if available_slots:
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
                
                # Replace old content
                old_widget = self.availableSlot.layout().itemAt(0)
                if old_widget and old_widget.widget():
                    old_widget.widget().deleteLater()
                self.availableSlot.layout().insertWidget(0, slots_scroll)
                
                # Create slot buttons for each available time
                for slot in available_slots:
                    start_time = slot['start']
                    end_time = slot['end']
                    
                    # Parse datetime strings
                    if 'T' in start_time:
                        start_dt = QDateTime.fromString(start_time, "yyyy-MM-ddTHH:mm:ss")
                        end_dt = QDateTime.fromString(end_time, "yyyy-MM-ddTHH:mm:ss")
                        time_text = f"{start_dt.toString('hh:mm AP')} - {end_dt.toString('hh:mm AP')}"
                        slot_start_time = start_dt.toString("HH:mm")
                    else:
                        time_text = f"{start_time} - {end_time}"
                        slot_start_time = start_time
                    
                    # Create button
                    btn = QtWidgets.QPushButton(time_text)
                    btn.setFixedHeight(45)
                    btn.setCheckable(True)
                    btn.setProperty("start_time", slot_start_time)
                    
                    # Check if slot is in the past
                    is_past = self._is_past_appointment(self.selected_date, slot_start_time)
                    
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
                        btn.clicked.connect(lambda checked, b=btn, s=slot: self.select_slot(b, s))
                    
                    self.slots_layout.addWidget(btn)
                    self.slot_buttons.append(btn)
                
                self.slots_layout.addStretch(1)
                
                # Enable first available slot by default
                available_buttons = [btn for btn in self.slot_buttons if btn.isEnabled()]
                if available_buttons:
                    available_buttons[0].setChecked(True)
                    available_buttons[0].setStyleSheet(self.slot_style(selected=True))
                    self.selected_slot = available_slots[0]
                    self.button_4.setEnabled(True)
                else:
                    self.selected_slot = None
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
            else:
                self._showNoSlotsMessage()
                
        except Exception as e:
            logging.error(f"Error loading available slots: {e}")
            self._showNoSlotsMessage()

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
        
        # Clear existing scroll area
        old_widget = self.availableSlot.layout().itemAt(0)
        if old_widget and old_widget.widget():
            old_widget.widget().deleteLater()
        
        self.availableSlot.layout().insertWidget(0, no_slots_label)
        self.selected_slot = None
        if hasattr(self, 'button_4') and self.button_4:
            self.button_4.setEnabled(False)

    def _check_existing_appointments(self, start_time_str):
        """Check if student already has an appointment at this time"""
        try:
            appointments = self.appointment_crud.get_student_appointments()
            if not appointments:
                return False
            
            # Parse selected appointment time
            if 'T' in start_time_str:
                selected_dt = QDateTime.fromString(start_time_str, "yyyy-MM-ddTHH:mm:ss")
            else:
                selected_dt = QDateTime.fromString(f"{self.selected_date} {start_time_str}", "yyyy-MM-dd HH:mm")
            
            for appointment in appointments:
                if appointment.get('status') in ['PENDING', 'APPROVED']:
                    appt_start = appointment.get('start_at')
                    if appt_start:
                        if 'T' in appt_start:
                            appt_dt = QDateTime.fromString(appt_start, "yyyy-MM-ddTHH:mm:ss")
                        else:
                            appt_dt = QDateTime.fromString(appt_start, "yyyy-MM-dd HH:mm:ss")
                        
                        # Check if this is the same time
                        if appt_dt == selected_dt:
                            return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error checking existing appointments: {e}")
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
        initial_message = QtWidgets.QLabel("Please select a faculty first")
        initial_message.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        initial_message.setStyleSheet("""
            QLabel {
                font: 12pt 'Poppins';
                color: #666666;
                background: #f8f9fa;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        available_layout.addWidget(initial_message)

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
        self.selected_date = self.calendarWidget.selectedDate().toString('yyyy-MM-dd')
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

    def _showRequestDialog(self):
        """Show request dialog to collect appointment details"""
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
        if 'T' in start_time:
            start_time_str = QDateTime.fromString(start_time, "yyyy-MM-ddTHH:mm:ss").toString("HH:mm")
        else:
            start_time_str = start_time
        
        if self._is_past_appointment(self.selected_date, start_time_str):
            QMessageBox.warning(
                self, 
                "Invalid Time Slot", 
                "You cannot request an appointment for a past date and time. "
                "Please select a future time slot."
            )
            return

        # Check for existing appointments
        appointment_datetime_str = f"{self.selected_date}T{start_time_str}:00"
        if self._check_existing_appointments(appointment_datetime_str):
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
        
        if 'T' in start_time:
            start_dt = QDateTime.fromString(start_time, "yyyy-MM-ddTHH:mm:ss")
            end_dt = QDateTime.fromString(end_time, "yyyy-MM-ddTHH:mm:ss")
            time_display = f"{start_dt.toString('hh:mm AP')} - {end_dt.toString('hh:mm AP')}"
        else:
            time_display = f"{start_time} - {end_time}"
        
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
                "additional_details": reason_text,
                "address": location
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