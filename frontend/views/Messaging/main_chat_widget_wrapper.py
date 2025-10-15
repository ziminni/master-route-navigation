from PyQt6 import QtCore, QtWidgets
from .data_manager import DataManager
from .inquiry import InquiryDialog
from .main_chat_widget import MainChatWidget
from .msg_main import Ui_MainWindow  # import your existing Ui_MainWindow


class MainChatWidgetWrapper(QtWidgets.QWidget):
    """
    QWidget-based wrapper for Ui_MainWindow.
    Allows you to use the UI inside other widgets (e.g. stacked layouts or tabs)
    without needing a QMainWindow parent.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self._build_ui()

    def _build_ui(self):
        """Initializes the UI components inside this QWidget."""
        # Create a dummy QMainWindow to satisfy setupUi(), then reparent its central widget
        dummy_main = QtWidgets.QMainWindow()
        self.ui.setupUi(dummy_main)

        # Extract the central widget and adopt it as this wrapper’s layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ui.centralwidget)

        # Keep data manager and context setup here
        self.data_manager = DataManager()
        self.current_user_id = 1  # Default user ID

        # Hook up button actions
        self.ui.create_inquiry.clicked.connect(self.open_inquiry_dialog)
        self.ui.push_all.clicked.connect(lambda: self.filter_chats("all"))
        self.ui.push_unread.clicked.connect(lambda: self.filter_chats("unread"))
        self.ui.push_comm.clicked.connect(lambda: self.filter_chats("comm"))
        self.ui.push_group.clicked.connect(lambda: self.filter_chats("group"))
        self.ui.search_recipt.textChanged.connect(self.search_chats)
        self.ui.chat_list.itemClicked.connect(self.on_chat_selected)

        # Initial load
        self.current_filter = "all"
        self.filter_chats(self.current_filter)
        self.start_inquiry_realtime_updates()

    # === Reuse logic from MainApp ===
    def open_inquiry_dialog(self):
        dialog = InquiryDialog(self)
        if dialog.exec():
            inquiry_data = dialog.get_inquiry_data()
            if inquiry_data:
                created_inquiry = self.data_manager.create_inquiry(inquiry_data)
                if created_inquiry:
                    print(f"Inquiry Created! ID: {created_inquiry['id']}")
                    self.filter_chats(self.current_filter)

    def filter_chats(self, filter_type: str):
        self.current_filter = filter_type
        self.ui.chat_list.clear()
        self.data_manager.reload_data()

        all_users = {user['id']: user for user in self.data_manager.data.get("users", [])}
        current_user_id = self.current_user_id

        for conv in self.data_manager.data.get("conversations", []):
            participants = conv.get("participants", [])
            other_users = [all_users.get(uid) for uid in participants if uid != current_user_id]

            display_name = ", ".join([u['name'] for u in other_users if u]) or "Self Chat"

            # Store conversation ID AND participant info
            item = QtWidgets.QListWidgetItem(display_name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, {
                "conversation_id": conv.get("id"),
                "participants": participants,
                "other_users": other_users  # full user dicts
            })
            self.ui.chat_list.addItem(item)


    def search_chats(self, text: str):
        query = text.lower()
        for i in range(self.ui.chat_list.count()):
            item = self.ui.chat_list.item(i)
            item.setHidden(query not in item.text().lower())

    def on_chat_selected(self, item):
        data = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if not data:
            return

        conversation_id = data.get("conversation_id")
        other_users = data.get("other_users", [])

        # Update chat header
        names = ", ".join([u['name'] for u in other_users])
        self.ui.chat_box.ui.name_header.setText(names or "Chat")
        self.ui.chat_box.ui.header2_accesslvl.setText("Active chat")

        # Update contact info panel
        if other_users:
            user = other_users[0]  # assume one-on-one chat
            contact_text = (
                f"Name: {user.get('name')}\n"
                f"Role: {user.get('role', 'Unknown').title()}\n"
                f"Department: {user.get('department', 'Unknown')}\n"
                f"Email: {user.get('email', 'Unknown')}\n"
                f"Status: {user.get('status', 'offline').title()}\n"
                f"Last seen: {user.get('last_seen', 'Unknown')}"
            )
        else:
            contact_text = "No contact info available"
        
        self.ui.contact_details.setText(contact_text)

        # Show message/chat widget
        self.ui.message_widget.hide()
        self.ui.chat_box.show()


    def start_inquiry_realtime_updates(self):
        self.inquiry_timer = QtCore.QTimer(self)
        self.inquiry_timer.setInterval(1500)
        self.inquiry_timer.timeout.connect(lambda: self.filter_chats(self.current_filter))
        self.inquiry_timer.start()
