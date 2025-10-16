"""
Faculty Application for CISC Virtual Hub Messaging System
========================================================

This is the main application for faculty members to manage their messages,
inquiries, and communications with students.

This app allows faculty to:
- View all messages and inquiries assigned to them
- Filter messages by priority, status, and type
- Respond to student inquiries
- Manage their message categories
"""

import sys
from PyQt6 import QtCore, QtGui, QtWidgets
from .data_manager import DataManager
from .faculty.message_dialog import Ui_Form
from .faculty.message_compose import Ui_Form as ComposeUI


class FacultyMainUI(QtWidgets.QWidget):
    """Custom UI class that includes sidebar and header for faculty app"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FacultyMainUI")

        # Data
        self.data_manager = DataManager()
        self.current_faculty_id = 2  # Dr. Maria Santos

       


        # Main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # # ===== Header =====
        # self.header = Header(parent=self)
        # self.header.setFixedHeight(84)
        # main_layout.addWidget(self.header)

        # ===== Content area =====
        content_widget = QtWidgets.QWidget(parent=self)
        content_layout = QtWidgets.QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 8, 0, 8)
        content_layout.setSpacing(8)

        # # ===== Sidebar placeholder =====
        # self.sidebar_container = QtWidgets.QWidget(parent=content_widget)
        # self.sidebar_container.setFixedWidth(250)
        # self.sidebar_container_layout = QtWidgets.QVBoxLayout(self.sidebar_container)
        # self.sidebar_container_layout.setContentsMargins(0, 0, 0, 0)
        # self.sidebar_container_layout.setSpacing(0)
        # content_layout.addWidget(self.sidebar_container)

        # ===== Faculty Content Area =====
        self.faculty_content = QtWidgets.QWidget(parent=content_widget)
        self.faculty_content.setObjectName("faculty_content")
        self.setup_faculty_content()
        content_layout.addWidget(self.faculty_content, stretch=1)

        main_layout.addWidget(content_widget)

         # Buttons and filters
        self.connect_buttons()

        # Load
        self.load_faculty_data()
        self.load_messages()
        

    def setup_faculty_content(self):
        """Set up the faculty content area with proper layout"""
        faculty_layout = QtWidgets.QHBoxLayout(self.faculty_content)
        faculty_layout.setContentsMargins(0, 0, 0, 0)
        faculty_layout.setSpacing(8)

        # ===== Left Panel - Message Categories =====
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

        inquiry_layout = QtWidgets.QVBoxLayout(self.inquiry_widget)
        inquiry_layout.setContentsMargins(8, 8, 8, 8)
        inquiry_layout.setSpacing(6)

        # Message Categories header
        self.label_header1 = QtWidgets.QLabel("Message Categories")
        self.label_header1.setFont(QtGui.QFont("Arial", 14))
        inquiry_layout.addWidget(self.label_header1)

        # Separator
        self.line = QtWidgets.QFrame()
        self.line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        inquiry_layout.addWidget(self.line)

        # Filter buttons
        filter_layout = QtWidgets.QVBoxLayout()
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

        self.push_all = QtWidgets.QPushButton("All Messages")
        self.push_all.setStyleSheet(button_style)
        filter_layout.addWidget(self.push_all)

        self.push_unread = QtWidgets.QPushButton("Unread")
        self.push_unread.setStyleSheet(button_style)
        filter_layout.addWidget(self.push_unread)

        self.push_acadin = QtWidgets.QPushButton("Academic Inquiries")
        self.push_acadin.setStyleSheet(button_style)
        filter_layout.addWidget(self.push_acadin)

        self.push_assgt = QtWidgets.QPushButton("Assignment Help")
        self.push_assgt.setStyleSheet(button_style)
        filter_layout.addWidget(self.push_assgt)

        self.push_office = QtWidgets.QPushButton("Office Hours")
        self.push_office.setStyleSheet(button_style)
        filter_layout.addWidget(self.push_office)

        inquiry_layout.addLayout(filter_layout)

        # Separator
        self.line_2 = QtWidgets.QFrame()
        self.line_2.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        inquiry_layout.addWidget(self.line_2)

        # Quick Actions
        self.label_actions = QtWidgets.QLabel("Quick Actions")
        self.label_actions.setFont(QtGui.QFont("Arial", 12))
        inquiry_layout.addWidget(self.label_actions)

        self.push_compose = QtWidgets.QPushButton("Compose Message")
        self.push_compose.setStyleSheet(button_style)
        inquiry_layout.addWidget(self.push_compose)

        inquiry_layout.addStretch()
        faculty_layout.addWidget(self.inquiry_widget)

        # ===== Center Panel - Search and Messages =====
        center_widget = QtWidgets.QWidget(parent=self.faculty_content)
        center_layout = QtWidgets.QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(8)

        # Search and filter bar (top-fixed)
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
        search_layout.setContentsMargins(8, 8, 8, 8)
        search_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignLeft)

        # Search box
        self.lineEdit_faculty = QtWidgets.QLineEdit()
        self.lineEdit_faculty.setPlaceholderText("Search messages...")
        self.lineEdit_faculty.setStyleSheet("""
            QLineEdit {
                background-color: #f0f0f0;
                border-radius: 10px;
                border: 1px solid #ccc;
                padding: 5px 7px;
                font-size: 14px;
                color: #333;
            }
            QLineEdit:focus {
                border: 1px solid #084924;
            }
            QLineEdit:hover {
                border: 1px solid #888;
                background-color: #e9e9e9;
            }
        """)
        search_layout.addWidget(self.lineEdit_faculty)

        # Priority filter
        self.comboBox_prio = QtWidgets.QComboBox()
        self.comboBox_prio.addItems(["All Priorities", "Urgent", "High", "Normal"])
        self.comboBox_prio.setStyleSheet("""
            QComboBox {
                background-color: #f7f7f7;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 14px;
                color: #333;
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

        # Status filter
        self.comboBox_stat = QtWidgets.QComboBox()
        self.comboBox_stat.addItems(["All Status", "Pending", "Sent", "Resolved"])
        self.comboBox_stat.setStyleSheet("""
            QComboBox {
                background-color: #f7f7f7;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 14px;
                color: #333;
            }
            QComboBox:hover {
                border: 1px solid #888;
                background-color: #e9e9e9;
            }
            QComboBox:focus {
                border: 1px solid #084924;
            }
        """)
        search_layout.addWidget(self.comboBox_stat)

        # Make search bar not grow vertically
        self.chat_info.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                                     QtWidgets.QSizePolicy.Policy.Fixed)
        self.chat_info.setFixedHeight(64)  # adjust if needed

        center_layout.addWidget(self.chat_info, 0, QtCore.Qt.AlignmentFlag.AlignTop)

        # Messages area container
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

        # Messages header
        self.label_header1_4 = QtWidgets.QLabel("Recent Messages")
        self.label_header1_4.setFont(QtGui.QFont("Arial", 14))
        message_layout.addWidget(self.label_header1_4)

        # Separator
        self.line_7 = QtWidgets.QFrame()
        self.line_7.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.line_7.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        message_layout.addWidget(self.line_7)

        # Persistent messages scroll area (top-aligned)
        self.messages_scroll = QtWidgets.QScrollArea()
        self.messages_scroll.setWidgetResizable(True)
        self.messages_scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.messages_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.messages_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.messages_scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        self.messages_container = QtWidgets.QWidget()
        self.messages_list_layout = QtWidgets.QVBoxLayout(self.messages_container)
        self.messages_list_layout.setContentsMargins(5, 5, 5, 5)
        self.messages_list_layout.setSpacing(10)
        self.messages_list_layout.addStretch()  # keeps cards pinned to the top

        self.messages_scroll.setWidget(self.messages_container)
        message_layout.addWidget(self.messages_scroll)

        center_layout.addWidget(self.message_widget, 1)
        faculty_layout.addWidget(center_widget, stretch=1)

   

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


    def load_faculty_data(self):
        faculty = self.data_manager.get_user(self.current_faculty_id)
        if faculty:
            print(f"Faculty logged in: {faculty['name']} ({faculty['department']})")

    def load_messages(self):
        faculty_messages = [m for m in self.data_manager.data['messages'] if m.get('receiver_id') == self.current_faculty_id]
        faculty_inquiries = self.data_manager.get_inquiries_by_faculty(self.current_faculty_id)

        all_items = []
        for msg in faculty_messages:
            sender = self.data_manager.get_user(msg.get('sender_id'))
            all_items.append({
                'type': 'message',
                'id': msg['id'],
                'title': msg.get('subject', 'No Subject'),
                'content': msg.get('content', ''),
                'sender': sender['name'] if sender else 'Unknown',
                'priority': msg.get('priority', 'normal'),
                'status': msg.get('status', 'pending'),
                'date': msg.get('created_at', ''),
                'is_read': msg.get('is_read', False)
            })

        for inq in faculty_inquiries:
            student = self.data_manager.get_user(inq.get('student_id'))
            all_items.append({
                'type': 'inquiry',
                'id': inq['id'],
                'title': inq.get('subject', 'No Subject'),
                'content': inq.get('description', ''),
                'sender': student['name'] if student else 'Unknown',
                'priority': inq.get('priority', 'normal'),
                'status': inq.get('status', 'pending'),
                'date': inq.get('created_at', ''),
                'is_read': True
            })

        all_items.sort(key=lambda x: x['date'], reverse=True)
        self.all_items = all_items
        self.filtered_items = all_items.copy()
        self.display_items()

    def display_items(self):
        """Render cards in the persistent top-aligned scroll area"""
        layout = self.messages_list_layout

        # Clear old cards but keep final stretch
        while layout.count() > 1:
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not self.filtered_items:
            empty = QtWidgets.QLabel("No messages found!")
            empty.setWordWrap(True)
            empty.setStyleSheet("font-size: 14px; color: #666; margin: 8px 4px;")
            layout.insertWidget(0, empty)
            return

        for itm in self.filtered_items:
            card = self.create_message_card(itm)
            layout.insertWidget(layout.count() - 1, card)


    def create_message_card(self, item):
        card = QtWidgets.QFrame()
        card.setObjectName("message_card")
        card.setFrameStyle(QtWidgets.QFrame.Shape.NoFrame)
        card.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                        QtWidgets.QSizePolicy.Policy.Fixed)

        # Make the entire card react on hover (single hit target)
        card.setAttribute(QtCore.Qt.WidgetAttribute.WA_Hover, True)
        card.setMouseTracking(True)

        card.setStyleSheet("""
            #message_card {
                background-color: #ffffff;   /* keep white background for the whole card */
                border: none;                /* no border */
                border-radius: 0;            /* no rounded corners */
                padding: 0;                  /* no inner padding on the frame */
            }
            #message_card:hover {
                background-color: #f7f7f7;   /* whole-card hover */
            }
            #message_card * {
                background: transparent;     /* children don't paint backgrounds */
            }
        """)

        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # no inner padding
        layout.setSpacing(4)

        # Header
        header_layout = QtWidgets.QHBoxLayout()
        sender_label = QtWidgets.QLabel(item['sender'])
        sender_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #084924;")
        header_layout.addWidget(sender_label)
        header_layout.addStretch()

        status = item['status']
        status_color = {
            'pending': '#fbbf24', 'sent': '#10b981',
            'resolved': '#6b7280', 'in_progress': '#3b82f6'
        }.get(status, '#6b7280')
        status_label = QtWidgets.QLabel(status.upper())
        status_label.setStyleSheet(f"""
            background-color: {status_color};
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 10px;
            font-weight: bold;
        """)
        header_layout.addWidget(status_label)
        layout.addLayout(header_layout)

        # Title
        title_label = QtWidgets.QLabel(item['title'])
        title_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #333;")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # Content preview
        content_preview = item['content'][:100] + "..." if len(item['content']) > 100 else item['content']
        content_label = QtWidgets.QLabel(content_preview)
        content_label.setStyleSheet("font-size: 12px; color: #666;")
        content_label.setWordWrap(True)
        layout.addWidget(content_label)

        # Footer
        footer_layout = QtWidgets.QHBoxLayout()
        date_text = item['date'][:10] if item['date'] else 'Unknown'
        date_label = QtWidgets.QLabel(date_text)
        date_label.setStyleSheet("font-size: 10px; color: #999;")
        footer_layout.addWidget(date_label)
        footer_layout.addStretch()

        priority = item['priority']
        priority_color = {'urgent': '#ef4444', 'high': '#f59e0b', 'normal': '#6b7280'}.get(priority, '#6b7280')
        priority_label = QtWidgets.QLabel(priority.upper())
        priority_label.setStyleSheet(f"color: {priority_color}; font-size: 10px; font-weight: bold;")
        footer_layout.addWidget(priority_label)
        layout.addLayout(footer_layout)

        # Single click target
        card.mousePressEvent = lambda event, item=item: self.on_message_clicked(item)
        return card

    def on_message_clicked(self, item):
        print(f"Clicked on {item['type']}: {item['title']}")
        if item.get('type') == 'message':
            try:
                self.data_manager.update_message(item['id'], {'is_read': True})
            except Exception:
                pass

        self.show_message_overlay(item)

        dialog = QtWidgets.QDialog(self)
        ui = Ui_Form()
        ui.setupUi(dialog)
        dialog.setWindowTitle(f"{item.get('type', 'Message').title()} Details")

        # Populate fields
        ui.label_header.setText(item.get('title', ''))
        ui.label_recipient.setText(f"From: {item.get('sender', 'Unknown')}")
        sender_email = item.get('sender_email', '')
        ui.label_email.setText(f"({sender_email})" if sender_email else "")
        ui.label_day.setText(item.get('date', ''))  # or a relative string if you prefer
        ui.textEdit_body.setPlainText(item.get('content', ''))

        # Wire close button
        ui.btn_close.clicked.connect(dialog.accept)

        # Optional: wire actions
        # ui.btn_reply.clicked.connect(lambda: ...)
        # ui.btn_resolve.clicked.connect(lambda: ...)
        # ui.btn_fwd.clicked.connect(lambda: ...)

        dialog.exec()

    def filter_messages(self, filter_type):
        print(f"Filtering by: {filter_type}")

        if filter_type == "all":
            filtered = self.all_items.copy()
        elif filter_type == "unread":
            filtered = [item for item in self.all_items if not item.get('is_read', True)]
        elif filter_type == "academic":
            filtered = [item for item in self.all_items if item['type'] == 'inquiry']
        elif filter_type == "assignment":
            filtered = [item for item in self.all_items if 'assignment' in item['title'].lower()]
        elif filter_type == "office":
            filtered = [item for item in self.all_items if 'office' in item['title'].lower()]
        else:
            filtered = self.all_items.copy()

        self.filtered_items = filtered
        self.apply_filters()  # also applies the combo filters

    def apply_filters(self):
        priority_filter = self.comboBox_prio.currentText()
        status_filter = self.comboBox_stat.currentText()

        filtered = self.filtered_items.copy()

        if priority_filter != "All Priorities":
            priority_map = {"Urgent": "urgent", "High": "high", "Normal": "normal"}
            if priority_filter in priority_map:
                filtered = [item for item in filtered if item['priority'] == priority_map[priority_filter]]

        if status_filter != "All Status":
            status_map = {"Pending": "pending", "Sent": "sent", "Resolved": "resolved"}
            if status_filter in status_map:
                filtered = [item for item in filtered if item['status'] == status_map[status_filter]]

        self.filtered_items = filtered
        self.display_items()

    def search_messages(self, search_text):
        if not search_text.strip():
            self.filtered_items = self.all_items.copy()
        else:
            s = search_text.lower()
            self.filtered_items = [
                item for item in self.all_items
                if (s in item['title'].lower() or s in item['content'].lower() or s in item['sender'].lower())
            ]
        self.apply_filters()  # keep combo filters active

    def compose_message(self):
        self.message_app = ComposeUI()
        self.message_app.show()

    def show_message_overlay(self, item: dict):
    # Full-window dimmed overlay, child of central area (no separate OS window)
        parent_area = self.centralWidget()
        overlay = QtWidgets.QWidget(parent_area)
        overlay.setObjectName("overlay")
        overlay.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        overlay.setStyleSheet("#overlay { background: rgba(0, 0, 0, 120); }")
        overlay.setGeometry(parent_area.rect())
        overlay.show()
        overlay.raise_()

        # Build your Ui_Form on the overlay
        ui = Ui_Form()
        ui.setupUi(overlay)

        # Populate fields
        ui.label_header.setText(item.get("title", ""))
        ui.label_recipient.setText(f"From: {item.get('sender', 'Unknown')}")
        sender_email = item.get("sender_email", "")
        ui.label_email.setText(f"({sender_email})" if sender_email else "")
        ui.label_day.setText(item.get("date", ""))
        ui.textEdit_body.setPlainText(item.get("content", ""))

        # Center the message card
        frame = ui.message_frame
        frame.adjustSize()
        ow, oh = overlay.width(), overlay.height()
        fw, fh = frame.width(), frame.height()
        frame.move(max(0, (ow - fw) // 2), max(0, (oh - fh) // 2))

        # Close behaviors
        ui.btn_close.clicked.connect(overlay.deleteLater)
        def overlay_mousePressEvent(e):
            # Close only if clicking outside the white card
            if not frame.geometry().contains(e.pos()):
                overlay.deleteLater()
        overlay.mousePressEvent = overlay_mousePressEvent

