from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont


class UserDash(QWidget):
    """
    Non-Admin User Dashboard Widget
    
    This widget displays a document management interface for non-admin users
    
    Args:
        username (str): The logged-in user's username
        roles (list): List of user roles
        primary_role (str): The user's primary role
        token (str): Authentication token
    """
    
    def __init__(self, username, roles, primary_role, token):
        super().__init__()

        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout()

        title_label = QLabel("Documents")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        
        desc_label = QLabel(f"Welcome, {self.username}! Non-admin dashboard is under construction.")
        desc_label.setFont(QFont("Arial", 12))
        
        main_layout.addWidget(title_label)
        main_layout.addWidget(desc_label)
        main_layout.addStretch()

        self.setLayout(main_layout)
