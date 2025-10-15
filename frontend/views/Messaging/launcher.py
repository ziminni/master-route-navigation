<<<<<<< Updated upstream
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
=======
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl
import os
import shutil

from .msg_main import Ui_MainWindow
from .data_manager import DataManager
from .faculty_app import FacultyApp
from .faculty.faculty_main import Ui_MainWindow as FacultyUi_MainWindow


class Main_Chat_Widget(QtWidgets.QWidget):
    def __init__(self, username="", roles=None, primary_role="", token="", parent=None, chat_name="Chat"):
        super().__init__(parent)
        roles = roles or []  # prevent mutable default

        # Optional: Store session info if needed
>>>>>>> Stashed changes
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token

<<<<<<< Updated upstream
         # Initialize DataManager with session info
        self.data_manager = DataManager(
            data_file_path="data.json",
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


=======
        # The rest of your initialization code...
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("QWidget { border: none; background: transparent; }")
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding
        )

        # Load UI based on primary role
        print(f"[DEBUG] Primary role: {self.primary_role}")
        if self.primary_role == "faculty":
            print("[DEBUG] Loading FacultyApp for faculty role")
            # FacultyApp is a complete widget (QMainWindow), no setupUi needed
            self.ui = FacultyUi_MainWindow()
            self.ui.setupUi(self)
            # For FacultyApp, we need to embed it differently since it's a complete widget
            layout = QtWidgets.QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            layout.addWidget(self.ui)
        else:
            print(f"[DEBUG] Loading Ui_MainWindow for role: {self.primary_role}")
            # Ui_MainWindow is a UI class that needs setupUi called
            self.ui = Ui_MainWindow()
            self.ui.setupUi(self)
            
            # Make centralwidget/message_widget flexible and borderless
            self.ui.centralwidget.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Expanding,
                QtWidgets.QSizePolicy.Policy.Expanding
            )
            self.ui.centralwidget.setContentsMargins(0, 0, 0, 0)

            self.ui.message_widget.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Expanding,
                QtWidgets.QSizePolicy.Policy.Expanding
            )
            self.ui.message_widget.setStyleSheet("""
                QWidget#message_widget {
                    background-color: white;
                    border-radius: 0px;
                    border: none;
                    padding: 10px;
                }
            """)

            # Embed the built centralwidget into this wrapper
            layout = QtWidgets.QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            layout.addWidget(self.ui.centralwidget)

        # Header text
        # self.ui.name_header.setText(chat_name)

        # Conversation context (must be set by MainApp)
        self.data_manager = None
        self.current_user_id = None
        self.other_user_id = None
        self.conversation_id = None

        # # Wire actions
        # self.ui.button_send.clicked.connect(self.handle_send)
        # self.ui.lineedit_msg.returnPressed.connect(self.handle_send)
        # self.ui.button_attachments.clicked.connect(self.handle_attach)
        # self.ui.button_link.clicked.connect(self.handle_link)
        # self.ui.lineedit_msg.setPlaceholderText("Type a message...")

        # Size hints
        self.setMinimumSize(400, 300)

    def sizeHint(self):
        return QtCore.QSize(600, 500)

    def minimumSizeHint(self):
        return QtCore.QSize(400, 300)

    def set_context(self, data_manager, current_user_id, other_user_id, conversation_id):
        """Provide conversation context so send/attach/link can persist correctly."""
        self.data_manager = data_manager
        self.current_user_id = current_user_id
        self.other_user_id = other_user_id
        self.conversation_id = conversation_id

    def handle_send(self):
        print("[CTX]", self.data_manager, self.current_user_id, self.other_user_id, self.conversation_id)
        if not self._has_context():
            QtWidgets.QMessageBox.warning(self, "No conversation", "Select a conversation first.")
            return

        text = self.ui.lineedit_msg.text().strip()
        if not text:
            return

        payload = {
            "sender_id": self.current_user_id,
            "receiver_id": self.other_user_id,
            "conversation_id": self.conversation_id,
            "content": text,
            "message_type": "general",
            "priority": "normal",
            "status": "sent",
            "is_read": False,
        }
        created = self.data_manager.create_message(payload)
        if created:
            self.append_text_bubble(created)
            self.ui.lineedit_msg.clear()
            self.scroll_to_bottom()

    def handle_attach(self):
        if not self._has_context():
            QtWidgets.QMessageBox.warning(self, "No conversation", "Select a conversation first.")
            return

        files, _ = QtWidgets.QFileDialog.getOpenFileNames(self, "Attach files")
        if not files:
            return

        os.makedirs("attachments", exist_ok=True)
        saved = []
        for src in files:
            name = os.path.basename(src)
            base, ext = os.path.splitext(name)
            dest = os.path.join("attachments", name)
            i = 1
            while os.path.exists(dest):
                dest = os.path.join("attachments", f"{base}_{i}{ext}")
                i += 1
            shutil.copy2(src, dest)
            saved.append(dest)

        body = "\n".join(f"[Attachment] {os.path.basename(p)}" for p in saved)
        payload = {
            "sender_id": self.current_user_id,
            "receiver_id": self.other_user_id,
            "conversation_id": self.conversation_id,
            "content": body,
            "message_type": "general",
            "priority": "normal",
            "status": "sent",
            "is_read": False,
            "attachments": saved,
        }
        created = self.data_manager.create_message(payload)
        if created:
            self.append_attachments_bubble(saved)
            self.scroll_to_bottom()

    def handle_link(self):
        if not self._has_context():
            QtWidgets.QMessageBox.warning(self, "No conversation", "Select a conversation first.")
            return

        url, ok = QtWidgets.QInputDialog.getText(self, "Send link", "URL:")
        if not ok or not url.strip():
            return
        url = url.strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "https://" + url

        payload = {
            "sender_id": self.current_user_id,
            "receiver_id": self.other_user_id,
            "conversation_id": self.conversation_id,
            "content": url,
            "message_type": "link",
            "priority": "normal",
            "status": "sent",
            "is_read": False,
        }
        created = self.data_manager.create_message(payload)
        if created:
            self.append_link_bubble(url)
            self.scroll_to_bottom()

    def append_text_bubble(self, message):
        is_sender = (message.get("sender_id") == self.current_user_id)
        bubble = QtWidgets.QLabel(message.get("content", ""))
        bubble.setWordWrap(True)
        bubble.setStyleSheet(
            "QLabel {"
            f"background-color: {'#76a979' if is_sender else '#e0e0e0'};"
            f"color: {'white' if is_sender else 'black'};"
            "border-radius: 10px; padding: 10px; max-width: 320px;}"
        )

        row = QtWidgets.QHBoxLayout()
        row.setContentsMargins(10, 5, 10, 5)
        if is_sender:
            row.addStretch()
            row.addWidget(bubble)
        else:
            row.addWidget(bubble)
            row.addStretch()

        holder = QtWidgets.QWidget()
        holder.setLayout(row)
        self.ui.messages_layout.insertWidget(self.ui.messages_layout.count() - 1, holder)

    def append_attachments_bubble(self, paths):
        links_col = QtWidgets.QVBoxLayout()
        for p in paths:
            url = QUrl.fromLocalFile(os.path.abspath(p)).toString()
            link = QtWidgets.QLabel(f"<a href='{url}'>{os.path.basename(p)}</a>")
            link.setOpenExternalLinks(True)
            links_col.addWidget(link)

        inner = QtWidgets.QWidget()
        inner.setLayout(links_col)
        inner.setStyleSheet("QWidget {background-color:#76a979; color:white; border-radius:10px; padding:10px;}")

        row = QtWidgets.QHBoxLayout()
        row.setContentsMargins(10, 5, 10, 5)
        row.addStretch()
        row.addWidget(inner)

        holder = QtWidgets.QWidget()
        holder.setLayout(row)
        self.ui.messages_layout.insertWidget(self.ui.messages_layout.count() - 1, holder)

    def append_link_bubble(self, url):
        label = QtWidgets.QLabel(f"<a href='{url}'>{url}</a>")
        label.setOpenExternalLinks(True)
        label.setStyleSheet("QLabel {background-color:#76a979; color:white; border-radius:10px; padding:10px;}")

        row = QtWidgets.QHBoxLayout()
        row.setContentsMargins(10, 5, 10, 5)
        row.addStretch()
        row.addWidget(label)

        holder = QtWidgets.QWidget()
        holder.setLayout(row)
        self.ui.messages_layout.insertWidget(self.ui.messages_layout.count() - 1, holder)

    def clear_messages(self):
        # Remove all widgets from messages_layout except the final stretch
        while self.ui.messages_layout.count() > 1:
            item = self.ui.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def scroll_to_bottom(self):
        bar = self.ui.scroll_area.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _has_context(self) -> bool:
        return all([
            self.data_manager is not None,
            self.current_user_id is not None,
            self.other_user_id is not None,
            self.conversation_id is not None
        ])
>>>>>>> Stashed changes
