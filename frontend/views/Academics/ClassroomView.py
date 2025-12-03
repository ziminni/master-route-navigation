# ClassroomView.py - Classroom tab container with detailed signal documentation
from PyQt6.QtWidgets import QWidget, QPushButton, QTabWidget, QVBoxLayout, QSizePolicy, QHBoxLayout, QButtonGroup, QMainWindow, QStackedWidget, QApplication, QLabel
from PyQt6.QtCore import pyqtSignal, Qt, QRect, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFontMetrics

from frontend.views.Academics.Classroom.Shared.post_details import PostDetails
from frontend.views.Academics.Classroom.Shared.classroom_stream import ClassroomStream
from frontend.views.Academics.Classroom.Shared.classroom_classworks import ClassroomClassworks
from frontend.views.Academics.Classroom.Shared.classroom_students import ClassroomStudents
from frontend.views.Academics.Classroom.Shared.classroom_attendance import ClassroomAttendanceView
from frontend.views.Academics.Classroom.Faculty.classroom_grades_view import FacultyGradesView
from frontend.views.Academics.Classroom.Student.classroom_grades_view import StudentGradesView
from frontend.services.Academics.Classroom.post_service import PostService
from frontend.services.Academics.Classroom.topic_service import TopicService
from frontend.controller.Academics.Classroom.post_controller import PostController

