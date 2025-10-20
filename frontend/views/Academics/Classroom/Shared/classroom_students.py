# classroom_students.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QFrame, QScrollArea, QMessageBox, QSpacerItem, QSizePolicy,
                             QMenu)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QIcon, QFont, QFontDatabase, QAction
import os

try:
    from frontend.widgets.Academics.add_student_dialog import AddStudentDialog
except ImportError:
    try:
        from widgets.Academics.add_student_dialog import AddStudentDialog
    except ImportError:
        # Fallback import
        from add_student_dialog import AddStudentDialog

class ClassroomStudents(QWidget):
    """
    Classroom Students Tab - Displays instructor and student roster
    Integrates with Add Student Dialog for enrollment
    """
    
    def __init__(self, cls, username, roles, primary_role, token, parent=None):
        super().__init__(parent)
        self.cls = cls
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        
        # Store students data
        self.students_data = []
        
        self.setup_ui()
        self.load_class_data()
        
    def setup_ui(self):
        """Setup the students interface based on the UI structure"""
        # Load Poppins font
        self.load_poppins_font()
        
        self.setStyleSheet("""
            ClassroomStudents {
                background-color: white;
                font-family: "Poppins", Arial, sans-serif;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QPushButton {
                background-color: #084924;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 5px;
                font-weight: 400;
                font-size: 11px;
                font-family: "Poppins", Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #1B5E20;
            }
            QPushButton:pressed {
                background-color: #0D4E12;
            }
            QFrame#instructorFrame, QFrame#studentFrame {
                background-color: white;
                margin-left: 20px;
                border-radius: 20px;
                border: 1px solid #E0E0E0;
            }
            QFrame#instructorFrame:hover, QFrame#studentFrame:hover {
                background-color: #F8F9FA;
                border-color: #D0D7DE;
            }
            QLabel {
                background-color: transparent;
                border: none;
                font-family: "Poppins", Arial, sans-serif;
            }
        """)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Scroll area for content
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #F1F1F1;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #C1C1C1;
                border-radius: 4px;
                min-height: 20px;
            }
        """)
        
        # Scroll content widget
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(20, 20, 20, 20)
        self.scroll_layout.setSpacing(15)
        
        # Header with enroll button (for faculty/admin)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addStretch()
        
        if self.primary_role in ["faculty", "admin"]:
            self.enroll_button = QPushButton("Enroll Student")
            self.enroll_button.setMinimumSize(100, 30)
            self.enroll_button.setIcon(self._load_icon("baseline-add.svg"))
            self.enroll_button.setIconSize(QSize(18, 18))
            self.enroll_button.clicked.connect(self.open_add_student_dialog)
            header_layout.addWidget(self.enroll_button)
        
        self.scroll_layout.addLayout(header_layout)
        
        # Instructor section
        instructor_header = self.create_section_header("Instructor", "24px")
        self.scroll_layout.addWidget(instructor_header)
        
        # Separator
        separator1 = self.create_separator()
        self.scroll_layout.addWidget(separator1)
        
        # Instructor frame
        self.instructor_frame = self.create_person_frame(
            "Carlos Fidel Castro", 
            "Lecture Instructor",
            "instructorFrame"
        )
        self.scroll_layout.addWidget(self.instructor_frame)
        
        # Spacer between sections
        self.scroll_layout.addSpacing(25)
        
        # Students section
        students_header = self.create_section_header("Students", "24px")
        self.scroll_layout.addWidget(students_header)
        
        # Separator
        separator2 = self.create_separator()
        self.scroll_layout.addWidget(separator2)
        
        # Students container (will be populated dynamically)
        self.students_container = QVBoxLayout()
        self.students_container.setSpacing(10)
        self.students_container.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.addLayout(self.students_container)
        
        # Add stretch to push content to top
        self.scroll_layout.addStretch()
        
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)
        
    def load_poppins_font(self):
        """Load Poppins font if available"""
        try:
            # Try to load Poppins from common locations
            font_paths = [
                "frontend/assets/fonts/Poppins-Regular.ttf",
                "assets/fonts/Poppins-Regular.ttf",
                "fonts/Poppins-Regular.ttf",
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font_id = QFontDatabase.addApplicationFont(font_path)
                    if font_id != -1:
                        print(f"Successfully loaded Poppins font from {font_path}")
                    break
            else:
                print("Poppins font not found, using system font")
        except Exception as e:
            print(f"Error loading Poppins font: {e}")
    
    def _load_icon(self, icon_name):
        """Load icon from assets"""
        try:
            icon_path = os.path.join("frontend", "assets", "icons", icon_name)
            if os.path.exists(icon_path):
                return QIcon(icon_path)
        except:
            pass
        return QIcon()
    
    def create_section_header(self, text, font_size):
        """Create section header label with proper margins"""
        header = QLabel(text)
        header.setMinimumHeight(40)  # Increased height for better text display
        header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Create font with Poppins
        font = QFont("Poppins")
        font.setPointSize(int(font_size.replace("px", "")) - 8)  # Convert px to approximate points
        font.setWeight(QFont.Weight.Normal)
        
        header.setFont(font)
        header.setStyleSheet(f"""
            QLabel {{
                font-size: {font_size};
                font-weight: 400;
                margin-left: 20px;
                margin-top: 10px;
                margin-bottom: 5px;
                color: #000000;
                background-color: transparent;
            }}
        """)
        header.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        return header
    
    def create_separator(self):
        """Create horizontal separator line"""
        separator = QFrame()
        separator.setMinimumHeight(1)
        separator.setMaximumHeight(1)
        separator.setStyleSheet("""
            QFrame {
                background-color: #A9A9A9;
                border: none;
                margin-left: 20px;
                margin-right: 20px;
            }
        """)
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        return separator
    
    def create_person_frame(self, name, role, frame_id, student_data=None):
        """Create a person frame (instructor or student) with proper styling"""
        frame = QFrame()
        frame.setObjectName(frame_id)
        frame.setMinimumHeight(80)  # Increased height for better content display
        frame.setMaximumHeight(80)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 15, 20, 15)  # Increased padding
        layout.setSpacing(15)
        
        # Profile picture/icon
        profile_label = QLabel()
        profile_label.setFixedSize(50, 50)  # Slightly larger for better visibility
        profile_label.setStyleSheet("""
            QLabel {
                background-color: #084924;
                border-radius: 25px;
                border: 2px solid white;
                overflow: hidden;
            }
        """)
        profile_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Try to load profile icon
        try:
            icon_path = "frontend/assets/icons/person.png"
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                profile_label.setPixmap(pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, 
                                                    Qt.TransformationMode.SmoothTransformation))
            else:
                profile_label.setText("👤")
                profile_label.setStyleSheet(profile_label.styleSheet() + """
                    QLabel {
                        color: white;
                        font-size: 20px;
                    }
                """)
        except:
            profile_label.setText("👤")
            profile_label.setStyleSheet(profile_label.styleSheet() + """
                QLabel {
                    color: white;
                    font-size: 20px;
                }
            """)
        
        layout.addWidget(profile_label)
        
        # Name and role
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        name_label = QLabel(name)
        name_font = QFont("Poppins")
        name_font.setPointSize(12)
        name_font.setWeight(QFont.Weight.Normal)
        name_label.setFont(name_font)
        name_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 400;
                color: #24292f;
                background-color: transparent;
            }
        """)
        info_layout.addWidget(name_label)
        
        role_label = QLabel(role)
        role_font = QFont("Poppins")
        role_font.setPointSize(9)
        role_label.setFont(role_font)
        role_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #656d76;
                background-color: transparent;
            }
        """)
        info_layout.addWidget(role_label)
        
        info_layout.addStretch()
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Menu button (three dots) - only for students and faculty/admin
        if frame_id == "studentFrame" and self.primary_role in ["faculty", "admin"]:
            menu_button = QPushButton("⋮")
            menu_button.setFixedSize(30, 30)
            menu_font = QFont("Poppins")
            menu_font.setPointSize(16)
            menu_button.setFont(menu_font)
            menu_button.setStyleSheet("""
                QPushButton {
                    border: none;
                    background-color: transparent;
                    color: #656d76;
                    border-radius: 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #F3F4F6;
                }
            """)
            
            # Store student data in the button for context menu
            if student_data:
                menu_button.student_data = student_data
                menu_button.student_name = name
            
            # Connect to context menu
            menu_button.clicked.connect(self._show_student_menu)
            layout.addWidget(menu_button)
        
        return frame
    
    def _show_student_menu(self):
        """Show context menu for student management"""
        button = self.sender()
        if not hasattr(button, 'student_data'):
            return
        
        student_data = button.student_data
        student_name = button.student_name
        
        # Create context menu
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 8px;
            }
            QMenu::item {
                padding: 8px 16px;
                border-radius: 4px;
                font-family: "Poppins", Arial, sans-serif;
                font-size: 11px;
            }
            QMenu::item:selected {
                background-color: #E8F5E9;
                color: #084924;
            }
        """)
        
        # Add unenroll action
        unenroll_action = QAction("Unenroll Student", self)
        unenroll_action.triggered.connect(lambda: self._unenroll_student(student_data, student_name))
        menu.addAction(unenroll_action)
        
        # Add view details action (placeholder for future functionality)
        view_action = QAction("View Details", self)
        view_action.triggered.connect(lambda: self._view_student_details(student_data))
        menu.addAction(view_action)
        
        # Show menu at button position
        menu.exec(button.mapToGlobal(button.rect().bottomLeft()))
    
    def _unenroll_student(self, student_data, student_name):
        """Unenroll a student from the class"""
        # Confirm unenrollment
        reply = QMessageBox.question(
            self,
            "Confirm Unenrollment",
            f"Are you sure you want to unenroll {student_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Remove student from data
                self.students_data = [s for s in self.students_data if s.get('id') != student_data.get('id')]
                
                # Refresh the students list
                self.refresh_students_list()
                
                # Show success message
                QMessageBox.information(
                    self,
                    "Unenrollment Successful",
                    f"Successfully unenrolled {student_name} from the class."
                )
                
                print(f"Unenrolled student: {student_name} (ID: {student_data.get('id')})")
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to unenroll student:\n{str(e)}"
                )
                print(f"Error unenrolling student: {e}")
    
    def _view_student_details(self, student_data):
        """View student details (placeholder for future functionality)"""
        QMessageBox.information(
            self,
            "Student Details",
            f"Name: {student_data.get('name', 'N/A')}\n"
            f"ID: {student_data.get('id', 'N/A')}\n"
            f"Year Level: {student_data.get('year', 'N/A')}\n\n"
            "Detailed student information will be available in future updates."
        )
    
    def load_class_data(self):
        """Load class data including instructor and students"""
        # For now, using dummy data - in real implementation, fetch from controller
        self.load_dummy_students()
        
    def load_dummy_students(self):
        """Load dummy student data - replace with actual data from controller"""
        # Clear existing students
        while self.students_container.count():
            item = self.students_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Dummy student data with IDs - replace with actual data from your database
        self.students_data = [
            {"id": "20223010001", "name": "Michael Rj Kate Endino", "year": "2", "role": "Student"},
            {"id": "20223010002", "name": "John Doe", "year": "1", "role": "Student"},
            {"id": "20223010003", "name": "Jane Smith", "year": "3", "role": "Student"},
            {"id": "20223010004", "name": "Robert Johnson", "year": "2", "role": "Student"},
            {"id": "20223010005", "name": "Maria Garcia", "year": "1", "role": "Student"},
            {"id": "20223010006", "name": "David Wilson", "year": "4", "role": "Student"},
            {"id": "20223010007", "name": "Lisa Brown", "year": "2", "role": "Student"},
            {"id": "20223010008", "name": "James Miller", "year": "3", "role": "Student"},
        ]
        
        for student in self.students_data:
            student_frame = self.create_person_frame(
                student["name"], 
                student["role"], 
                "studentFrame",
                student_data=student  # Pass student data for context menu
            )
            self.students_container.addWidget(student_frame)
    
    def open_add_student_dialog(self):
        """Open the Add Student Dialog for enrollment"""
        try:
            dialog = AddStudentDialog()
            result = dialog.exec()
            
            if result == AddStudentDialog.DialogCode.Accepted:
                enrolled_students = dialog.get_enrolled_students()
                
                if enrolled_students:
                    # Add enrolled students to our data
                    for student in enrolled_students:
                        # Check if student already exists
                        if not any(s['id'] == student['id'] for s in self.students_data):
                            self.students_data.append({
                                'id': student['id'],
                                'name': student['name'],
                                'year': student['year'],
                                'role': 'Student'
                            })
                    
                    # Show success message
                    QMessageBox.information(
                        self,
                        "Enrollment Successful",
                        f"Successfully enrolled {len(enrolled_students)} student(s)!"
                    )
                    
                    # Refresh students list
                    self.refresh_students_list()
                    
                    print(f"Enrolled students: {[s['name'] for s in enrolled_students]}")
                else:
                    QMessageBox.information(
                        self,
                        "No Students Enrolled",
                        "No students were enrolled."
                    )
            else:
                print("Add Student Dialog cancelled")
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open Add Student Dialog:\n{str(e)}"
            )
            print(f"Error opening Add Student Dialog: {e}")
    
    def refresh_students_list(self):
        """Refresh the students list after enrollment or unenrollment"""
        # Clear existing students
        while self.students_container.count():
            item = self.students_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Repopulate with current data
        for student in self.students_data:
            student_frame = self.create_person_frame(
                student["name"], 
                student["role"], 
                "studentFrame",
                student_data=student  # Pass student data for context menu
            )
            self.students_container.addWidget(student_frame)
        
        # Show updated count
        student_count = len(self.students_data)
        print(f"Students list refreshed. Total students: {student_count}")
    
    def clear(self):
        """Clean up method"""
        # Clear the students container
        while self.students_container.count():
            item = self.students_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()