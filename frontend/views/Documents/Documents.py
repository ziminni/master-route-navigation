from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont
from .Users.Admin.AdminDash import AdminDash
from .Users.Non_Admin.Dash import UserDash
from .utils.role_utils import RoleRouter
from .Mock.initializer import initialize_documents_data


class DocumentsView(QWidget):
    """
    Main Documents View with role-based routing.
    
    This view automatically routes users to the appropriate dashboard
    based on their role using the RoleRouter utility.
    
    Also handles initialization of JSON data files on first access.
    """
    
    def __init__(self, username, roles, primary_role, token):
        super().__init__()

        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        
        # Initialize data files on first access
        initialize_documents_data()
        
        main_layout = QVBoxLayout(self)
        
        # Use RoleRouter to get appropriate dashboard
        dashboard = RoleRouter.route_to_dashboard(
            username, roles, primary_role, token,
            admin_dashboard=AdminDash,
            faculty_dashboard=UserDash,
            staff_dashboard=UserDash,
            student_dashboard=UserDash,
            default_dashboard=self._create_default_dashboard,
        )
        
        if dashboard:
            main_layout.addWidget(dashboard)
        else:
            # Fallback if no dashboard returned
            fallback = self._create_default_dashboard(username, roles, primary_role, token)
            main_layout.addWidget(fallback)
            
        self.setLayout(main_layout)
    
    def _create_default_dashboard(self, username, roles, primary_role, token):
        """
        Create a default/guest dashboard for users without specific role dashboard.
        
        Returns:
            QWidget: Default dashboard widget
        """
        default_widget = QWidget()
        layout = QVBoxLayout(default_widget)
        
        title_label = QLabel("Documents")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        desc_label = QLabel(f"Welcome, {username}! Access to documents is limited for your role.")
        desc_label.setFont(QFont("Arial", 12))
        
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addStretch()
        
        return default_widget
