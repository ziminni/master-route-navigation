from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QDialog, QTimeEdit, QMessageBox
from PyQt6.QtCore import QDate, QTime
import requests
import json
from datetime import datetime, timedelta
import logging

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class APIClient:
    def __init__(self, base_url="http://localhost:8000/api", token=None):
        self.base_url = base_url
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}

    def create_availability_rule(self, data):
        """Create availability rule"""
        try:
            response = requests.post(
                f"{self.base_url}/appointment/create_availability_rule/", 
                json=data, 
                headers={**self.headers, "Content-Type": "application/json"}
            )
            if response.status_code == 201:
                return response.json()
            else:
                logging.error(f"Error creating availability rule: {response.text}")
                return None
        except Exception as e:
            logging.error(f"Error creating availability rule: {e}")
            return None

    def get_availability_rules(self, faculty_id=None, semester_id=None):
        """Get availability rules for faculty"""
        try:
            params = {}
            if faculty_id:
                params['faculty_id'] = faculty_id
            if semester_id:
                params['semester_id'] = semester_id
                
            response = requests.get(f"{self.base_url}/appointment/get_availability_rule/", 
                                  params=params, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logging.error(f"Error fetching availability rules: {e}")
            return []

    def get_faculty_profiles(self):
        """Get all faculty profiles"""
        try:
            response = requests.get(f"{self.base_url}/appointment/faculty_profiles/", headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logging.error(f"Error fetching faculty profiles: {e}")
            return []

class FacultyEditSchedulePage_ui(QWidget):
    back = QtCore.pyqtSignal()

    def __init__(self, username, roles, primary_role, token, parent=None):
        super().__init__(parent)
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        self.crud = APIClient(token=token)
        self.faculty_id = self._get_faculty_id()
        self.current_date = QDate.currentDate()
        self.time_frames = {}  # Track time frames: {(day, start_row, end_row): True}
        self._setupEditSchedulePage()
        self.retranslateUi()
        self._populateEditWeeklyGrid()
        self.setFixedSize(1100, 600)

    def _get_faculty_id(self):
        faculty_profiles = self.crud.get_faculty_profiles()
        for faculty in faculty_profiles:
            if faculty['user']['username'] == self.username:
                return faculty['id']
        return None

    def _setupEditSchedulePage(self):
        self.setObjectName("Editschedule")
        edit_layout = QtWidgets.QVBoxLayout(self)
        edit_layout.setContentsMargins(10, 10, 10, 10)
        edit_layout.setSpacing(10)

        header_widget = QtWidgets.QWidget()
        header_layout = QtWidgets.QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        self.RequestPage = QtWidgets.QLabel("Edit Schedule")
        font = QtGui.QFont("Poppins", 24)
        self.RequestPage.setFont(font)
        self.RequestPage.setStyleSheet("color: #084924;")
        header_layout.addWidget(self.RequestPage)
        header_layout.addStretch(1)

        self.backButton_3 = QtWidgets.QPushButton("<- Back")
        self.backButton_3.setFixedSize(100, 40)
        self.backButton_3.setStyleSheet("""
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
        self.backButton_3.clicked.connect(self.back.emit)
        header_layout.addWidget(self.backButton_3)

        edit_layout.addWidget(header_widget)

        self.widget_26 = QtWidgets.QWidget()
        self.widget_26.setStyleSheet("background-color: #FFFFFF; border-radius: 20px;")
        widget_layout = QtWidgets.QVBoxLayout(self.widget_26)
        widget_layout.setContentsMargins(20, 20, 20, 20)
        widget_layout.setSpacing(15)

        controls_widget = QtWidgets.QWidget()
        controls_layout = QtWidgets.QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        self.label_93 = QtWidgets.QLabel("Set Available Time Frames")
        font = QtGui.QFont("Poppins", 18, QtGui.QFont.Weight.Bold)
        self.label_93.setFont(font)
        controls_layout.addWidget(self.label_93)

        self.prevWeekButton = QtWidgets.QPushButton("←")
        self.prevWeekButton.setFixedSize(40, 35)
        self.prevWeekButton.setStyleSheet("""
            QPushButton { background-color: #084924; color: white; border-radius: 6px; font: 600 12pt 'Poppins'; }
            QPushButton:hover { background-color: #0a5a2f; }
        """)
        self.prevWeekButton.clicked.connect(self._prevWeek)
        controls_layout.addWidget(self.prevWeekButton)

        self.dateEdit = QtWidgets.QDateEdit()
        self.dateEdit.setDate(self.current_date)
        self.dateEdit.setCalendarPopup(True)
        self.dateEdit.setStyleSheet("""
            QDateEdit { border: 2px solid #064420; border-radius: 6px; padding: 4px 8px; font: 10pt 'Poppins'; color: #064420; background: white; }
        """)
        self.dateEdit.dateChanged.connect(self._updateWeek)
        controls_layout.addWidget(self.dateEdit)

        self.nextWeekButton = QtWidgets.QPushButton("→")
        self.nextWeekButton.setFixedSize(40, 35)
        self.nextWeekButton.setStyleSheet("""
            QPushButton { background-color: #084924; color: white; border-radius: 6px; font: 600 12pt 'Poppins'; }
            QPushButton:hover { background-color: #0a5a2f; }
        """)
        self.nextWeekButton.clicked.connect(self._nextWeek)
        controls_layout.addWidget(self.nextWeekButton)

        controls_layout.addStretch(1)

        self.comboBox_3 = QtWidgets.QComboBox()
        self.comboBox_3.setFixedSize(200, 35)
        self.comboBox_3.setStyleSheet("""
            QComboBox { border: 2px solid #064420; border-radius: 6px; padding: 4px 8px; font: 10pt 'Poppins'; color: #064420; background: white; }
        """)
        self.comboBox_3.addItems(["1st Semester 2025 - 2026", "2nd Semester 2025 - 2026", "Summer 2026"])
        controls_layout.addWidget(self.comboBox_3)

        # Add Time Frame Button
        self.addTimeFrameButton = QtWidgets.QPushButton("Add Time Frame")
        self.addTimeFrameButton.setFixedSize(120, 35)
        self.addTimeFrameButton.setStyleSheet("""
            QPushButton { 
                background-color: #084924; 
                color: white; 
                border-radius: 6px; 
                font: 600 10pt 'Poppins'; 
            }
            QPushButton:hover { 
                background-color: #0a5a2f; 
            }
        """)
        self.addTimeFrameButton.clicked.connect(self._showAddTimeFrameDialog)
        controls_layout.addWidget(self.addTimeFrameButton)

        # Clear All Button
        self.clearAllButton = QtWidgets.QPushButton("Clear All")
        self.clearAllButton.setFixedSize(100, 35)
        self.clearAllButton.setStyleSheet("""
            QPushButton { 
                background-color: #dc3545; 
                color: white; 
                border-radius: 6px; 
                font: 600 10pt 'Poppins'; 
            }
            QPushButton:hover { 
                background-color: #c82333; 
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.clearAllButton.clicked.connect(self._clearAllTimeFrames)
        self.clearAllButton.setEnabled(False)
        controls_layout.addWidget(self.clearAllButton)

        # Save Schedule Button
        self.saveButton = QtWidgets.QPushButton("Save Schedule")
        self.saveButton.setFixedSize(120, 35)
        self.saveButton.setStyleSheet("""
            QPushButton { 
                background-color: #084924; 
                color: white; 
                border-radius: 6px; 
                font: 600 10pt 'Poppins'; 
            }
            QPushButton:hover { 
                background-color: #0a5a2f; 
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.saveButton.clicked.connect(self._saveSchedule)
        self.saveButton.setEnabled(False)
        controls_layout.addWidget(self.saveButton)

        widget_layout.addWidget(controls_widget)
        self._setupEditWeeklyGrid(widget_layout)

        edit_layout.addWidget(self.widget_26, 1)

    def _setupEditWeeklyGrid(self, parent_layout):
        grid_container = QtWidgets.QWidget()
        grid_layout = QtWidgets.QVBoxLayout(grid_container)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(0)

        self.weeklyGridEdit = QtWidgets.QTableWidget()
        self.weeklyGridEdit.setColumnCount(8)
        self.weeklyGridEdit.setRowCount(32)  # 8:00 AM to 12:00 AM with 30-min increments
        self.weeklyGridEdit.setShowGrid(True)
        self.weeklyGridEdit.verticalHeader().setVisible(False)
        self.weeklyGridEdit.horizontalHeader().setVisible(True)
        self.weeklyGridEdit.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.weeklyGridEdit.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.weeklyGridEdit.setStyleSheet("""
            QTableWidget { 
                background: #f9f9f9; 
                font: 10pt 'Poppins'; 
                border: 1px solid #e0e0e0; 
            }
            QTableWidget::item { 
                padding: 5px; 
                border: 1px solid #e0e0e0; 
            }
            QHeaderView::section { 
                background-color: #0a5a2f; 
                color: white; 
                border: 0; 
                padding: 12px 8px; 
                font: 600 11pt 'Poppins'; 
            }
        """)
        headers = ["Time", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for i, h in enumerate(headers):
            self.weeklyGridEdit.setHorizontalHeaderItem(i, QtWidgets.QTableWidgetItem(h))

        self.weeklyGridEdit.setColumnWidth(0, 100)
        header = self.weeklyGridEdit.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Fixed)
        for c in range(1, 8):
            header.setSectionResizeMode(c, QtWidgets.QHeaderView.ResizeMode.Stretch)

        # Create time labels (8:00 AM to 12:00 AM with 30-min increments)
        times = []
        for hour in range(8, 24):  # 8 AM to 12 AM
            times.append(f"{hour % 12 or 12}:00 {'AM' if hour < 12 else 'PM'}")
            times.append(f"{hour % 12 or 12}:30 {'AM' if hour < 12 else 'PM'}")
        
        for r, t in enumerate(times):
            item = QtWidgets.QTableWidgetItem(t)
            item.setForeground(QtGui.QBrush(QtGui.QColor("#6b6b6b")))
            item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.weeklyGridEdit.setItem(r, 0, item)
            self.weeklyGridEdit.setRowHeight(r, 35)
            for c in range(1, 8):
                self._addEmptyCell(r, c)

        grid_layout.addWidget(self.weeklyGridEdit, 1)
        parent_layout.addWidget(grid_container, 1)

    def _addEmptyCell(self, row, col):
        """Add an empty cell to the grid"""
        container = QtWidgets.QWidget()
        container.setStyleSheet("QWidget { background: white; border: 1px solid #e0e0e0; }")
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        self.weeklyGridEdit.setCellWidget(row, col, container)

    def _showAddTimeFrameDialog(self):
        """Show dialog to add a time frame"""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Add Time Frame")
        dialog.setModal(True)
        dialog.setFixedSize(400, 300)
        dialog.setStyleSheet("""
            QDialog { 
                background-color: white; 
                border-radius: 12px; 
            }
            QLabel {
                font: 11pt 'Poppins';
                color: #333;
            }
            QComboBox, QTimeEdit {
                border: 2px solid #064420;
                border-radius: 6px;
                padding: 8px;
                font: 10pt 'Poppins';
                color: #064420;
                background: white;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header_label = QtWidgets.QLabel("Add Available Time Frame")
        header_label.setStyleSheet("QLabel { color: #084924; font: 600 16pt 'Poppins'; }")
        header_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header_label)

        # Day selection
        day_layout = QtWidgets.QHBoxLayout()
        day_label = QtWidgets.QLabel("Day:")
        day_label.setStyleSheet("QLabel { font: 600 11pt 'Poppins'; color: #333; }")
        day_combo = QtWidgets.QComboBox()
        day_combo.addItems(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        day_layout.addWidget(day_label)
        day_layout.addWidget(day_combo)
        layout.addLayout(day_layout)

        # Start time
        start_time_layout = QtWidgets.QHBoxLayout()
        start_time_label = QtWidgets.QLabel("Start Time:")
        start_time_label.setStyleSheet("QLabel { font: 600 11pt 'Poppins'; color: #333; }")
        start_time_edit = QTimeEdit()
        start_time_edit.setTime(QTime(8, 0))  # Default to 8:00 AM
        start_time_edit.setDisplayFormat("hh:mm AP")
        start_time_layout.addWidget(start_time_label)
        start_time_layout.addWidget(start_time_edit)
        layout.addLayout(start_time_layout)

        # End time
        end_time_layout = QtWidgets.QHBoxLayout()
        end_time_label = QtWidgets.QLabel("End Time:")
        end_time_label.setStyleSheet("QLabel { font: 600 11pt 'Poppins'; color: #333; }")
        end_time_edit = QTimeEdit()
        end_time_edit.setTime(QTime(17, 0))  # Default to 5:00 PM
        end_time_edit.setDisplayFormat("hh:mm AP")
        end_time_layout.addWidget(end_time_label)
        end_time_layout.addWidget(end_time_edit)
        layout.addLayout(end_time_layout)

        # Slot duration
        duration_layout = QtWidgets.QHBoxLayout()
        duration_label = QtWidgets.QLabel("Slot Duration (minutes):")
        duration_label.setStyleSheet("QLabel { font: 600 11pt 'Poppins'; color: #333; }")
        duration_combo = QtWidgets.QComboBox()
        duration_combo.addItems(["15", "30", "45", "60"])
        duration_combo.setCurrentText("30")
        duration_layout.addWidget(duration_label)
        duration_layout.addWidget(duration_combo)
        layout.addLayout(duration_layout)

        layout.addStretch(1)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.setFixedHeight(35)
        cancel_btn.setStyleSheet("""
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
        cancel_btn.clicked.connect(dialog.reject)
        
        add_btn = QtWidgets.QPushButton("Add Time Frame")
        add_btn.setFixedHeight(35)
        add_btn.setStyleSheet("""
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
        
        def add_time_frame():
            day = day_combo.currentText()
            start_time = start_time_edit.time().toString("hh:mm AP")
            end_time = end_time_edit.time().toString("hh:mm AP")
            slot_duration = int(duration_combo.currentText())
            
            self._addTimeFrameToGrid(day, start_time, end_time, slot_duration)
            dialog.accept()
        
        add_btn.clicked.connect(add_time_frame)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch(1)
        button_layout.addWidget(add_btn)
        layout.addLayout(button_layout)
        
        dialog.exec()

    def _addTimeFrameToGrid(self, day, start_time_str, end_time_str, slot_duration):
        """Add a time frame to the grid visualization"""
        # Convert day to column number
        day_map = {"Sunday": 1, "Monday": 2, "Tuesday": 3, "Wednesday": 4, 
                  "Thursday": 5, "Friday": 6, "Saturday": 7}
        col = day_map.get(day)
        if not col:
            return

        # Convert time strings to row numbers
        start_row = self._timeToRow(start_time_str)
        end_row = self._timeToRow(end_time_str)
        
        if start_row is None or end_row is None or start_row >= end_row:
            QMessageBox.warning(self, "Invalid Time", "Please check the start and end times.")
            return

        # Store the time frame
        time_frame_key = (day, start_row, end_row, slot_duration)
        self.time_frames[time_frame_key] = True

        # Visualize the time frame on the grid
        for row in range(start_row, end_row):
            self._colorTimeSlot(row, col, day, start_time_str, end_time_str, slot_duration)

        # Update button states
        self._updateButtonStates()

    def _timeToRow(self, time_str):
        """Convert time string to row number"""
        try:
            # Parse time string (e.g., "08:00 AM", "05:30 PM")
            time_part, period = time_str.split()
            hour, minute = map(int, time_part.split(':'))
            
            # Convert to 24-hour format
            if period.upper() == "PM" and hour != 12:
                hour += 12
            elif period.upper() == "AM" and hour == 12:
                hour = 0
            
            # Calculate row (each row is 30 minutes starting from 8:00 AM)
            base_hour = 8  # Grid starts at 8:00 AM
            total_minutes = (hour - base_hour) * 60 + minute
            row = total_minutes // 30
            
            return max(0, min(row, self.weeklyGridEdit.rowCount() - 1))
        except:
            return None

    def _colorTimeSlot(self, row, col, day, start_time, end_time, slot_duration):
        """Color a time slot in the grid"""
        container = QtWidgets.QWidget()
        container.setStyleSheet("""
            QWidget { 
                background: #ffc000; 
                border: 1px solid #e6ac00; 
                border-radius: 4px; 
                margin: 1px;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(1)
        
        # Time label
        time_label = QtWidgets.QLabel(self._getTimeFromRow(row))
        time_label.setStyleSheet("""
            QLabel { 
                color: #2b2b2b; 
                font: 600 8pt 'Poppins'; 
                background: transparent; 
            }
        """)
        time_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        
        # Duration label
        duration_label = QtWidgets.QLabel(f"{slot_duration}min")
        duration_label.setStyleSheet("""
            QLabel { 
                color: #2b2b2b; 
                font: 7pt 'Poppins'; 
                background: transparent; 
            }
        """)
        duration_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(time_label)
        layout.addWidget(duration_label)
        
        # Add delete button
        delete_btn = QtWidgets.QPushButton("×")
        delete_btn.setFixedSize(16, 16)
        delete_btn.setStyleSheet("""
            QPushButton { 
                background-color: #dc3545; 
                color: white; 
                border-radius: 8px; 
                font: bold 7pt 'Poppins'; 
                border: none;
            }
            QPushButton:hover { 
                background-color: #c82333; 
            }
        """)
        delete_btn.clicked.connect(lambda: self._removeTimeFrame(day, row, col))
        layout.addWidget(delete_btn, 0, QtCore.Qt.AlignmentFlag.AlignRight)
        
        self.weeklyGridEdit.setCellWidget(row, col, container)

    def _getTimeFromRow(self, row):
        """Convert row number back to time string"""
        base_hour = 8  # Grid starts at 8:00 AM
        total_minutes = row * 30
        hour = base_hour + total_minutes // 60
        minute = total_minutes % 60
        
        period = "AM" if hour < 12 else "PM"
        hour_12 = hour % 12 if hour != 12 else 12
        return f"{hour_12}:{minute:02d} {period}"

    def _removeTimeFrame(self, day, row, col):
        """Remove a specific time frame"""
        # Find and remove the time frame that includes this row
        for time_frame_key in list(self.time_frames.keys()):
            frame_day, start_row, end_row, slot_duration = time_frame_key
            if frame_day == day and start_row <= row < end_row:
                # Remove all slots in this time frame
                for r in range(start_row, end_row):
                    self._addEmptyCell(r, col)
                # Remove from time frames
                del self.time_frames[time_frame_key]
                break
        
        self._updateButtonStates()

    def _clearAllTimeFrames(self):
        """Clear all time frames"""
        if not self.time_frames:
            return
            
        reply = QMessageBox.question(
            self,
            "Clear All Time Frames",
            "Are you sure you want to clear all time frames?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Clear all colored cells
            for row in range(self.weeklyGridEdit.rowCount()):
                for col in range(1, self.weeklyGridEdit.columnCount()):
                    self._addEmptyCell(row, col)
            
            # Clear time frames dictionary
            self.time_frames.clear()
            self._updateButtonStates()

    def _saveSchedule(self):
        """Save the schedule by creating availability rules"""
        if not self.time_frames:
            QMessageBox.warning(self, "No Time Frames", "Please add time frames before saving.")
            return

        if not self.faculty_id:
            QMessageBox.critical(self, "Error", "Faculty ID not found.")
            return

        # Map day names to Django format
        day_map = {
            "Monday": "MON", "Tuesday": "TUE", "Wednesday": "WED",
            "Thursday": "THU", "Friday": "FRI", "Saturday": "SAT", "Sunday": "SUN"
        }

        success_count = 0
        error_count = 0

        for time_frame_key in self.time_frames:
            day, start_row, end_row, slot_duration = time_frame_key
            
            # Convert rows back to time
            start_time = self._rowToTime(start_row)
            end_time = self._rowToTime(end_row)
            
            if start_time and end_time and day in day_map:
                # Create availability rule data
                rule_data = {
                    "faculty": self.faculty_id,
                    "day_of_week": day_map[day],
                    "start_time": start_time,
                    "end_time": end_time,
                    "slot_minutes": slot_duration
                }
                
                # Send to API
                result = self.crud.create_availability_rule(rule_data)
                if result:
                    success_count += 1
                else:
                    error_count += 1

        # Show result message
        if success_count > 0:
            message = f"Successfully created {success_count} availability rule(s)."
            if error_count > 0:
                message += f" {error_count} rule(s) failed to create."
            QMessageBox.information(self, "Success", message)
            
            # Clear the grid after successful save
            self._clearAllTimeFrames()
        else:
            QMessageBox.critical(self, "Error", "Failed to create any availability rules.")

    def _rowToTime(self, row):
        """Convert row number to time string (HH:MM:SS)"""
        base_hour = 8  # Grid starts at 8:00 AM
        total_minutes = row * 30
        hour = base_hour + total_minutes // 60
        minute = total_minutes % 60
        
        return f"{hour:02d}:{minute:02d}:00"

    def _updateButtonStates(self):
        """Update button states based on whether there are time frames"""
        has_time_frames = len(self.time_frames) > 0
        self.clearAllButton.setEnabled(has_time_frames)
        self.saveButton.setEnabled(has_time_frames)

    def _populateEditWeeklyGrid(self):
        """Populate the grid with existing availability rules"""
        if not self.faculty_id:
            return

        # Clear existing time frames and grid
        self.time_frames.clear()
        for row in range(self.weeklyGridEdit.rowCount()):
            for col in range(1, self.weeklyGridEdit.columnCount()):
                self._addEmptyCell(row, col)

        # Get existing availability rules
        rules = self.crud.get_availability_rules(faculty_id=self.faculty_id)
        
        # Map Django day format to full day names
        day_map = {
            "MON": "Monday", "TUE": "Tuesday", "WED": "Wednesday",
            "THU": "Thursday", "FRI": "Friday", "SAT": "Saturday", "SUN": "Sunday"
        }

        for rule in rules:
            day_full = day_map.get(rule['day_of_week'])
            if not day_full:
                continue

            # Convert time strings to row numbers
            start_time = rule['start_time']
            end_time = rule['end_time']
            slot_duration = rule.get('slot_minutes', 30)

            start_row = self._timeStringToRow(start_time)
            end_row = self._timeStringToRow(end_time)

            if start_row is not None and end_row is not None:
                # Add to time frames
                time_frame_key = (day_full, start_row, end_row, slot_duration)
                self.time_frames[time_frame_key] = True

                # Visualize on grid
                col = list(day_map.values()).index(day_full) + 1
                for row in range(start_row, end_row):
                    self._colorTimeSlot(row, col, day_full, start_time, end_time, slot_duration)

        self._updateButtonStates()

    def _timeStringToRow(self, time_str):
        """Convert time string (HH:MM:SS) to row number"""
        try:
            # Parse time string (e.g., "08:00:00")
            parts = time_str.split(':')
            hour = int(parts[0])
            minute = int(parts[1])
            
            # Calculate row (each row is 30 minutes starting from 8:00 AM)
            base_hour = 8  # Grid starts at 8:00 AM
            total_minutes = (hour - base_hour) * 60 + minute
            row = total_minutes // 30
            
            return max(0, min(row, self.weeklyGridEdit.rowCount() - 1))
        except:
            return None

    def _updateWeek(self):
        self.current_date = self.dateEdit.date()
        # Note: For availability rules, week navigation might not be needed
        # as rules are day-based rather than date-based

    def _prevWeek(self):
        self.current_date = self.current_date.addDays(-7)
        self.dateEdit.setDate(self.current_date)

    def _nextWeek(self):
        self.current_date = self.current_date.addDays(7)
        self.dateEdit.setDate(self.current_date)

    def retranslateUi(self):
        self.RequestPage.setText("Edit Schedule")
        self.label_93.setText("Set Available Time Frames")
        self.addTimeFrameButton.setText("Add Time Frame")
        self.clearAllButton.setText("Clear All")
        self.saveButton.setText("Save Schedule")
