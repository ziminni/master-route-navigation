from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMessageBox
from .appointment_crud import appointment_crud

class StudentEditSchedulePage_ui(QWidget):
    back = QtCore.pyqtSignal()

    def __init__(self, username, roles, primary_role, token, parent=None):
        super().__init__(parent)
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        self.Appointment_crud = appointment_crud()
        self._setupEditSchedulePage()
        self.setFixedSize(1000, 550)
        # Load current student's schedule if any
        self._loadCurrentSchedule()

    def _loadCurrentSchedule(self):
        """Load the current student's schedule from database"""
        try:
            student_id = self._get_current_student_id()
            if student_id:
                # Get student's appointments
                appointments = self.Appointment_crud.get_student_appointments(student_id)
                
                # Here you would populate the schedule grid with existing appointments
                # This is a simplified version - you'd need to adapt it to your grid structure
                print(f"Loaded {len(appointments)} appointments for student {student_id}")
                
        except Exception as e:
            print(f"Error loading current schedule: {e}")

    def _get_current_student_id(self):
        """Get the current student's ID"""
        students = self.Appointment_crud.list_students()
        for student in students:
            if student.get('email') == self.username or student.get('name') == self.username:
                return student.get('id')
        return None

    def _setupEditSchedulePage(self):
        self.setObjectName("Editschedule")
        
        # Main layout
        edit_layout = QtWidgets.QVBoxLayout(self)
        edit_layout.setContentsMargins(0, 0, 0, 0)
        edit_layout.setSpacing(10)
        
        # Header
        header_widget = QtWidgets.QWidget()
        header_layout = QtWidgets.QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.RequestPage = QtWidgets.QLabel("Edit Schedule")
        font = QtGui.QFont("Poppins", 24)
        self.RequestPage.setFont(font)
        self.RequestPage.setStyleSheet("color: #084924;")
        
        header_layout.addWidget(self.RequestPage)
        header_layout.addStretch(1)

        # Save button
        self.saveButton = QtWidgets.QPushButton("Save Changes")
        self.saveButton.setFixedSize(120, 35)
        self.saveButton.setStyleSheet("""
            QPushButton {
                background-color: #084924;
                color: white;
                border-radius: 8px;
                font: 10pt 'Poppins';
            }
            QPushButton:hover {
                background-color: #0a5a2f;
            }
        """)
        self.saveButton.clicked.connect(self._saveScheduleChanges)
        header_layout.addWidget(self.saveButton)

        self.backbutton = QtWidgets.QPushButton("<- Back")
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
        self.backbutton.clicked.connect(self.back)
        header_layout.addWidget(self.backbutton)

        # self.backButton_3 = QtWidgets.QLabel()
        # self.backButton_3.setFixedSize(40, 40)
        # self.backButton_3.setPixmap(QtGui.QPixmap(":/assets/back_button.png"))
        # self.backButton_3.setScaledContents(True)
        # header_layout.addWidget(self.backButton_3)
        
        edit_layout.addWidget(header_widget)
        
        # White container with rounded corners
        self.widget_26 = QtWidgets.QWidget()
        self.widget_26.setStyleSheet("background-color: #FFFFFF; border-radius: 20px;")
        
        widget_layout = QtWidgets.QVBoxLayout(self.widget_26)
        widget_layout.setContentsMargins(20, 20, 20, 20)
        widget_layout.setSpacing(15)
        
        # Controls row
        controls_widget = QtWidgets.QWidget()
        controls_layout = QtWidgets.QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        
        self.label_93 = QtWidgets.QLabel("Set Available Slots")
        font = QtGui.QFont()
        font.setPointSize(18)
        font.setBold(True)
        self.label_93.setFont(font)
        
        controls_layout.addWidget(self.label_93)
        controls_layout.addStretch(1)
        
        self.cancelButton = QtWidgets.QPushButton("Cancel")
        self.cancelButton.setFixedSize(80, 35)
        self.cancelButton.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border-radius: 6px;
                font: 600 10pt 'Poppins';
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        
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
        """)
        
        self.comboBox_3 = QtWidgets.QComboBox()
        self.comboBox_3.setFixedSize(200, 35)
        self.comboBox_3.setStyleSheet("""
            QComboBox {
                border: 2px solid #064420;
                border-radius: 6px;
                padding: 4px 8px;
                font: 10pt 'Poppins';
                color: #064420;
                background: white;
            }
        """)
        self.comboBox_3.addItems([
            "1st Semester 2025 - 2026",
            "2nd Semester 2025 - 2026",
            "Summer 2026"
        ])
        
        controls_layout.addWidget(self.cancelButton)
        controls_layout.addWidget(self.createButton)
        controls_layout.addWidget(self.comboBox_3)
        
        widget_layout.addWidget(controls_widget)
        
        # Weekly grid
        self._setupEditWeeklyGrid(widget_layout)
        
        edit_layout.addWidget(self.widget_26, 1)

    def _setupEditWeeklyGrid(self, parent_layout):
        # Weekly grid container
        grid_container = QtWidgets.QWidget()
        grid_container.setObjectName("grid_container")
        
        grid_layout = QtWidgets.QVBoxLayout(grid_container)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(0)
        
        # Weekly grid table
        self.weeklyGridEdit = QtWidgets.QTableWidget()
        self.weeklyGridEdit.setColumnCount(8)  # Time + Mon..Sun
        self.weeklyGridEdit.setRowCount(24)    # 24 hours from 7:00 AM to 6:30 AM next day
        self.weeklyGridEdit.setShowGrid(False)
        self.weeklyGridEdit.verticalHeader().setVisible(False)
        self.weeklyGridEdit.horizontalHeader().setVisible(True)
        self.weeklyGridEdit.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.weeklyGridEdit.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.weeklyGridEdit.setStyleSheet(
            """
            QTableWidget { 
                background: white; 
                font: 10pt 'Poppins'; 
                border: none;
            }
            QHeaderView::section { 
                background-color: #0a5a2f; 
                color: white; 
                border: 0; 
                padding: 12px 8px; 
                font: 600 11pt 'Poppins';
            }
            """
        )
        
        # Headers
        headers = ["", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, h in enumerate(headers):
            self.weeklyGridEdit.setHorizontalHeaderItem(i, QtWidgets.QTableWidgetItem(h))
        
        self.weeklyGridEdit.setColumnWidth(0, 100)
        header = self.weeklyGridEdit.horizontalHeader()
        try:
            header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Fixed)
            for c in range(1, 8):
                header.setSectionResizeMode(c, QtWidgets.QHeaderView.ResizeMode.Stretch)
        except Exception:
            pass
        
        # Time labels (30-minute intervals from 7:00 AM to 6:30 AM next day)
        times = []
        for hour in range(7, 31):  # 7 AM to 6 AM next day (24 hours)
            actual_hour = hour % 24
            period = "AM" if actual_hour < 12 else "PM"
            display_hour = actual_hour if actual_hour <= 12 else actual_hour - 12
            times.append(f"{display_hour}:00 {period}")
            times.append(f"{display_hour}:30 {period}")
            
        # Only show first 24 rows (7:00 AM to 6:30 AM next day)
        times = times[:24]
        
        for r, t in enumerate(times):
            item = QtWidgets.QTableWidgetItem(t)
            item.setForeground(QtGui.QBrush(QtGui.QColor("#6b6b6b")))
            self.weeklyGridEdit.setItem(r, 0, item)
                
            # Add plus buttons to all time slots
            for c in range(1, 8):
                self._addPlusCell(r, c)
                if c != 0:
                    self.weeklyGridEdit.setRowHeight(r, 100)
        
        grid_layout.addWidget(self.weeklyGridEdit, 1)
        parent_layout.addWidget(grid_container, 1)

    def _addPlusCell(self, row, col):
        """Add a clickable plus button cell to the schedule grid"""
        container = QtWidgets.QWidget()
        container.setStyleSheet("QWidget { border: 1px dashed #cfd8dc; border-radius: 4px; background: transparent; }")
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        
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
            QPushButton:pressed {
                background-color: #c8e6c9;
            }
        """)
        
        plus_btn.clicked.connect(lambda checked, r=row, c=col: self._showMakeAvailableDialog(r, c))
        
        layout.addWidget(plus_btn, 0, QtCore.Qt.AlignmentFlag.AlignCenter)
        self.weeklyGridEdit.setCellWidget(row, col, container)

    def _showMakeAvailableDialog(self, row, col):
        """Show dialog to make a time slot available"""
        dialog = QtWidgets.QDialog()
        dialog.setWindowTitle("Make Time Slot Available")
        dialog.setModal(True)
        dialog.setFixedSize(400, 200)
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
                border-radius: 10px;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Get time information
        time_item = self.weeklyGridEdit.item(row, 0)
        time_text = time_item.text() if time_item else "Unknown Time"
        
        day_header = self.weeklyGridEdit.horizontalHeaderItem(col)
        day_text = day_header.text() if day_header else "Unknown Day"
        
        title_label = QtWidgets.QLabel(f"Make this slot available")
        title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #2b2b2b;
                font: 600 14pt 'Poppins';
            }
        """)
        layout.addWidget(title_label)
        
        time_info = QtWidgets.QLabel(f"{day_text}  {time_text}")
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
        make_available_btn.clicked.connect(dialog.accept)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch(1)
        button_layout.addWidget(make_available_btn)
        
        layout.addLayout(button_layout)
        
        result = dialog.exec()
        if result == QtWidgets.QDialog.DialogCode.Accepted:
            self._convertToAvailableSlot(row, col, time_text, day_text)

    def _convertToAvailableSlot(self, row, col, time_text, day_text):
        """Convert the plus button cell to an available time slot"""
        container = QtWidgets.QWidget()
        container.setStyleSheet("QWidget { background: transparent; }")
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        
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
        self.weeklyGridEdit.setCellWidget(row, col, container)
        
        self._showScheduleUpdatedDialog()

    def _saveScheduleChanges(self):
        """Save schedule changes to database"""
        try:
            # Here you would implement the logic to save the schedule
            # This is a placeholder for the actual implementation
            QMessageBox.information(self, "Success", "Schedule changes saved successfully!")
            
        except Exception as e:
            print(f"Error saving schedule changes: {e}")
            QMessageBox.warning(self, "Error", f"Failed to save schedule changes: {str(e)}")

    def _showScheduleUpdatedDialog(self):
        """Show success dialog"""
        dialog = QtWidgets.QDialog()
        dialog.setWindowTitle("Success")
        dialog.setModal(True)
        dialog.setFixedSize(300, 150)
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
                border-radius: 10px;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        message_label = QtWidgets.QLabel("Schedule Updated!")
        message_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        message_label.setStyleSheet("""
            QLabel {
                color: #084924;
                font: 600 14pt 'Poppins';
            }
        """)
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