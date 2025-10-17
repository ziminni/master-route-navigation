"""
CISC Virtual Hub Launcher (Unified Window Version)
==================================================

This launcher dynamically switches between:
- The launcher menu
- The student portal
- The faculty portal
All inside the same QMainWindow, using show/hide toggling.
"""

import sys
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWidgets import QApplication

# --- Import your existing widgets (must inherit QWidget) ---
from .main_chat_widget_wrapper import MainChatWidgetWrapper as StudentMainUI
from .faculty_app import FacultyMainUI
from .data_manager import DataManager


class LauncherWindow(QtWidgets.QMainWindow):
    def __init__(self ,username, roles, primary_role, token, parent=None):
        super().__init__(parent)
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token


         # Initialize DataManager with session info
        self.data_manager = DataManager(
            data_file_path="dummy_data.json",
            username=username,
            roles=roles,
            primary_role=primary_role,
            token=token
        )
        
        self.setWindowTitle("🎓 CISC Virtual Hub")
        self.setGeometry(100, 100, 900, 600)
        self.setStyleSheet("background-color: #f8f9fa;")

        # --- Central container ---
        self.container = QtWidgets.QWidget()
        self.main_layout = QtWidgets.QStackedLayout(self.container)
        self.setCentralWidget(self.container)

        # --- Launcher screen ---
        self.launcher_widget = self.create_launcher_widget()
        self.main_layout.addWidget(self.launcher_widget)

        # --- Student & Faculty screens ---
        self.student_widget = None
        self.faculty_widget = None

        if "student" in self.roles:
            self.toggle_student_portal()  # Auto-open student portal if role present
        elif "faculty" in self.roles:
            self.toggle_faculty_portal()  # Auto-open faculty portal if role present

    # ------------------------------------------------------------
    # Create the launcher screen (main menu)
    # ------------------------------------------------------------
    def create_launcher_widget(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        title = QtWidgets.QLabel("🎓 CISC Virtual Hub")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #084924;")

        subtitle = QtWidgets.QLabel("Unified Messaging System")
        subtitle.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 16px; color: #666; margin-bottom: 10px;")

        self.student_btn = QtWidgets.QPushButton("👨‍🎓 Student Portal")
        self.student_btn.setStyleSheet(self.button_style("#084924"))
        self.student_btn.clicked.connect(self.toggle_student_portal)

        self.faculty_btn = QtWidgets.QPushButton("👨‍🏫 Faculty Portal")
        self.faculty_btn.setStyleSheet(self.button_style("#1e4d2b"))
        self.faculty_btn.clicked.connect(self.toggle_faculty_portal)

        self.exit_btn = QtWidgets.QPushButton("Exit")
        self.exit_btn.setStyleSheet(self.button_style("#6b7280", small=True))
        self.exit_btn.clicked.connect(self.close)

        desc = QtWidgets.QLabel(
            "Choose your role to access the messaging system.\n"
            "Students can create inquiries and chat with faculty.\n"
            "Faculty can manage messages and respond to inquiries."
        )
        desc.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("font-size: 13px; color: #666;")
        desc.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)
        layout.addWidget(self.student_btn)
        layout.addWidget(self.faculty_btn)
        layout.addWidget(desc)
        layout.addSpacing(20)
        layout.addWidget(self.exit_btn, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        return widget

    # ------------------------------------------------------------
    # Button style helper
    # ------------------------------------------------------------
    def button_style(self, color, small=False):
        padding = "10px 20px" if small else "15px 30px"
        font_size = "14px" if small else "18px"
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                font-size: {font_size};
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: {padding};
                min-height: 50px;
            }}
            QPushButton:hover {{
                background-color: {self.darken(color, 0.15)};
            }}
            QPushButton:pressed {{
                background-color: {self.darken(color, 0.3)};
            }}
        """

    def darken(self, hex_color, factor):
        """Darken a hex color for hover/pressed effects"""
        c = int(hex_color.lstrip('#'), 16)
        r, g, b = (c >> 16) & 255, (c >> 8) & 255, c & 255
        r = int(r * (1 - factor))
        g = int(g * (1 - factor))
        b = int(b * (1 - factor))
        return f"#{r:02x}{g:02x}{b:02x}"

    # ------------------------------------------------------------
    # Toggling between launcher / student / faculty
    # ------------------------------------------------------------
    def toggle_student_portal(self):
        if self.student_widget is None:
            self.student_widget = StudentMainUI()
            self.main_layout.addWidget(self.student_widget)

            # Optional: add a back button signal if your widget supports it
            if hasattr(self.student_widget, "go_back"):
                self.student_widget.go_back.connect(self.return_to_launcher)

        # Toggle view
        if self.main_layout.currentWidget() == self.launcher_widget:
            self.main_layout.setCurrentWidget(self.student_widget)
        else:
            self.main_layout.setCurrentWidget(self.launcher_widget)

    def toggle_faculty_portal(self):
        if self.faculty_widget is None:
            self.faculty_widget = FacultyMainUI()
            self.main_layout.addWidget(self.faculty_widget)

            # Optional back button support
            if hasattr(self.faculty_widget, "go_back"):
                self.faculty_widget.go_back.connect(self.return_to_launcher)

        # Toggle view
        if self.main_layout.currentWidget() == self.launcher_widget:
            self.main_layout.setCurrentWidget(self.faculty_widget)
        else:
            self.main_layout.setCurrentWidget(self.launcher_widget)

    # ------------------------------------------------------------
    # Return to launcher
    # ------------------------------------------------------------
    def return_to_launcher(self):
        self.main_layout.setCurrentWidget(self.launcher_widget)



