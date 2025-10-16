import sys
from PyQt6 import QtCore, QtGui, QtWidgets
from .inquiry import InquiryDialog
from .data_manager import DataManager
from .main_chat_widget import MainChatWidget  # ✅ Import your wrapper


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1400, 914)
        MainWindow.setWindowTitle("Messaging Center")
        MainWindow.setMinimumSize(1980, 1080)

        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)

        # Main layout
        main_layout = QtWidgets.QVBoxLayout(self.centralwidget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # # ===== Header =====
        # self.header = Header(parent=self.centralwidget)
        # self.header.setFixedHeight(84)
        # main_layout.addWidget(self.header)

        # ===== Content area =====
        content_widget = QtWidgets.QWidget(parent=self.centralwidget)
        content_layout = QtWidgets.QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 16, 0, 16)
        content_layout.setSpacing(16)

<<<<<<< Updated upstream
        # # ===== Sidebar placeholder =====
=======
        # ===== Sidebar placeholder =====
>>>>>>> Stashed changes
        # self.sidebar_container = QtWidgets.QWidget(parent=content_widget)
        # self.sidebar_container.setFixedWidth(250)
        # self.sidebar_container.setObjectName("sidebar_container")
        # self.sidebar_container_layout = QtWidgets.QVBoxLayout(self.sidebar_container)
        # self.sidebar_container_layout.setContentsMargins(0, 0, 0, 0)
        # self.sidebar_container_layout.setSpacing(0)
        # content_layout.addWidget(self.sidebar_container)

        # ===== Chat Info Panel =====
        self.chat_info = QtWidgets.QWidget(parent=content_widget)
        self.chat_info.setMinimumWidth(231)
        self.chat_info.setMaximumWidth(280)
        self.chat_info.setObjectName("chat_info")
        self.chat_info.setStyleSheet("""
            QWidget#chat_info {
                background-color: white;
                border-radius: 16px;
                border: 1px solid #e0e0e0;
            }
        """)
        chat_layout = QtWidgets.QVBoxLayout(self.chat_info)
        chat_layout.setContentsMargins(10, 10, 10, 10)
        chat_layout.setSpacing(10)

        # Chat header
        chat_header_layout = QtWidgets.QHBoxLayout()
        self.label_2 = QtWidgets.QLabel("Chats")
        self.label_2.setFont(QtGui.QFont("Arial", 18))
        chat_header_layout.addWidget(self.label_2)
        chat_header_layout.addStretch()

        self.push_edit = QtWidgets.QPushButton("Edit")
        self.push_edit.setStyleSheet("""
            QPushButton {
                color: black;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #005a2e;
                color: white;
            }
            QPushButton:pressed {
                background-color: #002d17;
            }
        """)
        chat_header_layout.addWidget(self.push_edit)
        chat_layout.addLayout(chat_header_layout)

        # Search
        self.search_recipt = QtWidgets.QLineEdit()
        self.search_recipt.setPlaceholderText("Search conversations...")
        self.search_recipt.setStyleSheet("""
            QLineEdit {
                background-color: #f5f5f5;
                border: 1px solid #cfcfcf;
                border-radius: 15px;
                padding: 6px 12px;
                font-size: 13px;
            }
        """)
        chat_layout.addWidget(self.search_recipt)

        # Separator
        self.line = QtWidgets.QFrame()
        self.line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        chat_layout.addWidget(self.line)

        # Filter buttons
        filter_layout = QtWidgets.QHBoxLayout()
        button_style = """
            QPushButton {
                color: black;
                border: none;
                border-radius: 5px;
                font-size: 12px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #005a2e;
                color: white;
            }
            QPushButton:pressed {
                background-color: #002d17;
            }
        """
        self.push_unread = QtWidgets.QPushButton("Unread")
        self.push_unread.setStyleSheet(button_style)
        filter_layout.addWidget(self.push_unread)

        self.push_all = QtWidgets.QPushButton("All")
        self.push_all.setStyleSheet(button_style)
        filter_layout.addWidget(self.push_all)

        self.push_comm = QtWidgets.QPushButton("Comm")
        self.push_comm.setStyleSheet(button_style)
        filter_layout.addWidget(self.push_comm)

        self.push_group = QtWidgets.QPushButton("Group")
        self.push_group.setStyleSheet(button_style)
        filter_layout.addWidget(self.push_group)
        chat_layout.addLayout(filter_layout)

        # Chat list
        self.chat_list = QtWidgets.QListWidget()
        self.chat_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: transparent;
            }
            QListWidget::item {
                padding: 10px 12px;
                border: none;
            }
            QListWidget::item:hover {
                background-color: #f1f5f3;
                border-radius: 8px;
            }
            QListWidget::item:selected:active {
                background-color: #e6efe9;
                color: #0f172a;
                border-radius: 8px;
            }
            QListWidget::item:selected:inactive {
                background-color: #eef4f0;
                color: #0f172a;
                border-radius: 8px;
            }
        """)
        self.chat_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        chat_layout.addWidget(self.chat_list)

        content_layout.addWidget(self.chat_info)

        # ===== Message Widget =====
        self.message_widget = QtWidgets.QWidget(parent=content_widget)
        self.message_widget.setObjectName("message_widget")
        self.message_widget.setStyleSheet("""
            QWidget#message_widget {
                background-color: white;
                border-radius: 16px;
                border: 1px solid #e0e0e0;
            }
        """)
        message_layout = QtWidgets.QVBoxLayout(self.message_widget)

        # New recipient label (hidden by default)
        self.recipient_label = QtWidgets.QLabel()
        self.recipient_label.setFont(QtGui.QFont("Arial", 18, QtGui.QFont.Weight.Bold))
        self.recipient_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.recipient_label.setVisible(False)
        message_layout.addWidget(self.recipient_label)

        # Default message label
        self.label_8 = QtWidgets.QLabel("No message found!")
        self.label_8.setFont(QtGui.QFont("Arial", 20))
<<<<<<< Updated upstream
        self.label_8.setStyleSheet("color: black;")
=======
>>>>>>> Stashed changes
        self.label_8.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        message_layout.addWidget(self.label_8)

        content_layout.addWidget(self.message_widget)
        self.message_widget.show()

<<<<<<< Updated upstream
        # ===== Load MainChatWidget =====
        try:
            self.chat_box = MainChatWidget(parent=content_widget, chat_name="Welcome Chat")
=======
        try:
            self.chat_box = MainChatWidget(parent=content_widget, chat_name="Welcome Chat")
            
>>>>>>> Stashed changes
            content_layout.addWidget(self.chat_box)
            self.chat_box.hide()
            self.chat_info.setFixedWidth(260)
        except Exception as e:
            print(f"Error loading chat widget: {e}")
            error_label = QtWidgets.QLabel(f"Failed to load chat: {e}")
            error_label.setStyleSheet("color: red; font-weight: bold;")
            content_layout.addWidget(error_label)

<<<<<<< Updated upstream
=======

>>>>>>> Stashed changes
        # ===== Contact Info Panel =====
        self.contact_info = QtWidgets.QWidget(parent=content_widget)
        self.contact_info.setFixedWidth(250)
        self.contact_info.setObjectName("contact_info")
        self.contact_info.setStyleSheet("""
            QWidget#contact_info {
                background-color: white;
                border-radius: 16px;
                border: 1px solid #e0e0e0;
            }
        """)
        contact_layout = QtWidgets.QVBoxLayout(self.contact_info)
        contact_layout.setContentsMargins(10, 10, 10, 10)
        contact_layout.setSpacing(10)

        self.label_9 = QtWidgets.QLabel("Contact Info")
        self.label_9.setFont(QtGui.QFont("Arial", 18))
        contact_layout.addWidget(self.label_9)

        self.line_2 = QtWidgets.QFrame()
        self.line_2.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        contact_layout.addWidget(self.line_2)

        # Scroll area
        self.contact_scroll = QtWidgets.QScrollArea()
        self.contact_scroll.setWidgetResizable(True)
        self.contact_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.contact_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.contact_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        # Details label (top-left)
        self.contact_details = QtWidgets.QLabel("Select a conversation\nto view contact details")
        self.contact_details.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignLeft)
        self.contact_details.setWordWrap(True)
        self.contact_details.setStyleSheet("color:#666; font-size:14px; padding:5px; line-height:1.4;")
        self.contact_details.setMinimumWidth(200)

        # Wrap label in a top-aligned container
        self.contact_container = QtWidgets.QWidget()
        self.contact_container_layout = QtWidgets.QVBoxLayout(self.contact_container)
        self.contact_container_layout.setContentsMargins(0, 0, 0, 0)
        self.contact_container_layout.setSpacing(6)
        self.contact_container_layout.addWidget(self.contact_details, alignment=QtCore.Qt.AlignmentFlag.AlignTop)
        self.contact_container_layout.addStretch()

        self.contact_scroll.setWidget(self.contact_container)
        self.contact_scroll.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        contact_layout.addWidget(self.contact_scroll)

        # Push button to bottom
        contact_layout.addStretch()

        # Create Inquiry button at the bottom (single source)
        self.create_inquiry = QtWidgets.QPushButton("Create an Inquiry")
        self.create_inquiry.setObjectName("create_inquiry")
        self.create_inquiry.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed
        )
        self.create_inquiry.setFixedHeight(44)
        self.create_inquiry.setStyleSheet("""
            QPushButton#create_inquiry {
                background-color: #003d1f;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 10px;
                padding: 8px 20px;
                font-size: 14px;
            }
            QPushButton#create_inquiry:hover { background-color: #005a2e; }
            QPushButton#create_inquiry:pressed { background-color: #002d17; }
        """)
        contact_layout.addWidget(self.create_inquiry)

        content_layout.addWidget(self.contact_info)

        # Mount content in central widget
        main_layout.addWidget(content_widget)
        MainWindow.setCentralWidget(self.centralwidget)

<<<<<<< Updated upstream


class MainApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Data manager
        self.data_manager = DataManager()
        self.current_user_id = 1  # Carlos Fidel Castro
=======
    # def add_sidebar(self, sidebar_widget):
    #     sidebar_widget.setParent(self.sidebar_container)
    #     self.sidebar_container_layout.addWidget(sidebar_widget)

    # def update_sidebar_width(self, is_collapsed):
    #     if is_collapsed:
    #         self.sidebar_container.setFixedWidth(60)
    #     else:
    #         self.sidebar_container.setFixedWidth(250)


class MainApp(QtWidgets.QMainWindow):
    def __init__(self, username="", roles=None, primary_role="", token="", parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Store user session data
        self.username = username
        self.roles = roles or []  # prevent mutable default
        self.primary_role = primary_role
        self.token = token

        # Data manager
        self.data_manager = DataManager()
        # Get current user ID from session data - we'll need to map username to user ID
        self.current_user_id = self._get_user_id_from_session()
>>>>>>> Stashed changes

        # # Sidebar
        # self.sidebar = Sidebar()
        # self.ui.add_sidebar(self.sidebar)
        # self.sidebar.toggle_btn.clicked.connect(self.on_sidebar_toggle)

        # Header actions
        # self.connect_header_actions()

        # Buttons
        self.ui.create_inquiry.clicked.connect(self.open_inquiry_dialog)
        self.ui.push_all.clicked.connect(lambda: self.filter_chats("all"))
        self.ui.push_unread.clicked.connect(lambda: self.filter_chats("unread"))
        self.ui.push_comm.clicked.connect(lambda: self.filter_chats("comm"))
        self.ui.push_group.clicked.connect(lambda: self.filter_chats("group"))
        self.ui.search_recipt.textChanged.connect(self.search_chats)
        self.ui.chat_list.itemClicked.connect(self.on_chat_selected)

<<<<<<< Updated upstream
=======
        # ===== Load MainChatWidget with session data =====
        try:
            self.chat_box = MainChatWidget(
                username=self.username,
                roles=self.roles,
                primary_role=self.primary_role,
                token=self.token,
                parent=self, 
                chat_name="Welcome Chat"
            )
            # The chat_box will be added to the UI later when needed
            self.chat_box.hide()
        except Exception as e:
            print(f"Error loading chat widget: {e}")

>>>>>>> Stashed changes
        # Initial load
        self.current_filter = "all"
        self.load_chats_from_database()
        self.load_user_info()
        self.filter_chats(self.current_filter)

        # Realtime updates (rebuild current filter view)
        self.start_inquiry_realtime_updates()

<<<<<<< Updated upstream
=======
    def _get_user_id_from_session(self):
        """Get user ID from session data by matching username"""
        if not self.username:
            return 1  # Fallback to default user ID
        
        # Look for user in data manager by username
        for user in self.data_manager.data.get('users', []):
            if user.get('name') == self.username or user.get('email', '').split('@')[0] == self.username:
                return user.get('id', 1)
        
        # If not found, create a new user entry based on session data
        user_data = {
            'name': self.username,
            'email': f"{self.username}@cmu.edu.ph",
            'role': self.primary_role,
            'department': 'Computer Science',  # Default department
            'status': 'online',
            'last_seen': self.data_manager._get_current_timestamp()
        }
        
        created_user = self.data_manager.create_user(user_data)
        return created_user.get('id', 1) if created_user else 1

>>>>>>> Stashed changes
    # def connect_header_actions(self):
    #     actions = self.ui.header.profile_menu.actions()
    #     for action in actions:
    #         if action.text() == "My Profile":
    #             action.triggered.connect(self.show_profile)
    #         elif action.text() == "Log Out":
    #             action.triggered.connect(self.logout)

    def _get_or_create_conversation(self, uid_a: int, uid_b: int):
        for conv in self.data_manager.data.get('conversations', []):
            if not conv.get('is_group', False) and set(conv.get('participants', [])) == {uid_a, uid_b}:
                return conv
        conv_data = {
            'participants': [uid_a, uid_b],
            'is_group': False,
            'created_at': self.data_manager._get_current_timestamp(),
            'last_activity': self.data_manager._get_current_timestamp(),
        }
        conv = self.data_manager.create_conversation(conv_data)
        if conv:
            self.add_conversation_to_chat_list(conv)
        return conv

    def show_profile(self):
        QtWidgets.QMessageBox.information(self, "Profile", "Profile feature coming soon!")

    def logout(self):
        reply = QtWidgets.QMessageBox.question(
            self,
            "Logout",
            "Are you sure you want to logout?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self.close()

    def open_inquiry_dialog(self):
<<<<<<< Updated upstream
        print("[DEBUG] open_inquiry_dialog() triggered")
        try:
            dialog = InquiryDialog(self)
            print("[DEBUG] InquiryDialog created:", dialog)
            result = dialog.exec()
            print("[DEBUG] Dialog exec() result:", result)
            if result:
                inquiry_data = dialog.get_inquiry_data()
                if inquiry_data:
                    created_inquiry = self.data_manager.create_inquiry(inquiry_data)
                    if created_inquiry:
                        print(f"Inquiry Created! ID: {created_inquiry['id']}")
                        self.filter_chats(self.current_filter)
                    else:
                        print("Failed to create inquiry")
        except Exception as e:
            print("[ERROR] open_inquiry_dialog failed:", e)

=======
        dialog = InquiryDialog(self)
        if dialog.exec():
            inquiry_data = dialog.get_inquiry_data()
            if inquiry_data:
                created_inquiry = self.data_manager.create_inquiry(inquiry_data)
                if created_inquiry:
                    print(f"Inquiry Created! ID: {created_inquiry['id']}")
                    self.filter_chats(self.current_filter)
                else:
                    print("Failed to create inquiry")
>>>>>>> Stashed changes

    def filter_chats(self, filter_type: str):
        self.current_filter = filter_type
        self.ui.chat_list.clear()
        self.data_manager.reload_data()

        # Conversations
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

        # Inquiries (All/Unread)
        if filter_type in ("all", "unread"):
            cur = self.data_manager.get_user(self.current_user_id) or {}
            role = cur.get("role", "student")
            if role == "faculty":
                inquiries = [i for i in self.data_manager.data.get("inquiries", []) if i.get("faculty_id") == self.current_user_id]
            else:
                inquiries = [i for i in self.data_manager.data.get("inquiries", []) if i.get("student_id") == self.current_user_id]
            if filter_type == "unread":
                inquiries = [i for i in inquiries if (i.get("status") or "").lower() == "pending"]

            for inq in inquiries:
                label = self._display_name_for_inquiry(inq)
                item = QtWidgets.QListWidgetItem(label)
                item.setData(QtCore.Qt.ItemDataRole.UserRole, {
                    "type": "inquiry",
                    "inquiry_id": inq.get("id"),
                    "display_name": label,
                    "subject": inq.get("subject", ""),
                })
                self.ui.chat_list.addItem(item)

    def search_chats(self, text: str):
        query = (text or "").strip().lower()
        for i in range(self.ui.chat_list.count()):
            item = self.ui.chat_list.item(i)
            data = item.data(QtCore.Qt.ItemDataRole.UserRole) or {}
            name = (data.get("display_name") or item.text()).lower()
            subj = (data.get("subject") or "").lower()
            item.setHidden(bool(query) and (query not in name and query not in subj))

    def on_chat_selected(self, item):
        data = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if isinstance(data, dict) and data.get("type") == "inquiry":
            self.show_inquiry(data["inquiry_id"])
            return

        chat_name = item.text()
        self.ui.message_widget.hide()
        self.ui.chat_box.show()

        conversation = self.get_conversation_by_chat_name(chat_name)
        if not conversation:
            self.ui.chat_box.ui.name_header.setText(f"Chat with {chat_name}")
            self.ui.chat_box.ui.header2_accesslvl.setText("Unknown User")
            self.ui.contact_details.setText(f"Contact: {chat_name}\nStatus: Online\nLast seen: Now")
            return

        if conversation.get('is_group', False):
            self.ui.chat_box.ui.name_header.setText(f"Group: {chat_name}")
            self.ui.chat_box.ui.header2_accesslvl.setText(
                f"Group Chat - {len(conversation.get('participants', []))} participants"
            )
            group_text = (
                f"Group Chat\nParticipants: {len(conversation.get('participants', []))}\n"
                f"Last Activity: {conversation.get('last_activity', 'Unknown')}"
            )
            self.ui.contact_details.setText(group_text)
            self.load_conversation_messages(conversation['id'])
            return

        # Individual conversation
        other_participant_id = next((pid for pid in conversation.get('participants', []) if pid != self.current_user_id), None)
        if not other_participant_id:
            return

        other_user = self.data_manager.get_user(other_participant_id)
        if not other_user:
            self.ui.chat_box.ui.name_header.setText(f"Chat with {chat_name}")
            self.ui.chat_box.ui.header2_accesslvl.setText("Unknown User")
            self.ui.contact_details.setText(f"Contact: {chat_name}\nStatus: Unknown")
            return

        status = other_user.get('status', 'offline')
        last_seen = other_user.get('last_seen', 'Unknown')
        department = other_user.get('department', 'Unknown')
        role = other_user.get('role', 'Unknown')

        self.ui.chat_box.ui.name_header.setText(other_user['name'])
        self.ui.chat_box.ui.header2_accesslvl.setText(f"{role.title()} - {department}")

        self.ui.chat_box.set_context(
            data_manager=self.data_manager,
            current_user_id=self.current_user_id,
            other_user_id=other_participant_id,
            conversation_id=conversation['id'],
        )

        self.load_conversation_messages(conversation['id'])

        contact_text = (
            f"Contact: {other_user['name']}\n"
            f"Role: {role.title()}\n"
            f"Department: {department}\n"
            f"Status: {status.title()}\n"
            f"Last seen: {last_seen}"
        )
        self.ui.contact_details.setText(contact_text)

    def create_new_conversation(self, recipient):
        existing_conversation = None
        for conv in self.data_manager.data['conversations']:
            participants = conv.get('participants', [])
            if (self.current_user_id in participants and
                recipient['id'] in participants and
                not conv.get('is_group', False)):
                existing_conversation = conv
                break

        if existing_conversation:
            conversation = existing_conversation
        else:
            conversation_data = {
                'participants': [self.current_user_id, recipient['id']],
                'is_group': False,
                'created_at': self.data_manager._get_current_timestamp(),
                'last_activity': self.data_manager._get_current_timestamp()
            }
            conversation = self.data_manager.create_conversation(conversation_data)

        if conversation:
            inquiry_message = {
                'sender_id': self.current_user_id,
                'receiver_id': recipient['id'],
                'conversation_id': conversation['id'],
                'content': f"Hello! I would like to inquire about {recipient['department']} matters.",
                'message_type': 'inquiry',
                'priority': 'normal',
                'status': 'sent',
                'is_read': False
            }
            self.data_manager.create_message(inquiry_message)
            self.show_chat_with_recipient(recipient, conversation)
            self.add_conversation_to_chat_list(conversation)

    def show_chat_with_recipient(self, recipient, conversation):
        self.ui.message_widget.hide()
        self.ui.chat_box.show()

        self.ui.chat_box.ui.name_header.setText(recipient['name'])
        self.ui.chat_box.ui.header2_accesslvl.setText(f"{recipient['role'].title()} - {recipient['department']}")

        self.ui.chat_box.set_context(
            data_manager=self.data_manager,
            current_user_id=self.current_user_id,
            other_user_id=recipient['id'],
            conversation_id=conversation['id'],
        )

        self.load_conversation_messages(conversation['id'])
        self.ui.contact_details.setText(
            f"Contact: {recipient['name']}\n"
            f"Role: {recipient['role'].title()}\n"
            f"Department: {recipient['department']}\n"
            f"Email: {recipient['email']}"
        )

    def load_conversation_messages(self, conversation_id):
        self.clear_messages()
        messages = [m for m in self.data_manager.data['messages'] if m.get('conversation_id') == conversation_id]
        messages.sort(key=lambda x: x.get('created_at', ''))
        for msg in messages:
            self.add_message_bubble(msg)

    def clear_messages(self):
        while self.ui.chat_box.ui.messages_layout.count() > 1:
            child = self.ui.chat_box.ui.messages_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def add_message_bubble(self, message):
        sender_id = message.get('sender_id')
        content = message.get('content', '')
        is_sender = (sender_id == self.current_user_id)

        bubble_widget = QtWidgets.QWidget()
        bubble_layout = QtWidgets.QHBoxLayout(bubble_widget)
        bubble_layout.setContentsMargins(10, 5, 10, 5)

        bubble = QtWidgets.QLabel(content)
        if is_sender:
            bubble.setStyleSheet("""
                QLabel {
                    background-color: #76a979;
                    color: white;
                    border-radius: 10px;
                    padding: 10px;
                    max-width: 250px;
                }
            """)
            bubble_layout.addStretch()
            bubble_layout.addWidget(bubble)
        else:
            bubble.setStyleSheet("""
                QLabel {
                    background-color: #e0e0e0;
                    color: black;
                    border-radius: 10px;
                    padding: 10px;
                    max-width: 250px;
                }
            """)
            bubble_layout.addWidget(bubble)
            bubble_layout.addStretch()

        self.ui.chat_box.ui.messages_layout.insertWidget(
            self.ui.chat_box.ui.messages_layout.count() - 1,
            bubble_widget
        )

    def add_conversation_to_chat_list(self, conversation):
        if conversation.get('is_group', False):
            chat_name = conversation.get('group_name', f"Group {conversation['id']}")
        else:
            other_participant_id = next((pid for pid in conversation.get('participants', []) if pid != self.current_user_id), None)
            if other_participant_id:
                other_user = self.data_manager.get_user(other_participant_id)
                chat_name = other_user.get('name', f"User {other_participant_id}") if other_user else f"User {other_participant_id}"
            else:
                chat_name = f"Chat {conversation['id']}"

        item = QtWidgets.QListWidgetItem(chat_name)
        item.setData(
            QtCore.Qt.ItemDataRole.UserRole,
            {
                "type": "conversation",
                "conversation_id": conversation.get("id"),
                "display_name": chat_name,
            },
        )
        self.ui.chat_list.addItem(item)

    def update_sidebar_container(self):
        self.ui.update_sidebar_width(self.sidebar.is_collapsed)

    def on_sidebar_toggle(self):
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(50, self.update_sidebar_container)

    def load_chats_from_database(self):
        self.ui.chat_list.clear()

    def load_user_info(self):
        current_user = self.data_manager.get_user(self.current_user_id)
        if current_user:
            print(f"Current user: {current_user['name']} ({current_user['role']})")

    def get_conversation_by_chat_name(self, chat_name):
        for conv in self.data_manager.data['conversations']:
            if conv.get('is_group', False):
                if conv.get('group_name') == chat_name:
                    return conv
            else:
                other_participant_id = next((pid for pid in conv.get('participants', []) if pid != self.current_user_id), None)
                if other_participant_id:
                    other_user = self.data_manager.get_user(other_participant_id)
                    if other_user and other_user.get('name') == chat_name:
                        return conv
        return None

    def show_inquiry(self, inquiry_id: int):
        self.data_manager.reload_data()

        inquiry = next((i for i in self.data_manager.data.get("inquiries", []) if i.get("id") == inquiry_id), None)
        if not inquiry:
            return

        self.ui.message_widget.hide()
        self.ui.chat_box.show()

        subject = inquiry.get("subject", f"Inquiry #{inquiry_id}")
        status = (inquiry.get("status") or "unknown").title()
        priority = (inquiry.get("priority") or "normal").title()
        self.ui.chat_box.ui.name_header.setText(subject)
        self.ui.chat_box.ui.header2_accesslvl.setText(f"Status: {status} • Priority: {priority}")

        self.clear_messages()
        student_id = inquiry.get("student_id")
        faculty_id = inquiry.get("faculty_id")

        self.add_message_bubble({
            "sender_id": student_id,
            "content": inquiry.get("description", "")
        })
        if inquiry.get("response"):
            self.add_message_bubble({
                "sender_id": faculty_id,
                "content": inquiry["response"]
            })

        other_id = faculty_id if self.current_user_id == student_id else student_id
        conv = self._get_or_create_conversation(student_id, faculty_id)
        if conv and other_id:
            self.ui.chat_box.set_context(
                data_manager=self.data_manager,
                current_user_id=self.current_user_id,
                other_user_id=other_id,
                conversation_id=conv['id'],
            )

        other = self.data_manager.get_user(other_id) if other_id is not None else None
        if other:
            self.ui.contact_details.setText(
                f"Contact: {other.get('name','Unknown')}\n"
                f"Role: {other.get('role','').title()}\n"
                f"Department: {other.get('department','Unknown')}\n"
                f"Email: {other.get('email','Unknown')}"
            )
        else:
            self.ui.contact_details.setText("Contact: Unknown")

    def start_inquiry_realtime_updates(self):
        self.inquiry_timer = QtCore.QTimer(self)
        self.inquiry_timer.setInterval(1500)
        self.inquiry_timer.timeout.connect(lambda: self.filter_chats(self.current_filter))
        self.inquiry_timer.start()

    def _get_user_name(self, user_id: int) -> str:
        u = self.data_manager.get_user(user_id)
        return u.get("name") if u else f"User {user_id}"

    def _display_name_for_conversation(self, conv: dict) -> str:
        if conv.get("is_group", False):
            return conv.get("group_name") or f"Group {conv.get('id')}"
        other = next((pid for pid in conv.get("participants", []) if pid != self.current_user_id), None)
        return self._get_user_name(other) if other else f"Chat {conv.get('id')}"

    def _display_name_for_inquiry(self, inq: dict) -> str:
        student_id = inq.get("student_id")
        faculty_id = inq.get("faculty_id")
        other_id = faculty_id if self.current_user_id == student_id else student_id
        return self._get_user_name(other_id) if other_id else f"Inquiry {inq.get('id')}"

    def _conversation_has_unread(self, conv_id: int) -> bool:
        msgs = self.data_manager.data.get("messages", [])
        return any(
            m.get("conversation_id") == conv_id and
            m.get("receiver_id") == self.current_user_id and
            not m.get("is_read", False)
            for m in msgs
        )

<<<<<<< Updated upstream
=======

# Wrapper class for router compatibility
class MessagingWidget(QtWidgets.QWidget):
    """Wrapper class to make messaging module compatible with router system"""
    def __init__(self, username="", roles=None, primary_role="", token="", parent=None):
        super().__init__(parent)
        roles = roles or []  # prevent mutable default
        
        # Optional: Store session info if needed
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        
        # Create the main messaging app
        self.messaging_app = MainApp(username, roles, primary_role, token, parent)
        
        # Create a layout and add the messaging app's central widget
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Add the messaging app's central widget to this widget
        central_widget = self.messaging_app.centralWidget()
        layout.addWidget(central_widget)
        self.setLayout(layout)

>>>>>>> Stashed changes
