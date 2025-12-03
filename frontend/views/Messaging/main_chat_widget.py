from PyQt6 import QtWidgets, QtCore
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl
import os
import shutil

from .main_chat import Ui_MainWindow


class MainChatWidget(QtWidgets.QWidget):
    searchRequested = QtCore.pyqtSignal()
    deleteRequested = QtCore.pyqtSignal()

    def __init__(self, parent=None, chat_name="Chat"):
        super().__init__(parent)

        # Borderless + responsive container
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("QWidget { border: none; background: transparent; }")
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )

        # Build UI from generated class inside a dummy QMainWindow
        self.window = QtWidgets.QMainWindow()
        self.window.setStyleSheet("QMainWindow { border: none; }")

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.window)

        # Make centralwidget/message_widget flexible and borderless
        self.ui.centralwidget.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.ui.centralwidget.setContentsMargins(0, 0, 0, 0)

        self.ui.message_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.ui.message_widget.setStyleSheet(
            """
            QWidget#message_widget {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #ccc;
                padding: 10px;
            }
        """
        )

        # ✅ NEW: Create header_buttons layout if it doesn't exist
        self._setup_header_buttons()

        # options menu for current chat
        self.options_menu = QtWidgets.QMenu(self)
        self.options_menu.setStyleSheet(
            """
            QMenu {
                background-color: #ffffff;
                border: 1px solid #c0c0c0;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 18px;
                color: #111111;
                background-color: transparent;
            }
            QMenu::item:selected {
                background-color: #003d1f;
                color: #ffffff;
            }
        """
        )
        action_delete = self.options_menu.addAction("Delete conversation")
        action_search = self.options_menu.addAction("Search messages")

        # Just emit signals; wrapper decides what to do
        action_delete.triggered.connect(self.deleteRequested.emit)
        action_search.triggered.connect(self.searchRequested.emit)

        self.ui.toolButton.clicked.connect(self._show_options_menu)

        # Embed the built centralwidget into this wrapper
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.ui.centralwidget)

        # Header text
        self.ui.name_header.setText(chat_name)

        # Conversation context (must be set by MainChatWidgetWrapper)
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

    # ✅ NEW: Setup header buttons layout
    def _setup_header_buttons(self):
        """Create header_buttons layout for white '_' and existing '...'."""
        try:
            header = getattr(self.ui, "header_widget", None)
            name_lbl = getattr(self.ui, "name_header", None)
            menu_btn = getattr(self.ui, "toolButton", None)

            if not header or not menu_btn:
                print("[MainChatWidget] ⚠ header_widget or toolButton not found")
                return

            layout = header.layout()
            if layout is None:
                layout = QtWidgets.QHBoxLayout(header)
            layout.setContentsMargins(16, 0, 12, 0)
            layout.setSpacing(8)

            # make sure name label is on the left
            if name_lbl and name_lbl.parent() is header:
                layout.insertWidget(0, name_lbl)
            layout.addStretch()

            # create white '_' button
            minimize_btn = QtWidgets.QPushButton("_", header)
            minimize_btn.setFixedSize(24, 24)
            minimize_btn.setStyleSheet(
                "QPushButton {"
                "  background-color: transparent;"
                "  color: white;"
                "  border: none;"
                "  font-weight: bold;"
                "  font-size: 16px;"
                "}"
                "QPushButton:hover {"
                "  background-color: rgba(255,255,255,0.15);"
                "  border-radius: 4px;"
                "}"
            )
            layout.addWidget(minimize_btn)

            # move existing 3-dot button to the right of '_'
            menu_btn.setParent(header)
            layout.addWidget(menu_btn)

            # expose '_' for wrapper
            self.ui.btn_minimize = minimize_btn
            self.ui.header_buttons = layout
        except Exception as e:
            print(f"[MainChatWidget] Error setting up header buttons: {e}")

    def set_context(self, data_manager, current_user_id, other_user_id, conversation_id):
        """Provide conversation context so send/attach/link can persist correctly."""
        self.data_manager = data_manager
        self.current_user_id = current_user_id
        self.other_user_id = other_user_id
        self.conversation_id = conversation_id

    def handle_send(self):
        text = self.ui.lineedit_msg.text().strip()

        if not text: return

        print("[CTX]", self.data_manager, self.current_user_id, self.other_user_id, self.conversation_id)
        if not self._has_context():
            QtWidgets.QMessageBox.warning(self, "No conversation", "Select a conversation first.")
            return


        text = self.ui.lineedit_msg.text().strip()
        if not text:
            return

        subject = text[:50] or "Chat message"
        payload = {
            "conversation": self.conversation_id,
            "content": text,
            "subject": subject,
            "priority": "normal",
            "status": "sent",
            "department": "General",
            "message_type": "general",
            "is_broadcast": False,
            "receiver": self.other_user_id,
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
        subject = "Attachments"  # or body[:50]

        payload = {
            "conversation": self.conversation_id,
            "content": body,
            "subject": subject,
            "priority": "normal",
            "status": "sent",
            "department": "General",
            "message_type": "general",
            "is_broadcast": False,
            "receiver": self.other_user_id,
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
            print(url)
            return
        url = url.strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "https://" + url
        subject = "Link"  # or body[:50]

        payload = {
            "conversation": self.conversation_id,
            "content": url,
            "subject": subject,
            "priority": "normal",
            "status": "sent",
            "department": "General",
            "message_type": "general",
            "is_broadcast": False,
            "receiver": self.other_user_id,
        }
        created = self.data_manager.create_message(payload)
        if created:
            self.append_link_bubble(url)
            self.scroll_to_bottom()

    def append_text_bubble(self, message):
        is_sender = (message.get("sender") == self.current_user_id)
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
        return all(
            [
                self.data_manager is not None,
                self.current_user_id is not None,
                self.other_user_id is not None,
                self.conversation_id is not None,
                ]
        )

    def _show_options_menu(self):
        btn = self.ui.toolButton
        pos = btn.mapToGlobal(QtCore.QPoint(0, btn.height()))
        self.options_menu.exec(pos)
