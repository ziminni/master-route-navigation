import os
from datetime import datetime
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QHBoxLayout, 
                            QMessageBox, QDialog, QScrollArea, QPushButton,
                            QTableWidget, QTableWidgetItem, QLineEdit, 
                            QDateEdit, QFrame, QFormLayout, QScrollArea,
                            QAbstractItemView, QHeaderView, QSizePolicy,
                            QApplication)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QFont, QBrush, QColor, QCursor, QPixmap
import requests
import json
import logging
from ..api_client import APIClient


# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class AdminAppointmentPage_ui(QWidget):
    def __init__(self, username, roles, primary_role, token, parent=None):
        super().__init__(parent)
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        
        # Initialize API client with debug output
        print(f"DEBUG: Initializing AdminAppointmentPage for user: {username}")
        print(f"DEBUG: Token: {token[:20]}...")
        
        self.appointment_crud = APIClient(token=token)
        
        # Test API connection
        self.test_api_connection()
        
        self.rows = []  # Store appointment data
        self.all_appointments = []  # Store all appointments for filtering
        self._setupAppointmentsPage()
        self._populateAppointmentsTable()  # Load initial data
        self.setFixedSize(1000, 550)
        # Set expanding size policy for the entire page
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, 
            QtWidgets.QSizePolicy.Policy.Expanding
        )

    def get_faculty_name(self, faculty_id):
        faculties = self.appointment_crud.get_faculties()
        print(f"Faculties list: {faculties}")
        for faculty in faculties:
            print(f"{faculty}")
            print("Hello Lord!")
            if int(faculty["id"]) == int(faculty_id):
                return faculty['full_name']
            
    def get_student_name(self, student_id):
        students = self.appointment_crud.get_students()
        print(f"Students list: {students}")
        for student in students:
            print(f"{student}")
            print("Hello Lord!")
            if int(student["id"]) == int(student_id):
                return student['full_name']


    def test_api_connection(self):
        """Test API connection and authentication"""
        try:
            print(f"DEBUG: Testing API connection for admin...")
            print(f"DEBUG: Base URL: {self.appointment_crud.base_url if hasattr(self.appointment_crud, 'base_url') else 'Not set'}")
            
            # Test getting all appointments
            print(f"DEBUG: Testing get_all_appointments()...")
            appointments = self.appointment_crud.get_all_appointments()
            print(f"DEBUG: get_all_appointments() response type: {type(appointments)}")
            print(f"DEBUG: get_all_appointments() response sample: {appointments[:2] if appointments and isinstance(appointments, list) and len(appointments) > 0 else appointments}")
            
            # Test getting faculties
            print(f"DEBUG: Testing get_faculties()...")
            faculties = self.appointment_crud.get_faculties()
            print(f"DEBUG: get_faculties() response type: {type(faculties)}")
            print(f"DEBUG: get_faculties() response sample: {faculties[:2] if faculties and isinstance(faculties, list) and len(faculties) > 0 else faculties}")
            
            if appointments is None:
                print("ERROR: get_all_appointments() returned None - likely authentication or connection issue")
            elif isinstance(appointments, list):
                print(f"DEBUG: Successfully retrieved {len(appointments)} appointments")
            else:
                print(f"DEBUG: Unexpected response type for appointments: {type(appointments)}")
                
            if faculties is None:
                print("ERROR: get_faculties() returned None - likely authentication or connection issue")
            elif isinstance(faculties, list):
                print(f"DEBUG: Successfully retrieved {len(faculties)} faculty profiles")
            else:
                print(f"DEBUG: Unexpected response type for faculties: {type(faculties)}")
                
        except Exception as e:
            print(f"ERROR: Failed to test API connection: {e}")
            import traceback
            traceback.print_exc()

    def _setupAppointmentsPage(self):
        self.setObjectName("Appointments_2")
        appointments_layout = QtWidgets.QVBoxLayout(self)
        appointments_layout.setContentsMargins(10, 10, 10, 10)
        appointments_layout.setSpacing(15)
        appointments_layout.setObjectName("appointments_layout")
        
        # Header section
        header_widget = QtWidgets.QWidget()
        header_layout = QtWidgets.QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)
        
        # Page title
        self.Academics_6 = QtWidgets.QLabel("Appointments")
        font = QtGui.QFont()
        font.setFamily("Poppins")
        font.setPointSize(24)
        self.Academics_6.setFont(font)
        self.Academics_6.setStyleSheet("QLabel { color: #084924; }")
        self.Academics_6.setObjectName("Academics_6")
        
        header_layout.addWidget(self.Academics_6)
        header_layout.addStretch(1)
        
        appointments_layout.addWidget(header_widget)
        
        # Content widget
        self.widget_27 = QtWidgets.QWidget()
        self.widget_27.setMinimumHeight(100)
        self.widget_27.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, 
            QtWidgets.QSizePolicy.Policy.Expanding
        )
        self.widget_27.setStyleSheet("""
            QWidget#widget_27 { 
                background-color: #FFFFFF; 
                border-radius: 20px;
                padding: 20px;
            }
        """)
        self.widget_27.setObjectName("widget_27")
        
        widget_layout = QtWidgets.QVBoxLayout(self.widget_27)
        widget_layout.setContentsMargins(10, 10, 10, 10)
        widget_layout.setSpacing(15)
        widget_layout.setObjectName("widget_layout")
        
        # Combined Filter and Search Section
        filter_search_widget = QtWidgets.QWidget()
        filter_search_widget.setFixedHeight(80)
        filter_search_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, 
            QtWidgets.QSizePolicy.Policy.Fixed
        )
        
        filter_search_layout = QtWidgets.QHBoxLayout(filter_search_widget)
        filter_search_layout.setContentsMargins(0, 10, 0, 10)
        filter_search_layout.setSpacing(20)
        
        # Date Filter Section
        filter_widget = QtWidgets.QWidget()
        filter_layout = QtWidgets.QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(20)
        
        from_widget = QtWidgets.QWidget()
        from_layout = QtWidgets.QVBoxLayout(from_widget)
        from_layout.setContentsMargins(0, 0, 0, 0)
        from_layout.setSpacing(5)
        
        from_label = QtWidgets.QLabel("From")
        from_label.setStyleSheet("QLabel { color: #333333; font: 600 12pt 'Poppins'; }")
        from_layout.addWidget(from_label)
        
        self.from_date_edit = QtWidgets.QDateEdit()
        self.from_date_edit.setCalendarPopup(True)
        self.from_date_edit.setDate(QtCore.QDate.currentDate().addDays(-30))
        self.from_date_edit.setStyleSheet("""
            QDateEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 8px 12px;
                font: 11pt 'Poppins';
                min-width: 120px;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 20px;
                border-left: 1px solid #dee2e6;
            }
        """)
        from_layout.addWidget(self.from_date_edit)
        
        to_widget = QtWidgets.QWidget()
        to_layout = QtWidgets.QVBoxLayout(to_widget)
        to_layout.setContentsMargins(0, 0, 0, 0)
        to_layout.setSpacing(5)
        
        to_label = QtWidgets.QLabel("To")
        to_label.setStyleSheet("QLabel { color: #333333; font: 600 12pt 'Poppins'; }")
        to_layout.addWidget(to_label)
        
        self.to_date_edit = QtWidgets.QDateEdit()
        self.to_date_edit.setCalendarPopup(True)
        self.to_date_edit.setDate(QtCore.QDate.currentDate())
        self.to_date_edit.setStyleSheet("""
            QDateEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 8px 12px;
                font: 11pt 'Poppins';
                min-width: 120px;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 20px;
                border-left: 1px solid #dee2e6;
            }
        """)
        to_layout.addWidget(self.to_date_edit)
        
        self.filter_button = QtWidgets.QPushButton("Apply Filter")
        self.filter_button.setFixedSize(120, 40)
        self.filter_button.setStyleSheet("""
            QPushButton {
                background-color: #084924;
                color: white;
                border-radius: 8px;
                font: 600 11pt 'Poppins';
                margin-top: 18px;
            }
            QPushButton:hover {
                background-color: #0a5a2f;
            }
        """)
        self.filter_button.clicked.connect(self.apply_date_filter)
        
        self.clear_filter_button = QtWidgets.QPushButton("Clear")
        self.clear_filter_button.setFixedSize(80, 40)
        self.clear_filter_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border-radius: 8px;
                font: 600 11pt 'Poppins';
                margin-top: 18px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.clear_filter_button.clicked.connect(self.clear_filters)
        
        filter_layout.addWidget(from_widget)
        filter_layout.addWidget(to_widget)
        filter_layout.addWidget(self.filter_button)
        filter_layout.addWidget(self.clear_filter_button)
        
        search_widget = QtWidgets.QWidget()
        search_layout = QtWidgets.QHBoxLayout(search_widget)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(15)
        
        search_label = QtWidgets.QLabel("Search:")
        search_label.setStyleSheet("QLabel { color: #333333; font: 600 12pt 'Poppins'; margin-left: 5px; }")
        search_layout.addWidget(search_label)
        
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("Search appointments...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px 15px;
                font: 11pt 'Poppins';
                min-width: 300px;
            }
            QLineEdit:focus {
                border-color: #084924;
                background-color: #ffffff;
            }
        """)
        self.search_input.textChanged.connect(self.apply_search_filter)
        search_layout.addWidget(self.search_input)
        
        filter_search_layout.addWidget(filter_widget)
        filter_search_layout.addStretch(1)
        filter_search_layout.addWidget(search_widget)
        
        widget_layout.addWidget(filter_search_widget)
        
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        separator.setStyleSheet("QFrame { background-color: #e0e0e0; margin: 5px 0; }")
        separator.setFixedHeight(1)
        widget_layout.addWidget(separator)
        
        # Appointments table
        self.tableWidget_8 = QtWidgets.QTableWidget()
        self.tableWidget_8.setAlternatingRowColors(True)
        self.tableWidget_8.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableWidget_8.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.tableWidget_8.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableWidget_8.setShowGrid(False)
        self.tableWidget_8.verticalHeader().setVisible(False)
        self.tableWidget_8.horizontalHeader().setVisible(True)
        self.tableWidget_8.setRowCount(0)
        self.tableWidget_8.setColumnCount(7)  # Added Actions column
        
        self.tableWidget_8.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, 
            QtWidgets.QSizePolicy.Policy.Expanding
        )
        self.tableWidget_8.setMinimumHeight(100)
        
        header = self.tableWidget_8.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
       
        self.tableWidget_8.setColumnWidth(0, 180)
        self.tableWidget_8.setColumnWidth(1, 150)
        self.tableWidget_8.setColumnWidth(2, 150)
        self.tableWidget_8.setColumnWidth(4, 120)
        self.tableWidget_8.setColumnWidth(5, 120)
        self.tableWidget_8.setColumnWidth(6, 100)
        
        self.tableWidget_8.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.tableWidget_8.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #0a5a2f;
                color: white;
                padding: 12px 8px;
                border: 0px;
                font: 600 11pt "Poppins";
                text-align: left;
            }
        """)
        self.tableWidget_8.setStyleSheet("""
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
        """)
        
        self.tableWidget_8.setWordWrap(True)
        self.tableWidget_8.verticalHeader().setDefaultSectionSize(60)
        
        headers = ["Date & Time", "Faculty", "Student", "Purpose", "Status", "Created", "Actions"]
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

    def apply_search_filter(self, search_text):
        """Apply search filter to the appointments table"""
        if not search_text.strip():
            self._updateTableWithData(self.all_appointments)
            return
        
        search_text_lower = search_text.lower().strip()
        filtered_appointments = []
        
        for appointment in self.all_appointments:
            if (search_text_lower in appointment['faculty_name'].lower() or 
                search_text_lower in appointment['student_name'].lower() or 
                search_text_lower in appointment['status'].lower() or
                search_text_lower in appointment['purpose'].lower()):
                filtered_appointments.append(appointment)
        
        self._updateTableWithData(filtered_appointments)
        if search_text.strip():
            self._showFilterStatus(len(filtered_appointments), len(self.all_appointments), f"Search: '{search_text}'")

    def apply_date_filter(self):
        """Apply date filter to the appointments table"""
        from_date = self.from_date_edit.date()
        to_date = self.to_date_edit.date()
        
        if from_date > to_date:
            QtWidgets.QMessageBox.warning(self, "Invalid Date Range", 
                                        "From date cannot be after To date.")
            return
        
        search_text = self.search_input.text().strip()
        date_filtered_appointments = []
        
        for appointment in self.all_appointments:
            appointment_date = QDate.fromString(appointment['date_time'].split('T')[0], "yyyy-MM-dd")
            if from_date <= appointment_date <= to_date:
                date_filtered_appointments.append(appointment)
        
        if search_text:
            search_text_lower = search_text.lower()
            final_filtered_appointments = []
            for appointment in date_filtered_appointments:
                if (search_text_lower in appointment['faculty_name'].lower() or 
                    search_text_lower in appointment['student_name'].lower() or 
                    search_text_lower in appointment['status'].lower() or
                    search_text_lower in appointment['purpose'].lower()):
                    final_filtered_appointments.append(appointment)
        else:
            final_filtered_appointments = date_filtered_appointments
        
        self._updateTableWithData(final_filtered_appointments)
        
        filter_info = f"Date: {from_date.toString('MM/dd/yyyy')} - {to_date.toString('MM/dd/yyyy')}"
        if search_text:
            filter_info += f" | Search: '{search_text}'"
        self._showFilterStatus(len(final_filtered_appointments), len(self.all_appointments), filter_info)

    def clear_filters(self):
        """Clear all filters and show all appointments"""
        self.search_input.clear()
        self.from_date_edit.setDate(QtCore.QDate.currentDate().addDays(-30))
        self.to_date_edit.setDate(QtCore.QDate.currentDate())
        self._updateTableWithData(self.all_appointments)
        self._showFilterStatus(len(self.all_appointments), len(self.all_appointments), "All filters cleared")

    def _showFilterStatus(self, showing_count, total_count, filter_info=""):
        """Show filter status message"""
        if showing_count == total_count:
            status_message = f"Showing all {total_count} appointments"
        else:
            status_message = f"Showing {showing_count} of {total_count} appointments"
        
        if filter_info:
            status_message += f" | {filter_info}"
        print(f"DEBUG: {status_message}")

    def _updateTableWithData(self, appointments_data):
        """Update table with provided appointments data"""
        status_colors = {
            "PENDING": "#F2994A",
            "CANCELED": "#EB5757",
            "APPROVED": "#219653",
            "DENIED": "#EB5757",
            "COMPLETED": "#2F80ED"
        }
        
        self.tableWidget_8.setRowCount(len(appointments_data))
        for r, appointment in enumerate(appointments_data):
            # Date & Time
            date_time = appointment['date_time']
            if 'T' in date_time:
                date_part, time_part = date_time.split('T')
                time_display = time_part[:5]  # Get HH:MM
                date_time_display = f"{date_part}\n{time_display}"
            else:
                date_time_display = date_time
            
            self.tableWidget_8.setItem(r, 0, QtWidgets.QTableWidgetItem(date_time_display))
            
            # Faculty
            self.tableWidget_8.setItem(r, 1, QtWidgets.QTableWidgetItem(appointment['faculty_name']))
            
            # Student
            self.tableWidget_8.setItem(r, 2, QtWidgets.QTableWidgetItem(appointment['student_name']))
            
            # Purpose (with View link)
            self.tableWidget_8.setCellWidget(r, 3, self._makePurposeViewCell(appointment['id'], appointment['purpose']))
            
            # Status
            self.tableWidget_8.setItem(r, 4, self._makeStatusItem(appointment['status'], status_colors.get(appointment['status'], "#333333")))
            
            # Created date
            created_date = appointment['created_at'].split('T')[0] if 'T' in appointment['created_at'] else appointment['created_at']
            self.tableWidget_8.setItem(r, 5, QtWidgets.QTableWidgetItem(created_date))
            
            # Actions
            self.tableWidget_8.setCellWidget(r, 6, self._makeActionsCell(appointment['id'], appointment['status']))
            
            self.tableWidget_8.setRowHeight(r, 60)

    def _populateAppointmentsTable(self):
        """Populate the table with appointment data from API"""
        try:
            print("DEBUG: Starting to populate admin appointments table...")
            
            # Get appointments - using the correct method name
            appointments = self.appointment_crud.get_all_appointments()
            print(f"DEBUG: Appointments response type: {type(appointments)}")
            print(f"DEBUG: Appointments response: {appointments}")
            
            if appointments is None:
                print("ERROR: get_all_appointments() returned None")
                QtWidgets.QMessageBox.warning(self, "Connection Error", 
                                          "Could not connect to the server. Please check your connection.")
                self.all_appointments = []
                self.rows = []
                return
                
            if not isinstance(appointments, list):
                print(f"ERROR: get_all_appointments() returned non-list: {type(appointments)}")
                QtWidgets.QMessageBox.warning(self, "Data Error", 
                                          "Invalid data received from server.")
                self.all_appointments = []
                self.rows = []
                return
            
            # Get faculty profiles - using the correct method name
            faculty_profiles = self.appointment_crud.get_faculties()
            print(f"DEBUG: Faculty profiles response type: {type(faculty_profiles)}")
            print(f"DEBUG: Faculty profiles response: {faculty_profiles}")
            
            if faculty_profiles is None:
                print("WARNING: get_faculties() returned None")
                faculty_profiles = []
            elif not isinstance(faculty_profiles, list):
                print(f"WARNING: get_faculties() returned non-list: {type(faculty_profiles)}")
                faculty_profiles = []
            
            # Create faculty mapping
            faculty_map = {}
            for faculty in faculty_profiles:
                try:
                    faculty_id = faculty.get('id')
                    if faculty_id:
                        # Try different field names for user information
                        user_info = faculty.get('user', {})
                        if isinstance(user_info, dict):
                            first_name = user_info.get('first_name', '')
                            last_name = user_info.get('last_name', '')
                            faculty_name = f"{first_name} {last_name}".strip()
                            if not faculty_name:
                                faculty_name = user_info.get('username', 'Unknown')
                        else:
                            faculty_name = self.get_faculty_name(faculty_id)
                            faculty_name = faculty.get('name', f"Faculty {faculty_id}")
                        
                        faculty_map[faculty_id] = faculty_name
                        print(f"DEBUG: Mapped faculty ID {faculty_id} to name: {faculty_name}")
                except Exception as e:
                    print(f"DEBUG: Error processing faculty profile: {e}")
                    continue
            
            print(f"DEBUG: Faculty map created with {len(faculty_map)} entries")
            self.get_faculty_name(faculty_id)
            self.all_appointments = []
            for appt in appointments:
                print(f"Testing Name: {appt}")
                try:
                    print(f"DEBUG: Processing appointment: {appt.get('id')}")
                    
                    # Get faculty ID and name
                    faculty_id = appt.get('faculty')
                    
                    
                    
                    # Get student info
                    student_info = appt.get('student', {})
                    student_name = self.get_student_name(appt["student"])
                    
                    if isinstance(student_info, dict):
                        user_info = student_info.get('user', {})
                    
                    faculty_name = self.get_faculty_name(faculty_id)
                    
                    # Format date and time
                    start_at = appt.get('start_at', '')
                    date_time = start_at
                    if start_at and 'T' in start_at:
                        try:
                            # Parse ISO format
                            date_part, time_part = start_at.split('T')
                            time_part = time_part.split('.')[0]  # Remove milliseconds if present
                            time_part = time_part[:5]  # Get HH:MM
                            date_time = f"{date_part} {time_part}"
                        except Exception as e:
                            print(f"DEBUG: Error parsing start_at date: {e}")
                    
                    # Format created date
                    created_at = appt.get('created_at', '')
                    if created_at and 'T' in created_at:
                        created_at = created_at.split('T')[0]
                    
                    # Get purpose/description
                    purpose = appt.get('reason', 'No details provided')
                    if not purpose or purpose.strip() == "":
                        purpose = "No details provided"
                    
                    # Get status
                    status = appt.get('status', 'PENDING')
                    if isinstance(status, str):
                        status = status.upper()
                    else:
                        status = 'PENDING'
                    
                    appointment_data = {
                        'id': appt.get('id', 'Unknown'),
                        'date_time': date_time,
                        'faculty_name': faculty_name,
                        'student_name': student_name,
                        'purpose': purpose,
                        'status': status,
                        'created_at': created_at
                    }
                    
                    self.all_appointments.append(appointment_data)
                    print(f"DEBUG: Added appointment {appt.get('id')}: {student_name} with {faculty_name}")
                    
                except Exception as e:
                    print(f"DEBUG: Error processing appointment: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            print(f"DEBUG: Successfully processed {len(self.all_appointments)} appointments")
            
            self.rows = self.all_appointments.copy()
            self._updateTableWithData(self.all_appointments)
            
        except Exception as e:
            print(f"ERROR: Error loading appointments data: {e}")
            import traceback
            traceback.print_exc()
            QtWidgets.QMessageBox.warning(self, "Error", f"Failed to load appointments: {str(e)}")

    def resizeEvent(self, event):
        """Handle window resize to adjust layout and table"""
        super().resizeEvent(event)
        window_width = self.width()
        available_width = window_width - 80
        
        if available_width > 1200:
            self.tableWidget_8.setColumnWidth(0, 180)
            self.tableWidget_8.setColumnWidth(1, 150)
            self.tableWidget_8.setColumnWidth(2, 150)
            self.tableWidget_8.setColumnWidth(4, 120)
            self.tableWidget_8.setColumnWidth(5, 120)
            self.tableWidget_8.setColumnWidth(6, 100)
        elif available_width > 900:
            self.tableWidget_8.setColumnWidth(0, 160)
            self.tableWidget_8.setColumnWidth(1, 130)
            self.tableWidget_8.setColumnWidth(2, 130)
            self.tableWidget_8.setColumnWidth(4, 110)
            self.tableWidget_8.setColumnWidth(5, 110)
            self.tableWidget_8.setColumnWidth(6, 90)
        elif available_width > 600:
            self.tableWidget_8.setColumnWidth(0, 140)
            self.tableWidget_8.setColumnWidth(1, 120)
            self.tableWidget_8.setColumnWidth(2, 120)
            self.tableWidget_8.setColumnWidth(4, 100)
            self.tableWidget_8.setColumnWidth(5, 100)
            self.tableWidget_8.setColumnWidth(6, 80)
        else:
            self.tableWidget_8.setColumnWidth(0, 120)
            self.tableWidget_8.setColumnWidth(1, 100)
            self.tableWidget_8.setColumnWidth(2, 100)
            self.tableWidget_8.setColumnWidth(4, 90)
            self.tableWidget_8.setColumnWidth(5, 90)
            self.tableWidget_8.setColumnWidth(6, 70)
        
        available_height = self.height() - 200
        self.tableWidget_8.setMinimumHeight(max(300, available_height))

    def _makeStatusItem(self, text, color_hex):
        """Create a styled status table item"""
        item = QtWidgets.QTableWidgetItem(text)
        brush = QtGui.QBrush(QtGui.QColor(color_hex))
        item.setForeground(brush)
        item.setFont(QtGui.QFont("Poppins", 10, QtGui.QFont.Weight.DemiBold))
        return item

    def _makePurposeViewCell(self, appointment_id, purpose_text):
        """Create a clickable 'View' link for the purpose column"""
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        link = QtWidgets.QLabel("View", parent=container)
        
        def showPurposeDetails(event):
            self._showPurposeDetailsDialog(appointment_id, purpose_text)
        
        link.mousePressEvent = showPurposeDetails
        font = QtGui.QFont()
        font.setFamily("Poppins")
        font.setPointSize(10)
        link.setFont(font)
        link.setStyleSheet("QLabel { color: #2F80ED; text-decoration: underline; }")
        link.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        layout.addWidget(link, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        return container

    def _makeActionsCell(self, appointment_id, current_status):
        """Create action buttons for admin actions"""
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # View Details button
        view_btn = QtWidgets.QPushButton("Details")
        view_btn.setFixedSize(70, 30)
        view_btn.setStyleSheet("""
            QPushButton {
                background-color: #2F80ED;
                color: white;
                border-radius: 4px;
                font: 600 9pt 'Poppins';
            }
            QPushButton:hover {
                background-color: #2a75e0;
            }
        """)
        view_btn.clicked.connect(lambda: self._showAppointmentDetails(appointment_id))
        layout.addWidget(view_btn)
        
        layout.addStretch(1)
        return container

    def _showPurposeDetailsDialog(self, appointment_id, purpose_text):
        """Show dialog with purpose details"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Appointment Purpose")
        dialog.setModal(True)
        dialog.setFixedSize(500, 300)
        dialog.setStyleSheet("QDialog { background-color: white; border-radius: 12px; }")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header_label = QLabel("Appointment Purpose")
        header_label.setStyleSheet("QLabel { color: #084924; font: 600 16pt 'Poppins'; }")
        layout.addWidget(header_label)
        
        # Purpose text
        purpose_label = QLabel(purpose_text or "No purpose details provided")
        purpose_label.setWordWrap(True)
        purpose_label.setStyleSheet("""
            QLabel {
                color: #2b2b2b;
                font: 11pt 'Poppins';
                line-height: 1.5;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
        """)
        purpose_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll_area.setWidget(purpose_label)
        layout.addWidget(scroll_area, 1)
        
        # Close button
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
        
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        dialog.exec()

    def _showAppointmentDetails(self, appointment_id):
        """Show detailed appointment information"""
        try:
            # Find appointment in our data
            appointment = None
            for appt in self.all_appointments:
                if appt['id'] == appointment_id:
                    appointment = appt
                    break
            
            if not appointment:
                QMessageBox.warning(self, "Error", "Appointment not found.")
                return
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Appointment Details")
            dialog.setModal(True)
            dialog.setFixedSize(600, 500)
            dialog.setStyleSheet("QDialog { background-color: white; border-radius: 12px; }")
            
            main_layout = QVBoxLayout(dialog)
            main_layout.setContentsMargins(0, 0, 0, 0)
            
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setStyleSheet("""
                QScrollArea { border: none; background: white; }
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
            """)
            
            scroll_content = QWidget()
            content_layout = QVBoxLayout(scroll_content)
            content_layout.setContentsMargins(24, 20, 24, 20)
            content_layout.setSpacing(20)

            # Header
            header_widget = QWidget()
            header_layout = QHBoxLayout(header_widget)
            icon_label = QLabel()
            icon_label.setFixedSize(32, 32)
            icon_label.setStyleSheet("QLabel { background-color: #084924; border-radius: 8px; }")
            title_label = QLabel("Appointment Details")
            title_label.setStyleSheet("QLabel { color: #084924; font: 600 20pt 'Poppins'; }")
            header_layout.addWidget(icon_label)
            header_layout.addSpacing(12)
            header_layout.addWidget(title_label)
            header_layout.addStretch(1)
            content_layout.addWidget(header_widget)

            # Separator
            separator = QWidget()
            separator.setFixedHeight(1)
            separator.setStyleSheet("QWidget { background-color: #e0e0e0; }")
            content_layout.addWidget(separator)

            # Appointment Information
            info_group = QWidget()
            info_layout = QVBoxLayout(info_group)
            info_layout.setSpacing(15)
            
            # Status with color coding
            status_widget = QWidget()
            status_layout = QHBoxLayout(status_widget)
            status_label = QLabel("Status:")
            status_label.setStyleSheet("QLabel { font: 600 12pt 'Poppins'; color: #333; }")
            status_value = QLabel(appointment['status'])
            status_color = {
                "PENDING": "#F2994A",
                "CANCELED": "#EB5757",
                "APPROVED": "#219653",
                "DENIED": "#EB5757",
                "COMPLETED": "#2F80ED"
            }.get(appointment['status'], "#333333")
            status_value.setStyleSheet(f"""
                QLabel {{
                    color: {status_color};
                    font: 600 12pt 'Poppins';
                    padding: 5px 12px;
                    background-color: {status_color}20;
                    border-radius: 6px;
                    border: 1px solid {status_color}40;
                }}
            """)
            status_layout.addWidget(status_label)
            status_layout.addWidget(status_value)
            status_layout.addStretch(1)
            info_layout.addWidget(status_widget)

            # Details in a form layout
            details_group = QWidget()
            details_layout = QFormLayout(details_group)
            details_layout.setVerticalSpacing(10)
            details_layout.setHorizontalSpacing(20)
            
            details_data = [
                ("Date & Time:", appointment['date_time']),
                ("Faculty:", appointment['faculty_name']),
                ("Student:", appointment['student_name']),
                ("Created:", appointment['created_at']),
            ]
            
            for label, value in details_data:
                label_widget = QLabel(label)
                label_widget.setStyleSheet("QLabel { font: 600 11pt 'Poppins'; color: #333; }")
                value_widget = QLabel(str(value))
                value_widget.setStyleSheet("QLabel { font: 11pt 'Poppins'; color: #666; }")
                value_widget.setWordWrap(True)
                details_layout.addRow(label_widget, value_widget)
            
            info_layout.addWidget(details_group)
            content_layout.addWidget(info_group)

            # Purpose Section
            purpose_group = QWidget()
            purpose_layout = QVBoxLayout(purpose_group)
            purpose_layout.setSpacing(8)
            
            purpose_title = QLabel("Purpose:")
            purpose_title.setStyleSheet("QLabel { font: 600 12pt 'Poppins'; color: #333; }")
            purpose_layout.addWidget(purpose_title)
            
            purpose_content = QLabel(appointment['purpose'] or "No purpose details provided")
            purpose_content.setWordWrap(True)
            purpose_content.setStyleSheet("""
                QLabel {
                    color: #2b2b2b;
                    font: 11pt 'Poppins';
                    line-height: 1.5;
                    padding: 12px;
                    background-color: #f8f9fa;
                    border-radius: 8px;
                    border: 1px solid #e0e0e0;
                }
            """)
            purpose_content.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)
            
            purpose_scroll = QScrollArea()
            purpose_scroll.setWidgetResizable(True)
            purpose_scroll.setFixedHeight(120)
            purpose_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
            purpose_scroll.setWidget(purpose_content)
            purpose_layout.addWidget(purpose_scroll)
            
            content_layout.addWidget(purpose_group)
            content_layout.addStretch(1)

            scroll_area.setWidget(scroll_content)
            main_layout.addWidget(scroll_area)
            
            # Close button
            close_button = QPushButton("Close")
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
            
            button_layout = QHBoxLayout()
            button_layout.addStretch(1)
            button_layout.addWidget(close_button)
            main_layout.addLayout(button_layout)
            
            dialog.exec()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load appointment details: {str(e)}")

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    admin_appointment = AdminAppointmentPage_ui(
        "admin@university.edu",
        ["admin"],
        "admin",
        "sample_token"
    )
    admin_appointment.show()
    sys.exit(app.exec())