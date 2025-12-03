# StudentAppointmentPage_ui.py
from datetime import datetime
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMessageBox, QFileDialog
from ..api_client import APIClient
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
        self.appointment_crud = APIClient(token=token)
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
        if hasattr(self.student_request_page, 'backrefreshdata'):
            self.student_request_page.backrefreshdata.connect(self.refresh_appointments_data)

    def load_appointments_data(self):
        """Load appointments data from API for the current student"""
        self.rows.clear()
        try:
            print(f"DEBUG: Loading appointments for student with token: {self.token[:20]}...")
            
            appointments = self.appointment_crud.get_student_appointments()
            print(f"DEBUG: Retrieved appointments: {appointments}")
            
            if not appointments:
                print("DEBUG: No appointments found")
                # Show message in UI
                self._showNoAppointmentsMessage()
                return
            
            for appointment in appointments:
                print(f"DEBUG: Processing appointment: {appointment}")
                
                # Extract basic appointment info
                appointment_id = appointment.get('id')
                student_id = appointment.get('student')
                faculty_id = appointment.get('faculty')
                
                # Get faculty name
                faculty_name = "Unknown Faculty"
                if isinstance(faculty_id, dict):
                    # If faculty is nested object
                    faculty_user = faculty_id.get('user', {})
                    faculty_name = f"{faculty_user.get('first_name', '')} {faculty_user.get('last_name', '')}".strip()
                    if not faculty_name:
                        faculty_name = faculty_user.get('username', 'Unknown Faculty')
                elif faculty_id:
                    # If faculty is just ID, we could fetch details but for now use Unknown
                    faculty_name = f"Faculty ID: {faculty_id}"
                
                # Format time
                start_at = appointment.get('start_at', '')
                end_at = appointment.get('end_at', '')
                
                # Parse datetime strings
                time_display = ""
                date_display = ""
                
                if start_at:
                    try:
                        # Handle ISO format with timezone
                        start_dt_str = start_at.replace('Z', '') if 'Z' in start_at else start_at
                        end_dt_str = end_at.replace('Z', '') if end_at and 'Z' in end_at else end_at
                        
                        start_dt = datetime.fromisoformat(start_dt_str)
                        if end_dt_str:
                            end_dt = datetime.fromisoformat(end_dt_str)
                            time_display = f"{start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}"
                        else:
                            time_display = start_dt.strftime('%I:%M %p')
                        
                        date_display = start_dt.strftime('%Y-%m-%d')
                    except ValueError as e:
                        print(f"DEBUG: Error parsing datetime: {e}")
                        time_display = f"{start_at} - {end_at}" if end_at else start_at
                        date_display = "Unknown Date"
                else:
                    time_display = "Time not specified"
                    date_display = "Date not specified"
                
                # Get status
                status = appointment.get('status', 'pending').upper()
                
                # Get purpose/details
                purpose = appointment.get('additional_details', 'No details provided')
                
                # Get address/location
                address = appointment.get('address', 'Not specified')
                
                # Get created at
                created_at = appointment.get('created_at', '')
                if created_at:
                    try:
                        created_dt_str = created_at.replace('Z', '') if 'Z' in created_at else created_at
                        created_dt = datetime.fromisoformat(created_dt_str)
                        created_at_display = created_dt.strftime('%Y-%m-%d %I:%M %p')
                    except:
                        created_at_display = created_at
                else:
                    created_at_display = "Unknown"
                
                # Create row data
                row_data = [
                    f"{date_display} {time_display}",  # Time
                    faculty_name,  # Faculty
                    time_display,  # Time slot
                    purpose,  # Purpose/details
                    status,  # Status
                    appointment_id,  # Appointment ID (hidden)
                    student_id,  # Student ID (hidden)
                    faculty_id,  # Faculty ID (hidden)
                    address,  # Address (hidden)
                    date_display,  # Date only (hidden)
                    created_at_display,  # Created at (hidden)
                    appointment.get('image_path', ''),  # Image path (hidden)
                ]
                self.rows.append(row_data)
            
            print(f"DEBUG: Processed {len(self.rows)} appointments")
            
            # Populate table with data
            self._populateAppointmentsTable()

        except Exception as e:
            print(f"ERROR: Error loading appointments data: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "Error", f"Failed to load appointments: {str(e)}")
            # Show empty table
            self._populateAppointmentsTable()

    def _showNoAppointmentsMessage(self):
        """Show message when no appointments are found"""
        # Clear existing table
        self.tableWidget_8.setRowCount(0)
        
        # Add a single row with message
        self.tableWidget_8.setRowCount(1)
        message_item = QtWidgets.QTableWidgetItem("No appointments found. Click 'Browse Faculty' to schedule one.")
        message_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.tableWidget_8.setSpan(0, 0, 1, 6)  # Span across all columns
        self.tableWidget_8.setItem(0, 0, message_item)
        
        # Style the message
        font = QtGui.QFont("Poppins", 12)
        message_item.setFont(font)
        message_item.setForeground(QtGui.QColor("#666666"))

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
        
        # Prepare appointment data
        appointment_info = [
            ("Date & Time:", appointment_data[0]),
            ("Faculty:", appointment_data[1]),
            ("Time Slot:", appointment_data[2]),
            ("Status:", appointment_data[4]),
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
                    result = self.appointment_crud.update_appointment(appointment_id, {
                        "image_path": image_path,
                    })
                    if result:
                        self.load_appointments_data()
                        QMessageBox.information(self, "Success", "Image uploaded successfully!")
                    else:
                        QMessageBox.warning(self, "Error", "Failed to upload image")
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
            appointment_data = self.rows[row_index]
            appointment_id = appointment_data[5]  # Get appointment ID
            
            dlg = QtWidgets.QDialog(self)
            dlg.setWindowTitle("Cancel Appointment")
            dlg.setModal(True)
            dlg.setFixedSize(400, 200)

            layout = QtWidgets.QVBoxLayout(dlg)
            layout.setContentsMargins(24, 24, 24, 24)
            layout.setSpacing(20)

            title = QtWidgets.QLabel("Are you sure you want to cancel this appointment?")
            title.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
            title.setWordWrap(True)
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
            btn_confirm.clicked.connect(lambda: self._handleCancelAppointment(dlg, appointment_id))
            btn_layout.addWidget(btn_cancel)
            btn_layout.addStretch(1)
            btn_layout.addWidget(btn_confirm)
            layout.addLayout(btn_layout)

            dlg.exec()

    def _handleCancelAppointment(self, dialog, appointment_id):
        """Handle appointment cancellation"""
        try:
            result = self.appointment_crud.update_appointment(appointment_id, {
                "status": "CANCELED"
            })
            if result:
                QMessageBox.information(self, "Success", "Appointment canceled successfully!")
                self.load_appointments_data()
                dialog.accept()
            else:
                QMessageBox.warning(self, "Error", "Failed to cancel appointment.")
                dialog.reject()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to cancel appointment: {str(e)}")
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

    def showEvent(self, event):
        """Override showEvent to refresh data when the page is shown"""
        super().showEvent(event)
        self.load_appointments_data()