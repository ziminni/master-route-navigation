import os
from PyQt6 import QtCore, QtWidgets
from .data_manager import DataManager
from .inquiry import InquiryDialog
from .msg_main import Ui_MainWindow


class MainChatWidgetWrapper(QtWidgets.QWidget):
    """
    QWidget-based chat system wrapper that displays conversations (not inquiries).
    Automatically listens for JSON data changes and refreshes in real-time.
    """
    def __init__(
        self,
        parent=None,
        current_user_id=None,
        current_username=None,
        current_token=None
    ):
        super().__init__(parent)
        self.ui = Ui_MainWindow()

        # Setup UI inside this widget
        dummy_main = QtWidgets.QMainWindow()
        self.ui.setupUi(dummy_main)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ui.centralwidget)

        # Store user info from parent/session
        self.current_user_id = current_user_id
        self.current_username = current_username
        self.current_token = current_token

        # Core data manager with user context
        self.data_manager = DataManager(
            username=self.current_username,
            token=self.current_token
        )
        self.current_filter = "all"

        # Connect UI events
        self.ui.create_inquiry.clicked.connect(self.open_inquiry_dialog)
        self.ui.push_all.clicked.connect(lambda: self.filter_chats("all"))
        self.ui.push_unread.clicked.connect(lambda: self.filter_chats("unread"))
        self.ui.push_comm.clicked.connect(lambda: self.filter_chats("comm"))
        self.ui.push_group.clicked.connect(lambda: self.filter_chats("group"))
        self.ui.search_recipt.textChanged.connect(self.search_chats)
        self.ui.chat_list.itemClicked.connect(self.on_chat_selected)

        # Initial load
        self.filter_chats(self.current_filter)
        self.start_realtime_updates()

    def getDataManager(self):
        return self.data_manager

    # === Inquiry creation ===
    def open_inquiry_dialog(self):
        dialog = InquiryDialog(self)
        if dialog.exec():
            inquiry_data = dialog.get_inquiry_data()
            if inquiry_data:
                created_inquiry = self.data_manager.create_inquiry(inquiry_data)
                if created_inquiry:
                    print(f"✅ Inquiry Created! ID: {created_inquiry['id']}")
                    self.filter_chats(self.current_filter)
                    self.last_modified_time = self._get_data_file_mtime()


    # === Conversation List ===
    def filter_chats(self, filter_type: str):
        self.current_filter = filter_type
        self.ui.chat_list.clear()
        self.data_manager.reload_data()

        for conv in self.data_manager.data.get("conversations", []):
            is_group = conv.get("is_group", False)
            if filter_type == "group" and not is_group:
                continue
            if filter_type == "comm" and is_group:
                continue
            if filter_type == "unread" and not self._conversation_has_unread(conv.get("id")):
                continue

            label = self._display_name_for_conversation(conv)
            item = QtWidgets.QListWidgetItem(label)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, {
                "type": "conversation",
                "conversation_id": conv.get("id"),
                "display_name": label,
            })
            self.ui.chat_list.addItem(item)


    # === Search Chat ===
    def search_chats(self, text: str):
        query = (text or "").strip().lower()
        for i in range(self.ui.chat_list.count()):
            item = self.ui.chat_list.item(i)
            data = item.data(QtCore.Qt.ItemDataRole.UserRole) or {}
            name = (data.get("display_name") or item.text()).lower()
            item.setHidden(bool(query) and query not in name)


    # === Chat Selection ===
    def on_chat_selected(self, item):
        data = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if not data or data.get("type") != "conversation":
            return

        conv_id = data.get("conversation_id")
        conversation = self.data_manager.get_conversation(conv_id)
        if not conversation:
            print(f"⚠️ Conversation ID {conv_id} not found.")
            return

        if not hasattr(self.ui, "chat_box") or self.ui.chat_box is None:
            print("[ERROR] chat_box not found in UI.")
            return

        try:
            self.ui.message_widget.hide()
        except Exception:
            pass
        try:
            self.ui.chat_box.show()
        except Exception:
            pass

        if conversation.get("is_group", False):
            self._display_group_chat(conversation, item.text())
            return

        participants = conversation.get("participants", [])
        other_id = next((pid for pid in participants if pid != self.current_user_id), None)
        other_user = self.data_manager.get_user(other_id) if other_id else None

        self._display_private_chat(conversation, other_user)


    # === Group Chat Display ===
    def _display_group_chat(self, conversation, label):
        self.ui.chat_box.ui.name_header.setText(f"Group: {label}")
        self.ui.chat_box.ui.header2_accesslvl.setText(
            f"Group Chat - {len(conversation.get('participants', []))} members"
        )
        self.load_conversation_messages(conversation['id'])
        self.ui.contact_details.setText(
            f"Group Chat\nParticipants: {len(conversation.get('participants', []))}\n"
            f"Last Activity: {conversation.get('last_activity', 'Unknown')}"
        )


    # === Private Chat Display ===
    def _display_private_chat(self, conversation, other_user):
        if not other_user:
            self.ui.chat_box.ui.name_header.setText("Unknown User")
            self.ui.chat_box.ui.header2_accesslvl.setText("Unknown Role")
            self.ui.contact_details.setText("Contact: Unknown")
        else:
            self.ui.chat_box.ui.name_header.setText(other_user.get("name", "Unknown"))
            self.ui.chat_box.ui.header2_accesslvl.setText(
                f"{other_user.get('role', 'Unknown').title()} - {other_user.get('department', 'Unknown')}"
            )
            self.ui.contact_details.setText(
                f"Contact: {other_user.get('name', 'Unknown')}\n"
                f"Role: {other_user.get('role', 'Unknown').title()}\n"
                f"Department: {other_user.get('department', 'Unknown')}\n"
                f"Email: {other_user.get('email', 'Unknown')}"
            )

        self.ui.chat_box.set_context(
            data_manager=self.data_manager,
            current_user_id=self.current_user_id,
            other_user_id=other_user.get("id") if other_user else None,
            conversation_id=conversation['id'],
        )

        self.load_conversation_messages(conversation['id'])


    # === Load Conversation Messages ===
    def load_conversation_messages(self, conversation_id):
        layout = self.ui.chat_box.ui.messages_layout
        while layout.count() > 1:
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        messages = [m for m in self.data_manager.data['messages']
                    if m.get('conversation_id') == conversation_id]
        messages.sort(key=lambda x: x.get('created_at', ''))

        for msg in messages:
            sender_id = msg.get('sender_id')
            content = msg.get('content', '')
            sent_by_me = (sender_id == self.current_user_id)
            self._add_message_bubble(content, sent_by_me)


    # === Message Bubble ===
    def _add_message_bubble(self, text, sent_by_me=False):
        layout = self.ui.chat_box.ui.messages_layout
        bubble_widget = QtWidgets.QWidget()
        bubble_layout = QtWidgets.QHBoxLayout(bubble_widget)
        bubble_layout.setContentsMargins(10, 5, 10, 5)

        bubble = QtWidgets.QLabel(text)
        bubble.setWordWrap(True)
        bubble_style = """
            QLabel {
                background-color: %s;
                color: %s;
                border-radius: 10px;
                padding: 10px;
                max-width: 250px;
            }
        """ % (("#76a979" if sent_by_me else "#e0e0e0"),
               ("white" if sent_by_me else "black"))
        bubble.setStyleSheet(bubble_style)

        if sent_by_me:
            bubble_layout.addStretch()
            bubble_layout.addWidget(bubble)
        else:
            bubble_layout.addWidget(bubble)
            bubble_layout.addStretch()

        layout.insertWidget(layout.count() - 1, bubble_widget)


    # === Real-time File Watcher ===
    def start_realtime_updates(self):
        self.last_modified_time = self._get_data_file_mtime()
        self.refresh_timer = QtCore.QTimer(self)
        self.refresh_timer.setInterval(1500)
        self.refresh_timer.timeout.connect(self._check_data_updates)
        self.refresh_timer.start()

    def _get_data_file_mtime(self):
        try:
            return os.path.getmtime(self.data_manager.data_path)
        except Exception:
            return 0

    def _check_data_updates(self):
        current_mtime = self._get_data_file_mtime()
        if current_mtime != getattr(self, "last_modified_time", 0):
            self.last_modified_time = current_mtime
            print("🔄 JSON changed — refreshing conversation list...")
            self.filter_chats(self.current_filter)

    # === Helpers ===
    def _conversation_has_unread(self, conv_id: int) -> bool:
        msgs = self.data_manager.data.get("messages", [])
        return any(
            m.get("conversation_id") == conv_id and
            m.get("receiver_id") == self.current_user_id and
            not m.get("is_read", False)
            for m in msgs
        )

    def _display_name_for_conversation(self, conv: dict) -> str:
        if conv.get("is_group", False):
            return conv.get("group_name") or f"Group {conv.get('id')}"
        other = next((pid for pid in conv.get("participants", [])
                      if pid != self.current_user_id), None)
        user = self.data_manager.get_user(other)
        return user.get("name", f"User {other}") if user else f"Chat {conv.get('id')}"
