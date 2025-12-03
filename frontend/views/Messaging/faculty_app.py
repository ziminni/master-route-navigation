import sys
import json

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWebSockets import QWebSocket

print("[FacultyMainUI] Starting module import...")

try:
    from .data_manager import DataManager
    print("[FacultyMainUI] Imported DataManager successfully")
except Exception as e:
    print(f"[FacultyMainUI] ERROR importing DataManager: {e}")
    DataManager = None

try:
    from .faculty.message_dialog import Ui_Form
    print("[FacultyMainUI] Imported Ui_Form (message_dialog) successfully")
except Exception as e:
    print(f"[FacultyMainUI] ERROR importing message_dialog.Ui_Form: {e}")
    Ui_Form = None

try:
    from .faculty.message_compose import Ui_Form as ComposeUI
    print("[FacultyMainUI] Imported ComposeUI (message_compose.Ui_Form) successfully")
except Exception as e:
    print(f"[FacultyMainUI] ERROR importing message_compose.Ui_Form: {e}")
    ComposeUI = None


class FacultyMainUI(QtWidgets.QWidget):
    """Faculty Messaging UI with filtering, dialogs, and compose/reply."""

    def __init__(self, username=None, roles=None, primary_role=None, token=None,
                 data_manager=None, parent=None, layout_manager=None):
        print("[FacultyMainUI] __init__ called")
        super().__init__(parent)
        self.setObjectName("FacultyMainUI")

        self.username = username
        self.roles = roles or []
        self.primary_role = primary_role
        self.token = token
        self.data_manager = data_manager
        self.current_faculty_id = (
            self.data_manager.get_current_user_id() if self.data_manager else None
        )
        print("[FacultyMainUI] current_faculty_id:", self.current_faculty_id)

        self.last_broadcast_id = None
        self.all_items = []
        self.text_filtered_items = []
        self.filtered_items = []

        # ---------- ROOT LAYOUT ----------
        root_layout = QtWidgets.QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # get shared header from layout manager
        self.header = (
            layout_manager.get_header() if layout_manager is not None else None
        )

        # MAIN FACULTY CONTENT
        content_widget = QtWidgets.QWidget(parent=self)
        content_layout = QtWidgets.QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 8, 0, 8)
        content_layout.setSpacing(8)

        self.faculty_content = QtWidgets.QWidget(parent=content_widget)
        self.faculty_content.setObjectName("faculty_content")
        self.setup_faculty_content()
        content_layout.addWidget(self.faculty_content, stretch=1)

        root_layout.addWidget(content_widget, 1)

        self.connect_buttons()
        self.load_faculty_data()
        self.load_messages()

        # hook inbox dropdown click -> open message dialog
        if self.header is not None and hasattr(self.header, "mail_menu"):
            self.header.mail_menu.messageActivated.connect(
                self._on_inbox_item_clicked
            )
            self._refresh_inbox_popup()

        # WebSocket for realtime messages/broadcasts
        self._init_ws()

    # -------------------- WebSocket setup --------------------
    def _init_ws(self):
        """Connect to Django Channels broadcasts WebSocket."""
        if not self.data_manager:
            print("[FacultyMainUI] No data_manager, skipping WS init")
            return
        try:
            self.ws = QWebSocket()
            self.ws.errorOccurred.connect(
                lambda err: print("[FacultyMainUI] WS error:", err)
            )
            self.ws.textMessageReceived.connect(self._on_ws_message)

            url = QtCore.QUrl("ws://127.0.0.1:8001/ws/broadcasts/")
            print("[FacultyMainUI] Connecting WS:", url.toString())
            self.ws.open(url)
        except Exception as e:
            print("[FacultyMainUI] _init_ws error:", e)

    def _on_ws_message(self, msg: str):
        """Handle JSON messages from Channels (broadcasts + direct messages)."""
        try:
            data = json.loads(msg)
            print("[FacultyMainUI] WS message:", data)

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
            print("[FacultyMainUI] _on_ws_message error:", e)

    def _handle_incoming_message(self, data: dict):
        """New incoming message for this faculty (via WS)."""
        print("[FacultyMainUI] Incoming message via WS:", data)
        # reload list & inbox popup
        self.load_messages()
        self._refresh_inbox_popup()  # NEW

    def _show_broadcast_popup(self, msg: dict):
        """Simple green-header popup for system broadcasts."""
        try:
            dialog = QtWidgets.QDialog(self)
            shadow = QtWidgets.QGraphicsDropShadowEffect(dialog)
            shadow.setBlurRadius(20)
            shadow.setXOffset(0)
            shadow.setYOffset(4)
            shadow.setColor(QtGui.QColor(0, 0, 0, 120))
            dialog.setGraphicsEffect(shadow)

            dialog.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
            dialog.resize(550, 260)

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
            body_layout.setSpacing(10)

            subject = QtWidgets.QLabel(msg.get("subject", "No Subject"))
            subject.setStyleSheet("font-weight: bold; color: black;")
            body_layout.addWidget(subject)

            content = QtWidgets.QTextEdit()
            content.setReadOnly(True)
            content.setPlainText(msg.get("content", ""))
            body_layout.addWidget(content)

            ok_btn = QtWidgets.QPushButton("Close")
            ok_btn.clicked.connect(dialog.accept)
            body_layout.addWidget(ok_btn, alignment=QtCore.Qt.AlignmentFlag.AlignRight)

            layout.addWidget(body)
            dialog.exec()
        except Exception as e:
            print("[FacultyMainUI] _show_broadcast_popup error:", e)

    # ---------- NEW: inbox dropdown helpers ----------
    def _refresh_inbox_popup(self):
        """Fill header.mail_menu with faculty inbox summaries."""
        # guard: no header or no data_manager / user
        if not self.data_manager or not self.current_faculty_id or not self.header:
            print("[FacultyMainUI] _refresh_inbox_popup: no header/data_manager/user, skipping")
            return

        try:
            msgs = self.data_manager.get_message_summaries_for_user(self.current_faculty_id)
            print("[FacultyMainUI] _refresh_inbox_popup summaries:", len(msgs))
            for m in msgs:

                body = m.get("content", "") or ""
                m["preview"] = body[:60] + "..." if len(body) > 60 else body

            if hasattr(self.header, "mail_menu"):
                self.header.mail_menu.set_messages(msgs)
            else:
                print("[FacultyMainUI] _refresh_inbox_popup: header has no mail_menu")
        except Exception as e:
            print("[FacultyMainUI] _refresh_inbox_popup error:", e)


        def _on_inbox_item_clicked(self, msg: dict):
            """
            Called when user clicks an item in the MailPopup.
            Reuse on_message_clicked by mapping summary to item shape.
            """
            print("[FacultyMainUI] Inbox item clicked:", msg)
            mapped = {
                "type": "message",
                "id": msg.get("id"),
                "conversation_id": msg.get("conversation"),
                "title": msg.get("subject", "No Subject"),
                "content": msg.get("content", ""),
                "sender": msg.get("sender_name") or "Unknown",
                "priority": msg.get("priority", "normal"),
                "status": msg.get("status", "pending"),
                "date": msg.get("created_at", ""),
                "is_read": msg.get("read", False),
            }
            self.on_message_clicked(mapped)


    # -------------------- Setup Content --------------------
    def setup_faculty_content(self):
        faculty_layout = QtWidgets.QHBoxLayout(self.faculty_content)
        faculty_layout.setContentsMargins(0, 0, 0, 0)
        faculty_layout.setSpacing(8)

        self.setup_left_panel(faculty_layout)
        self.setup_center_panel(faculty_layout)

    def setup_left_panel(self, parent_layout):
        self.inquiry_widget = QtWidgets.QWidget(parent=self.faculty_content)
        self.inquiry_widget.setMinimumWidth(251)
        self.inquiry_widget.setMaximumWidth(280)
        self.inquiry_widget.setObjectName("inquiry_widget")
        self.inquiry_widget.setStyleSheet("""
            QWidget#inquiry_widget {
                background-color: white;
                border-radius: 20px;
                border: 1px solid #dddddd;
            }
        """)

        layout = QtWidgets.QVBoxLayout(self.inquiry_widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        label_header = QtWidgets.QLabel("Message Categories")
        label_header.setFont(QtGui.QFont("Arial", 14))
        label_header.setStyleSheet("color: #084924;")
        layout.addWidget(label_header)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        layout.addWidget(line)

        button_style = """
            QPushButton {
                color: black;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                text-align: left;
                padding: 6px 10px;
                margin: 1px 0px;
            }
            QPushButton:hover {
                background-color: #005a2e;
                color: white;
            }
            QPushButton:pressed {
                background-color: #002d17;
            }
        """
        self.push_all = QtWidgets.QPushButton("All Messages"); self.push_all.setStyleSheet(button_style)
        self.push_unread = QtWidgets.QPushButton("Unread"); self.push_unread.setStyleSheet(button_style)
        self.push_acadin = QtWidgets.QPushButton("Academic Inquiries"); self.push_acadin.setStyleSheet(button_style)
        self.push_assgt = QtWidgets.QPushButton("Assignment Help"); self.push_assgt.setStyleSheet(button_style)
        self.push_office = QtWidgets.QPushButton("Office Hours"); self.push_office.setStyleSheet(button_style)

        for btn in [self.push_all, self.push_unread, self.push_acadin, self.push_assgt, self.push_office]:
            layout.addWidget(btn)

        layout.addWidget(QtWidgets.QFrame(frameShape=QtWidgets.QFrame.Shape.HLine))
        label_actions = QtWidgets.QLabel("Quick Actions")
        label_actions.setFont(QtGui.QFont("Arial", 12))
        label_actions.setStyleSheet("color: #084924;")
        layout.addWidget(label_actions)
        self.push_compose = QtWidgets.QPushButton("Compose Message")
        self.push_compose.setStyleSheet(button_style)
        layout.addWidget(self.push_compose)
        layout.addStretch()

        parent_layout.addWidget(self.inquiry_widget)

    def setup_center_panel(self, parent_layout):
        center_widget = QtWidgets.QWidget(parent=self.faculty_content)
        center_layout = QtWidgets.QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(8)

        self.chat_info = QtWidgets.QWidget(parent=center_widget)
        self.chat_info.setObjectName("chat_info")
        self.chat_info.setStyleSheet("""    
            QWidget#chat_info {
                background-color: white;
                border-radius: 16px;
                border: 1px solid #e0e0e0;
                padding: 10px;
            }
        """)
        search_layout = QtWidgets.QHBoxLayout(self.chat_info)

        self.lineEdit_faculty = QtWidgets.QLineEdit()
        self.lineEdit_faculty.setPlaceholderText("Search messages...")
        self.lineEdit_faculty.setStyleSheet("""
            QLineEdit {
                color: black;
                background-color: #f0f0f0;
                border-radius: 10px;
                border: 1px solid #ccc;
                padding: 5px 7px;
                font-size: 14px;
            }
            QLineEdit:focus { border: 1px solid #084924; }
            QLineEdit:hover {
                border: 1px solid #888;
                background-color: #e9e9e9;
            }
        """)
        search_layout.addWidget(self.lineEdit_faculty)

        self.comboBox_prio = QtWidgets.QComboBox()
        self.comboBox_prio.addItems(["All Priorities", "Urgent", "High", "Normal"])
        self.comboBox_prio.setStyleSheet("""
            QComboBox {
                color: black;
                background-color: #f7f7f7;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 14px;
            }
            QComboBox QAbstractItemView {
                color: black;
                background-color: #f7f7f7;
            }
            QComboBox:hover {
                border: 1px solid #888;
                background-color: #e9e9e9;
            }
            QComboBox:focus {
                border: 1px solid #084924;
            }
        """)
        search_layout.addWidget(self.comboBox_prio)

        self.comboBox_stat = QtWidgets.QComboBox()
        self.comboBox_stat.addItems(["All Status", "Pending", "Sent", "Resolved"])
        self.comboBox_stat.setStyleSheet(self.comboBox_prio.styleSheet())
        search_layout.addWidget(self.comboBox_stat)

        self.chat_info.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.chat_info.setFixedHeight(64)
        center_layout.addWidget(self.chat_info, 0, QtCore.Qt.AlignmentFlag.AlignTop)

        self.message_widget = QtWidgets.QWidget(parent=center_widget)
        self.message_widget.setObjectName("message_widget")
        self.message_widget.setStyleSheet("""
            QWidget#message_widget {
                background-color: white;
                border-radius: 16px;
                border: 1px solid #e0e0e0;
                padding: 10px;
            }
        """)
        message_layout = QtWidgets.QVBoxLayout(self.message_widget)
        message_layout.setContentsMargins(8, 8, 8, 8)
        message_layout.setSpacing(8)

        self.messages_scroll = QtWidgets.QScrollArea()
        self.messages_scroll.setWidgetResizable(True)
        self.messages_container = QtWidgets.QWidget()
        self.messages_list_layout = QtWidgets.QVBoxLayout(self.messages_container)
        self.messages_list_layout.addStretch()
        self.messages_scroll.setWidget(self.messages_container)
        message_layout.addWidget(self.messages_scroll)
        center_layout.addWidget(self.message_widget, 1)

        parent_layout.addWidget(center_widget, stretch=1)

    # -------------------- Button Connections --------------------
    def connect_buttons(self):
        self.push_all.clicked.connect(lambda: self.filter_messages("all"))
        self.push_unread.clicked.connect(lambda: self.filter_messages("unread"))
        self.push_acadin.clicked.connect(lambda: self.filter_messages("academic"))
        self.push_assgt.clicked.connect(lambda: self.filter_messages("assignment"))
        self.push_office.clicked.connect(lambda: self.filter_messages("office"))
        self.push_compose.clicked.connect(self.compose_message)
        self.comboBox_prio.currentTextChanged.connect(self.apply_filters)
        self.comboBox_stat.currentTextChanged.connect(self.apply_filters)
        self.lineEdit_faculty.textChanged.connect(self.search_messages)

    # -------------------- Data Loading --------------------
    def load_faculty_data(self):
        if not self.data_manager or not self.current_faculty_id:
            return
        try:
            faculty = self.data_manager.get_user(self.current_faculty_id)
            print("[FacultyMainUI] faculty:", faculty)
        except Exception as e:
            print(f"[FacultyMainUI] Error loading faculty data: {e}")

    def load_messages(self):
        """
        Load messages visible to this faculty:

        - direct messages where this faculty is the receiver
        - inquiries where this faculty is the receiver
        """
        if not self.data_manager or not self.current_faculty_id:
            return
        try:
            messages = self.data_manager.get_all_messages(force=True)
            print(f"[FacultyMainUI] fetched {len(messages)} messages from API")

            print("\n[FacultyMainUI] ---- load_messages ----")
            print(f"[FacultyMainUI] total messages in data: {len(messages)}")
            print(f"[FacultyMainUI] current_faculty_id: {self.current_faculty_id}")

            faculty_messages = [
                m for m in messages
                if m.get("receiver") == self.current_faculty_id
            ]
            print(f"[FacultyMainUI] faculty_messages (receiver={self.current_faculty_id}):")
            for m in faculty_messages:
                print(
                    f"  msg id={m.get('id')} conv={m.get('conversation')} "
                    f"created_at={m.get('created_at')} content={m.get('content')!r}"
                )

            faculty_inquiries = []
            try:
                faculty_inquiries = self.data_manager.get_inquiries_by_faculty(
                    self.current_faculty_id
                )
            except Exception as e:
                print(f"[FacultyMainUI] Error calling get_inquiries_by_faculty: {e}")

            print(f"[FacultyMainUI] faculty_inquiries count: {len(faculty_inquiries)}")
            for inq in faculty_inquiries:
                print(
                    f"  inquiry id={inq.get('id')} conv={inq.get('conversation')} "
                    f"created_at={inq.get('created_at')} desc={inq.get('description')!r}"
                )

            def _get_conv_id(raw: dict):
                conv_field = raw.get("conversation")
                if isinstance(conv_field, dict):
                    return conv_field.get("id")
                return conv_field

            latest_by_conv: dict[int, dict] = {}

            # show messages per conversation BEFORE picking latest
            conv_groups: dict[int, list[dict]] = {}
            for m in faculty_messages:
                cid = _get_conv_id(m)
                if not cid:
                    continue
                conv_groups.setdefault(cid, []).append(m)

            print("[FacultyMainUI] faculty_messages grouped by conversation:")
            for cid, group in conv_groups.items():
                print(f"  conv {cid}:")
                for m in group:
                    print(
                        f"    msg id={m.get('id')} created_at={m.get('created_at')} "
                        f"content={m.get('content')!r}"
                    )

            # pick latest per conversation (by created_at)
            for msg in faculty_messages:
                conv_id = _get_conv_id(msg)
                if not conv_id:
                    continue
                existing = latest_by_conv.get(conv_id)
                if (not existing) or (msg.get("created_at", "") > existing.get("created_at", "")):
                    latest_by_conv[conv_id] = msg

            print("[FacultyMainUI] latest_by_conv chosen per conversation:")
            for conv_id, msg in latest_by_conv.items():
                print(
                    f"  conv {conv_id}: latest_msg_id={msg.get('id')} "
                    f"created_at={msg.get('created_at')} content={msg.get('content')!r}"
                )

            all_items = []

            # one card per conversation (last direct message)
            for conv_id, msg in latest_by_conv.items():
                has_inquiry = any(_get_conv_id(inq) == conv_id for inq in faculty_inquiries)
                if has_inquiry:
                    continue
                sender_name = msg.get("sender_name") or "Unknown"
                all_items.append({
                    "type": "message",
                    "id": msg.get("id"),
                    "conversation_id": conv_id,
                    "title": msg.get("subject", "No Subject"),
                    "content": msg.get("content", ""),
                    "sender": sender_name,
                    "priority": msg.get("priority", "normal"),
                    "status": msg.get("status", "pending"),
                    "date": msg.get("created_at", ""),
                    "is_read": msg.get("is_read", False),
                })

            # one card per inquiry conversation
            for inq in faculty_inquiries:
                conv_id = _get_conv_id(inq)

                latest_msg = latest_by_conv.get(conv_id)
                latest_content = (
                    latest_msg.get("content", "")
                    if latest_msg is not None
                    else inq.get("description", "")
                )

                print(
                    f"[FacultyMainUI] inquiry card for conv {conv_id}: "
                    f"latest_msg_id={latest_msg and latest_msg.get('id')} "
                    f"latest_content={latest_content!r}"
                )

                sender_name = inq.get("sender_name") or "Unknown"
                all_items.append({
                    "type": "inquiry",
                    "id": inq.get("id"),
                    "conversation_id": conv_id,
                    "title": inq.get("subject", "No Subject"),
                    "content": latest_content,
                    "sender": sender_name,
                    "priority": inq.get("priority", "normal"),
                    "status": inq.get("status", "pending"),
                    "date": inq.get("created_at", ""),
                    "is_read": True,
                })

            all_items.sort(key=lambda x: x["date"], reverse=True)
            print("[FacultyMainUI] final all_items:")
            for it in all_items:
                print(
                    f"  item type={it['type']} conv={it['conversation_id']} "
                    f"id={it['id']} date={it['date']} content={it['content']!r}"
                )

            self.all_items = all_items
            self.text_filtered_items = all_items.copy()
            self.filtered_items = all_items.copy()
            self.display_items()
        except Exception as e:
            print(f"[FacultyMainUI] Error loading messages: {e}")


    # -------------------- Display --------------------
    def display_items(self):
        layout = self.messages_list_layout
        while layout.count() > 1:
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not self.filtered_items:
            empty = QtWidgets.QLabel("No messages found!")
            empty.setStyleSheet("color: #888888; font-size: 16px;")
            empty.setWordWrap(True)
            layout.insertWidget(0, empty)
            return

        for itm in self.filtered_items:
            try:
                card = self.create_message_card(itm)
                layout.insertWidget(layout.count() - 1, card)
            except Exception as e:
                print(f"[FacultyMainUI] Error creating card: {e}")

    # -------------------- Cards --------------------
    def create_message_card(self, item):
        card = QtWidgets.QFrame()
        card.setFrameStyle(QtWidgets.QFrame.Shape.NoFrame)
        card.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        card.setAttribute(QtCore.Qt.WidgetAttribute.WA_Hover, True)
        card.setMouseTracking(True)

        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        header_layout = QtWidgets.QHBoxLayout()
        sender_label = QtWidgets.QLabel(item['sender'])
        sender_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #084924;")
        header_layout.addWidget(sender_label)
        header_layout.addStretch()

        status_color = {'pending': '#fbbf24', 'sent': '#10b981', 'resolved': '#6b7280'}.get(item['status'], '#6b7280')
        status_label = QtWidgets.QLabel(item['status'].upper())
        status_label.setStyleSheet(
            f"background-color: {status_color}; color: white; padding: 2px 8px; "
            "border-radius: 10px; font-size: 10px; font-weight: bold;"
        )
        header_layout.addWidget(status_label)
        layout.addLayout(header_layout)

        title_label = QtWidgets.QLabel(item['title'])
        title_label.setWordWrap(True)
        title_label.setStyleSheet("color: black;")
        layout.addWidget(title_label)

        content_preview = item['content'][:100] + "..." if len(item['content']) > 100 else item['content']
        content_label = QtWidgets.QLabel(content_preview)
        content_label.setWordWrap(True)
        content_label.setStyleSheet("color: black;")
        layout.addWidget(content_label)

        footer_layout = QtWidgets.QHBoxLayout()
        date_label = QtWidgets.QLabel(item['date'][:10] if item.get('date') else 'Unknown')
        date_label.setStyleSheet("color: black;")
        footer_layout.addWidget(date_label)
        footer_layout.addStretch()
        priority_label = QtWidgets.QLabel(item['priority'].upper())
        priority_label.setStyleSheet("color: black;")
        footer_layout.addWidget(priority_label)
        layout.addLayout(footer_layout)

        card.mousePressEvent = lambda event, item=item: self.on_message_clicked(item)
        return card

    # -------------------- Message Dialog + Reply --------------------
    # (rest of your methods: on_message_clicked, filter_messages, apply_filters,
    #  search_messages, compose_message) stay exactly as you posted


    # -------------------- Message Dialog + Reply --------------------
    def on_message_clicked(self, item):
        print("\n[FacultyUI] on_message_clicked item:", item)

        conv_id = item.get("conversation") or item.get("conversation_id")
        print("[FacultyUI] conversation id for dialog:", conv_id)

        # mark last message as read
        try:
            if item.get("type") == "message" and item.get("id"):
                print(f"[FacultyUI] Marking message {item.get('id')} as read")
                self.data_manager.update_message(item["id"], {"is_read": True})
        except Exception as e:
            print(f"Error updating message read status: {e}")

        # load full message thread for this conversation
        try:
            all_msgs = self.data_manager.get_all_messages()
        except Exception as e:
            print(f"[FacultyMainUI] Error getting all messages for dialog: {e}")
            all_msgs = []

        def _get_conv_id(raw: dict):
            conv_field = raw.get("conversation")
            if isinstance(conv_field, dict):
                return conv_field.get("id")
            return conv_field

        thread_msgs = [m for m in all_msgs if _get_conv_id(m) == conv_id]
        thread_msgs.sort(key=lambda m: m.get("created_at", ""))

        if not thread_msgs:
            thread_msgs = []

        # find current index (the message corresponding to card)
        current_index = 0
        for idx, m in enumerate(thread_msgs):
            if m.get("id") == item.get("id"):
                current_index = idx
                break
        else:
            if thread_msgs:
                current_index = len(thread_msgs) - 1

        print("[FacultyUI] thread message count:", len(thread_msgs), "start index:", current_index)

        try:
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowFlags(
                QtCore.Qt.WindowType.FramelessWindowHint |
                QtCore.Qt.WindowType.Dialog
            )
            dialog.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
            dialog.setStyleSheet("background: transparent;")

            ui = Ui_Form()
            ui.setupUi(dialog)

            # bottom widget/layout tweaks
            ui.widget1.setMinimumWidth(0)
            ui.horizontalLayout_2.setContentsMargins(10, 0, 10, 0)
            ui.horizontalLayout_2.setSpacing(8)

            ui.btn_reply.setText("Reply")
            ui.btn_resolve.setText("Resolved")
            ui.btn_fwd.setText("Forward")

            # prev / next buttons
            btn_prev = QtWidgets.QPushButton("Previous", parent=ui.widget1)
            btn_prev.setObjectName("btn_prev")
            btn_prev.setStyleSheet(
                "QPushButton {"
                "  background-color: transparent;"
                "  color: black;"
                "  padding: 6px 12px;"
                "  border: 1px solid #cccccc;"
                "  border-radius: 6px;"
                "  font-weight: bold;"
                "}"
                "QPushButton:hover {"
                "  background-color: #e0e0e0;"
                "}"
            )
            btn_prev.setSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum,
                                   QtWidgets.QSizePolicy.Policy.Fixed)

            btn_next = QtWidgets.QPushButton("Next", parent=ui.widget1)
            btn_next.setObjectName("btn_next")
            btn_next.setStyleSheet(btn_prev.styleSheet())
            btn_next.setSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum,
                                   QtWidgets.QSizePolicy.Policy.Fixed)

            hl = ui.horizontalLayout_2
            while hl.count():
                it = hl.takeAt(0)
                w = it.widget()
                if w:
                    w.setParent(None)

            hl.addWidget(ui.btn_reply)
            hl.addWidget(ui.btn_resolve)
            hl.addWidget(ui.btn_fwd)
            hl.addStretch()
            hl.addWidget(btn_prev)
            hl.addWidget(btn_next)

            ui.btn_prev = btn_prev
            ui.btn_next = btn_next

            # Delete button
            btn_delete = QtWidgets.QPushButton("Delete")
            btn_delete.setObjectName("btn_delete")
            btn_delete.setStyleSheet(
                "QPushButton {"
                "  background-color: #dc2626;"
                "  color: white;"
                "  padding: 6px 12px;"
                "  border-radius: 6px;"
                "  font-weight: bold;"
                "}"
                "QPushButton:hover {"
                "  background-color: #b91c1c;"
                "}"
            )
            btn_delete.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Maximum,
                QtWidgets.QSizePolicy.Policy.Fixed
            )

            hl.addWidget(btn_delete)
            ui.btn_delete = btn_delete
            conv_id_for_delete = conv_id

            def handle_delete_conversation():
                if not conv_id_for_delete or not self.data_manager:
                    return

                reply = QtWidgets.QMessageBox.question(
                    dialog,
                    "Delete Conversation",
                    "This will delete the entire conversation and all its messages. Continue?",
                    QtWidgets.QMessageBox.StandardButton.Yes
                    | QtWidgets.QMessageBox.StandardButton.No,
                    QtWidgets.QMessageBox.StandardButton.No,
                    )
                if reply != QtWidgets.QMessageBox.StandardButton.Yes:
                    return

                try:
                    self.data_manager.delete_conversation(conv_id_for_delete)
                    self.load_messages()
                    dialog.accept()
                except Exception as e:
                    QtWidgets.QMessageBox.critical(
                        dialog,
                        "Error",
                        f"Failed to delete conversation:\n{e}",
                    )

            ui.btn_delete.clicked.connect(handle_delete_conversation)

            # assume two participants: student + this faculty
            student_id = None
            for m in thread_msgs:
                sid = m.get("sender")
                if sid and sid != self.current_faculty_id:
                    student_id = sid
                    break

            def _render_current():
                if not thread_msgs:
                    ui.textEdit_body.setPlainText("No messages in this conversation.")
                    return

                msg = thread_msgs[current_index]
                sender_name = msg.get("sender_name") or item.get("sender", "Unknown")
                ui.label_header.setText(sender_name)
                ui.label_recipient.setText("Date:")
                ui.label_email.setText("")
                ui.label_day.setText(msg.get("created_at", "")[:19].replace("T", " "))

                base_text = msg.get("content") or msg.get("subject") or item.get("content", "")

                # find reply pair
                reply_text = ""
                if student_id and msg.get("sender") == student_id:
                    # look forward for faculty reply
                    for j in range(current_index + 1, len(thread_msgs)):
                        if thread_msgs[j].get("sender") == self.current_faculty_id:
                            reply_text = thread_msgs[j].get("content", "")
                            break
                elif student_id and msg.get("sender") == self.current_faculty_id:
                    # faculty message, show previous student message as "Original"
                    for j in range(current_index - 1, -1, -1):
                        if thread_msgs[j].get("sender") == student_id:
                            base_text = (
                                f"Original: {thread_msgs[j].get('content', '')}\n\n"
                                f"Reply: {msg.get('content', '')}"
                            )
                            reply_text = ""
                            break

                if reply_text:
                    full_text = f"{base_text}\n\nReply: {reply_text}"
                else:
                    full_text = base_text

                ui.textEdit_body.setPlainText(full_text)
                ui.textEdit_body.setReadOnly(True)
                ui.textEdit_body.setStyleSheet(
                    "QTextEdit#textEdit_body {"
                    "  background-color: #f9f9f9;"
                    "  border: 1px solid #ddd;"
                    "  border-radius: 8px;"
                    "  padding: 8px;"
                    "  font-size: 14px;"
                    "  color: black;"
                    "}"
                )

            def _update_nav_buttons():
                ui.btn_prev.setEnabled(current_index > 0)
                ui.btn_next.setEnabled(current_index < len(thread_msgs) - 1)

            def go_prev():
                nonlocal current_index
                if current_index > 0:
                    current_index -= 1
                    _render_current()
                    _update_nav_buttons()

            def go_next():
                nonlocal current_index
                if current_index < len(thread_msgs) - 1:
                    current_index += 1
                    _render_current()
                    _update_nav_buttons()

            ui.btn_prev.clicked.connect(go_prev)
            ui.btn_next.clicked.connect(go_next)

            dialog.resize(self.width(), self.height())
            dialog.move(self.mapToGlobal(QtCore.QPoint(0, 0)))
            frame = ui.message_frame
            frame.adjustSize()
            dw, dh = dialog.width(), dialog.height()
            fw, fh = frame.width(), frame.height()
            frame.move(max(0, (dw - fw) // 2), max(0, (dh - fh) // 2))

            ui.btn_close.clicked.connect(dialog.accept)

            def handle_reply():
                print("[FacultyUI] handle_reply called")

                if not thread_msgs:
                    return

                reply_dialog = QtWidgets.QDialog(self)
                reply_dialog.setWindowFlags(
                    QtCore.Qt.WindowType.FramelessWindowHint |
                    QtCore.Qt.WindowType.Dialog
                )
                reply_dialog.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
                reply_dialog.setStyleSheet("background: transparent;")

                compose_ui = ComposeUI()
                compose_ui.setupUi(reply_dialog)

                # display only; id will be taken from student_id
                compose_ui.lineEdit_to.setText(
                    thread_msgs[0].get("sender_name", "Unknown")
                )
                subject_base = thread_msgs[current_index].get("subject") or item.get("title", "")
                compose_ui.lineEdit_subject.setText(f"Re: {subject_base}")

                compose_ui.textEdit_msg.clear()
                compose_ui.label_placeholder.setVisible(True)

                def hide_placeholder():
                    compose_ui.label_placeholder.setVisible(False)
                compose_ui.textEdit_msg.textChanged.connect(hide_placeholder)

                backend_prio = (item.get("priority") or "").lower()
                print("[FacultyUI] original backend_prio:", backend_prio)
                priority_map = {
                    "urgent": "High Priority",
                    "high": "High Priority",
                    "normal": "Medium Priority",
                    "low": "Low Priority",
                }
                target_text = priority_map.get(backend_prio, "Medium Priority")
                idx = compose_ui.comboBox_prio.findText(target_text)
                if idx >= 0:
                    compose_ui.comboBox_prio.setCurrentIndex(idx)

                def send_reply():
                    # use numeric student_id as receiver
                    if not student_id:
                        QtWidgets.QMessageBox.warning(
                            reply_dialog, "Invalid Recipient", "Could not determine recipient."
                        )
                        return

                    receiver_id = student_id
                    receiver = self.data_manager.get_user(receiver_id)
                    if not receiver:
                        QtWidgets.QMessageBox.warning(
                            reply_dialog, "Invalid Recipient", "Recipient not found."
                        )
                        return

                    content = compose_ui.textEdit_msg.toPlainText().strip()
                    if not content:
                        QtWidgets.QMessageBox.warning(
                            reply_dialog, "Empty Message", "Message content cannot be empty."
                        )
                        return

                    prio_text = compose_ui.comboBox_prio.currentText()
                    prio_map = {
                        "High Priority": "high",
                        "Medium Priority": "normal",
                        "Low Priority": "low",
                        "": "normal",
                    }
                    backend_priority = prio_map.get(prio_text, "normal")

                    msg_payload = {
                        "conversation": conv_id,
                        "subject": compose_ui.lineEdit_subject.text().strip() or "No Subject",
                        "content": content,
                        "priority": backend_priority,
                        "status": "sent",
                        "message_type": "message",
                        "receiver": receiver_id,
                    }
                    print("[FacultyUI] reply msg_payload:", msg_payload)

                    try:
                        created = self.data_manager.create_message(msg_payload)
                        print("[FacultyUI] create_message response:", created)
                        if isinstance(created, dict):
                            thread_msgs.append(created)
                            thread_msgs.sort(key=lambda m: m.get("created_at", ""))
                    except Exception as e:
                        print("[FacultyUI] ERROR creating reply:", e)
                        QtWidgets.QMessageBox.critical(
                            reply_dialog, "Error", f"Failed to send reply:\n{e}"
                        )
                        return

                    QtWidgets.QMessageBox.information(
                        reply_dialog, "Sent", "Message sent successfully."
                    )
                    self.load_messages()
                    reply_dialog.accept()
                    _render_current()
                    _update_nav_buttons()

                compose_ui.btn_send.clicked.connect(send_reply)
                compose_ui.btn_cancel.clicked.connect(reply_dialog.reject)
                compose_ui.btn_close.clicked.connect(reply_dialog.reject)

                reply_dialog.exec()

            ui.btn_reply.clicked.connect(handle_reply)

            _render_current()
            _update_nav_buttons()

            dialog.exec()
        except Exception as e:
            print(f"Error opening dialog: {e}")





    # -------------------- Category Filter --------------------
    def filter_messages(self, filter_type):
        try:
            if filter_type == "all":
                base = self.all_items.copy()
            elif filter_type == "unread":
                base = [i for i in self.all_items if not i.get('is_read', True)]
            elif filter_type == "academic":
                base = [i for i in self.all_items if i['type'] == 'inquiry']
            elif filter_type == "assignment":
                base = [i for i in self.all_items if 'assignment' in i['title'].lower()]
            elif filter_type == "office":
                base = [i for i in self.all_items if 'office' in i['title'].lower()]
            else:
                base = self.all_items.copy()

            self.text_filtered_items = base.copy()
            self.apply_filters()
        except Exception as e:
            print(f"Error filtering messages: {e}")

    # -------------------- Priority + Status Filters --------------------
    def apply_filters(self):
        try:
            base = self.text_filtered_items if self.text_filtered_items else self.all_items
            filtered = base.copy()

            prio = self.comboBox_prio.currentText()
            status = self.comboBox_stat.currentText()

            if prio != "All Priorities":
                priority_map = {"Urgent": "urgent", "High": "high", "Normal": "normal"}
                filtered = [
                    i for i in filtered
                    if i['priority'] == priority_map.get(prio, i['priority'])
                ]

            if status != "All Status":
                status_map = {"Pending": "pending", "Sent": "sent", "Resolved": "resolved"}
                filtered = [
                    i for i in filtered
                    if i['status'] == status_map.get(status, i['status'])
                ]

            self.filtered_items = filtered
            self.display_items()
        except Exception as e:
            print(f"Error applying filters: {e}")

    # -------------------- Search by sender prefix --------------------
    def search_messages(self, text):
        try:
            s = text.lower().strip()
            if not s:
                self.text_filtered_items = self.all_items.copy()
            else:
                self.text_filtered_items = [
                    i for i in self.all_items
                    if i['sender'].lower().startswith(s)
                ]
            self.apply_filters()
        except Exception as e:
            print(f"Error searching messages: {e}")

    # -------------------- Compose (new message) --------------------
    def compose_message(self):
        try:
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowFlags(
                QtCore.Qt.WindowType.FramelessWindowHint
                | QtCore.Qt.WindowType.Dialog
            )
            dialog.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
            dialog.setStyleSheet("background: transparent;")

            ui = ComposeUI()
            ui.setupUi(dialog)

            ui.btn_cancel.clicked.connect(dialog.reject)
            ui.btn_close.clicked.connect(dialog.reject)

            ui.textEdit_msg.clear()
            ui.label_placeholder.setVisible(True)

            def hide_placeholder():
                ui.label_placeholder.setVisible(False)
                ui.textEdit_msg.textChanged.connect(hide_placeholder)

            ui.textEdit_msg.textChanged.connect(hide_placeholder)
            def send_new_message():
                receiver_username = ui.lineEdit_to.text().strip()
                print("[DEBUG] compose TO raw:", receiver_username)

                if not receiver_username:
                    QtWidgets.QMessageBox.warning(
                        dialog, "Invalid Recipient", "Receiver username is required."
                    )
                    return

                receiver_id = self.data_manager.get_user_id_by_username(receiver_username)
                print("[DEBUG] resolved receiver_id:", receiver_id)
                if not receiver_id:
                    QtWidgets.QMessageBox.warning(
                        dialog, "Invalid Recipient", "Recipient not found."
                    )
                    return

                receiver = self.data_manager.get_user(receiver_id)
                if not receiver:
                    QtWidgets.QMessageBox.warning(
                        dialog, "Invalid Recipient", "Recipient not found."
                    )
                    return

                content = ui.textEdit_msg.toPlainText().strip()
                if not content:
                    QtWidgets.QMessageBox.warning(
                        dialog, "Empty Message", "Message content cannot be empty."
                    )
                    return

                conv_id = self._get_or_create_conversation_with_user_id(receiver_id)
                if not conv_id:
                    QtWidgets.QMessageBox.critical(
                        dialog, "Error", "Failed to create or find a conversation."
                    )
                    return

                prio_text = ui.comboBox_prio.currentText()
                prio_map = {
                    "High Priority": "high",
                    "Medium Priority": "normal",
                    "Low Priority": "normal",
                    "": "normal",
                }
                backend_priority = prio_map.get(prio_text, "normal")

                msg_payload = {
                    "conversation": conv_id,
                    "subject": ui.lineEdit_subject.text().strip() or "No Subject",
                    "content": content,
                    "priority": backend_priority,
                    "status": "sent",
                    "message_type": "message",
                    "receiver": receiver_id,
                }
                print("[DEBUG] new msg_payload:", msg_payload)

                try:
                    created = self.data_manager.create_message(msg_payload)
                    print("[FacultyUI] create_message response:", created)
                    QtWidgets.QMessageBox.information(
                        dialog, "Sent", "Message sent successfully."
                    )
                except Exception as e:
                    print("[FacultyUI] ERROR creating message:", e)
                    QtWidgets.QMessageBox.critical(
                        dialog, "Error", f"Failed to send message:\n{e}"
                    )
                    return

                self.load_messages()
                dialog.accept()


            ui.btn_send.clicked.connect(send_new_message)
            dialog.exec()
        except Exception as e:
            print(f"Error composing message: {e}")

    def _get_or_create_conversation_with_user_id(self, receiver_id: int) -> int | None:
        """
        Find or create a direct conversation between this faculty and the
        user with the given id. Returns conversation id or None.
        """
        if not self.data_manager or not self.current_faculty_id:
            return None

        if not receiver_id or receiver_id == self.current_faculty_id:
            return None

        # look for existing conversation with both participants
        convs = self.data_manager.get_conversations_by_user(self.current_faculty_id)
        for c in convs:
            participants = c.get("participants", []) or []
            if self.current_faculty_id in participants and receiver_id in participants:
                return c.get("id")

        # else create a new direct conversation
        payload = {
            "title": "",
            "type": "direct",
            "participants": [self.current_faculty_id, receiver_id],
            "creator": self.current_faculty_id,
        }
        created = self.data_manager.create_conversation(payload)
        if isinstance(created, dict):
            return created.get("id")
        return None

