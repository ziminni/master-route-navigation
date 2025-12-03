
import json
from PyQt6 import QtCore, QtWidgets, QtGui
from PyQt6.QtWebSockets import QWebSocket

from .data_manager import DataManager
from .inquiry import InquiryDialog
from .msg_main import Ui_MainWindow


class ConfirmDialog(QtWidgets.QDialog):
    """
    Simple frameless confirmation dialog used when deleting conversations.
    """

    def __init__(self, parent=None, title="Delete Conversation", text=""):
        super().__init__(parent)

        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint
            | QtCore.Qt.WindowType.Dialog
        )
        self.setModal(True)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        container = QtWidgets.QWidget(self)
        container.setObjectName("confirm_container")
        container.setStyleSheet("""
            QWidget#confirm_container {
                background-color: gray;
                border-radius: 12px;
            }
            QLabel {
                color: black;
                font-size: 13px;
            }
            QPushButton {
                background-color: #f0f0f0;
                color: #222;
                border: none;
                border-radius: 6px;
                padding: 6px 18px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        inner = QtWidgets.QVBoxLayout(container)
        inner.setContentsMargins(20, 18, 20, 14)
        inner.setSpacing(10)

        title_lbl = QtWidgets.QLabel(title)
        title_lbl.setStyleSheet(
            "font-size: 15px; font-weight: bold; color: black;"
        )
        inner.addWidget(title_lbl)

        text_lbl = QtWidgets.QLabel(text)
        text_lbl.setWordWrap(True)
        inner.addWidget(text_lbl)

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch(1)

        btn_no = QtWidgets.QPushButton("No")
        btn_no.clicked.connect(self.reject)
        btn_row.addWidget(btn_no)

        btn_yes = QtWidgets.QPushButton("Yes")
        btn_yes.clicked.connect(self.accept)
        btn_row.addWidget(btn_yes)

        inner.addLayout(btn_row)
        layout.addWidget(container)


class MainChatWidgetWrapper(QtWidgets.QWidget):
    """
    Student messaging UI wrapper.

    - Hosts the generated Ui_MainWindow as its body.
    - Uses DataManager to talk to the Django REST API.
    - Uses QWebSocket to receive broadcast + message events from Channels.
    """

    def __init__(
            self,
            parent=None,
            current_user_id=None,
            current_username=None,
            current_token=None,
            data_manager: DataManager | None = None,
            layout_manager=None,
    ):
        super().__init__(parent)

        self.current_user_id = current_user_id
        self.current_username = current_username
        self.current_token = current_token
        self.data_manager = data_manager
        self.current_filter = "all"
        self.conversations: list[dict] = []
        self.current_conversation_id: int | None = None
        self.chat_box_minimized = False
        self.last_broadcast_id: int | None = None
        self.ws: QWebSocket | None = None

        # Shared header (for inbox popup)
        self.header = layout_manager.get_header() if layout_manager else None

        # Root layout
        root_layout = QtWidgets.QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Load main UI as body
        self.ui = Ui_MainWindow()
        dummy_main = QtWidgets.QMainWindow()
        self.ui.setupUi(dummy_main)
        self.body_widget = self.ui.centralwidget
        root_layout.addWidget(self.body_widget, 1)

        # Inbox popup wiring
        if self.header is not None and hasattr(self.header, "mail_menu"):
            self.header.mail_menu.messageActivated.connect(
                self._on_inbox_item_clicked
            )
            self._refresh_inbox_popup()

        # Chat list / filters
        self.ui.create_inquiry.clicked.connect(self.open_inquiry_dialog)
        self.ui.push_all.clicked.connect(lambda: self.filter_chats("all"))
        self.ui.push_unread.clicked.connect(lambda: self.filter_chats("unread"))
        self.ui.push_comm.clicked.connect(lambda: self.filter_chats("comm"))
        self.ui.push_group.clicked.connect(lambda: self.filter_chats("group"))
        self.ui.search_recipt.textChanged.connect(self.search_chats)
        self.ui.chat_list.itemClicked.connect(self.on_chat_selected)

        # Initial load
        self.filter_chats(self.current_filter)

        # Chat box integration
        if getattr(self.ui, "chat_box", None) is not None:
            self.ui.chat_box.searchRequested.connect(
                self._on_search_messages_from_chat
            )
            self.ui.chat_box.deleteRequested.connect(
                self._on_delete_current_conversation
            )
            self._setup_chat_box_buttons()

        # WebSocket for realtime messages/broadcasts
        self._init_ws()

    # -------------------- Inbox popup --------------------
    def _refresh_inbox_popup(self):
        """Fill header mail menu with recent message summaries for this user."""
        if not self.data_manager or not self.current_user_id or not self.header:
            return

        msgs = self.data_manager.get_message_summaries_for_user(
            self.current_user_id
        )
        for m in msgs:
            body = m.get("content", "") or ""
            m["preview"] = body[:60] + "..." if len(body) > 60 else body

        if hasattr(self.header, "mail_menu"):
            self.header.mail_menu.set_messages(msgs)

    def _on_inbox_item_clicked(self, msg: dict):
        """Open conversation when user clicks item in header mail popup."""
        conv_id = msg.get("conversation")
        if isinstance(conv_id, dict):
            conv_id = conv_id.get("id")
        if conv_id:
            self.open_conversation(conv_id)

    def getDataManager(self) -> DataManager | None:
        return self.data_manager

    # -------------------- WebSocket integration --------------------
    def _init_ws(self):
        """
        Connect to Django Channels WebSocket for realtime updates.

        Uses BroadcastConsumer at /ws/broadcasts/ which sends:
        - type="broadcast" for system broadcasts
        - type="message" for chat events (with a top-level 'conversation')
        """
        if not self.data_manager:
            print("[MainChat] No data_manager, skipping WS init")
            return
        try:
            self.ws = QWebSocket()
            self.ws.errorOccurred.connect(
                lambda err: print("[MainChat] WS error:", err)
            )
            self.ws.textMessageReceived.connect(self._on_ws_message)

            url = QtCore.QUrl("ws://127.0.0.1:8001/ws/broadcasts/")
            print("[MainChat] Connecting WS:", url.toString())
            self.ws.open(url)
        except Exception as e:
            print("[MainChat] _init_ws error:", e)

    def _on_ws_message(self, msg: str):
        """
        Handle JSON messages from Channels (broadcasts + direct messages).
        """
        print("[MainChat] WS raw msg:", msg)
        try:
            data = json.loads(msg)
            print("[MainChat] WS message:", data)

            msg_type = data.get("type", "broadcast")
            if msg_type == "broadcast":
                msg_id = data.get("id")
                if self.last_broadcast_id == msg_id:
                    return
                self.last_broadcast_id = msg_id
                self._show_broadcast_popup(data)
            elif msg_type == "message":
                self._handle_incoming_message(data)
        except Exception as e:
            print("[MainChat] _on_ws_message error:", e)

    def _handle_incoming_message(self, data: dict):
        """
        Fired when a new message for this user arrives via WebSocket.

        - Refreshes the conversation list so unread counts / ordering update.
        - If the event's conversation matches the currently open one,
          reloads its messages so the chat box updates live.
        """
        print("[MainChat] Incoming WS message:", data)

        # Refresh conversations list (left panel)
        self.filter_chats(self.current_filter)

        conv_id = data.get("conversation")
        if isinstance(conv_id, dict):
            conv_id = conv_id.get("id")

        if conv_id and conv_id == self.current_conversation_id:
            print("[MainChat] Reloading messages for conversation", conv_id)
            self.load_conversation_messages(conv_id,force=True)

    def _show_broadcast_popup(self, msg: dict):
        """Small popup dialog for system broadcasts."""
        try:
            dialog = QtWidgets.QDialog(self)

            shadow = QtWidgets.QGraphicsDropShadowEffect(dialog)
            shadow.setBlurRadius(20)
            shadow.setXOffset(0)
            shadow.setYOffset(4)
            shadow.setColor(QtGui.QColor(0, 0, 0, 120))
            dialog.setGraphicsEffect(shadow)

            dialog.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
            dialog.resize(500, 220)

            layout = QtWidgets.QVBoxLayout(dialog)
            layout.setContentsMargins(0, 0, 0, 0)

            header = QtWidgets.QFrame()
            header.setFixedHeight(40)
            header.setStyleSheet("background-color: #008000;")
            h_layout = QtWidgets.QHBoxLayout(header)
            h_layout.setContentsMargins(12, 0, 12, 0)

            title_lbl = QtWidgets.QLabel("System Broadcast")
            title_lbl.setStyleSheet("color: black; font-weight: bold;")
            h_layout.addWidget(title_lbl)
            h_layout.addStretch()

            close_btn = QtWidgets.QPushButton("×")
            close_btn.setFixedSize(24, 24)
            close_btn.setStyleSheet(
                "QPushButton { border: none; background: transparent; color: black; }"
                "QPushButton:hover { background: rgba(0,0,0,0.1); }"
            )
            close_btn.clicked.connect(dialog.reject)
            h_layout.addWidget(close_btn)

            layout.addWidget(header)

            body = QtWidgets.QWidget()
            body.setStyleSheet("""
                QWidget { background: #f8f8f8; color: black; }
                QTextEdit {
                    background: white;
                    color: black;
                    border: 1px solid #cccccc;
                }
                QPushButton {
                    color: black;
                    border: 1px solid #008000;
                    padding: 6px 14px;
                    border-radius: 4px;
                }
                QPushButton:hover { background-color: #e0ffe0; }
            """)
            body_layout = QtWidgets.QVBoxLayout(body)
            body_layout.setContentsMargins(16, 12, 16, 16)

            subject = QtWidgets.QLabel(msg.get("subject", "No Subject"))
            subject.setStyleSheet("font-weight: bold; color: black;")
            body_layout.addWidget(subject)

            content = QtWidgets.QTextEdit()
            content.setReadOnly(True)
            content.setPlainText(msg.get("content", ""))
            body_layout.addWidget(content)

            ok_btn = QtWidgets.QPushButton("Close")
            ok_btn.clicked.connect(dialog.accept)
            body_layout.addWidget(
                ok_btn,
                alignment=QtCore.Qt.AlignmentFlag.AlignRight
            )

            layout.addWidget(body)
            dialog.exec()
        except Exception as e:
            print("[MainChat] _show_broadcast_popup error:", e)

    # -------------------- Chat box header buttons --------------------
    def _setup_chat_box_buttons(self):
        """Add minimize button to chat box header."""
        try:
            chat_box = self.ui.chat_box
            if not hasattr(chat_box, "ui") or not hasattr(chat_box.ui, "header_buttons"):
                print("[MainChat] ⚠️ chat_box header structure not found")
                return

            header_layout = chat_box.ui.header_buttons
            if header_layout is None:
                print("[MainChat] ⚠️ header_buttons layout not found")
                return

            # minimize_btn = QtWidgets.QPushButton("_")
            # minimize_btn.setMaximumWidth(30)
            # minimize_btn.setMaximumHeight(30)
            # minimize_btn.setStyleSheet("""
            #     QPushButton {
            #         background-color: transparent;
            #         color: #555;
            #         border: none;
            #         font-weight: bold;
            #         font-size: 16px;
            #     }
            #     QPushButton:hover {
            #         background-color: #e0e0e0;
            #         border-radius: 4px;
            #     }
            # """)
            # minimize_btn.clicked.connect(self.toggle_chat_box_minimize)

            if header_layout.count() > 0:
                header_layout.insertWidget(
                    header_layout.count() - 1, minimize_btn
                )
            else:
                header_layout.addWidget(minimize_btn)

            print("[MainChat] ✅ Minimize button added to chat box")
        except Exception as e:
            print(f"[MainChat] Error setting up chat box buttons: {e}")

    def toggle_chat_box_minimize(self):
        """Toggle chat box minimize/restore state."""
        try:
            chat_box = self.ui.chat_box
            messages_layout = chat_box.ui.messages_layout

            if self.chat_box_minimized:
                for i in range(messages_layout.count()):
                    item = messages_layout.itemAt(i)
                    if item and item.widget():
                        item.widget().setVisible(True)
                chat_box.setMinimumHeight(300)
                chat_box.setMaximumHeight(16777215)
                self.chat_box_minimized = False
                print("[MainChat] ✅ Chat box restored")
            else:
                for i in range(messages_layout.count()):
                    item = messages_layout.itemAt(i)
                    if item and item.widget():
                        item.widget().setVisible(False)
                chat_box.setMaximumHeight(50)
                self.chat_box_minimized = True
                print("[MainChat] ✅ Chat box minimized")
        except Exception as e:
            print(f"[MainChat] Error toggling minimize: {e}")

    # -------------------- Inquiry creation --------------------
    def open_inquiry_dialog(self):
        """
        Open inquiry dialog and handle creation with auto-refresh.

        - Ensures a stable conversation id per (student, faculty) pair.
        - Creates/uses that conversation for the inquiry message.
        """
        dialog = InquiryDialog(self, self.current_user_id, self.data_manager)
        if not dialog.exec():
            return

        inquiry_data = dialog.get_inquiry_data()
        if not inquiry_data:
            return

        print("[Inquiry] raw inquiry_data:", inquiry_data)

        # Guard empty subject/title
        subject = (inquiry_data.get("subject") or "").strip()
        if not subject:
            subject = "[General Inquiry]"
        inquiry_data["subject"] = subject


        faculty_id = inquiry_data.get("receiver")
        conv_id = self._get_or_create_conversation(faculty_id,subject)
        if not conv_id:
            print("[MainChat] Failed to resolve conversation id for inquiry")
            return

        inquiry_data["conversation"] = conv_id

        created_inquiry = self.data_manager.create_inquiry(inquiry_data)
        if not created_inquiry:
            print("[MainChat] Failed to create inquiry")
            return

        print(f"✅ Inquiry Created! ID: {created_inquiry['id']}")
        self.refresh_and_show_new_conversation(created_inquiry)

    def _get_or_create_conversation(self, faculty_id: int, subject: str | None = None) -> int | None:
        """
        Return existing conversation id for (current_user, faculty_id) if present,
        otherwise create a new direct conversation and return its id.
        Optionally updates/sets the conversation title from subject.
        """
        if not self.data_manager or not self.current_user_id or not faculty_id:
            return None

        subj = (subject or "").strip()

        # 1) Look for an existing conversation with both participants
        convs = self.data_manager.get_conversations_by_user(self.current_user_id)
        print("[Inquiry] Loaded", len(convs), "conversations")
        for c in convs:
            participants = c.get("participants", []) or []
            print(" - conv:", c.get("id"), "participants:", participants)
            if self.current_user_id in participants and faculty_id in participants:
                conv_id = c.get("id")
                print("[Inquiry] Using existing conversation", conv_id)
                if subj:
                    print("[Inquiry] Updating conversation title to:", subj)
                    self.data_manager.update_conversation_title(conv_id, subj)
                return conv_id

        # 2) If none found, create a new direct conversation
        payload = {
            "title": subj if subj else "",
            "type": "direct",
            "participants": [self.current_user_id, faculty_id],
            "creator": self.current_user_id,
        }
        print("[Inquiry] Creating conversation:", payload)
        created = self.data_manager.create_conversation(payload)
        if isinstance(created, dict):
            print("[Inquiry] API returned:", created)
            return created.get("id")
        return None


    def refresh_and_show_new_conversation(self, created_inquiry: dict):
        """
        Reload conversations and automatically display the newly created inquiry.
        """
        try:
            self.filter_chats(self.current_filter)

            conv_id = created_inquiry.get("conversation")
            if not conv_id:
                print("[MainChat] No conversation ID in created inquiry")
                return

            for i in range(self.ui.chat_list.count()):
                item = self.ui.chat_list.item(i)
                data = item.data(QtCore.Qt.ItemDataRole.UserRole) or {}
                if data.get("conversation_id") == conv_id:
                    self.ui.chat_list.setCurrentItem(item)
                    self.on_chat_selected(item)
                    print(f"[MainChat] ✅ Auto-opened conversation {conv_id}")
                    return

            print(
                f"[MainChat] ⚠️ Conversation {conv_id} not found in list after refresh"
            )
        except Exception as e:
            print(f"[MainChat] Error refreshing and showing conversation: {e}")

    # -------------------- Backend loading helpers --------------------
    def load_conversations(self):
        """Load conversations for the current user from Django."""
        try:
            if self.current_user_id is not None and self.data_manager:
                self.conversations = self.data_manager.get_conversations_by_user(
                    self.current_user_id
                )
            else:
                self.conversations = []
            print("[MainChat] Loaded conversations:", len(self.conversations))
        except Exception as e:
            print("[MainChat] Error loading conversations:", e)
            self.conversations = []

    def load_messages_for_conversation(self, conversation_id: int,force: bool = False) -> list[dict]:
        """
        Load all messages for a specific conversation from Django.
        """
        try:
            if not self.data_manager:
                return []

            all_messages = self.data_manager.get_all_messages(force=force)
            print(f"[MainChat] total messages from API: {len(all_messages)}")

            messages: list[dict] = []
            for m in all_messages:
                conv_field = m.get("conversation")
                conv_id = conv_field.get("id") if isinstance(conv_field, dict) else conv_field
                if conv_id == conversation_id:
                    messages.append(m)

            sent_by_me = [m for m in messages if m.get("sender") == self.current_user_id]
            sent_by_others = [m for m in messages if m.get("sender") != self.current_user_id]

            print(
                f"[MainChat] convo {conversation_id}: total={len(messages)}, "
                f"mine={len(sent_by_me)}, replies={len(sent_by_others)}"
            )
            if sent_by_others:
                print("[MainChat] sample reply msg:", sent_by_others[-1])

            messages.sort(key=lambda x: x.get("created_at", ""))
            return messages
        except Exception as e:
            print("[MainChat] Error loading messages:", e)
            return []

    # -------------------- Conversation list --------------------
    def filter_chats(self, filter_type: str):
        """Filter and display conversations based on type."""
        self.current_filter = filter_type
        self.ui.chat_list.clear()

        self.load_conversations()

        for conv in self.conversations:
            conv_type = conv.get("type", "direct")
            is_group = conv_type == "group"

            if filter_type == "group" and not is_group:
                continue
            if filter_type == "comm" and is_group:
                continue
            if filter_type == "unread" and not self._conversation_has_unread(
                    conv.get("id")
            ):
                continue

            label = self._display_name_for_conversation(conv)
            item = QtWidgets.QListWidgetItem(label)
            item.setData(
                QtCore.Qt.ItemDataRole.UserRole,
                {
                    "type": "conversation",
                    "conversation_id": conv.get("id"),
                    "display_name": label,
                },
            )
            self.ui.chat_list.addItem(item)

    # -------------------- Search chat list --------------------
    def search_chats(self, text: str):
        """Filter chat list by search text."""
        query = (text or "").strip().lower()
        for i in range(self.ui.chat_list.count()):
            item = self.ui.chat_list.item(i)
            data = item.data(QtCore.Qt.ItemDataRole.UserRole) or {}
            name = (data.get("display_name") or item.text()).lower()
            item.setHidden(bool(query) and query not in name)

    # -------------------- Search from chat box --------------------
    def _on_search_messages_from_chat(self):
        """Handle search request from chat box search icon."""
        self.ui.search_recipt.setFocus()
        self.ui.search_recipt.selectAll()

        current_item = self.ui.chat_list.currentItem()
        if not current_item:
            return

        data = current_item.data(QtCore.Qt.ItemDataRole.UserRole) or {}
        label = data.get("display_name") or current_item.text()
        self.ui.search_recipt.setText(label)

        self.search_chats(label)

        row = self.ui.chat_list.currentRow()
        if row >= 0:
            self.ui.chat_list.scrollToItem(
                self.ui.chat_list.item(row),
                QtWidgets.QAbstractItemView.ScrollHint.PositionAtCenter,
            )

    # -------------------- Delete conversation --------------------
    def _on_delete_current_conversation(self):
        """Handle conversation deletion with confirmation."""
        current_item = self.ui.chat_list.currentItem()
        if not current_item or not self.data_manager:
            return

        data = current_item.data(QtCore.Qt.ItemDataRole.UserRole) or {}
        conv_id = data.get("conversation_id")
        if not conv_id:
            return

        dlg = ConfirmDialog(
            self,
            title="Delete Conversation",
            text="This will remove the conversation and all its messages. Continue?",
        )
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        if self.data_manager.delete_conversation(conv_id):
            self.current_conversation_id = None
            self.filter_chats(self.current_filter)
            self.ui.show_empty_state("Conversation deleted.")

    # -------------------- Chat selection --------------------
    def on_chat_selected(self, item: QtWidgets.QListWidgetItem):
        """Handle chat list item selection."""
        self.ui.show_chat_state()

        data = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if not data or data.get("type") != "conversation":
            return

        conv_id = data.get("conversation_id")
        self.current_conversation_id = conv_id

        conversation = (
            self.data_manager.get_conversation(conv_id) if self.data_manager else None
        )
        if not conversation:
            print(f"⚠️ Conversation ID {conv_id} not found.")
            return

        if not getattr(self.ui, "chat_box", None):
            print("[ERROR] chat_box not found in UI.")
            return

        conv_type = conversation.get("type", "direct")
        if conv_type == "group":
            self._display_group_chat(conversation, item.text())
        else:
            participants = conversation.get("participants", [])
            other_id = next(
                (pid for pid in participants if pid != self.current_user_id),
                None,
            )
            other_user = (
                self.data_manager.get_user(other_id)
                if (other_id and self.data_manager)
                else None
            )
            self._display_private_chat(conversation, other_user)

        self.load_conversation_messages(conv_id)

    # -------------------- Group chat display --------------------
    def _display_group_chat(self, conversation: dict, label: str):
        """Display group chat header and details."""
        name = conversation.get("group_name") or label
        self.ui.chat_box.ui.name_header.setText(f"Group: {name}")
        self.ui.chat_box.ui.header2_accesslvl.setText(
            f"Group Chat - {len(conversation.get('participants', []))} members"
        )
        self.ui.contact_details.setText(
            f"Group Chat\n"
            f"Participants: {len(conversation.get('participants', []))}\n"
            f"Last Activity: {conversation.get('last_activity', 'Unknown')}"
        )

    # -------------------- Private chat display --------------------
    def _display_private_chat(self, conversation: dict, other_user: dict | None):
        """Display private chat header and details for a direct conversation."""
        if not other_user:
            self.ui.chat_box.ui.name_header.setText("Unknown User")
            self.ui.chat_box.ui.header2_accesslvl.setText("Unknown Role")
            self.ui.contact_details.setText("Contact: Unknown")
            return

        name = (
                (other_user.get("first_name", "") + " " + other_user.get("last_name", ""))
                .strip()
                or other_user.get("username")
                or "Unknown"
        )
        groups = other_user.get("groups", []) or []
        role = (groups[0] if groups else "Unknown").title()
        dept = other_user.get("department", "Unknown")
        email = other_user.get("email", "Unknown")

        self.ui.chat_box.ui.name_header.setText(name)
        self.ui.chat_box.ui.header2_accesslvl.setText(f"{role} - {dept}")
        self.ui.contact_details.setText(
            f"Contact: {name}\n"
            f"Role: {role}\n"
            f"Department: {dept}\n"
            f"Email: {email}"
        )

        if hasattr(self.ui.chat_box, "set_context"):
            self.ui.chat_box.set_context(
                data_manager=self.data_manager,
                current_user_id=self.current_user_id,
                other_user_id=other_user.get("id"),
                conversation_id=conversation["id"],
            )

    # -------------------- Load conversation messages into UI --------------------
    def load_conversation_messages(self, conversation_id: int,force : bool = False):
        """Load and display all messages for a conversation in the chat box."""
        layout = self.ui.chat_box.ui.messages_layout
         # Clear existing bubbles (keep stretch at end)
        while layout.count() > 1:
            item = layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        messages = self.load_messages_for_conversation(conversation_id,force=force)

        print(
            f"[MainChat] rendering {len(messages)} messages in chat box "
            f"for conv {conversation_id}"
        )
        for idx, msg in enumerate(messages):
            sender_id = msg.get("sender")
            content = msg.get("content", "")
            sent_by_me = sender_id == self.current_user_id
            print(
                f"[MainChat]  bubble {idx}: sender={sender_id}, "
                f"me={sent_by_me}, content={content!r}"
            )
            self._add_message_bubble(content, sent_by_me)

        self._scroll_chat_to_bottom()

    # -------------------- Message bubble --------------------
    def _add_message_bubble(self, text: str, sent_by_me: bool = False):
        """Add a message bubble widget to the chat display."""
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
        """ % (
            "#76a979" if sent_by_me else "#e0e0e0",
            "white" if sent_by_me else "black",
        )
        bubble.setStyleSheet(bubble_style)

        if sent_by_me:
            bubble_layout.addStretch()
            bubble_layout.addWidget(bubble)
        else:
            bubble_layout.addWidget(bubble)
            bubble_layout.addStretch()

        layout.insertWidget(layout.count() - 1, bubble_widget)

    # -------------------- Scroll helpers --------------------
    def _scroll_chat_to_bottom(self):
        """Scroll chat box to show the latest messages."""
        try:
            chat_box = self.ui.chat_box

            scroll_area = None
            if hasattr(chat_box, "ui") and hasattr(chat_box.ui, "messages_scroll"):
                scroll_area = chat_box.ui.messages_scroll
            elif hasattr(chat_box, "messages_scroll"):
                scroll_area = chat_box.messages_scroll
            elif hasattr(chat_box.ui, "scrollArea"):
                scroll_area = chat_box.ui.scrollArea

            if scroll_area and isinstance(scroll_area, QtWidgets.QScrollArea):
                scroll_bar = scroll_area.verticalScrollBar()
                scroll_bar.setValue(scroll_bar.maximum())
                print("[MainChat] ✅ Scrolled chat to bottom")
            else:
                if (
                        hasattr(chat_box.ui, "messages_list")
                        and isinstance(chat_box.ui.messages_list, QtWidgets.QListWidget)
                ):
                    chat_box.ui.messages_list.scrollToBottom()
                    print("[MainChat] ✅ Scrolled QListWidget to bottom")
                else:
                    layout = chat_box.ui.messages_layout
                    parent = layout.parentWidget()
                    if parent and hasattr(parent, "repaint"):
                        parent.repaint()
                    QtWidgets.QApplication.processEvents()
                    print("[MainChat] ⚠️ Layout refreshed (scroll fallback)")
        except Exception as e:
            print(f"[MainChat] ⚠️ Error scrolling to bottom: {e}")

    # -------------------- Helpers --------------------
    def _conversation_has_unread(self, conv_id: int) -> bool:
        """Check if conversation has unread messages (placeholder)."""
        return False

    def _display_name_for_conversation(self, conv: dict) -> str:
        """Generate display name for a conversation."""
        conv_type = conv.get("type", "direct")
        if conv_type == "group":
            return (
                    conv.get("group_name")
                    or conv.get("title")
                    or f"Group {conv.get('id')}"
            )

        participants = conv.get("participants", []) or []
        other_id = next(
            (pid for pid in participants if pid != self.current_user_id),
            None,
        )

        user = (
            self.data_manager.get_user(other_id)
            if (other_id and self.data_manager)
            else None
        )
        if not user:
            return f"User {other_id}"

        name = (
                (user.get("first_name", "") + " " + user.get("last_name", ""))
                .strip()
                or user.get("username")
                or "Unknown"
        )
        groups = user.get("groups", []) or []
        role = (groups[0] if groups else "Unknown").title()
        return f"{name} ({role})"
