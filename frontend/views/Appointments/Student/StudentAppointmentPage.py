from datetime import datetime
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMessageBox, QFileDialog
from .appointment_crud import appointment_crud
from .StudentRequestPage import StudentRequestPage_ui
import logging
import os

class StudentAppointmentPage_ui(QWidget):
    go_to_AppointmentSchedulerPage = QtCore.pyqtSignal()
    appointment_created = QtCore.pyqtSignal()  # Signal to indicate new appointment
    refresh_data = QtCore.pyqtSignal()  # Signal to refresh data
    
    def __init__(self, username, roles, primary_role, token, parent=None):
        super().__init__(parent)
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        self.Appointment_crud = appointment_crud()
        self.rows = []
        self.student_request_page = None
        self.setFixedSize(1000, 550)
        self._setupAppointmentsPage()
        self.retranslateUi()
        self.load_appointments_data()  # Load initial data

    def set_student_request_page(self, request_page):
        """Set the student request page and connect signals"""
        self.student_request_page = request_page
        # Connect the refresh signal from request page
        self.student_request_page.backrefreshdata.connect(self.refresh_appointments_data)

    def load_appointments_data(self):
        """Load appointments data from JSON database for the current student"""
        self.rows.clear()
        try:
            # Get student ID based on username/email
            students = self.Appointment_crud.list_students()
            current_student_id = None
            current_student_name = None

            # Find the current student
            for student in students:
                if student.get('email') == self.username or student.get('name') == self.username:
                    current_student_id = student.get('id')
                    current_student_name = student.get('name', self.username)
                    break

            if current_student_id is None:
                print(f"Student not found for username: {self.username}")
                current_student_id = self.Appointment_crud.create_student(
                    name=self.username,
                    email=self.username,
                    course="Unknown Course",
                    year_level="Unknown Year"
                )
                current_student_name = self.username

            # Get appointments for this student
            appointments = self.Appointment_crud.get_student_appointments(current_student_id)
            self.rows = []

            for appointment in appointments:
                # Get schedule entry details
                schedule_entry_id = appointment.get('appointment_schedule_entry_id')
                schedule_entry = None
                if schedule_entry_id:
                    schedule_entry = self.Appointment_crud.entries_db.read_by_id(schedule_entry_id)

                # Get faculty details
                faculty_name = "Unknown Faculty"
                if schedule_entry:
                    block_id = schedule_entry.get('schedule_block_entry_id')
                    if block_id:
                        block = self.Appointment_crud.blocks_db.read_by_id(block_id)
                        if block:
                            faculty_id = block.get('faculty_id')
                            if faculty_id:
                                faculty = self.Appointment_crud.faculty_db.read_by_id(faculty_id)
                                if faculty:
                                    faculty_name = faculty.get('name', 'Unknown Faculty')

                # Format time slot
                time_slot = "Unknown Time"
                if schedule_entry:
                    start_time = schedule_entry.get('start_time', '')
                    end_time = schedule_entry.get('end_time', '')
                    day = schedule_entry.get('day_of_week', '')
                    time_slot = f"{day} {start_time} - {end_time}"

                # Format appointment date
                appointment_date = appointment.get('appointment_date', '')
                time_text = appointment_date
                if appointment_date and schedule_entry:
                    try:
                        dt = datetime.strptime(appointment_date, '%Y-%m-%d')
                        time_text = f"{dt.strftime('%Y-%m-%d')} {schedule_entry.get('start_time', '')}"
                    except ValueError:
                        pass

                # Create row data
                row_data = [
                    time_text,
                    faculty_name,
                    time_slot,
                    appointment.get('additional_details', 'No details'),
                    appointment.get('status', 'pending').upper(),
                    appointment.get('id'),  # Store appointment ID
                    appointment.get('student_id'),
                    schedule_entry_id,
                    appointment.get('address'),
                    appointment_date,
                    appointment.get('created_at'),
                    appointment.get('image_path'),
                ]
                self.rows.append(row_data)

            # Populate table with data
            self._populateAppointmentsTable()

        except Exception as e:
            print(f"Error loading appointments data: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load appointments: {str(e)}")
            # Fallback to sample data
            self._populateAppointmentsTable()

    def create_sample_data(self):
        """Create sample data for testing purposes"""
        try:
            # Create sample faculty if none exist
            faculty_list = self.Appointment_crud.list_faculty()
            if not faculty_list:
                self.Appointment_crud.create_faculty("Dr. Smith", "smith@university.edu", "Computer Science")
                self.Appointment_crud.create_faculty("Prof. Johnson", "johnson@university.edu", "Mathematics")
                self.Appointment_crud.create_faculty("Dr. Brown", "brown@university.edu", "Physics")

            # Create current student if not exists
            students = self.Appointment_crud.list_students()
            current_student_exists = any(student.get('email') == self.username for student in students)

            if not current_student_exists:
                self.Appointment_crud.create_student(
                    name="John Doe",
                    email=self.username,
                    course="Computer Science",
                    year_level="3rd Year"
                )

            # Create sample schedule blocks
            faculty1_id = 1
            time_slots = [
                {"start": "09:00", "end": "09:30", "day": "Monday"},
                {"start": "10:00", "end": "10:30", "day": "Tuesday"},
                {"start": "11:00", "end": "11:30", "day": "Wednesday"},
            ]
            self.Appointment_crud.plot_schedule(faculty1_id, time_slots)

            # Create sample appointments
            student_id = self.get_current_student_id()
            if student_id:
                entries = self.Appointment_crud.entries_db.read_all()
                if entries:
                    self.Appointment_crud.create_appointment(
                        student_id=student_id,
                        schedule_entry_id=entries[0]['id'],
                        details="Project consultation about final year project",
                        address="Room 305, CS Building",
                        date_str="2025-08-21",
                        image_path="Uploads/project_docs.png"
                    )
                    self.Appointment_crud.create_appointment(
                        student_id=student_id,
                        schedule_entry_id=entries[1]['id'],
                        details="Thesis proposal discussion and feedback",
                        address="Room 205, Math Building",
                        date_str="2025-08-22",
                        image_path=""
                    )
                    appointments = self.Appointment_crud.appointments_db.read_all()
                    if len(appointments) > 1:
                        self.Appointment_crud.update_appointment(appointments[1]['id'], {
                            "status": "approved",
                            "updated_at": str(datetime.now())
                        })
                    if len(appointments) > 2:
                        self.Appointment_crud.update_appointment(appointments[2]['id'], {
                            "status": "canceled",
                            "updated_at": str(datetime.now())
                        })

            # Reload data
            self.load_appointments_data()
            QMessageBox.information(self, "Success", "Sample data created successfully!")

        except Exception as e:
            print(f"Error creating sample data: {e}")
            QMessageBox.warning(self, "Error", f"Failed to create sample data: {str(e)}")

    def get_current_student_id(self):
        """Get the current student's ID"""
        students = self.Appointment_crud.list_students()
        for student in students:
            if student.get('email') == self.username or student.get('name') == self.username:
                return student.get('id')
        return None

    def cancel_appointment(self, appointment_data):
        """Cancel an appointment"""
        try:
            if appointment_data:
                result = self.Appointment_crud.update_appointment(appointment_data[2], {
                    "student_id": appointment_data[3],
                    "appointment_schedule_entry_id": appointment_data[4],
                    "additional_details": appointment_data[0],
                    "address": appointment_data[5],
                    "status": "canceled",
                    "appointment_date": appointment_data[6],
                    "created_at": appointment_data[7],
                    "updated_at": str(datetime.now()),
                    "image_path": appointment_data[8],
                })
                if result:
                    print(f"Result: {result}")
                    self.load_appointments_data()
                    QMessageBox.information(self, "Success", "Appointment canceled successfully!")
                    return True
                else:
                    QMessageBox.warning(self, "Error", "Failed to cancel appointment.")
                    return False
            return False
        except Exception as e:
            print(f"Error canceling appointment: {e}")
            QMessageBox.warning(self, "Error", f"Failed to cancel appointment: {str(e)}")
            return False

    def _setupAppointmentsPage(self):
        self.setObjectName("Appointments_2")
        appointments_layout = QtWidgets.QVBoxLayout(self)
        appointments_layout.setContentsMargins(10, 10, 10, 10)
        appointments_layout.setSpacing(15)

        # Header
        header_widget = QtWidgets.QWidget()
        header_layout = QtWidgets.QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        self.Academics_6 = QtWidgets.QLabel()
        font = QtGui.QFont()
        font.setFamily("Poppins")
        font.setPointSize(24)
        self.Academics_6.setFont(font)
        self.Academics_6.setStyleSheet("QLabel { color: #084924; }")
        self.Academics_6.setObjectName("Academics_6")

        header_layout.addWidget(self.Academics_6)
        header_layout.addStretch(1)

        # Browse Faculty Button
        self.browseFacultyButton = QtWidgets.QPushButton("Browse Faculty")
        self.browseFacultyButton.setFixedSize(200, 35)
        self.browseFacultyButton.setStyleSheet("""
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
        self.browseFacultyButton.clicked.connect(self._handleBrowseFaculty)
        header_layout.addWidget(self.browseFacultyButton)

        appointments_layout.addWidget(header_widget)

        # Main Content Widget
        self.widget_27 = QtWidgets.QWidget()
        self.widget_27.setMinimumHeight(100)
        self.widget_27.setStyleSheet("""
            QWidget#widget_27 { 
                background-color: #FFFFFF; 
                border-radius: 20px;
                padding: 20px;
            }
        """)

        widget_layout = QtWidgets.QVBoxLayout(self.widget_27)
        widget_layout.setContentsMargins(10, 10, 10, 10)
        widget_layout.setSpacing(15)

        # Table Widget
        self.tableWidget_8 = QtWidgets.QTableWidget()
        self.tableWidget_8.setAlternatingRowColors(True)
        self.tableWidget_8.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableWidget_8.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.tableWidget_8.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableWidget_8.setShowGrid(False)
        self.tableWidget_8.verticalHeader().setVisible(False)
        self.tableWidget_8.horizontalHeader().setVisible(True)
        self.tableWidget_8.setRowCount(0)
        self.tableWidget_8.setColumnCount(6)

        self.tableWidget_8.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding
        )
        self.tableWidget_8.setMinimumHeight(200)

        header = self.tableWidget_8.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        self.tableWidget_8.setColumnWidth(0, 200)  # Time
        self.tableWidget_8.setColumnWidth(1, 180)  # Faculty
        self.tableWidget_8.setColumnWidth(2, 180)  # Slot
        self.tableWidget_8.setColumnWidth(3, 250)  # Purpose
        self.tableWidget_8.setColumnWidth(4, 150)  # Status
        self.tableWidget_8.setColumnWidth(5, 150)  # Actions

        self.tableWidget_8.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.tableWidget_8.horizontalHeader().setStyleSheet(
            """
            QHeaderView::section {
                background-color: #0a5a2f;
                color: white;
                padding: 12px 8px;
                border: 0px;
                font: 600 11pt "Poppins";
                text-align: left;
            }
            """
        )
        self.tableWidget_8.setStyleSheet(
            """
            QTableWidget {
                background: white;
                gridline-color: transparent;
                border: none;
                font: 10pt "Poppins";
                selection-background-color: #e8f5e8;
            }
            QTableWidget::item { 
                padding: 10px 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            """
        )

        self.tableWidget_8.setWordWrap(True)
        self.tableWidget_8.verticalHeader().setDefaultSectionSize(60)

        headers = ["Time", "Faculty", "Slot", "Purpose", "Status", "Actions"]
        for i, header in enumerate(headers):
            item = QtWidgets.QTableWidgetItem()
            font = QtGui.QFont()
            font.setFamily("Poppins")
            font.setPointSize(11)
            item.setFont(font)
            item.setText(header)
            self.tableWidget_8.setHorizontalHeaderItem(i, item)

        widget_layout.addWidget(self.tableWidget_8, 1)
        appointments_layout.addWidget(self.widget_27, 1)

    def _handleBrowseFaculty(self):
        """Handle browse faculty button click - emit signal for main window"""
        self.go_to_AppointmentSchedulerPage.emit()

    def _makeStatusItem(self, text, color_hex):
        """Create a styled status table item"""
        item = QtWidgets.QTableWidgetItem(text)
        brush = QtGui.QBrush(QtGui.QColor(color_hex))
        item.setForeground(brush)
        item.setFont(QtGui.QFont("Poppins", 10, QtGui.QFont.Weight.DemiBold))
        return item

    def _makePurposeViewCell(self, purpose_text, appointment_data):
        """Create a clickable 'View' link for the purpose column"""
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        link = QtWidgets.QLabel("View", parent=container)

        def showPurposeDetails(event):
            self._showPurposeDetailsDialog(purpose_text, appointment_data)

        link.mousePressEvent = showPurposeDetails
        font = QtGui.QFont()
        font.setFamily("Poppins")
        font.setPointSize(10)
        link.setFont(font)
        link.setStyleSheet("QLabel { color: #2F80ED; text-decoration: underline; }")
        link.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        layout.addWidget(link, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        return container

    def _makeActionsCell(self, status, row_index):
        """Create action buttons for the Actions column"""
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        def make_btn(text, bg, enabled=True):
            btn = QtWidgets.QPushButton(text, parent=container)
            btn.setMinimumHeight(28)
            btn.setEnabled(enabled)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg};
                    color: white;
                    border-radius: 6px;
                    padding: 4px 10px;
                    font: 10pt 'Poppins';
                }}
                QPushButton:disabled {{
                    background-color: #bdbdbd;
                    color: #757575;
                }}
                QPushButton:hover {{
                    background-color: {bg if bg == '#bdbdbd' else '#d04545'};
                }}
            """)
            return btn

        # Cancel button for pending and approved appointments
        if status in ["PENDING", "APPROVED"]:
            cancel_btn = make_btn("Cancel", "#EB5757")
            cancel_btn.clicked.connect(lambda: self._openCancelDialog(row_index))
            layout.addWidget(cancel_btn)

        layout.addStretch(1)
        return container

    def _showPurposeDetailsDialog(self, purpose_text, appointment_data):
        """Show an enhanced dialog with purpose details and appointment info"""
        dialog = QtWidgets.QDialog()
        dialog.setWindowTitle("Appointment Details")
        dialog.setModal(True)
        dialog.setFixedSize(550, 600)
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
                border-radius: 12px;
            }
        """)
        
        # Main layout for the dialog
        main_layout = QtWidgets.QVBoxLayout(dialog)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
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
                width: 12px;
                margin: 0px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        
        # Create scroll content widget
        scroll_content = QtWidgets.QWidget()
        scroll_content.setStyleSheet("QWidget { background: white; }")
        
        # Main content layout for scroll area
        content_layout = QtWidgets.QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(24, 20, 24, 20)
        content_layout.setSpacing(20)
        
        # Header with icon and title
        header_widget = QtWidgets.QWidget()
        header_layout = QtWidgets.QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Icon
        icon_label = QtWidgets.QLabel()
        icon_label.setFixedSize(32, 32)
        icon_label.setStyleSheet("QLabel { background-color: #084924; border-radius: 8px; }")
        icon_label.setScaledContents(True)
        
        # Title
        title_label = QtWidgets.QLabel("Appointment Details")
        title_label.setStyleSheet("""
            QLabel {
                color: #084924;
                font: 600 20pt 'Poppins';
                background: transparent;
            }
        """)
        
        header_layout.addWidget(icon_label)
        header_layout.addSpacing(12)
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        
        content_layout.addWidget(header_widget)
        
        # Separator
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        separator.setStyleSheet("QFrame { background-color: #e0e0e0; }")
        separator.setFixedHeight(1)
        content_layout.addWidget(separator)
        
        # Appointment info section
        info_group = QtWidgets.QGroupBox("Appointment Information")
        info_group.setStyleSheet("""
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
        
        info_layout = QtWidgets.QFormLayout(info_group)
        info_layout.setVerticalSpacing(8)
        info_layout.setHorizontalSpacing(20)
        
        # Extract student info
        student_info = self.Appointment_crud.list_students()
        student_data = next((s for s in student_info if s.get('id') == appointment_data[6]), {})
        
        # Prepare appointment data
        appointment_info = [
            ("Student:", student_data.get('name', 'Unknown')),
            ("Date & Time:", appointment_data[0]),
            ("Duration:", "30 minutes"),  # Assuming default duration
            ("Status:", appointment_data[4]),
            ("Course:", student_data.get('course', 'Unknown')),
            ("Year Level:", student_data.get('year_level', 'Unknown')),
            ("Contact Email:", student_data.get('email', 'Unknown')),
            ("Address:", appointment_data[8] or "Not specified"),
            ("Created At:", appointment_data[10] or "Unknown"),
        ]
        
        for label, value in appointment_info:
            label_widget = QtWidgets.QLabel(label)
            label_widget.setStyleSheet("QLabel { font: 600 11pt 'Poppins'; color: #333; }")
            
            value_widget = QtWidgets.QLabel(str(value))
            value_widget.setStyleSheet("QLabel { font: 11pt 'Poppins'; color: #666; }")
            
            info_layout.addRow(label_widget, value_widget)
        
        content_layout.addWidget(info_group)
        
        # Image View Section
        image_group = QtWidgets.QGroupBox("Supporting Documents")
        image_group.setStyleSheet("""
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
        
        image_layout = QtWidgets.QVBoxLayout(image_group)
        
        # Image display area
        self.image_display = QtWidgets.QLabel()
        self.image_display.setFixedSize(400, 200)
        self.image_display.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        
        # Load image if available
        image_path = appointment_data[11]
        print(appointment_data)
        print(image_path)
        if image_path and os.path.exists(image_path):
            pixmap = QtGui.QPixmap(image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(400, 200, 
                                            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                                            QtCore.Qt.TransformationMode.SmoothTransformation)
                self.image_display.setPixmap(scaled_pixmap)
                self.image_display.setStyleSheet("""
                    QLabel {
                        background-color: #f8f9fa;
                        border: 2px solid #dee2e6;
                        border-radius: 8px;
                    }
                """)
            else:
                self.image_display.setText("Invalid image")
                self.image_display.setStyleSheet("""
                    QLabel {
                        background-color: #f8f9fa;
                        border: 2px dashed #dee2e6;
                        border-radius: 8px;
                        color: #6c757d;
                        font: 10pt 'Poppins';
                    }
                """)
        else:
            self.image_display.setText("No image available")
            self.image_display.setStyleSheet("""
                QLabel {
                    background-color: #f8f9fa;
                    border: 2px dashed #dee2e6;
                    border-radius: 8px;
                    color: #6c757d;
                    font: 10pt 'Poppins';
                }
            """)
        
        # Image controls
        image_controls_layout = QtWidgets.QHBoxLayout()
        
        upload_btn = QtWidgets.QPushButton("Upload Image")
        upload_btn.setFixedSize(120, 35)
        upload_btn.setStyleSheet("""
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
        upload_btn.clicked.connect(lambda: self._uploadImage(appointment_data[5]))
        
        view_btn = QtWidgets.QPushButton("View Full Size")
        view_btn.setFixedSize(120, 35)
        view_btn.setStyleSheet("""
            QPushButton {
                background-color: #2F80ED;
                color: white;
                border-radius: 6px;
                font: 600 10pt 'Poppins';
            }
            QPushButton:hover {
                background-color: #2a75e0;
            }
        """)
        view_btn.setEnabled(bool(image_path and os.path.exists(image_path)))
        view_btn.clicked.connect(lambda: self._viewImageFullscreen(image_path))
        
        image_controls_layout.addWidget(upload_btn)
        image_controls_layout.addWidget(view_btn)
        image_controls_layout.addStretch(1)
        
        image_layout.addWidget(self.image_display)
        image_layout.addLayout(image_controls_layout)
        
        content_layout.addWidget(image_group)
        
        # Purpose section
        purpose_group = QtWidgets.QGroupBox("Purpose Details")
        purpose_group.setStyleSheet("""
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
        
        purpose_layout = QtWidgets.QVBoxLayout(purpose_group)
        
        purpose_label = QtWidgets.QLabel(purpose_text)
        purpose_label.setWordWrap(True)
        purpose_label.setStyleSheet("""
            QLabel {
                color: #2b2b2b;
                font: 11pt 'Poppins';
                background: transparent;
                line-height: 1.5;
            }
        """)
        purpose_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)
        
        purpose_scroll_area = QtWidgets.QScrollArea()
        purpose_scroll_area.setWidgetResizable(True)
        purpose_scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        purpose_scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        purpose_scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #f0f0f0;
                border-radius: 6px;
                background: #fafafa;
            }
        """)
        purpose_scroll_area.setFixedHeight(150)
        
        purpose_scroll_content = QtWidgets.QWidget()
        purpose_scroll_layout = QtWidgets.QVBoxLayout(purpose_scroll_content)
        purpose_scroll_layout.setContentsMargins(12, 12, 12, 12)
        purpose_scroll_layout.addWidget(purpose_label)
        
        purpose_scroll_area.setWidget(purpose_scroll_content)
        purpose_layout.addWidget(purpose_scroll_area)
        
        content_layout.addWidget(purpose_group)
        
        # Add spacing before button
        content_layout.addStretch(1)
        
        # Button row
        button_widget = QtWidgets.QWidget()
        button_widget.setStyleSheet("QWidget { background: white; }")
        button_layout = QtWidgets.QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        close_button = QtWidgets.QPushButton("Close")
        close_button.setFixedSize(120, 40)
        close_button.setStyleSheet("""
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
        close_button.clicked.connect(dialog.accept)
        
        button_layout.addStretch(1)
        button_layout.addWidget(close_button)
        
        content_layout.addWidget(button_widget)
        
        # Set the scroll content
        scroll_area.setWidget(scroll_content)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)
        
        dialog.exec()

    def _uploadImage(self, appointment_id):
        """Handle image upload for an appointment"""
        try:
            file_dialog = QFileDialog(self)
            file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp)")
            file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
            if file_dialog.exec():
                selected_files = file_dialog.selectedFiles()
                if selected_files:
                    image_path = selected_files[0]
                    # Update appointment with new image path
                    self.Appointment_crud.update_appointment(appointment_id, {
                        "image_path": image_path,
                        "updated_at": str(datetime.now())
                    })
                    self.load_appointments_data()
                    QMessageBox.information(self, "Success", "Image uploaded successfully!")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to upload image: {str(e)}")

    def _viewImageFullscreen(self, image_path):
        """Show image in fullscreen dialog"""
        try:
            if not image_path or not os.path.exists(image_path):
                QtWidgets.QMessageBox.warning(self, "Error", "No valid image available")
                return
                
            fullscreen_dialog = QtWidgets.QDialog(self)
            fullscreen_dialog.setWindowTitle("Image View")
            fullscreen_dialog.setModal(True)
            fullscreen_dialog.resize(800, 600)
            fullscreen_dialog.setStyleSheet("QDialog { background-color: black; }")
            
            layout = QtWidgets.QVBoxLayout(fullscreen_dialog)
            layout.setContentsMargins(0, 0, 0, 0)
            
            # Image label
            pixmap = QtGui.QPixmap(image_path)
            if not pixmap.isNull():
                # Scale to fit screen while maintaining aspect ratio
                screen_geometry = QtWidgets.QApplication.primaryScreen().availableGeometry()
                max_width = screen_geometry.width() - 100
                max_height = screen_geometry.height() - 100
                
                scaled_pixmap = pixmap.scaled(max_width, max_height, 
                                            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                                            QtCore.Qt.TransformationMode.SmoothTransformation)
                
                image_label = QtWidgets.QLabel()
                image_label.setPixmap(scaled_pixmap)
                image_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                image_label.setStyleSheet("QLabel { background-color: black; }")
                
                layout.addWidget(image_label)
            
            # Close button
            close_button = QtWidgets.QPushButton("Close")
            close_button.setFixedSize(100, 30)
            close_button.setStyleSheet("""
                QPushButton {
                    background-color: #d32f2f;
                    color: white;
                    border-radius: 4px;
                    font: 600 10pt 'Poppins';
                }
                QPushButton:hover {
                    background-color: #b71c1c;
                }
            """)
            close_button.clicked.connect(fullscreen_dialog.accept)
            
            button_layout = QtWidgets.QHBoxLayout()
            button_layout.addStretch(1)
            button_layout.addWidget(close_button)
            button_layout.addStretch(1)
            layout.addLayout(button_layout)
            
            fullscreen_dialog.exec()
            
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Could not load image: {str(e)}")

    def _openCancelDialog(self, row_index):
        """Open confirmation dialog for canceling an appointment"""
        if 0 <= row_index < len(self.rows):
            appointment_data = self.rows[row_index][3:]
            dlg = QtWidgets.QDialog(self)
            dlg.setWindowTitle("Cancel Appointment")
            dlg.setModal(True)
            dlg.setFixedSize(400, 200)

            layout = QtWidgets.QVBoxLayout(dlg)
            layout.setContentsMargins(24, 24, 24, 24)
            layout.setSpacing(20)

            title = QtWidgets.QLabel("Are you sure you want to cancel this appointment?")
            title.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
            title.setStyleSheet("QLabel { color: #2b2b2b; font: 600 12pt 'Poppins'; }")
            layout.addWidget(title)

            layout.addStretch(1)

            btn_layout = QtWidgets.QHBoxLayout()
            btn_cancel = QtWidgets.QPushButton("No, Keep")
            btn_confirm = QtWidgets.QPushButton("Yes, Cancel")
            btn_cancel.setStyleSheet("""
                QPushButton {
                    background: #e0e0e0;
                    border-radius: 6px;
                    padding: 8px 20px;
                    font: 10pt 'Poppins';
                    color: #2b2b2b;
                }
                QPushButton:hover {
                    background: #d0d0d0;
                }
            """)
            btn_confirm.setStyleSheet("""
                QPushButton {
                    background: #EB5757;
                    border-radius: 6px;
                    padding: 8px 20px;
                    font: 10pt 'Poppins';
                    color: white;
                }
                QPushButton:hover {
                    background: #d04545;
                }
            """)
            btn_cancel.clicked.connect(dlg.reject)
            btn_confirm.clicked.connect(lambda: self._handleCancelAppointment(dlg, appointment_data))
            btn_layout.addWidget(btn_cancel)
            btn_layout.addStretch(1)
            btn_layout.addWidget(btn_confirm)
            layout.addLayout(btn_layout)

            dlg.exec()

    def _handleCancelAppointment(self, dialog, appointment_data):
        """Handle appointment cancellation"""
        if self.cancel_appointment(appointment_data):
            dialog.accept()
        else:
            dialog.reject()

    def _populateAppointmentsTable(self):
        """Update the table with appointment data"""
        status_colors = {
            "PENDING": "#F2994A",
            "RESCHEDULED": "#2F80ED",
            "CANCELED": "#EB5757",
            "APPROVED": "#219653",
            "DENIED": "#EB5757",
            "COMPLETED": "#219653"
        }

        self.tableWidget_8.setRowCount(len(self.rows))
        for r, row_data in enumerate(self.rows):
            time_text, faculty, slot, purpose, status, appointment_id, student_id, schedule_entry, address, appointment_date, created_at, image_path = row_data
            self.tableWidget_8.setItem(r, 0, QtWidgets.QTableWidgetItem(time_text))
            self.tableWidget_8.setItem(r, 1, QtWidgets.QTableWidgetItem(faculty))
            self.tableWidget_8.setItem(r, 2, QtWidgets.QTableWidgetItem(slot))
            self.tableWidget_8.setCellWidget(r, 3, self._makePurposeViewCell(purpose, row_data))
            self.tableWidget_8.setItem(r, 4, self._makeStatusItem(status, status_colors.get(status, "#333333")))
            self.tableWidget_8.setCellWidget(r, 5, self._makeActionsCell(status, r))
            self.tableWidget_8.setRowHeight(r, 60)

    def retranslateUi(self):
        """Set UI text"""
        self.Academics_6.setText("My Appointments")
        self.browseFacultyButton.setText("Browse Faculty")
        headers = ["Time", "Faculty", "Slot", "Purpose", "Status", "Actions"]
        for i, header in enumerate(headers):
            item = self.tableWidget_8.horizontalHeaderItem(i)
            if item is not None:
                item.setText(header)

    def refresh_appointments_data(self):
        """Refresh the appointments data - called when returning from request page"""
        print("Refreshing appointments data...")
        self.load_appointments_data()
        QMessageBox.information(self, "Success", "Appointments data refreshed!")

    def showEvent(self, event):
        """Override showEvent to refresh data when the page is shown"""
        super().showEvent(event)
        self.load_appointments_data()

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    student_appointment = StudentAppointmentPage_ui(
        "john.doe@student.edu",
        ["student"],
        "student",
        "sample_token"
    )
    student_appointment.show()
    sys.exit(app.exec())