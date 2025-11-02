from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QWidget, QSizePolicy
from .StudentAppointmentPage import StudentAppointmentPage_ui 
from .StudentBrowseFacultyPage import StudentBrowseFaculty_ui
from .StudentRequestPage import StudentRequestPage_ui
from .StudentEditSchedulePage import StudentEditSchedulePage_ui

class Student_Ui_MainWindow(QWidget):
    def __init__(self, username, roles, primary_role, token, parent=None):
        super().__init__(parent)
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        self.backIndexList = [0]
        self.currentPage = 0

        # Set minimum size to allow flexibility
        self.setMinimumSize(1200, 600)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Initialize pages
        self.AppointmentPage = StudentAppointmentPage_ui(self.username, self.roles, self.primary_role, self.token)
        self.AppointmentBrowseFacultyPage = StudentBrowseFaculty_ui(self.username, self.roles, self.primary_role, self.token)
        self.StudentRequestPage = StudentRequestPage_ui(self.username, self.roles, self.primary_role, self.token)
        self.StudentEditSchedulePage = StudentEditSchedulePage_ui(self.username, self.roles, self.primary_role, self.token)

        # Connect signals
        self.AppointmentPage.go_to_AppointmentSchedulerPage.connect(self.changetoAppointmentScheduler)
        self.AppointmentBrowseFacultyPage.go_to_RequestPage.connect(self.changetoRequestPage)
        self.AppointmentBrowseFacultyPage.back.connect(self.backclicked)
        self.StudentEditSchedulePage.back.connect(self.backclicked)
        self.StudentRequestPage.back.connect(self.backclicked)

        # Initialize the UI
        self.setupUi(self)

        self.setup_navigation()
        
        print(f"Ui_MainWindow: Initialized for user {username} with role {primary_role}")
        # In your main window class
    def setup_navigation(self):
        # Create pages
        self.student_appointment_page = StudentAppointmentPage_ui(
            self.username, self.roles, self.primary_role, self.token
        )
        self.student_request_page = StudentRequestPage_ui(
            self.username, self.roles, self.primary_role, self.token
        )
        
        # Connect signals
        self.student_appointment_page.go_to_AppointmentSchedulerPage.connect(
            lambda: self.show_student_request_page()
        )
        
        self.student_request_page.back.connect(
            lambda: self.show_student_appointments_page()
        )
        
        # Connect the refresh signal
        self.student_request_page.backrefreshdata.connect(
            self.student_appointment_page.refresh_appointments_data
        )
        
        # Add to stacked widget
        self.stackedWidget.addWidget(self.student_appointment_page)
        self.stackedWidget.addWidget(self.student_request_page)

    def show_student_appointments_page(self):
        self.stackedWidget.setCurrentWidget(self.student_appointment_page)

    def show_student_request_page(self, faculty_data=None):
        if faculty_data:
            self.student_request_page.set_faculty_data(faculty_data)
        self.stackedWidget.setCurrentWidget(self.student_request_page)
    def setupUi(self, MainWindow):
        self._setupCentralWidget(MainWindow)
        self.stackedWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def _setupCentralWidget(self, MainWindow):
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.centralwidget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self.main_layout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(0)
        self.main_layout.setObjectName("main_layout")
        
        self._setupStackedWidget()

    def _setupStackedWidget(self):
        self.widget = QtWidgets.QWidget(parent=self.centralwidget)
        self.widget.setObjectName("widget")
        self.widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.widget.setStyleSheet("""
            QWidget#widget {
                background-color: #f1f1f3; 
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }
        """)
        
        self.content_layout = QtWidgets.QGridLayout(self.widget)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(0)
        self.content_layout.setObjectName("content_layout")
        
        self.stackedWidget = QtWidgets.QStackedWidget()
        self.stackedWidget.setObjectName("stackedWidget")
        self.stackedWidget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self.stackedWidget.addWidget(self.AppointmentPage)
        self.stackedWidget.addWidget(self.AppointmentBrowseFacultyPage)
        self.stackedWidget.addWidget(self.StudentRequestPage)
        self.stackedWidget.addWidget(self.StudentEditSchedulePage)
        
        self.content_layout.addWidget(self.stackedWidget, 0, 0)
        self.content_layout.setRowStretch(0, 1)
        self.content_layout.setColumnStretch(0, 1)
        
        self.main_layout.addWidget(self.widget)

    def goBackPage(self):
        if self.currentPage > 0:
            self.currentPage = self.backIndexList[-2]
            self.backIndexList.pop()
            self.stackedWidget.setCurrentIndex(self.currentPage)

    def changetoAppointmentScheduler(self):
        self.currentPage = 1
        self.backIndexList.append(1)
        self.stackedWidget.setCurrentIndex(1)

    def changetoReschedule(self):
        self.currentPage = 2
        self.backIndexList.append(2)
        self.stackedWidget.setCurrentIndex(2)

    def changetoRequestPage(self, faculty_data):
        self.currentPage = 2
        self.backIndexList.append(2)
        self.StudentRequestPage.set_faculty_data(faculty_data)
        self.stackedWidget.setCurrentIndex(2)

    def changetoEditschedule(self):
        self.currentPage = 3
        self.backIndexList.append(3)
        self.stackedWidget.setCurrentIndex(3)

    def backclicked(self):
        if len(self.backIndexList) > 1:
            self.backIndexList.pop()
        self.currentPage = self.backIndexList[-1]
        self.stackedWidget.setCurrentIndex(self.currentPage)

    def resizeEvent(self, event):
        """Handle window resize to ensure proper scaling"""
        super().resizeEvent(event)
        
        # Update all layouts
        self.updateGeometry()
        self.centralwidget.updateGeometry()
        self.widget.updateGeometry()
        self.stackedWidget.updateGeometry()
        
        # Notify child widgets of resize (if they implement resizeEvent)
        current_widget = self.stackedWidget.currentWidget()
        if hasattr(current_widget, 'resizeEvent'):
            current_widget.resizeEvent(event)
        
        # Debug output for size verification
        print(f"Window size: {event.size().width()}x{event.size().height()}")
        print(f"Stacked widget size: {self.stackedWidget.width()}x{self.stackedWidget.height()}")

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QMainWindow, QApplication

    app = QApplication(sys.argv)
    main_window = QMainWindow()
    main_window.setWindowTitle("Student Appointment System")
    main_window.resize(1200, 800)
    
    student_ui = Student_Ui_MainWindow(
        username="john_doe",
        roles=["student"],
        primary_role="student",
        token="sample_token_123"
    )
    
    main_window.setCentralWidget(student_ui)
    main_window.show()
    
    sys.exit(app.exec())