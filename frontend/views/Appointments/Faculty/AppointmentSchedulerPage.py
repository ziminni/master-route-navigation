from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QDialog, QFormLayout, QPushButton, QDateEdit, QMessageBox
from PyQt6.QtCore import QDate
import requests
import json
from datetime import datetime, timedelta
from ..api_client import APIClient

import logging

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
class AppointmentSchedulerPage_ui(QWidget):
    go_to_EditSchedulePage = QtCore.pyqtSignal()
    back = QtCore.pyqtSignal()

    def convert_time(self, time_str):
        """Convert 24-hour format to 12-hour format with AM/PM."""
        if ":" in time_str:
            hour, minute = map(int, time_str.split(":"))
            period = "AM" if hour < 12 else "PM"
            hour = hour % 12 if hour != 0 else 12
            return f"{hour}:{minute:02d} {period}"
        return time_str

    def __init__(self, username, roles, primary_role, token, parent=None):
        super().__init__(parent)
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        self.crud = APIClient(token=token)
        self.faculty_id = None  # Will be set based on user role
        self.current_faculty_id = None  # For faculty selection
       
        self._setupAppointmentSchedulerPage()
        self.retranslateUi()
        self.setFixedSize(1000, 550)
        self._initialize_user_data()

    def _initialize_user_data(self):
        """Initialize user data based on role"""
        if self.primary_role == "faculty":
            # For faculty, get their own profile
            faculty_profiles = self.crud.get_faculty_profiles()
            user_profile = next((fp for fp in faculty_profiles if fp['user']['username'] == self.username), None)
            if user_profile:
                self.faculty_id = user_profile['id']
                self.current_faculty_id = self.faculty_id
        else:
            # For students, show all faculty
            faculty_profiles = self.crud.get_faculty_profiles()
            if faculty_profiles:
                self.current_faculty_id = faculty_profiles[0]['id']
        
        self._populateFacultyComboBox()
        self._populateWeeklySchedule()

    def _populateFacultyComboBox(self):
        """Populate faculty selection combo box"""
        faculty_profiles = self.crud.get_faculty_profiles()
        self.facultyComboBox.clear()
        
        for faculty in faculty_profiles:
            user_info = faculty.get('user', {})
            display_name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
            if not display_name:
                display_name = user_info.get('username', 'Unknown')
            self.facultyComboBox.addItem(display_name, faculty['id'])
        
        if self.current_faculty_id:
            index = self.facultyComboBox.findData(self.current_faculty_id)
            if index >= 0:
                self.facultyComboBox.setCurrentIndex(index)

    def _setupAppointmentSchedulerPage(self):
        self.setObjectName("AppointmentScheduler")
        scheduler_layout = QtWidgets.QVBoxLayout(self)
        scheduler_layout.setContentsMargins(10, 10, 10, 10)
        scheduler_layout.setSpacing(10)

        header_widget = QtWidgets.QWidget()
        header_layout = QtWidgets.QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        self.Academics_5 = QtWidgets.QLabel()
        font = QtGui.QFont("Poppins", 24)
        self.Academics_5.setFont(font)
        self.Academics_5.setStyleSheet("QLabel { color: #084924; }")
        header_layout.addWidget(self.Academics_5)
        header_layout.addStretch(1)

        self.delete_3 = QtWidgets.QPushButton()
        self.delete_3.setFixedSize(80, 30)
        self.delete_3.setStyleSheet("""
            QPushButton { background-color: #EB5757; color: white; border-radius: 4px; font: 10pt 'Poppins'; }
            QPushButton:hover { background-color: #d43f3f; }
        """)
        self.delete_3.clicked.connect(self._deleteSelectedSlots)
        header_layout.addWidget(self.delete_3)

        self.createschedule_2 = QtWidgets.QPushButton()
        self.createschedule_2.setFixedSize(120, 30)
        self.createschedule_2.setStyleSheet("""
            QPushButton { background-color: #084924; color: white; border-radius: 8px; font: 10pt 'Poppins'; }
            QPushButton:hover { background-color: #0a5a2f; }
        """)
        self.createschedule_2.clicked.connect(self.go_to_EditSchedulePage.emit)
        header_layout.addWidget(self.createschedule_2)

        # Faculty selection combo box
        self.facultyComboBox = QtWidgets.QComboBox()
        self.facultyComboBox.setFixedSize(200, 30)
        self.facultyComboBox.setStyleSheet("""
            QComboBox { border: 2px solid #064420; border-radius: 6px; padding: 4px 8px; font: 10pt 'Poppins'; color: #064420; background: white; }
        """)
        self.facultyComboBox.currentIndexChanged.connect(self._onFacultyChanged)
        header_layout.addWidget(self.facultyComboBox)

        self.comboBox_2 = QtWidgets.QComboBox()
        self.comboBox_2.setFixedSize(200, 30)
        self.comboBox_2.setStyleSheet("""
            QComboBox { border: 2px solid #064420; border-radius: 6px; padding: 4px 8px; font: 10pt 'Poppins'; color: #064420; background: white; }
        """)
        self.comboBox_2.addItems(["1st Semester 2025 - 2026", "2nd Semester 2025 - 2026", "Summer 2026"])
        self.comboBox_2.currentTextChanged.connect(self._populateWeeklySchedule)
        header_layout.addWidget(self.comboBox_2)

        # Date selection controls
        self.dateEdit = QDateEdit()
        self.dateEdit.setCalendarPopup(True)
        self.dateEdit.setDisplayFormat("yyyy-MM-dd")
        self.dateEdit.setDate(QtCore.QDate.currentDate())
        self.dateEdit.setStyleSheet("""
            QDateEdit { border: 2px solid #064420; border-radius: 6px; padding: 4px 8px; font: 10pt 'Poppins'; color: #064420; background: white; }
        """)
        self.dateEdit.dateChanged.connect(self._updateWeek)
        header_layout.addWidget(self.dateEdit)

        self.backButton_7 = QtWidgets.QPushButton("<- Back")
        self.backButton_7.setContentsMargins(0,0,10,0)
        self.backButton_7.setStyleSheet("""
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
        self.backButton_7.setFixedSize(100, 40)
        self.backButton_7.clicked.connect(self.back.emit)
        header_layout.addWidget(self.backButton_7)

        scheduler_layout.addWidget(header_widget)

        self.widget_25 = QtWidgets.QWidget()
        self.widget_25.setStyleSheet("QWidget#widget_25 { background-color: #FFFFFF; border-radius: 20px; }")
        widget_layout = QtWidgets.QVBoxLayout(self.widget_25)
        widget_layout.setContentsMargins(20, 20, 20, 20)
        widget_layout.setSpacing(15)

        controls_widget = QtWidgets.QWidget()
        controls_layout = QtWidgets.QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        self.label_92 = QtWidgets.QLabel()
        font = QtGui.QFont("Poppins", 18, QtGui.QFont.Weight.Bold)
        self.label_92.setFont(font)
        controls_layout.addWidget(self.label_92)
        controls_layout.addStretch(1)

        self.prevWeekButton = QPushButton("Previous Week")
        self.prevWeekButton.setFixedSize(100, 30)
        self.prevWeekButton.setStyleSheet("""
            QPushButton { background-color: #084924; color: white; border-radius: 4px; font: 10pt 'Poppins'; }
            QPushButton:hover { background-color: #0a5a2f; }
        """)
        self.prevWeekButton.clicked.connect(self._prevWeek)
        controls_layout.addWidget(self.prevWeekButton)

        self.nextWeekButton = QPushButton("Next Week")
        self.nextWeekButton.setFixedSize(100, 30)
        self.nextWeekButton.setStyleSheet("""
            QPushButton { background-color: #084924; color: white; border-radius: 4px; font: 10pt 'Poppins'; }
            QPushButton:hover { background-color: #0a5a2f; }
        """)
        self.nextWeekButton.clicked.connect(self._nextWeek)
        controls_layout.addWidget(self.nextWeekButton)

        self.prevMonthButton = QPushButton("Previous Month")
        self.prevMonthButton.setFixedSize(120, 30)
        self.prevMonthButton.setStyleSheet("""
            QPushButton { background-color: #084924; color: white; border-radius: 4px; font: 10pt 'Poppins'; }
            QPushButton:hover { background-color: #0a5a2f; }
        """)
        self.prevMonthButton.clicked.connect(self._prevMonth)
        controls_layout.addWidget(self.prevMonthButton)

        self.nextMonthButton = QPushButton("Next Month")
        self.nextMonthButton.setFixedSize(120, 30)
        self.nextMonthButton.setStyleSheet("""
            QPushButton { background-color: #084924; color: white; border-radius: 4px; font: 10pt 'Poppins'; }
            QPushButton:hover { background-color: #0a5a2f; }
        """)
        self.nextMonthButton.clicked.connect(self._nextMonth)
        controls_layout.addWidget(self.nextMonthButton)

        widget_layout.addWidget(controls_widget)
        self._setupWeeklySchedule(widget_layout)
        scheduler_layout.addWidget(self.widget_25, 1)

    def _setupWeeklySchedule(self, parent_layout):
        grid_container = QtWidgets.QWidget()
        grid_layout = QtWidgets.QVBoxLayout(grid_container)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(0)

        self.weeklyGrid = QtWidgets.QTableWidget()
        self.weeklyGrid.setColumnCount(8)
        self.weeklyGrid.setRowCount(48)  # 12:00 AM to 12:00 PM with 30-min increments
        self.weeklyGrid.setShowGrid(True)
        self.weeklyGrid.verticalHeader().setVisible(True)
        self.weeklyGrid.horizontalHeader().setVisible(True)
        self.weeklyGrid.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.weeklyGrid.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.MultiSelection)
        self.weeklyGrid.setStyleSheet("""
            QTableWidget { background: #f9f9f9; font: 10pt 'Poppins'; border: 1px solid #e0e0e0; }
            QTableWidget::item { padding: 5px; border: 1px solid #e0e0e0; }
            QHeaderView::section { background-color: #0a5a2f; color: white; border: 0; padding: 10px; font: 600 11pt 'Poppins'; }
        """)
        headers = ["Time", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for i, h in enumerate(headers):
            self.weeklyGrid.setHorizontalHeaderItem(i, QtWidgets.QTableWidgetItem(h))

        self.weeklyGrid.setColumnWidth(0, 80)
        header = self.weeklyGrid.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Fixed)
        for c in range(1, 8):
            header.setSectionResizeMode(c, QtWidgets.QHeaderView.ResizeMode.Stretch)

        times = []
        for hour in range(0, 24):  # 12:00 AM to 12:00 PM
            times.append(f"{hour % 12 or 12}:00 {'AM' if hour < 12 else 'PM'}")
            times.append(f"{hour % 12 or 12}:30 {'AM' if hour < 12 else 'PM'}")
        for r, t in enumerate(times):
            item = QtWidgets.QTableWidgetItem(t)
            item.setForeground(QtGui.QBrush(QtGui.QColor("#6b6b6b")))
            item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.weeklyGrid.setItem(r, 0, item)
            self.weeklyGrid.setRowHeight(r, 40)
            for c in range(1, 8):
                w = QtWidgets.QWidget()
                w.setStyleSheet("QWidget { background: white; }")
                self.weeklyGrid.setCellWidget(r, c, w)

        grid_layout.addWidget(self.weeklyGrid, 1)
        parent_layout.addWidget(grid_container, 1)

    def _addWeeklySlot(self, row, col, title="Available", appt_id=None, is_available=True):
        """Add a slot to the weekly grid"""
        slot = QtWidgets.QLabel(title)
        
        if appt_id:
            # Booked appointment - different color based on status
            if "Pending" in title:
                slot.setStyleSheet("QLabel { background: #FFA500; color: white; border-radius: 4px; font: 9pt 'Poppins'; text-align: center; padding: 2px; }")
            elif "Approved" in title:
                slot.setStyleSheet("QLabel { background: #4CAF50; color: white; border-radius: 4px; font: 9pt 'Poppins'; text-align: center; padding: 2px; }")
            elif "Denied" in title or "Canceled" in title:
                slot.setStyleSheet("QLabel { background: #EB5757; color: white; border-radius: 4px; font: 9pt 'Poppins'; text-align: center; padding: 2px; }")
            else:
                slot.setStyleSheet("QLabel { background: #2196F3; color: white; border-radius: 4px; font: 9pt 'Poppins'; text-align: center; padding: 2px; }")
        elif is_available:
            # Available slot
            slot.setStyleSheet("QLabel { background: #ffc000; border-radius: 4px; font: 9pt 'Poppins'; text-align: center; padding: 2px; }")
        else:
            # Unavailable slot
            slot.setStyleSheet("QLabel { background: #e0e0e0; border-radius: 4px; font: 9pt 'Poppins'; text-align: center; padding: 2px; color: #999; }")
            slot.setText("Unavailable")
        
        if appt_id or is_available:
            slot.mousePressEvent = lambda event, r=row, c=col, aid=appt_id, avail=is_available: self._handleSlotClick(r, c, aid, avail)
        
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.addWidget(slot, 1)
        self.weeklyGrid.setCellWidget(row, col, container)

    def _handleSlotClick(self, row, col, appt_id, is_available):
        """Handle click on a schedule slot"""
        if appt_id:
            # Show appointment details
            self._showAppointmentDetails(row, col, appt_id)
        elif is_available and self.primary_role == "student":
            # Student can book appointment
            self._bookAppointment(row, col)
        elif is_available and self.primary_role == "faculty":
            # Faculty can mark as busy
            self._markAsBusy(row, col)

    def _bookAppointment(self, row, col):
        """Book an appointment for student"""
        if not self.current_faculty_id:
            QMessageBox.warning(self, "Error", "Please select a faculty member.")
            return

        # Get date and time from grid position
        selected_date = self.dateEdit.date()
        day_offset = col - 1  # Column 1 is Sunday, 2 is Monday, etc.
        target_date = selected_date.addDays(day_offset - selected_date.dayOfWeek() + 1)  # Adjust to get correct day
        
        # Calculate time from row
        hour = row // 2
        minute = 30 if row % 2 else 0
        start_time = f"{hour:02d}:{minute:02d}"
        
        # Calculate end time (30 minutes later)
        end_hour = hour + (1 if minute == 30 else 0)
        end_minute = 0 if minute == 30 else 30
        if end_hour == 24:
            end_hour = 0
        end_time = f"{end_hour:02d}:{end_minute:02d}"
        
        # Show booking dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Book Appointment")
        dialog.setModal(True)
        dialog.setFixedSize(400, 300)
        dialog.setStyleSheet("QDialog { background-color: white; border-radius: 12px; }")

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header_label = QLabel("Book New Appointment")
        header_label.setStyleSheet("QLabel { color: #084924; font: 600 16pt 'Poppins'; }")
        layout.addWidget(header_label)

        # Form
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(10)
        form_layout.setHorizontalSpacing(15)

        date_label = QLabel("Date:")
        date_label.setStyleSheet("QLabel { font: 600 11pt 'Poppins'; color: #333; }")
        date_value = QLabel(target_date.toString("yyyy-MM-dd"))
        date_value.setStyleSheet("QLabel { font: 11pt 'Poppins'; color: #666; }")
        form_layout.addRow(date_label, date_value)

        time_label = QLabel("Time:")
        time_label.setStyleSheet("QLabel { font: 600 11pt 'Poppins'; color: #333; }")
        time_value = QLabel(f"{self.convert_time(start_time)} - {self.convert_time(end_time)}")
        time_value.setStyleSheet("QLabel { font: 11pt 'Poppins'; color: #666; }")
        form_layout.addRow(time_label, time_value)

        purpose_label = QLabel("Purpose:")
        purpose_label.setStyleSheet("QLabel { font: 600 11pt 'Poppins'; color: #333; }")
        purpose_edit = QtWidgets.QTextEdit()
        purpose_edit.setMaximumHeight(80)
        purpose_edit.setStyleSheet("QTextEdit { border: 1px solid #ccc; border-radius: 4px; padding: 8px; font: 10pt 'Poppins'; }")
        form_layout.addRow(purpose_label, purpose_edit)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch(1)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setFixedSize(100, 35)
        cancel_button.setStyleSheet("""
            QPushButton { 
                background-color: #6c757d; 
                color: white; 
                border-radius: 6px; 
                font: 600 11pt 'Poppins'; 
            }
            QPushButton:hover { 
                background-color: #5a6268; 
            }
        """)
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button)
        
        book_button = QPushButton("Book Appointment")
        book_button.setFixedSize(140, 35)
        book_button.setStyleSheet("""
            QPushButton { 
                background-color: #084924; 
                color: white; 
                border-radius: 6px; 
                font: 600 11pt 'Poppins'; 
            }
            QPushButton:hover { 
                background-color: #0a5a2f; 
            }
        """)
        button_layout.addWidget(book_button)
        
        layout.addLayout(button_layout)

        def handle_booking():
            purpose = purpose_edit.toPlainText().strip()
            if not purpose:
                QMessageBox.warning(dialog, "Error", "Please enter appointment purpose.")
                return

            # Create appointment data
            appointment_data = {
                "faculty": self.current_faculty_id,
                "start_at": f"{target_date.toString('yyyy-MM-dd')}T{start_time}:00",
                "end_at": f"{target_date.toString('yyyy-MM-dd')}T{end_time}:00",
                "additional_details": purpose
            }

            result = self.crud.create_appointment(appointment_data)
            if result:
                QMessageBox.information(dialog, "Success", "Appointment booked successfully!")
                dialog.accept()
                self._populateWeeklySchedule()
            else:
                QMessageBox.critical(dialog, "Error", "Failed to book appointment. Please try again.")

        book_button.clicked.connect(handle_booking)
        dialog.exec()

    def _populateWeeklySchedule(self):
        """Populate weekly schedule with available slots and appointments"""
        if not self.current_faculty_id:
            return

        # Clear all cells first
        for r in range(self.weeklyGrid.rowCount()):
            for c in range(1, self.weeklyGrid.columnCount()):
                self.weeklyGrid.removeCellWidget(r, c)
                w = QtWidgets.QWidget()
                w.setStyleSheet("QWidget { background: white; border: 1px solid #e0e0e0; }")
                self.weeklyGrid.setCellWidget(r, c, w)

        # Get the selected week (Monday to Sunday based on dateEdit)
        selected_date = self.dateEdit.date()
        start_of_week = selected_date.addDays(-(selected_date.dayOfWeek() - 1))  # First day of the week (Monday)
        
        # Day mapping for columns (0: Time, 1: Sun, 2: Mon, ..., 7: Sat)
        day_map = {1: "Sun", 2: "Mon", 3: "Tue", 4: "Wed", 5: "Thu", 6: "Fri", 7: "Sat"}
        date_map = {}
        
        # Map dates to columns
        for i in range(7):
            current_date = start_of_week.addDays(i)
            col = i + 1  # Columns 1-7 for Sun-Sat
            date_map[col] = current_date.toString("yyyy-MM-dd")

        # Get available slots and appointments for each day
        for col, date_str in date_map.items():
            available_slots = self.crud.get_faculty_available_schedule(self.current_faculty_id, date_str)
            appointments = self.crud.get_faculty_appointments() if self.primary_role == "faculty" else self.crud.get_student_appointments()
            
            # Create time map for rows
            time_map = {}
            for row in range(48):  # 48 half-hour slots
                hour = row // 2
                minute = 30 if row % 2 else 0
                time_key = f"{hour:02d}:{minute:02d}"
                time_map[time_key] = row

            # Mark available slots
            for slot in available_slots:
                start_time = slot['start'].split('T')[1][:5]  # Extract HH:MM
                if start_time in time_map:
                    row = time_map[start_time]
                    self._addWeeklySlot(row, col, "Available", None, True)

            # Mark appointments
            for appt in appointments:
                if appt.get('faculty', {}).get('id') == self.current_faculty_id:
                    appt_date = appt['start_at'].split('T')[0]
                    if appt_date == date_str:
                        start_time = appt['start_at'].split('T')[1][:5]
                        if start_time in time_map:
                            row = time_map[start_time]
                            status = appt.get('status', 'Pending')
                            student_name = appt.get('student', {}).get('user', {}).get('first_name', 'Unknown')
                            title = f"{status}: {student_name}"
                            self._addWeeklySlot(row, col, title, appt['id'], False)

    def _onFacultyChanged(self, index):
        """Handle faculty selection change"""
        if index >= 0:
            self.current_faculty_id = self.facultyComboBox.itemData(index)
            self._populateWeeklySchedule()

    def _updateWeek(self):
        self._populateWeeklySchedule()

    def _prevWeek(self):
        current_date = self.dateEdit.date()
        self.dateEdit.setDate(current_date.addDays(-7))
        self._populateWeeklySchedule()

    def _nextWeek(self):
        current_date = self.dateEdit.date()
        self.dateEdit.setDate(current_date.addDays(7))
        self._populateWeeklySchedule()

    def _prevMonth(self):
        current_date = self.dateEdit.date()
        self.dateEdit.setDate(current_date.addMonths(-1))
        self._populateWeeklySchedule()

    def _nextMonth(self):
        current_date = self.dateEdit.date()
        self.dateEdit.setDate(current_date.addMonths(1))
        self._populateWeeklySchedule()

    def _showAppointmentDetails(self, row, col, appt_id):
        """Show appointment details dialog"""
        appointments = self.crud.get_faculty_appointments() if self.primary_role == "faculty" else self.crud.get_student_appointments()
        appt = next((a for a in appointments if a["id"] == appt_id), None)
        
        if not appt:
            QMessageBox.warning(self, "Error", "Appointment not found.")
            return

        # Format appointment details
        start_time = appt['start_at'].replace('T', ' ').split('.')[0]
        end_time = appt['end_at'].replace('T', ' ').split('.')[0]
        
        if self.primary_role == "faculty":
            user_info = appt.get('student', {}).get('user', {})
            user_name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
            user_role = "Student"
        else:
            user_info = appt.get('faculty', {}).get('user', {})
            user_name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
            user_role = "Faculty"

        details = [
            (f"{user_role}:", user_name),
            ("Date:", start_time.split()[0]),
            ("Time:", f"{self.convert_time(start_time.split()[1][:5])} - {self.convert_time(end_time.split()[1][:5])}"),
            ("Purpose:", appt.get('additional_details', 'N/A')),
            ("Status:", appt.get('status', 'Pending').capitalize()),
            ("Contact:", user_info.get('email', 'N/A'))
        ]
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Appointment Details")
        dialog.setModal(True)
        dialog.setMinimumSize(450, 400)
        dialog.setStyleSheet("QDialog { background-color: white; border-radius: 12px; }")

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header_label = QLabel("Appointment Details")
        header_label.setStyleSheet("QLabel { color: #084924; font: 600 16pt 'Poppins'; }")
        layout.addWidget(header_label)

        # Details group
        group = QtWidgets.QGroupBox()
        group.setStyleSheet("""
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
        form_layout = QFormLayout(group)
        form_layout.setVerticalSpacing(8)
        form_layout.setHorizontalSpacing(20)
        
        for label, value in details:
            label_widget = QLabel(label)
            label_widget.setStyleSheet("QLabel { font: 600 11pt 'Poppins'; color: #333; }")
            value_widget = QLabel(value)
            value_widget.setStyleSheet("QLabel { font: 11pt 'Poppins'; color: #666; }")
            value_widget.setWordWrap(True)
            form_layout.addRow(label_widget, value_widget)
        layout.addWidget(group)

        # Action buttons for faculty
        if self.primary_role == "faculty" and appt.get('status') in ['pending', 'Pending']:
            button_layout = QtWidgets.QHBoxLayout()
            
            approve_button = QPushButton("Approve")
            approve_button.setFixedSize(100, 35)
            approve_button.setStyleSheet("""
                QPushButton { 
                    background-color: #4CAF50; 
                    color: white; 
                    border-radius: 6px; 
                    font: 600 11pt 'Poppins'; 
                }
                QPushButton:hover { 
                    background-color: #45a049; 
                }
            """)
            approve_button.clicked.connect(lambda: self._updateAppointmentStatus(appt_id, 'approved', dialog))
            button_layout.addWidget(approve_button)
            
            deny_button = QPushButton("Deny")
            deny_button.setFixedSize(100, 35)
            deny_button.setStyleSheet("""
                QPushButton { 
                    background-color: #EB5757; 
                    color: white; 
                    border-radius: 6px; 
                    font: 600 11pt 'Poppins'; 
                }
                QPushButton:hover { 
                    background-color: #d43f3f; 
                }
            """)
            deny_button.clicked.connect(lambda: self._updateAppointmentStatus(appt_id, 'denied', dialog))
            button_layout.addWidget(deny_button)
            
            layout.addLayout(button_layout)

        # Button layout
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch(1)
        
        if self.primary_role == "student" and appt.get('status') in ['pending', 'Pending', 'approved', 'Approved']:
            cancel_button = QPushButton("Cancel Appointment")
            cancel_button.setFixedSize(140, 35)
            cancel_button.setStyleSheet("""
                QPushButton { 
                    background-color: #EB5757; 
                    color: white; 
                    border-radius: 6px; 
                    font: 600 11pt 'Poppins'; 
                }
                QPushButton:hover { 
                    background-color: #d43f3f; 
                }
            """)
            cancel_button.clicked.connect(lambda: self._updateAppointmentStatus(appt_id, 'canceled', dialog))
            button_layout.addWidget(cancel_button)
        
        close_button = QPushButton("Close")
        close_button.setFixedSize(100, 35)
        close_button.setStyleSheet("""
            QPushButton { 
                background-color: #084924; 
                color: white; 
                border-radius: 6px; 
                font: 600 11pt 'Poppins'; 
            }
            QPushButton:hover { 
                background-color: #0a5a2f; 
            }
        """)
        close_button.clicked.connect(dialog.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)

        dialog.exec()

    def _updateAppointmentStatus(self, appointment_id, status, dialog):
        """Update appointment status"""
        result = self.crud.update_appointment(appointment_id, {"status": status})
        if result:
            QMessageBox.information(self, "Success", f"Appointment {status} successfully!")
            dialog.accept()
            self._populateWeeklySchedule()
        else:
            QMessageBox.critical(self, "Error", f"Failed to {status} appointment.")

    def _markAsBusy(self, row, col):
        """Mark time slot as busy (for faculty)"""
        # This would require creating a BusyBlock via the API
        # For now, show a message
        QMessageBox.information(self, "Feature", "Mark as busy functionality would be implemented here.")

    def _deleteSelectedSlots(self):
        """Delete selected slots/appointments"""
        selected = self.weeklyGrid.selectedIndexes()
        if not selected:
            QMessageBox.information(self, "No Selection", "Please select appointment slots to delete.")
            return

        # For now, this will cancel selected appointments
        appointment_ids = []
        for index in selected:
            row, col = index.row(), index.column()
            if col == 0:  # Skip time column
                continue
            
            # In a real implementation, you would map the cell back to an appointment ID
            # For now, we'll just collect potentially affected appointments
            
        if appointment_ids:
            reply = QMessageBox.question(
                self, 
                "Confirm Cancellation", 
                f"Cancel {len(appointment_ids)} selected appointment(s)?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                for appt_id in appointment_ids:
                    self.crud.update_appointment(appt_id, {"status": "canceled"})
                self._populateWeeklySchedule()
                QMessageBox.information(self, "Success", "Appointments cancelled successfully.")
        else:
            QMessageBox.information(self, "Info", "No appointments found in selected slots.")

    def retranslateUi(self):
        self.Academics_5.setText("Appointment Scheduler")
        self.label_92.setText("Weekly Schedule")
        self.createschedule_2.setText("Create Schedule")
        self.delete_3.setText("Clear")
        self.comboBox_2.setItemText(0, "1st Semester 2025 - 2026")
        self.comboBox_2.setItemText(1, "2nd Semester 2025 - 2026")
        self.comboBox_2.setItemText(2, "Summer 2026")
