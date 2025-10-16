# ClassroomView.py - Classroom tab container with detailed signal documentation
from PyQt6.QtWidgets import QWidget, QPushButton, QTabWidget, QVBoxLayout, QHBoxLayout, QButtonGroup, QMainWindow, QStackedWidget, QApplication, QLabel
from PyQt6.QtCore import pyqtSignal, Qt
from frontend.views.Academics.Classroom.Shared.post_details import PostDetails
from frontend.views.Academics.Classroom.Shared.classroom_stream import ClassroomStream
from frontend.views.Academics.Classroom.Shared.classroom_classworks import ClassroomClassworks
from frontend.views.Academics.Classroom.Shared.classroom_students import ClassroomStudents
from frontend.views.Academics.Classroom.Faculty.classroom_grades_view import FacultyGradesView
from frontend.views.Academics.Classroom.Student.classroom_grades_view import StudentGradesView
from frontend.services.Academics.Classroom.post_service import PostService
from frontend.services.Academics.Classroom.topic_service import TopicService
from frontend.controller.Academics.Classroom.post_controller import PostController

class ClassroomView(QWidget):
    """
    CLASSROOM VIEW - Container for classroom tabs (Stream, Classworks, Students, Attendance, Grades)
    
    SIGNAL ARCHITECTURE:
    ┌─────────────────┐    post_selected      ┌─────────────────┐
    │ ClassroomStream │ ────────────────────► │  ClassroomView  │
    │                 │                       │                 │
    │ ClassroomClass- │ ────────────────────► │                 │
    │     works       │    post_selected      │                 │
    └─────────────────┘                       └─────────────────┘
                                                       │
                                                       │ post_selected (emits up)
                                                       ▼
    ┌─────────────────┐                       ┌─────────────────┐
    │  ClassroomMain  │ ◄─────────────────────│                 │
    └─────────────────┘                       └─────────────────┘
    
    ┌─────────────────┐    navigate_to_form   ┌─────────────────┐
    │ ClassroomClass- │ ────────────────────► │  ClassroomView  │
    │     works       │                       │                 │
    └─────────────────┘                       └─────────────────┘
                                                       │
                                                       │ navigate_to_form (emits up)
                                                       ▼
    ┌─────────────────┐                       ┌─────────────────┐
    │  ClassroomMain  │ ◄─────────────────────│                 │
    └─────────────────┘                       └─────────────────┘
    """
    
    # SIGNAL DEFINITIONS:
    # - back_clicked: Emitted when user wants to return to home view
    # - post_selected: Emitted when any post is clicked in Stream or Classworks
    # - navigate_to_form: Emitted when faculty clicks to create Material/Assessment
    
    back_clicked = pyqtSignal()                    # No data - simple back navigation
    post_selected = pyqtSignal(dict)               # Carries post data {id, title, content, type, etc.}
    navigate_to_form = pyqtSignal(str, object)     # Carries (form_type, class_data)

    def __init__(self, cls, username, roles, primary_role, token, parent=None):
        super().__init__(parent)
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        self.cls = cls  # Store class data for form creation
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("background-color: white;")
        layout = QVBoxLayout(self)
        
        # Header with lecture/lab toggle buttons
        header_layout = QHBoxLayout()
        header_layout.addStretch()
        lecture_btn = QPushButton("LECTURE")
        lecture_btn.setStyleSheet("""
            QPushButton { background-color: #084924; color: white; border-radius: 5px; padding: 5px 10px; }
            QPushButton:checked { background-color: #1B5E20; }
        """)
        lecture_btn.setCheckable(True)
        lecture_btn.setChecked(True)
        lab_btn = QPushButton("LABORATORY")
        lab_btn.setStyleSheet("""
            QPushButton { background-color: #084924; color: white; border-radius: 5px; padding: 5px 10px; }
            QPushButton:checked { background-color: #1B5E20; }
        """)
        lab_btn.setCheckable(True)
        group = QButtonGroup()  # Ensures only one button is active at a time
        group.addButton(lecture_btn)
        group.addButton(lab_btn)
        header_layout.addWidget(lecture_btn)
        header_layout.addWidget(lab_btn)
        layout.addLayout(header_layout)
        
        # Main tab widget for different classroom sections
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: none; background-color: white; }
            QTabBar::tab {
                background: white;
                padding: 10px 20px;
                font-size: 14px;
                font-family: "Poppins", Arial, sans-serif;
                text-transform: uppercase;
                border: none;
            }
            QTabBar::tab:selected {
                border-bottom: 4px solid #FFD700;
                color: black;
            }
        """)
        
        # === SERVICE LAYER SETUP ===
        # Create data services and controller for shared data access
        post_service = PostService("services/Academics/data/classroom_data.json")      # Handles post CRUD operations
        topic_service = TopicService("services/Academics/data/classroom_data.json")    # Handles topic management
        
        # Create post controller that coordinates between services and views
        post_controller = PostController(
            post_service=post_service,    # 🔗 Inject post service
            topic_service=topic_service   # 🔗 Inject topic service
        )
        post_controller.set_class(self.cls["id"])  # 🎯 Set current class context
        
        # === VIEW CREATION ===
        # Create Stream and Classworks views with shared controller for data consistency
        self.stream_view = ClassroomStream(
            self.cls, self.username, self.roles, self.primary_role, 
            self.token, post_controller  # 🔗 Same controller instance for data sync
        )
        self.classworks_view = ClassroomClassworks(
            self.cls, self.username, self.roles, self.primary_role, 
            self.token, post_controller  # 🔗 Same controller instance
        )
        # NEW: Create students view
        self.students_view = ClassroomStudents(
            self.cls, self.username, self.roles, self.primary_role, 
            self.token
        )
        # === SIGNAL CONNECTIONS: POST SELECTION ===
        # When post is clicked in either Stream or Classworks, bubble up to ClassroomMain
        # Stream → ClassroomView → ClassroomMain
        self.stream_view.post_selected.connect(self.post_selected)
        # Classworks → ClassroomView → ClassroomMain  
        self.classworks_view.post_selected.connect(self.post_selected)
        
        # === SIGNAL CONNECTIONS: CROSS-VIEW REFRESH ===
        # When new content is created in one view, refresh the other view
        # Classworks → Stream: New post created in Classworks, refresh Stream
        self.classworks_view.post_created.connect(self.stream_view.refresh_posts)
        # Stream → Classworks: New post created in Stream, refresh Classworks  
        self.stream_view.post_created.connect(self.classworks_view.refresh_posts)
        self.classworks_view.syllabus_created.connect(self.stream_view.refresh_syllabus)
        self.classworks_view.syllabus_created.connect(self.stream_view.refresh_posts)
        # Set up bidirectional references
        self.classworks_view.set_stream_reference(self.stream_view)
        self.stream_view.set_classworks_reference(self.classworks_view)
        
        # Create placeholder views for other tabs (to be implemented)
        students_view = QWidget()      # Students management (future)
        attendance_view = QWidget()    # Attendance tracking (future)
        
        # === GRADES VIEW SETUP (Role-based) ===
        # Faculty sees grading interface, students see their grades
        # FIXED: Corrected the role checking logic
        if self.primary_role in ["faculty", "admin"]:  # ✅ FIXED: Use 'in' for multiple roles
            try:
                self.grades_view = FacultyGradesView(
                    self.cls, self.username, self.roles, self.primary_role, self.token
                )
                print(f"✅ Loaded FacultyGradesView for {self.primary_role}")
            except ImportError as e:
                # Fallback if FacultyGradesView is not available
                print(f"FacultyGradesView not available: {e}, using placeholder")
                self.grades_view = self._create_placeholder_view("Faculty Grades View - Not Available")
        else:
            try:
                self.grades_view = StudentGradesView(
                    self.cls, self.username, self.roles, self.primary_role, self.token
                )
                print(f"✅ Loaded StudentGradesView for {self.primary_role}")
            except ImportError as e:
                print(f"StudentGradesView not available: {e}, using placeholder")
                self.grades_view = self._create_placeholder_view("Student Grades View - Not Available")
            
        # === TAB POPULATION ===
        # Add all views to the tab widget
        tabs.addTab(self.stream_view, "STREAM")           # Post stream and announcements
        tabs.addTab(self.classworks_view, "CLASSWORKS")   # Materials and assessments
        tabs.addTab(self.students_view, "STUDENTS")  # CHANGED: Use actual students view
        tabs.addTab(attendance_view, "ATTENDANCE")        # Attendance (placeholder)
        tabs.addTab(self.grades_view, "GRADES")           # Grades management
        
        # === SIGNAL CONNECTION: FORM NAVIGATION ===
        # When Classworks requests form creation, pass it up to ClassroomMain
        # 📡 Classworks → ClassroomView → ClassroomMain
        self.classworks_view.navigate_to_form.connect(self.navigate_to_form.emit)
        # Note: .emit is used here because we're forwarding the signal, not connecting to a slot
        
        layout.addWidget(tabs)

    def _create_placeholder_view(self, message):
        """Helper to create placeholder views for unimplemented features"""
        placeholder = QWidget()
        placeholder.setStyleSheet("background-color: white;")
        layout = QVBoxLayout(placeholder)
        label = QLabel(message)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 16px; color: #666; padding: 50px;")
        layout.addWidget(label)
        return placeholder

    def clear(self):
        """Cleanup method to prevent memory leaks"""
        self.stream_view.clear()
        self.classworks_view.clear()