# Add this class at the top of your ClassroomView.py file, after the imports
class ClassroomNavbar(QWidget):
    """
    Custom navbar for Classroom tabs with animated underline.
    """
    
    def __init__(self, active_tab="STREAM", callback=None, parent=None):
        super().__init__(parent)
        self.callback = callback
        self.active_tab = active_tab
        self.nav_buttons = []

        # --- Main layout ---
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(8)

        # --- Nav row ---
        self.nav_row = QHBoxLayout()
        self.nav_row.setSpacing(20)

        nav_container = QWidget()
        nav_container.setObjectName("navContainer")
        nav_container.setLayout(self.nav_row)
        self.main_layout.addWidget(nav_container)

        # --- Classroom-specific tabs ---
        classroom_tabs = ["STREAM", "CLASSWORKS", "STUDENTS", "ATTENDANCE", "GRADES"]
        
        for tab in classroom_tabs:
            btn = QPushButton(tab)
            btn.setCheckable(True)
            btn.setChecked(tab == self.active_tab)
            btn.setObjectName("navButton")
            btn.clicked.connect(lambda checked, t=tab: self._on_tab_clicked(t))
            self.nav_row.addWidget(btn)
            self.nav_buttons.append(btn)
        self.nav_row.addStretch()

        # --- Yellow underline ---
        self.nav_highlight = QWidget(self)
        self.nav_highlight.setObjectName("navHighlight")
        self.nav_highlight.setFixedHeight(12)
        self.nav_highlight.setStyleSheet("""
            QWidget#navHighlight {
                background-color: #FDC601;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
        """)

        # --- Divider line ---
        divider = QWidget()
        divider.setFixedHeight(2)
        divider.setObjectName("dividerLine")
        divider.setStyleSheet("""
            QWidget#dividerLine {
                background-color: #084924;
                border: none;
            }
        """)
        self.main_layout.addWidget(divider)

        # --- Stylesheet for buttons ---
        self.setStyleSheet("""
            QPushButton#navButton {
                width: 122px;
                height: 31px;
                font-family: 'Poppins';
                font-weight: 310;
                font-size: 14px;
                color: #084924;
                text-align: center;
                background: transparent;
                border: none;
            }
            QPushButton#navButton:checked {
                font-weight: 600;
            }
            QPushButton#navButton:hover {
                color: #0B6630;
            }
        """)

        # Track underline animation
        self.nav_anim = None
        self.nav_highlight.raise_()
        self._initialized = False

    # -------------------------------
    # INTERNAL METHODS
    # -------------------------------

    def _on_tab_clicked(self, tab_name):
        """Trigger tab activation and underline animation"""
        for btn in self.nav_buttons:
            is_active = (btn.text() == tab_name)
            btn.setChecked(is_active)
            if is_active:
                self.active_tab = tab_name
                self._animate_highlight(btn)

        if self.callback:
            self.callback(tab_name)

    def _animate_highlight(self, btn):
        """Animate the underline (yellow bar) below active tab"""
        metrics = QFontMetrics(btn.font())
        text_width = metrics.horizontalAdvance(btn.text())
        btn_pos = btn.mapTo(self, btn.rect().topLeft())

        divider = self.findChild(QWidget, "dividerLine")
        divider_y = divider.mapTo(self, divider.rect().topLeft()).y()
        underline_y = divider_y - self.nav_highlight.height() + 1

        anim = QPropertyAnimation(self.nav_highlight, b"geometry")
        anim.setDuration(250)
        anim.setStartValue(self.nav_highlight.geometry())
        anim.setEndValue(QRect(
            int(btn_pos.x() + (btn.width() - text_width) / 2),
            underline_y,
            int(text_width),
            self.nav_highlight.height()
        ))
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        anim.start()
        self.nav_anim = anim  # prevent garbage collection

    def showEvent(self, event):
        """Initialize highlight position when the navbar first shows"""
        super().showEvent(event)
        if not self._initialized:
            self._initialized = True
            for btn in self.nav_buttons:
                if btn.text() == self.active_tab:
                    self._animate_highlight(btn)
                    break

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
        
        # # Main tab widget for different classroom sections
        # tabs = QTabWidget()
        # tabs.setStyleSheet("""
        #     QTabWidget::pane { border: none; background-color: white; }
        #     QTabBar::tab {
        #         background: white;
        #         padding: 10px 20px;
        #         font-size: 14px;
        #         font-family: "Poppins", Arial, sans-serif;
        #         text-transform: uppercase;
        #         border: none;
        #     }
        #     QTabBar::tab:selected {
        #         border-bottom: 4px solid #FFD700;
        #         color: black;
        #     }
        # """)
        
        # # === SERVICE LAYER SETUP ===
        # # Create data services and controller for shared data access
        # post_service = PostService("services/Academics/data/classroom_data.json")      # Handles post CRUD operations
        # topic_service = TopicService("services/Academics/data/classroom_data.json")    # Handles topic management
        
        # # Create post controller that coordinates between services and views
        # post_controller = PostController(
        #     post_service=post_service,    # 🔗 Inject post service
        #     topic_service=topic_service   # 🔗 Inject topic service
        # )
        # post_controller.set_class(self.cls["id"])  # 🎯 Set current class context
        
        # # === VIEW CREATION ===
        # # Create Stream and Classworks views with shared controller for data consistency
        # self.stream_view = ClassroomStream(
        #     self.cls, self.username, self.roles, self.primary_role, 
        #     self.token, post_controller  # 🔗 Same controller instance for data sync
        # )
        # self.classworks_view = ClassroomClassworks(
        #     self.cls, self.username, self.roles, self.primary_role, 
        #     self.token, post_controller  # 🔗 Same controller instance
        # )
        # # NEW: Create students view
        # self.students_view = ClassroomStudents(
        #     self.cls, self.username, self.roles, self.primary_role, 
        #     self.token
        # )
        # # === SIGNAL CONNECTIONS: POST SELECTION ===
        # # When post is clicked in either Stream or Classworks, bubble up to ClassroomMain
        # # Stream → ClassroomView → ClassroomMain
        # self.stream_view.post_selected.connect(self.post_selected)
        # # Classworks → ClassroomView → ClassroomMain  
        # self.classworks_view.post_selected.connect(self.post_selected)
        
        # # === SIGNAL CONNECTIONS: CROSS-VIEW REFRESH ===
        # # When new content is created in one view, refresh the other view
        # # Classworks → Stream: New post created in Classworks, refresh Stream
        # self.classworks_view.post_created.connect(self.stream_view.refresh_posts)
        # # Stream → Classworks: New post created in Stream, refresh Classworks  
        # self.stream_view.post_created.connect(self.classworks_view.refresh_posts)
        # self.classworks_view.syllabus_created.connect(self.stream_view.refresh_syllabus)
        # self.classworks_view.syllabus_created.connect(self.stream_view.refresh_posts)
        # # Set up bidirectional references
        # self.classworks_view.set_stream_reference(self.stream_view)
        # self.stream_view.set_classworks_reference(self.classworks_view)
        
        # # Create placeholder views for other tabs (to be implemented)
        # students_view = QWidget()      # Students management (future)
        # attendance_view = QWidget()    # Attendance tracking (future)
        
        # # === GRADES VIEW SETUP (Role-based) ===
        # # Faculty sees grading interface, students see their grades
        # # FIXED: Corrected the role checking logic
        # if self.primary_role in ["faculty", "admin"]:  # ✅ FIXED: Use 'in' for multiple roles
        #     try:
        #         self.grades_view = FacultyGradesView(
        #             self.cls, self.username, self.roles, self.primary_role, self.token
        #         )
        #         print(f"✅ Loaded FacultyGradesView for {self.primary_role}")
        #     except ImportError as e:
        #         # Fallback if FacultyGradesView is not available
        #         print(f"FacultyGradesView not available: {e}, using placeholder")
        #         self.grades_view = self._create_placeholder_view("Faculty Grades View - Not Available")
        # else:
        #     try:
        #         self.grades_view = StudentGradesView(
        #             self.cls, self.username, self.roles, self.primary_role, self.token
        #         )
        #         print(f"✅ Loaded StudentGradesView for {self.primary_role}")
        #     except ImportError as e:
        #         print(f"StudentGradesView not available: {e}, using placeholder")
        #         self.grades_view = self._create_placeholder_view("Student Grades View - Not Available")
            
        # # === TAB POPULATION ===
        # # Add all views to the tab widget
        # tabs.addTab(self.stream_view, "STREAM")           # Post stream and announcements
        # tabs.addTab(self.classworks_view, "CLASSWORKS")   # Materials and assessments
        # tabs.addTab(self.students_view, "STUDENTS")  # CHANGED: Use actual students view
        # tabs.addTab(attendance_view, "ATTENDANCE")        # Attendance (placeholder)
        # tabs.addTab(self.grades_view, "GRADES")           # Grades management
        
        # # === SIGNAL CONNECTION: FORM NAVIGATION ===
        # # When Classworks requests form creation, pass it up to ClassroomMain
        # # 📡 Classworks → ClassroomView → ClassroomMain
        # self.classworks_view.navigate_to_form.connect(self.navigate_to_form.emit)
        # # Note: .emit is used here because we're forwarding the signal, not connecting to a slot
        
        # layout.addWidget(tabs)

        # === SERVICE LAYER SETUP ===
        post_service = PostService("services/Academics/data/classroom_data.json")
        topic_service = TopicService("services/Academics/data/classroom_data.json")
        post_controller = PostController(
            post_service=post_service,
            topic_service=topic_service
        )
        post_controller.set_class(self.cls["id"])
        
        # === CREATE TAB WIDGET (LAZY-LOADING) ===
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabBarAutoHide(False)  # Keep tabs visible
        self.tab_widget.tabBar().setVisible(False)  # Hide default tab bar
        
        # Style the tab widget pane only
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { 
                border: none; 
                background-color: white; 
            }
        """)
        
        # === CUSTOM CLASSROOM NAVBAR ===
        self.navbar = ClassroomNavbar(
            active_tab="STREAM", 
            callback=self.on_tab_changed
        )
        
        # === CREATE AND ADD VIEWS TO TAB WIDGET ===
        # Create views dictionary for reference
        # === CREATE AND ADD VIEWS TO TAB WIDGET ===
        # Create views dictionary for reference
        self.views = {}
        
        # STREAM tab
        self.stream_view = ClassroomStream(
            self.cls, self.username, self.roles, self.primary_role, 
            self.token, post_controller
        )
        self.tab_widget.addTab(self.stream_view, "")
        self.views["STREAM"] = self.stream_view
        
        # CLASSWORKS tab
        self.classworks_view = ClassroomClassworks(
            self.cls, self.username, self.roles, self.primary_role, 
            self.token, post_controller
        )
        self.tab_widget.addTab(self.classworks_view, "")
        self.views["CLASSWORKS"] = self.classworks_view
        
        # STUDENTS tab
        self.students_view = ClassroomStudents(
            self.cls, self.username, self.roles, self.primary_role, 
            self.token
        )
        self.tab_widget.addTab(self.students_view, "")
        self.views["STUDENTS"] = self.students_view
        
        # ATTENDANCE tab - Embedded attendance view
        try:
            self.attendance_view = ClassroomAttendanceView(
                cls=self.cls,
                username=self.username,
                roles=self.roles,
                primary_role=self.primary_role,
                token=self.token,
                parent=self
            )
            
            # Make attendance view fill available space
            self.attendance_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            
            self.tab_widget.addTab(self.attendance_view, "")
            self.views["ATTENDANCE"] = self.attendance_view
            print(f"✅ Loaded AttendanceView for {self.primary_role}")
        except Exception as e:
            print(f"Error loading attendance view: {e}, using placeholder")
            self.attendance_view = self._create_placeholder_view(f"Attendance View Error: {str(e)}")
            self.tab_widget.addTab(self.attendance_view, "")
            self.views["ATTENDANCE"] = self.attendance_view
        
        # GRADES tab
        if self.primary_role in ["faculty", "admin"]:
            try:
                self.grades_view = FacultyGradesView(
                    self.cls, self.username, self.roles, self.primary_role, self.token
                )
                print(f"✅ Loaded FacultyGradesView for {self.primary_role}")
            except ImportError as e:
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
        
        self.tab_widget.addTab(self.grades_view, "")
        self.views["GRADES"] = self.grades_view
        
        # === SIGNAL CONNECTIONS ===
        # Post selection signals
        self.stream_view.post_selected.connect(self.post_selected)
        self.classworks_view.post_selected.connect(self.post_selected)
        
        # Cross-view refresh signals
        self.classworks_view.post_created.connect(self.stream_view.refresh_posts)
        self.stream_view.post_created.connect(self.classworks_view.refresh_posts)
        self.classworks_view.syllabus_created.connect(self.stream_view.refresh_syllabus)
        self.classworks_view.syllabus_created.connect(self.stream_view.refresh_posts)
        
        # Form navigation signal
        self.classworks_view.navigate_to_form.connect(self.navigate_to_form.emit)
        
        # Cross-view references
        self.classworks_view.set_stream_reference(self.stream_view)
        self.stream_view.set_classworks_reference(self.classworks_view)
        
        # Add navbar and tab widget to layout
        layout.addWidget(self.navbar)
        layout.addWidget(self.tab_widget)

    def on_tab_changed(self, tab_name):
        """Handle navbar tab selection - switch QTabWidget tabs"""
        tab_order = ["STREAM", "CLASSWORKS", "STUDENTS", "ATTENDANCE", "GRADES"]
        
        if tab_name in tab_order:
            tab_index = tab_order.index(tab_name)
            self.tab_widget.setCurrentIndex(tab_index)
            
            # Optional: Refresh attendance data when tab is selected
            if tab_name == "ATTENDANCE" and hasattr(self, 'attendance_view'):
                try:
                    self.attendance_view.load_class_data()
                except Exception as e:
                    print(f"Error refreshing attendance data: {e}")
                    
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