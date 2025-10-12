from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont
from views.Dashboard.AdminDashboard import AdminDashboard
from views.Dashboard.StaffDashboard import StaffDashboard
from views.Dashboard.FacultyDashboard import FacultyDashboard
from views.Dashboard.StudentDashboard import StudentDashboard

class Dashboard(QWidget):
    def __init__(self, username, roles, primary_role, token):
        super().__init__()
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token

        # Initialize layout
        layout = QVBoxLayout()

        # Select dashboard based on primary_role
        if primary_role == "student":
            dashboard_widget = StudentDashboard(username, roles, primary_role, token)
        elif primary_role == "staff":
            dashboard_widget = StaffDashboard(username, roles, primary_role, token)
        elif primary_role == "faculty":
            dashboard_widget = FacultyDashboard(username, roles, primary_role, token)
        elif primary_role == "admin":
            dashboard_widget = AdminDashboard(username, roles, primary_role, token)
        else:
            # Fallback for unrecognized roles
            dashboard_widget = self._create_default_widget(
                "Invalid Role", f"No dashboard available for role: {primary_role}"
            )

        # Add the dashboard widget to the layout
        layout.addWidget(dashboard_widget)
        self.setLayout(layout)

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