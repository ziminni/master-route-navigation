from PyQt6 import QtWidgets, QtCore
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl
import os
import shutil

from .main_chat import Ui_MainWindow


class MainChatWidget(QtWidgets.QWidget):
    def __init__(self, parent=None, chat_name="Chat"):
        super().__init__(parent)

        # Borderless + responsive container
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("QWidget { border: none; background: transparent; }")
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding
        )

        # Build UI from generated class inside a dummy QMainWindow
        self.window = QtWidgets.QMainWindow()
        self.window.setStyleSheet("QMainWindow { border: none; }")

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.window)

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
                border-radius: 10px;
                border: 1px solid #ccc;
                padding: 10px;
            }
        """)

        # Embed the built centralwidget into this wrapper
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.ui.centralwidget)

        # Header text
        self.ui.name_header.setText(chat_name)

        # Conversation context (must be set by MainApp)
        self.data_manager = None
        self.current_user_id = None
        self.other_user_id = None
        self.conversation_id = None

        # Wire actions
        self.ui.button_send.clicked.connect(self.handle_send)
        self.ui.lineedit_msg.returnPressed.connect(self.handle_send)
        self.ui.button_attachments.clicked.connect(self.handle_attach)
        self.ui.button_link.clicked.connect(self.handle_link)
        self.ui.lineedit_msg.setPlaceholderText("Type a message...")

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