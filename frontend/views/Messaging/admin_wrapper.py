import sys
import json
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWebSockets import QWebSocket

print("[AdminMainUI] Starting module import...")

try:
    from .data_manager import DataManager
    print("[AdminMainUI] Imported DataManager successfully")
    from .admin.admin_details import Ui_Form
except Exception as e:
    print(f"[AdminMainUI] ERROR importing modules: {e}")
    DataManager = None


class AdminMainUI(QtWidgets.QWidget):
    """Admin Dashboard - manual UI + DataManager + header + WebSocket."""

    def __init__(self, username=None, roles=None, primary_role=None, token=None,
                 data_manager=None, parent=None, layout=None):
        super().__init__(parent)
        print("[AdminMainUI] __init__ called")
        self.setObjectName("AdminMainUI")

        # ---- session / auth ----
        self.username = username
        self.roles = roles or ["admin"]
        self.primary_role = primary_role or "admin"
        self.token = token

        # DataManager
        self.data_manager = data_manager
        if self.data_manager is None and DataManager is not None:
            try:
                self.data_manager = DataManager(
                    username=self.username,
                    roles=self.roles,
                    primary_role=self.primary_role,
                    token=self.token,
                )
                print("[AdminMainUI] DataManager created successfully")
            except Exception as e:
                print(f"[AdminMainUI] ERROR creating DataManager: {e}")
                self.data_manager = None

        self.current_admin_id = (
            self.data_manager.get_current_user_id() if self.data_manager else None
        )
        self.last_broadcast_id = None
        self.all_items = []
        self.filtered_items = []
        self.stat_labels = {}

        # ========== HEADER FROM LAYOUT MANAGER ==========
        self.header = layout.get_header() if layout is not None else None

        # ========== ROOT LAYOUT ==========
        root_layout = QtWidgets.QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ---- Content area ----
        content_widget = QtWidgets.QWidget(parent=self)
        content_layout = QtWidgets.QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 8, 0, 8)
        content_layout.setSpacing(8)

        self.admin_content = QtWidgets.QWidget(parent=content_widget)
        self.admin_content.setObjectName("admin_content")
        try:
            self.setup_admin_content()
        except Exception as e:
            print(f"[AdminMainUI] ERROR in setup_admin_content: {e}")
        content_layout.addWidget(self.admin_content, stretch=1)

        root_layout.addWidget(content_widget)
        print("[AdminMainUI] Layouts set up")

        # ---- header inbox click -> open message ----
        if self.header is not None and hasattr(self.header, "mail_menu"):
            self.header.mail_menu.messageActivated.connect(
                self._on_inbox_item_clicked
            )

        # Connect buttons
        try:
            self.connect_buttons()
            print("[AdminMainUI] Buttons connected")
        except Exception as e:
            print(f"[AdminMainUI] ERROR in connect_buttons: {e}")

        # Load data
        try:
            self._load_dashboard_counts()
            self._load_messages()
            self._refresh_inbox_popup()
            print("[AdminMainUI] Initial data loaded")
        except Exception as e:
            print(f"[AdminMainUI] Error loading initial data: {e}")

        # WebSocket for realtime broadcasts/messages
        self._init_broadcast_ws()

    def _refresh_inbox_popup(self):
        if not self.data_manager or not self.current_admin_id or not self.header:
            return
        msgs = self.data_manager.get_message_summaries_for_user(self.current_admin_id)
        for m in msgs:
            body = m.get("content", "") or ""
            m["preview"] = body[:60] + "..." if len(body) > 60 else body
        if hasattr(self.header, "mail_menu"):
            self.header.mail_menu.set_messages(msgs)

    # ---------------- WebSocket ----------------
    def _init_broadcast_ws(self):
        if not self.data_manager:
            print("[AdminMainUI] No data_manager, skipping WS init")
            return
        try:
            self.broadcast_ws = QWebSocket()
            self.broadcast_ws.textMessageReceived.connect(
                self._on_broadcast_ws_message
            )
            url = QtCore.QUrl("ws://127.0.0.1:8001/ws/broadcasts/")
            print("[AdminMainUI] Connecting broadcast WS:", url.toString())
            self.broadcast_ws.open(url)
        except Exception as e:
            print("[AdminMainUI] _init_broadcast_ws error:", e)

    def _on_broadcast_ws_message(self, msg: str):
        try:
            data = json.loads(msg)
            print("[AdminMainUI] Received WS message:", data)

            msg_type = data.get("type", "broadcast")
            msg_id = data.get("id")

            if msg_type == "broadcast":
                if self.last_broadcast_id == msg_id:
                    return
                self.last_broadcast_id = msg_id
                self._show_broadcast_popup(data)
            elif msg_type == "message":
                # refresh admin messages + inbox
                self._load_messages()
                self._refresh_inbox_popup()
        except Exception as e:
            print("[AdminMainUI] _on_broadcast_ws_message error:", e)

    def _show_broadcast_popup(self, msg: dict):
        dialog = QtWidgets.QDialog(self)

        shadow = QtWidgets.QGraphicsDropShadowEffect(dialog)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QtGui.QColor(0, 0, 0, 120))
        dialog.setGraphicsEffect(shadow)

        dialog.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        dialog.resize(600, 300)

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

        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch()
        close_bottom = QtWidgets.QPushButton("Close")
        close_bottom.clicked.connect(dialog.accept)
        btn_layout.addWidget(close_bottom)
        body_layout.addLayout(btn_layout)

        layout.addWidget(body)
        dialog.exec()

    # --------------- Header inbox helpers ---------------
    def _refresh_inbox_popup(self):
        if not self.data_manager or not self.current_admin_id:
            return
        try:
            msgs = self.data_manager.get_message_summaries_for_user(self.current_admin_id)
            for m in msgs:
                body = m.get("content", "") or ""
                m["preview"] = body[:60] + "..." if len(body) > 60 else body
            self.header.mail_menu.set_messages(msgs)
        except Exception as e:
            print("[AdminMainUI] _refresh_inbox_popup error:", e)

    def _on_inbox_item_clicked(self, msg: dict):
        """When an inbox item is clicked from the header dropdown."""
        print("[AdminMainUI] Inbox item clicked:", msg)
        # Map to your existing message-card shape and reuse the same dialog logic
        mapped = {
            "id": msg.get("id"),
            "title": msg.get("subject", "No Subject"),
            "content": msg.get("content", ""),
            "sender": msg.get("sender_name") or msg.get("sender_email") or "Unknown",
            "priority": msg.get("priority", "normal"),
            "status": msg.get("status", "pending"),
            "date": msg.get("created_at", ""),
            "department": msg.get("department", "System"),
        }
        # if you have a method like self._open_message_details(mapped):
        if hasattr(self, "_open_message_details"):
            self._open_message_details(mapped)

    # -------------------- Setup Content --------------------
    def setup_admin_content(self):
        print("[AdminMainUI] setup_admin_content start")
        admin_layout = QtWidgets.QHBoxLayout(self.admin_content)
        admin_layout.setContentsMargins(0, 0, 0, 0)
        admin_layout.setSpacing(8)

        self.setup_left_panel(admin_layout)
        self.setup_center_panel(admin_layout)
        print("[AdminMainUI] setup_admin_content end")

    # ... keep the rest of your existing methods:
    # setup_left_panel, setup_center_panel, connect_buttons,
    # _load_dashboard_counts, _load_messages, _create_message_card, filters, etc.

    def setup_left_panel(self, parent_layout):
        print("[AdminMainUI] setup_left_panel start")
        self.category_widget = QtWidgets.QWidget(parent=self.admin_content)
        self.category_widget.setMinimumWidth(251)
        self.category_widget.setMaximumWidth(280)
        self.category_widget.setObjectName("category_widget")
        self.category_widget.setStyleSheet("""
            QWidget#category_widget {
                background-color: white;
                border-radius: 20px;
                border: 1px solid #dddddd;
            }
        """)

        layout = QtWidgets.QVBoxLayout(self.category_widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Message Category Header
        label_header = QtWidgets.QLabel("Message Category")
        label_header.setFont(QtGui.QFont("Arial", 14))
        label_header.setStyleSheet("color: #084924; font-weight: bold;")
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
        self.push_all = QtWidgets.QPushButton("All messages")
        self.push_all.setStyleSheet(button_style)
        self.push_critical = QtWidgets.QPushButton("Critical Issues")
        self.push_critical.setStyleSheet(button_style)
        self.push_system = QtWidgets.QPushButton("System Issues")
        self.push_system.setStyleSheet(button_style)
        self.push_technical = QtWidgets.QPushButton("Technical Support")
        self.push_technical.setStyleSheet(button_style)

        for btn in [self.push_all, self.push_critical, self.push_system, self.push_technical]:
            layout.addWidget(btn)

        layout.addWidget(QtWidgets.QFrame(frameShape=QtWidgets.QFrame.Shape.HLine))

        # Admin Actions Header
        label_actions = QtWidgets.QLabel("Admin Actions")
        label_actions.setFont(QtGui.QFont("Arial", 12))
        label_actions.setStyleSheet("color: #084924; font-weight: bold;")
        layout.addWidget(label_actions)

        self.btn_broadcast = QtWidgets.QPushButton("System Broadcast")
        self.btn_broadcast.setStyleSheet(button_style)
        self.btn_report = QtWidgets.QPushButton("Generate Reports")
        self.btn_report.setStyleSheet(button_style)
        self.btn_settings = QtWidgets.QPushButton("System Settings")
        self.btn_settings.setStyleSheet(button_style)
        self.btn_user = QtWidgets.QPushButton("User Management")
        self.btn_user.setStyleSheet(button_style)

        for btn in [self.btn_broadcast, self.btn_report, self.btn_settings, self.btn_user]:
            layout.addWidget(btn)

        layout.addStretch()
        parent_layout.addWidget(self.category_widget)
        print("[AdminMainUI] setup_left_panel end")

    def setup_center_panel(self, parent_layout):
        print("[AdminMainUI] setup_center_panel start")
        center_widget = QtWidgets.QWidget(parent=self.admin_content)
        center_layout = QtWidgets.QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(8)

        # Dashboard Stats
        stats_layout = QtWidgets.QHBoxLayout()
        stats_layout.setSpacing(16)

        stat_cards = [
            ("Total Messages", "total_messages", "0 messages"),
            ("Critical Issues", "critical_issues", "Requires immediate action"),
            ("Pending Responses", "pending_responses", "Average response time 2 hrs"),
            ("Resolved Today", "resolved_today", "94% satisfaction rate"),
        ]

        for title, key, subtitle in stat_cards:
            card, number_label = self.create_stat_card(title, "0", subtitle)
            self.stat_labels[key] = number_label
            stats_layout.addWidget(card, stretch=1)

        center_layout.addLayout(stats_layout)

        # Search and filters
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

        self.lineEdit_search = QtWidgets.QLineEdit()
        self.lineEdit_search.setPlaceholderText("Search messages, users, etc")
        self.lineEdit_search.setStyleSheet("""
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
        search_layout.addWidget(self.lineEdit_search, stretch=1)

        self.comboBox_prio = QtWidgets.QComboBox()
        self.comboBox_prio.addItems(["All Priorities", "Urgent", "High", "Normal"])
        self.comboBox_prio.setStyleSheet(self._get_combobox_style())
        search_layout.addWidget(self.comboBox_prio)

        self.comboBox_stat = QtWidgets.QComboBox()
        self.comboBox_stat.addItems(["All Status", "Pending", "Sent", "Resolved"])
        self.comboBox_stat.setStyleSheet(self._get_combobox_style())
        search_layout.addWidget(self.comboBox_stat)

        self.comboBox_dept = QtWidgets.QComboBox()
        self.comboBox_dept.addItems(["All Departments", "IT", "HR", "Finance", "General"])
        self.comboBox_dept.setStyleSheet(self._get_combobox_style())
        search_layout.addWidget(self.comboBox_dept)

        self.chat_info.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.chat_info.setFixedHeight(64)
        center_layout.addWidget(self.chat_info, 0, QtCore.Qt.AlignmentFlag.AlignTop)

        # Messages widget
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

        label_title = QtWidgets.QLabel("System Messages")
        label_title.setFont(QtGui.QFont("Arial", 14))
        label_title.setStyleSheet("color: #084924; font-weight: bold;")
        message_layout.addWidget(label_title)

        self.messages_scroll = QtWidgets.QScrollArea()
        self.messages_scroll.setWidgetResizable(True)
        self.messages_container = QtWidgets.QWidget()
        self.messages_list_layout = QtWidgets.QVBoxLayout(self.messages_container)
        self.messages_list_layout.addStretch()
        self.messages_scroll.setWidget(self.messages_container)
        message_layout.addWidget(self.messages_scroll)
        center_layout.addWidget(self.message_widget, stretch=1)

        parent_layout.addWidget(center_widget, stretch=1)
        print("[AdminMainUI] setup_center_panel end")

    def create_stat_card(self, title, number, subtitle):
        """Create a statistics card. Returns (card_widget, number_label) for updating."""
        card = QtWidgets.QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
                padding: 15px;
            }
        """)
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        title_label = QtWidgets.QLabel(title)
        title_label.setStyleSheet("color: #084924; font-weight: bold; font-size: 12px;")
        layout.addWidget(title_label)

        number_label = QtWidgets.QLabel(number)
        number_label.setStyleSheet("color: black; font-size: 28px; font-weight: bold;")
        number_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(number_label)

        subtitle_label = QtWidgets.QLabel(subtitle)
        subtitle_label.setStyleSheet("color: #888888; font-size: 12px;")
        subtitle_label.setWordWrap(True)
        layout.addWidget(subtitle_label)

        return card, number_label

    def _get_combobox_style(self):
        return """
            QComboBox {
                color: black;
                background-color: #f7f7f7;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 12px;
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
        """

    # -------------------- Button Connections --------------------
    def connect_buttons(self):
        print("[AdminMainUI] connect_buttons start")
        # Category filters
        self.push_all.clicked.connect(lambda: self.filter_messages("all"))
        self.push_critical.clicked.connect(lambda: self.filter_messages("critical"))
        self.push_system.clicked.connect(lambda: self.filter_messages("system"))
        self.push_technical.clicked.connect(lambda: self.filter_messages("technical"))

        # Admin actions
        self.btn_broadcast.clicked.connect(self._on_broadcast)
        self.btn_report.clicked.connect(self._on_report)
        self.btn_settings.clicked.connect(self._on_settings)
        self.btn_user.clicked.connect(self._on_user_management)

        # Search and filters
        self.comboBox_prio.currentTextChanged.connect(self._apply_filters)
        self.comboBox_stat.currentTextChanged.connect(self._apply_filters)
        self.comboBox_dept.currentTextChanged.connect(self._apply_filters)
        self.lineEdit_search.textChanged.connect(self._search_items)
        print("[AdminMainUI] connect_buttons end")

    # -------------------- Data Loading & Display --------------------
    def _load_dashboard_counts(self):
        """Load dashboard statistics from DataManager."""
        if self.data_manager is None:
            print("[AdminMainUI] No data_manager, skipping counts")
            return

        try:
            stats = self.data_manager.get_admin_dashboard_stats()

            if "total_messages" in self.stat_labels:
                self.stat_labels["total_messages"].setText(str(stats.get("total_messages", 0)))
            if "critical_issues" in self.stat_labels:
                self.stat_labels["critical_issues"].setText(str(stats.get("critical_issues", 0)))
            if "pending_responses" in self.stat_labels:
                self.stat_labels["pending_responses"].setText(str(stats.get("pending_responses", 0)))
            if "resolved_today" in self.stat_labels:
                self.stat_labels["resolved_today"].setText(str(stats.get("resolved_today", 0)))
        except Exception as e:
            print(f"[AdminMainUI] Error loading counts: {e}")

    def _load_messages(self):
        """Load all admin messages from DataManager."""
        if self.data_manager is None:
            print("[AdminMainUI] No data_manager, skipping messages")
            return

        try:
            messages = self.data_manager.get_admin_messages()

            self.all_items = [
                {
                    'id': msg.get('id'),
                    'title': msg.get('subject', 'No Subject'),
                    'content': msg.get('content', ''),
                    'sender': msg.get('sender_name', 'Unknown'),
                    'priority': msg.get('priority', 'normal'),
                    'status': msg.get('status', 'pending'),
                    'date': msg.get('created_at', ''),
                    'department': msg.get('department', 'General'),
                }
                for msg in messages
            ]
            self.filtered_items = self.all_items.copy()
            self._refresh_message_list()
        except Exception as e:
            print(f"[AdminMainUI] Error loading messages: {e}")

    def _refresh_message_list(self):
        """Refresh the displayed message list."""
        try:
            while self.messages_list_layout.count() > 1:
                item = self.messages_list_layout.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()

            if not self.filtered_items:
                empty = QtWidgets.QLabel("No messages found!")
                empty.setStyleSheet("color: #888888; font-size: 14px;")
                empty.setWordWrap(True)
                empty.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.messages_list_layout.insertWidget(0, empty)
                return

            for item in self.filtered_items:
                card = self._create_message_card(item)
                self.messages_list_layout.insertWidget(self.messages_list_layout.count() - 1, card)
        except Exception as e:
            print(f"[AdminMainUI] Error refreshing message list: {e}")
    def _open_message_details(self, message_id, message_data):
        """
        Open the existing message-details dialog.

        message_id: backend ID (can be used to refetch full data if needed)
        message_data: the summary dict already on the card.
        """
        try:
            # If your dialog expects DataManager + message id:
            dlg = Ui_Form(
                parent=self,
                data_manager=self.data_manager,
                message_id=message_id,
                initial_data=message_data,  # optional, if your dialog supports it
            )
            dlg.exec()
        except Exception as e:
            print("[AdminMainUI] Error opening message details:", e)
            box = QtWidgets.QMessageBox(self)
            box.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            box.setWindowTitle("Error")
            box.setText(f"Could not open message details: {e}")
            box.exec()
    def _create_message_card(self, item):
        """Create a message card widget."""
        card = QtWidgets.QFrame()
        card.setFrameStyle(QtWidgets.QFrame.Shape.NoFrame)
        card.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                           QtWidgets.QSizePolicy.Policy.Fixed)
        card.setStyleSheet("""
            #message_card {
                background-color: #ffffff;
                border: 1px solid #f0f0f0;
                border-radius: 8px;
                padding: 10px;
            }
            #message_card:hover {
                background-color: #f9f9f9;
                border: 1px solid #e0e0e0;
                cursor: pointer;
            }
        """)
        card.setObjectName("message_card")

        # store data on the widget
        card.message_data = item
        message_id = item.get("id")

        def on_click(event):
            if event.button() == QtCore.Qt.MouseButton.LeftButton:
                self._open_message_details(message_id, card.message_data)

            # IMPORTANT: assign function, do NOT call it
            card.mousePressEvent = on_click

            layout = QtWidgets.QVBoxLayout(card)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(4)

            header_layout = QtWidgets.QHBoxLayout()
            sender_label = QtWidgets.QLabel(item.get('sender', 'Unknown'))
            sender_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #084924;")
            header_layout.addWidget(sender_label)
            header_layout.addStretch()

            status_color = {
                'pending': '#fbbf24',
                'sent':   '#10b981',
                'resolved': '#6b7280',
            }.get(item.get('status', 'pending').lower(), '#6b7280')
            status_label = QtWidgets.QLabel(item.get('status', 'Unknown').upper())
            status_label.setStyleSheet(
                f"background-color: {status_color}; color: white; padding: 2px 8px; "
                "border-radius: 10px; font-size: 10px; font-weight: bold;"
            )
            header_layout.addWidget(status_label)
            layout.addLayout(header_layout)

            title_label = QtWidgets.QLabel(item.get('title', 'No Subject'))
            title_label.setStyleSheet("font-weight: bold; font-size: 12px; color: black;")
            title_label.setWordWrap(True)
            layout.addWidget(title_label)

            content = item.get('content', '')
            content_preview = content[:100] + "..." if len(content) > 100 else content
            content_label = QtWidgets.QLabel(content_preview)
            content_label.setStyleSheet("color: #666666; font-size: 11px;")
            content_label.setWordWrap(True)
            layout.addWidget(content_label)

            footer_layout = QtWidgets.QHBoxLayout()
            footer_layout.addWidget(
                QtWidgets.QLabel(item.get('date', '')[:10] if item.get('date') else 'Unknown')
            )
            footer_layout.addStretch()
            footer_layout.addWidget(QtWidgets.QLabel(f"Dept: {item.get('department', 'General')}"))
            footer_layout.addWidget(QtWidgets.QLabel(f"Priority: {item.get('priority', 'normal').upper()}"))
            layout.addLayout(footer_layout)

            return card

    # -------------------- Filtering & Searching --------------------
    def filter_messages(self, filter_type):
        """Filter messages by category."""
        try:
            if filter_type == "all":
                messages = self.data_manager.get_admin_messages()
            elif filter_type == "critical":
                messages = self.data_manager.get_critical_issues()
            elif filter_type == "system":
                messages = self.data_manager.get_system_issues()
            elif filter_type == "technical":
                messages = self.data_manager.get_technical_support()
            else:
                messages = self.data_manager.get_admin_messages()

            self.all_items = [
                {
                    'id': msg.get('id'),
                    'title': msg.get('subject', 'No Subject'),
                    'content': msg.get('content', ''),
                    'sender': msg.get('sender_name', 'Unknown'),
                    'priority': msg.get('priority', 'normal'),
                    'status': msg.get('status', 'pending'),
                    'date': msg.get('created_at', ''),
                    'department': msg.get('department', 'General'),
                }
                for msg in messages
            ]
            self.filtered_items = self.all_items.copy()
            self._apply_filters()
        except Exception as e:
            print(f"[AdminMainUI] Error filtering messages: {e}")

    def _apply_filters(self):
        """Apply priority, status, and department filters."""
        try:
            filtered = self.all_items.copy()

            prio_text = self.comboBox_prio.currentText()
            if prio_text and prio_text != "All Priorities":
                priority_map = {"Urgent": "urgent", "High": "high", "Normal": "normal"}
                target_priority = priority_map.get(prio_text, prio_text.lower())
                filtered = [i for i in filtered if i.get('priority', '').lower() == target_priority]

            status_text = self.comboBox_stat.currentText()
            if status_text and status_text != "All Status":
                status_map = {"Pending": "pending", "Sent": "sent", "Resolved": "resolved"}
                target_status = status_map.get(status_text, status_text.lower())
                filtered = [i for i in filtered if i.get('status', '').lower() == target_status]

            dept_text = self.comboBox_dept.currentText()
            if dept_text and dept_text != "All Departments":
                filtered = [i for i in filtered if i.get('department', '').lower() == dept_text.lower()]

            self.filtered_items = filtered
            self._refresh_message_list()
        except Exception as e:
            print(f"[AdminMainUI] Error applying filters: {e}")

    def _search_items(self, text):
        """Search messages by text."""
        try:
            if not text.strip():
                self.filtered_items = self.all_items.copy()
            else:
                search_lower = text.lower()
                self.filtered_items = [
                    i for i in self.all_items
                    if search_lower in i.get('title', '').lower()
                       or search_lower in i.get('content', '').lower()
                       or search_lower in i.get('sender', '').lower()
                ]
            self._apply_filters()
        except Exception as e:
            print(f"[AdminMainUI] Error searching items: {e}")

    # -------------------- Admin Actions --------------------
    def _on_broadcast(self):
        try:
            dialog = QtWidgets.QDialog(self)
            # Shadow effect so it doesn't merge with background
            shadow = QtWidgets.QGraphicsDropShadowEffect(dialog)
            shadow.setBlurRadius(20)
            shadow.setXOffset(0)
            shadow.setYOffset(4)
            shadow.setColor(QtGui.QColor(0, 0, 0, 120))
            dialog.setGraphicsEffect(shadow)

            dialog.setWindowFlags(
                QtCore.Qt.WindowType.FramelessWindowHint
            )
            dialog.resize(600, 350)

            layout = QtWidgets.QVBoxLayout(dialog)
            layout.setContentsMargins(0, 0, 0, 0)

            # --- Custom green header ---
            header = QtWidgets.QFrame()
            header.setFixedHeight(40)
            header.setStyleSheet("background-color: #008000;")
            header_layout = QtWidgets.QHBoxLayout(header)
            header_layout.setContentsMargins(12, 0, 12, 0)

            title_lbl = QtWidgets.QLabel("System Broadcast")
            title_lbl.setStyleSheet("color: black; font-weight: bold;")
            header_layout.addWidget(title_lbl)
            header_layout.addStretch()

            close_btn = QtWidgets.QPushButton("×")
            close_btn.setFixedSize(24, 24)
            close_btn.setStyleSheet(
                "QPushButton { border: none; background: transparent; color: black; }"
                "QPushButton:hover { background: rgba(0,0,0,0.1); }"
            )
            close_btn.clicked.connect(dialog.reject)
            header_layout.addWidget(close_btn)

            layout.addWidget(header)

            # --- Content area ---
            body = QtWidgets.QWidget()
            body.setStyleSheet("""
                QWidget { background: #f8f8f8; color: black; }
                QLineEdit, QTextEdit {
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

            title_label = QtWidgets.QLabel("Broadcast Title:")
            title_input = QtWidgets.QLineEdit()
            title_input.setPlaceholderText("Enter broadcast title...")
            body_layout.addWidget(title_label)
            body_layout.addWidget(title_input)

            content_label = QtWidgets.QLabel("Message Content:")
            content_input = QtWidgets.QTextEdit()
            content_input.setPlaceholderText("Enter broadcast message...")
            body_layout.addWidget(content_label)
            body_layout.addWidget(content_input)

            button_layout = QtWidgets.QHBoxLayout()
            button_layout.addStretch()
            send_btn = QtWidgets.QPushButton("Send Broadcast")
            cancel_btn = QtWidgets.QPushButton("Cancel")
            button_layout.addWidget(send_btn)
            button_layout.addWidget(cancel_btn)
            body_layout.addLayout(button_layout)

            layout.addWidget(body)

            def send():
                title = title_input.text().strip()
                content = content_input.toPlainText().strip()
                if not title or not content:
                    QtWidgets.QMessageBox.warning(dialog, "Error", "Title and content cannot be empty!")
                    return
                result = self.data_manager.send_system_broadcast(title, content)
                print("[AdminMainUI] send_system_broadcast result:", result)
                if result:
                    self._show_message(self,
                                       QtWidgets.QMessageBox.Icon.Warning,
                            "Success", "Broadcast sent successfully!")

                    self._load_messages()
                    self._load_dashboard_counts()
                    dialog.accept()
                else:
                    self._show_message(self,
                               QtWidgets.QMessageBox.Icon.Warning,
                            "Error", "Failed to send broadcast!")

            send_btn.clicked.connect(send)
            cancel_btn.clicked.connect(dialog.reject)

            dialog.exec()
        except Exception as e:

            print(f"[AdminMainUI] Error in broadcast: {e}")
            self._show_message(self,
                               QtWidgets.QMessageBox.Icon.Warning,
                             "Error",  f"Broadcast error: {e}")


    def _on_report(self):
        """Handle generate reports action."""
        try:
            report = self.data_manager.get_user_activity_report(days=7)
            response_times = self.data_manager.get_message_response_time_stats()
            dept_stats = self.data_manager.get_department_stats()

            report_lines = [
                "=== User Activity Report (Last 7 Days) ===",
                "",
                f"Total Messages Sent: {report.get('total_messages_sent', 0)}",
                f"Active Users: {report.get('active_users', 0)}",
                f"Most Active User: {report.get('most_active_user', 'N/A')}",
                "",
                "Messages by Department:",
            ]
            for dept, count in dept_stats.items():
                report_lines.append(f"  - {dept}: {count}")
            report_lines.extend([
                "",
                "=== Response Time Statistics ===",
                f"Average Response Time: {response_times.get('avg_response_time_hours', 0):.2f} hours",
                f"Fastest Response: {response_times.get('fastest_response_hours', 0):.2f} hours",
                f"Slowest Response: {response_times.get('slowest_response_hours', 0):.2f} hours",
            ])
            report_text = "\n".join(report_lines)

            dialog = QtWidgets.QDialog(self)


            shadow = QtWidgets.QGraphicsDropShadowEffect(dialog)
            shadow.setBlurRadius(20)
            shadow.setXOffset(0)
            shadow.setYOffset(4)
            shadow.setColor(QtGui.QColor(0, 0, 0, 120))
            dialog.setGraphicsEffect(shadow)

            dialog.setWindowFlags(
                QtCore.Qt.WindowType.FramelessWindowHint
            )
            dialog.resize(700, 400)



            dialog.setWindowFlags(
                QtCore.Qt.WindowType.FramelessWindowHint
            )
            dialog.resize(700, 400)

            root_layout = QtWidgets.QVBoxLayout(dialog)
            root_layout.setContentsMargins(0, 0, 0, 0)

            header = QtWidgets.QFrame()
            header.setFixedHeight(40)
            header.setStyleSheet("background-color: #008000;")
            h_layout = QtWidgets.QHBoxLayout(header)
            h_layout.setContentsMargins(12, 0, 12, 0)

            title_lbl = QtWidgets.QLabel("System Reports")
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

            root_layout.addWidget(header)

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

            text_edit = QtWidgets.QTextEdit()
            text_edit.setPlainText(report_text)
            text_edit.setReadOnly(True)
            body_layout.addWidget(text_edit)

            btn_layout = QtWidgets.QHBoxLayout()
            btn_layout.addStretch()
            close_bottom = QtWidgets.QPushButton("Close")
            close_bottom.clicked.connect(dialog.accept)
            btn_layout.addWidget(close_bottom)
            body_layout.addLayout(btn_layout)

            root_layout.addWidget(body)

            dialog.exec()
        except Exception as e:
            self._show_message(self,
                               QtWidgets.QMessageBox.Icon.Warning,
                               "Error", f"Report error: {e}")
            print(f"[AdminMainUI] Error in report: {e}")

    def _on_settings(self):
        self._show_message(self,
                           QtWidgets.QMessageBox.Icon.Warning,
                           "System Settings",
                           "System settings UI not implemented yet.\n\nPlease use the admin panel to manage settings."
                           )


    def _show_message(self, parent, icon, title, text):
        box = QtWidgets.QMessageBox(parent)
        box.setIcon(icon)
        box.setWindowTitle(title)
        box.setText(text)
        box.setStyleSheet("""
            QMessageBox {
                background-color: #ffffff;
            }
            QMessageBox QLabel {
                color: black;
            }
            QMessageBox QPushButton {
                color: black;
                min-width: 70px;
            }
        """)
        box.exec()


    def _on_user_management(self):
        try:
            users = self.data_manager.get_user_list_for_management()

            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle("User Management")
            dialog.setGeometry(100, 100, 800, 500)

            layout = QtWidgets.QVBoxLayout(dialog)

            table = QtWidgets.QTableWidget()
            table.setColumnCount(6)
            table.setHorizontalHeaderLabels(["ID", "Name", "Email", "Role", "Department", "Status"])
            table.setRowCount(len(users))

            for row, user in enumerate(users):
                table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(user.get('id', ''))))
                table.setItem(row, 1, QtWidgets.QTableWidgetItem(user.get('name', '')))
                table.setItem(row, 2, QtWidgets.QTableWidgetItem(user.get('email', '')))
                table.setItem(row, 3, QtWidgets.QTableWidgetItem(user.get('role', '')))
                table.setItem(row, 4, QtWidgets.QTableWidgetItem(user.get('department', '')))
                table.setItem(row, 5, QtWidgets.QTableWidgetItem(user.get('status', '')))

            table.resizeColumnsToContents()
            layout.addWidget(table)

            close_btn = QtWidgets.QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)

            dialog.exec()
        except Exception as e:
            print(f"[AdminMainUI] Error in user management: {e}")
            QtWidgets.QMessageBox.warning(self, "Error", f"User management error: {e}")


