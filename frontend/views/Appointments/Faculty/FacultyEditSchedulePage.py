from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QDialog
from PyQt6.QtCore import QDate
from .appointment_crud import appointment_crud

class FacultyEditSchedulePage_ui(QWidget):
    back = QtCore.pyqtSignal()

    def __init__(self, username, roles, primary_role, token, parent=None):
        super().__init__(parent)
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        self.crud = appointment_crud()
        self.faculty_id = self._get_faculty_id()
        self.current_date = QDate.currentDate()
        self.selected_slots = {}  # Track selected slots: {(row, col): True}
        self._setupEditSchedulePage()
        self.retranslateUi()
        self._populateEditWeeklyGrid()
        self.setFixedSize(1100, 550)

    def _get_faculty_id(self):
        faculty_list = self.crud.list_faculty()
        for faculty in faculty_list:
            if faculty["email"] == self.username:
                return faculty["id"]
        return 1

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

        self.backButton_3 = QtWidgets.QPushButton()
        self.backButton_3.setFixedSize(40, 40)
        self.backButton_3.setStyleSheet("border: none; background: transparent;")
        self.backButton_3.setIcon(QtGui.QIcon(":/assets/back_button.png"))
        self.backButton_3.setIconSize(QtCore.QSize(40, 40))
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

        self.label_93 = QtWidgets.QLabel("Set Available Slots")
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

        # Unselect All Button
        self.unselectButton = QtWidgets.QPushButton("Unselect All")
        self.unselectButton.setFixedSize(100, 35)
        self.unselectButton.setStyleSheet("""
            QPushButton { 
                background-color: #6c757d; 
                color: white; 
                border-radius: 6px; 
                font: 600 10pt 'Poppins'; 
            }
            QPushButton:hover { 
                background-color: #5a6268; 
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.unselectButton.clicked.connect(self._unselectAllSlots)
        self.unselectButton.setEnabled(False)  # Initially disabled
        controls_layout.addWidget(self.unselectButton)

        self.createButton = QtWidgets.QPushButton("Create")
        self.createButton.setFixedSize(80, 35)
        self.createButton.setStyleSheet("""
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
        self.createButton.clicked.connect(self._createSchedule)
        self.createButton.setEnabled(False)  # Initially disabled
        controls_layout.addWidget(self.createButton)

        self.cancelButton = QtWidgets.QPushButton("Cancel")
        self.cancelButton.setFixedSize(80, 35)
        self.cancelButton.setStyleSheet("""
            QPushButton { 
                background-color: #dc3545; 
                color: white; 
                border-radius: 6px; 
                font: 600 10pt 'Poppins'; 
            }
            QPushButton:hover { 
                background-color: #c82333; 
            }
        """)
        self.cancelButton.clicked.connect(self._cancelChanges)
        controls_layout.addWidget(self.cancelButton)

        self.backButton_7 = QtWidgets.QPushButton("<- Back")
        self.backButton_7.setFixedSize(40, 40)
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
        controls_layout.addWidget(self.backButton_7)

        widget_layout.addWidget(controls_widget)
        self._setupEditWeeklyGrid(widget_layout)

        edit_layout.addWidget(self.widget_26, 1)

    def resizeEvent(self, event):
        width = self.weeklyGridEdit.width()
        self.weeklyGridEdit.setColumnWidth(0, 100)
        for c in range(1, 8):
            self.weeklyGridEdit.setColumnWidth(c, int((width - 100) / 7))
        super().resizeEvent(event)

    def _setupEditWeeklyGrid(self, parent_layout):
        grid_container = QtWidgets.QWidget()
        grid_layout = QtWidgets.QVBoxLayout(grid_container)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(0)

        self.weeklyGridEdit = QtWidgets.QTableWidget()
        self.weeklyGridEdit.setColumnCount(8)
        self.weeklyGridEdit.setRowCount(24)  # 7 AM to 7 PM with 30-min increments
        self.weeklyGridEdit.setShowGrid(False)
        self.weeklyGridEdit.verticalHeader().setVisible(False)
        self.weeklyGridEdit.horizontalHeader().setVisible(True)
        self.weeklyGridEdit.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.weeklyGridEdit.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.weeklyGridEdit.setStyleSheet("""
            QTableWidget { background: white; font: 10pt 'Poppins'; border: none; }
            QHeaderView::section { background-color: #0a5a2f; color: white; border: 0; padding: 12px 8px; font: 600 11pt 'Poppins'; }
        """)
        headers = ["", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for i, h in enumerate(headers):
            self.weeklyGridEdit.setHorizontalHeaderItem(i, QtWidgets.QTableWidgetItem(h))

        self.weeklyGridEdit.setColumnWidth(0, 100)
        header = self.weeklyGridEdit.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Fixed)
        for c in range(1, 8):
            header.setSectionResizeMode(c, QtWidgets.QHeaderView.ResizeMode.Stretch)

        # Create time labels (7:00 AM to 7:00 PM with 30-min increments)
        times = []
        for hour in range(7, 19):  # 7 AM to 7 PM
            times.append(f"{hour % 12 or 12}:00 {'AM' if hour < 12 else 'PM'}")
            times.append(f"{hour % 12 or 12}:30 {'AM' if hour < 12 else 'PM'}")
        
        for r, t in enumerate(times):
            item = QtWidgets.QTableWidgetItem(t)
            item.setForeground(QtGui.QBrush(QtGui.QColor("#6b6b6b")))
            item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.weeklyGridEdit.setItem(r, 0, item)
            self.weeklyGridEdit.setRowHeight(r, 40)  # Reduced height for better fit
            for c in range(1, 8):
                self._addPlusCell(r, c)

        grid_layout.addWidget(self.weeklyGridEdit, 1)
        parent_layout.addWidget(grid_container, 1)

    def _addPlusCell(self, row, col):
        container = QtWidgets.QWidget()
        container.setStyleSheet("QWidget { border: 1px dashed #cfd8dc; border-radius: 4px; background: transparent; }")
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(2, 2, 2, 2)
        plus_btn = QtWidgets.QPushButton("+")
        plus_btn.setFixedSize(24, 24)
        plus_btn.setStyleSheet("""
            QPushButton { 
                background-color: #e8f5e8; 
                color: #084924; 
                border: 1px solid #084924; 
                border-radius: 12px; 
                font: bold 12pt 'Poppins'; 
            }
            QPushButton:hover { 
                background-color: #d4edda; 
                border: 2px solid #084924; 
            }
        """)
        plus_btn.clicked.connect(lambda checked, r=row, c=col: self._showMakeAvailableDialog(r, c))
        layout.addWidget(plus_btn, 0, QtCore.Qt.AlignmentFlag.AlignCenter)
        self.weeklyGridEdit.setCellWidget(row, col, container)

    def _showMakeAvailableDialog(self, row, col):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Make Time Slot Available")
        dialog.setModal(True)
        dialog.setFixedSize(400, 200)
        dialog.setStyleSheet("QDialog { background-color: white; border-radius: 10px; }")
        
        layout = QtWidgets.QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        time_item = self.weeklyGridEdit.item(row, 0)
        time_text = time_item.text() if time_item else "Unknown"
        day_header = self.weeklyGridEdit.horizontalHeaderItem(col)
        day_text = day_header.text() if day_header else "Unknown"

        title_label = QtWidgets.QLabel("Make this slot available")
        title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("QLabel { color: #2b2b2b; font: 600 14pt 'Poppins'; }")
        layout.addWidget(title_label)

        time_info = QtWidgets.QLabel(f"{day_text} {time_text}")
        time_info.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        time_info.setStyleSheet("""
            QLabel { 
                color: #6b6b6b; 
                font: 11pt 'Poppins'; 
                background-color: #f8f9fa; 
                padding: 8px; 
                border-radius: 6px; 
            }
        """)
        layout.addWidget(time_info)

        layout.addStretch(1)
        
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
        
        make_available_btn = QtWidgets.QPushButton("Make Available")
        make_available_btn.setFixedHeight(35)
        make_available_btn.setStyleSheet("""
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
        make_available_btn.clicked.connect(lambda: self._convertToAvailableSlot(row, col, time_text, day_text))
        make_available_btn.clicked.connect(dialog.accept)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch(1)
        button_layout.addWidget(make_available_btn)
        layout.addLayout(button_layout)
        
        dialog.exec()

    def _convertToAvailableSlot(self, row, col, time_text, day_text):
        container = QtWidgets.QWidget()
        container.setStyleSheet("QWidget { background: transparent; }")
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(2, 2, 2, 2)
        
        slot_widget = QtWidgets.QWidget()
        slot_widget.setStyleSheet("""
            QWidget { 
                background: #ffc000; 
                border-radius: 6px; 
                border: 1px solid #e6ac00; 
            }
        """)
        slot_widget.setMinimumHeight(36)
        
        slot_layout = QtWidgets.QVBoxLayout(slot_widget)
        slot_layout.setContentsMargins(8, 4, 8, 4)
        slot_layout.setSpacing(2)
        
        time_label = QtWidgets.QLabel(time_text)
        time_label.setStyleSheet("""
            QLabel { 
                color: #2b2b2b; 
                font: 600 9pt 'Poppins'; 
                background: transparent; 
            }
        """)
        time_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        
        status_label = QtWidgets.QLabel("Available")
        status_label.setStyleSheet("""
            QLabel { 
                color: #2b2b2b; 
                font: 8pt 'Poppins'; 
                background: transparent; 
            }
        """)
        status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        
        slot_layout.addWidget(time_label)
        slot_layout.addWidget(status_label)
        layout.addWidget(slot_widget)
        
        # Add unselect button
        unselect_btn = QtWidgets.QPushButton("×")
        unselect_btn.setFixedSize(20, 20)
        unselect_btn.setStyleSheet("""
            QPushButton { 
                background-color: #dc3545; 
                color: white; 
                border-radius: 10px; 
                font: bold 8pt 'Poppins'; 
                border: none;
            }
            QPushButton:hover { 
                background-color: #c82333; 
            }
        """)
        unselect_btn.clicked.connect(lambda: self._unselectSlot(row, col))
        layout.addWidget(unselect_btn)
        
        self.weeklyGridEdit.setCellWidget(row, col, container)
        
        # Mark as selected
        self.selected_slots[(row, col)] = True
        
        # Enable buttons
        self._updateButtonStates()

    def _unselectSlot(self, row, col):
        """Remove the selected slot and restore the plus button"""
        # Remove from selected slots
        if (row, col) in self.selected_slots:
            del self.selected_slots[(row, col)]
        
        # Restore the plus button
        self._addPlusCell(row, col)
        
        # Update button states
        self._updateButtonStates()

    def _unselectAllSlots(self):
        """Unselect all selected slots"""
        if not self.selected_slots:
            return
            
        # Show confirmation dialog
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Unselect All Slots")
        dialog.setModal(True)
        dialog.setFixedSize(350, 180)
        dialog.setStyleSheet("QDialog { background-color: white; border-radius: 10px; }")
        
        layout = QtWidgets.QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title_label = QtWidgets.QLabel("Unselect All Slots?")
        title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("QLabel { color: #2b2b2b; font: 600 14pt 'Poppins'; }")
        layout.addWidget(title_label)
        
        message_label = QtWidgets.QLabel(f"This will unselect all {len(self.selected_slots)} selected time slots.")
        message_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        message_label.setStyleSheet("QLabel { color: #666666; font: 11pt 'Poppins'; }")
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
        layout.addStretch(1)
        
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
        
        confirm_btn = QtWidgets.QPushButton("Unselect All")
        confirm_btn.setFixedHeight(35)
        confirm_btn.setStyleSheet("""
            QPushButton { 
                background-color: #dc3545; 
                color: white; 
                border-radius: 6px; 
                font: 600 11pt 'Poppins'; 
            }
            QPushButton:hover { 
                background-color: #c82333; 
            }
        """)
        confirm_btn.clicked.connect(dialog.accept)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch(1)
        button_layout.addWidget(confirm_btn)
        layout.addLayout(button_layout)
        
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            # Unselect all slots
            for (row, col) in list(self.selected_slots.keys()):
                self._unselectSlot(row, col)

    def _cancelChanges(self):
        """Cancel all changes and go back"""
        if self.selected_slots:
            # Show confirmation dialog if there are unsaved changes
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle("Cancel Changes")
            dialog.setModal(True)
            dialog.setFixedSize(350, 180)
            dialog.setStyleSheet("QDialog { background-color: white; border-radius: 10px; }")
            
            layout = QtWidgets.QVBoxLayout(dialog)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(15)
            
            title_label = QtWidgets.QLabel("Cancel Changes?")
            title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            title_label.setStyleSheet("QLabel { color: #2b2b2b; font: 600 14pt 'Poppins'; }")
            layout.addWidget(title_label)
            
            message_label = QtWidgets.QLabel(f"You have {len(self.selected_slots)} unsaved changes. Are you sure you want to cancel?")
            message_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            message_label.setStyleSheet("QLabel { color: #666666; font: 11pt 'Poppins'; }")
            message_label.setWordWrap(True)
            layout.addWidget(message_label)
            
            layout.addStretch(1)
            
            button_layout = QtWidgets.QHBoxLayout()
            no_btn = QtWidgets.QPushButton("No")
            no_btn.setFixedHeight(35)
            no_btn.setStyleSheet("""
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
            no_btn.clicked.connect(dialog.reject)
            
            yes_btn = QtWidgets.QPushButton("Yes, Cancel")
            yes_btn.setFixedHeight(35)
            yes_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #dc3545; 
                    color: white; 
                    border-radius: 6px; 
                    font: 600 11pt 'Poppins'; 
                }
                QPushButton:hover { 
                    background-color: #c82333; 
                }
            """)
            yes_btn.clicked.connect(dialog.accept)
            
            button_layout.addWidget(no_btn)
            button_layout.addStretch(1)
            button_layout.addWidget(yes_btn)
            layout.addLayout(button_layout)
            
            if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
                self.back.emit()
        else:
            # No changes, just go back
            self.back.emit()

    def _updateButtonStates(self):
        """Update the state of buttons based on selected slots"""
        has_selections = len(self.selected_slots) > 0
        self.unselectButton.setEnabled(has_selections)
        self.createButton.setEnabled(has_selections)

    def _createSchedule(self):
        # Create time map for 12-hour to 24-hour conversion
        time_map = {}
        index = 0
        for hour in range(7, 19):  # 7 AM to 7 PM
            for minute in [0, 30]:
                period = "AM" if hour < 12 else "PM"
                hour_12 = hour % 12 if hour != 12 else 12
                time_12h = f"{hour_12}:{minute:02d} {period}"
                time_map[index] = time_12h
                index += 1
       
        day_map = {1: "Sunday", 2: "Monday", 3: "Tuesday", 4: "Wednesday", 5: "Thursday", 6: "Friday", 7: "Saturday"}
        time_slots = []
        
        # Find all available slots
        for (row, col) in self.selected_slots.keys():
            time_12h = time_map.get(row)
            day_name = day_map.get(col)
            
            if time_12h and day_name:
                # Convert 12-hour time to 24-hour format
                time_part, period = time_12h.split()
                hour_12, minute = map(int, time_part.split(':'))
                
                # Convert to 24-hour format
                if period == "PM" and hour_12 != 12:
                    hour_24 = hour_12 + 12
                elif period == "AM" and hour_12 == 12:
                    hour_24 = 0
                else:
                    hour_24 = hour_12
                
                start_time = f"{hour_24:02d}:{minute:02d}"
                
                # Calculate end time (30 minutes later)
                end_minute = minute + 30
                end_hour = hour_24
                if end_minute >= 60:
                    end_hour += 1
                    end_minute -= 60
                end_time = f"{end_hour:02d}:{end_minute:02d}"
                
                time_slots.append({
                    "start": start_time,
                    "end": end_time,
                    "day": day_name
                })
        
        if time_slots:
            try:
                result = self.crud.plot_schedule(self.faculty_id, time_slots)
                if result:
                    self._showScheduleUpdatedDialog("Schedule created successfully!")
                    # Clear selections after successful creation
                    self.selected_slots.clear()
                    self._updateButtonStates()
                    # Reload the grid to show existing schedule
                    self._populateEditWeeklyGrid()
                else:
                    self._showScheduleUpdatedDialog("Failed to create schedule.", is_error=True)
            except Exception as e:
                self._showScheduleUpdatedDialog(f"Error creating schedule: {str(e)}", is_error=True)
        else:
            self._showScheduleUpdatedDialog("No time slots selected. Please add available slots first.", is_error=True)

    def _populateEditWeeklyGrid(self):
        # Clear all cells first
        for row in range(self.weeklyGridEdit.rowCount()):
            for col in range(1, self.weeklyGridEdit.columnCount()):
                self.weeklyGridEdit.removeCellWidget(row, col)
                self._addPlusCell(row, col)
        
        # Clear selected slots
        self.selected_slots.clear()
        self._updateButtonStates()
        
        # Load existing schedule
        block = self.crud.get_active_block(self.faculty_id)
        if "error" not in block:
            entries = self.crud.get_block_entries(block["id"])
            day_map = {"Sunday": 1, "Monday": 2, "Tuesday": 3, "Wednesday": 4, "Thursday": 5, "Friday": 6, "Saturday": 7}
            
            # Create time map for conversion
            time_map = {}
            index = 0
            for hour in range(7, 19):  # 7 AM to 7 PM
                for minute in [0, 30]:
                    period = "AM" if hour < 12 else "PM"
                    hour_12 = hour % 12 if hour != 12 else 12
                    time_12h = f"{hour_12}:{minute:02d} {period}"
                    time_24h = f"{hour:02d}:{minute:02d}"
                    time_map[time_24h] = index
                    index += 1
            
            for entry in entries:
                col = day_map.get(entry["day_of_week"])
                start_time_24h = entry["start_time"]
                if start_time_24h in time_map and col:
                    row = time_map[start_time_24h]
                    # Convert to 12-hour format for display
                    hour, minute = map(int, start_time_24h.split(':'))
                    period = "AM" if hour < 12 else "PM"
                    hour_12 = hour % 12 if hour != 0 else 12
                    time_12h = f"{hour_12}:{minute:02d} {period}"
                    self._convertToAvailableSlot(row, col, time_12h, entry["day_of_week"])

    def _updateWeek(self):
        self.current_date = self.dateEdit.date()
        self._populateEditWeeklyGrid()

    def _prevWeek(self):
        self.current_date = self.current_date.addDays(-7)
        self.dateEdit.setDate(self.current_date)
        self._populateEditWeeklyGrid()

    def _nextWeek(self):
        self.current_date = self.current_date.addDays(7)
        self.dateEdit.setDate(self.current_date)
        self._populateEditWeeklyGrid()

    def _showScheduleUpdatedDialog(self, message="Schedule Updated!", is_error=False):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Success" if not is_error else "Error")
        dialog.setModal(True)
        dialog.setFixedSize(300, 150)
        
        if is_error:
            dialog.setStyleSheet("QDialog { background-color: white; border-radius: 10px; }")
        else:
            dialog.setStyleSheet("QDialog { background-color: white; border-radius: 10px; }")
        
        layout = QtWidgets.QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        
        message_label = QtWidgets.QLabel(message)
        message_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        if is_error:
            message_label.setStyleSheet("QLabel { color: #d32f2f; font: 600 12pt 'Poppins'; }")
        else:
            message_label.setStyleSheet("QLabel { color: #084924; font: 600 14pt 'Poppins'; }")
        layout.addWidget(message_label)
        
        ok_button = QtWidgets.QPushButton("OK")
        ok_button.setFixedHeight(40)
        if is_error:
            ok_button.setStyleSheet("""
                QPushButton { 
                    background-color: #d32f2f; 
                    color: white; 
                    border-radius: 8px; 
                    font: 600 12pt 'Poppins'; 
                }
                QPushButton:hover { 
                    background-color: #b71c1c; 
                }
            """)
        else:
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
        self.RequestPage.setText("Edit Schedule")
        self.label_93.setText("Set Available Slots")
        self.unselectButton.setText("Unselect All")
        self.cancelButton.setText("Cancel")
        self.createButton.setText("Create")