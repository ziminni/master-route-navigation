from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class Dashboard(QWidget):
    def __init__(self, username, roles, primary_role, token, parent=None):
        super().__init__(parent)
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token 

        self.setWindowTitle("Dasboard")
        self.resize(800, 600)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Welcome, {self.username}"))
        layout.addWidget(QLabel(f"Your primary role: {self.primary_role}"))
        layout.addWidget(QLabel(f"All roles: [{', '.join(self.roles)}]"))
        

        if "admin" in self.roles:
            layout.addWidget(QLabel("Admin panel here"))
        elif "faculty" in self.roles:
            layout.addWidget(QLabel("Faculty dashboard here"))
        elif "student" in self.roles:
            layout.addWidget(QLabel("Student dashboard here"))


# def __init__(self, username: str, parent=None):
#         super().__init__(parent)

#         self.setWindowTitle("Dashboard")
#         self.resize(800, 600)

#         layout = QVBoxLayout(self)

#         welcome = QLabel(f"Welcome to the Dashboard, {username}!", self)
#         welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
#         welcome.setStyleSheet("font-size: 20px; font-weight: bold;")

#         layout.addWidget(welcome)