from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from .Faculty.Faculty_Appointment_main_ui import Ui_MainWindow
from .Admin.Admin_Appointment_main import Admin_Appointment_Main
from .Student.Student_Appointment_main_ui import Student_Ui_MainWindow

class Appointment_main(QWidget):
    def __init__(self, username, roles, primary_role, token):
        super().__init__()
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token

        # Set window properties
        self.setWindowTitle("Appointment Dashboard")
        self.setWindowFlags(Qt.WindowType.Window)  # Make it a top-level window
        self.setMinimumSize(800, 600)  # Set a reasonable default size

        # Initialize layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        print("Roles in Appointment_main:", roles)

        # Select dashboard based on primary_role
        if primary_role == "student":
            Appointment_main = Student_Ui_MainWindow(username, roles, primary_role, token)
        elif primary_role == "admin":
            Appointment_main = Admin_Appointment_Main(username, roles, primary_role, token)
        elif primary_role == "faculty":
            Appointment_main = Ui_MainWindow(username, roles, primary_role, token)
        else:
            # Fallback for unrecognized roles
            Appointment_main = self._create_default_widget(
                "Invalid Role", f"No dashboard available for role: {primary_role}"
            )

        # Add the dashboard widget to the layout
        layout.addWidget(Appointment_main)
        self.setLayout(layout)

        # Center the window on the screen
        self.center_on_screen()

    def _create_default_widget(self, title, desc):
        """Create a fallback widget for invalid roles."""
        widget = QWidget()
        layout = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        desc_label = QLabel(desc)
        desc_label.setFont(QFont("Arial", 12))
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def center_on_screen(self):
        """Center the widget on the screen."""
        # Get the screen geometry
        screen = QApplication.primaryScreen().availableGeometry()
        screen_rect = screen  # Available geometry excludes taskbar, etc.

        # Get the widget's size
        size = self.sizeHint() if self.sizeHint().isValid() else self.size()

        # Calculate the position to center the widget
        x = (screen_rect.width() - size.width()) // 2 + screen_rect.x()
        y = (screen_rect.height() - size.height()) // 2 + screen_rect.y()

        # Move the widget to the calculated position
        self.move(x, y)