import sys
from PyQt6 import QtCore, QtGui, QtWidgets
from .data_manager import DataManager
from .faculty.message_dialog import Ui_Form
from .faculty.message_compose import Ui_Form as ComposeUI


class FacultyMainUI(QtWidgets.QWidget):
    """Faculty Messaging UI with crash-safe overlays and dialogs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FacultyMainUI")

        # Data manager and faculty info
        self.data_manager = DataManager()
        faculty_user = self.data_manager.get_user_by_email("kimjongun@cmu.edu.ph")  # Example for faculty login
        self.current_faculty_id = faculty_user["id"] if faculty_user else None


        # Layouts
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Content area
        content_widget = QtWidgets.QWidget(parent=self)
        content_layout = QtWidgets.QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 8, 0, 8)
        content_layout.setSpacing(8)

        # Faculty content
        self.faculty_content = QtWidgets.QWidget(parent=content_widget)
        self.faculty_content.setObjectName("faculty_content")
        self.setup_faculty_content()
        content_layout.addWidget(self.faculty_content, stretch=1)

        main_layout.addWidget(content_widget)

        # Connect buttons and filters
        self.connect_buttons()

        # Load data safely
        try:
            self.load_faculty_data()
            self.load_messages()
        except Exception as e:
            print(f"Error loading initial data: {e}")

    # -------------------- Setup Content --------------------
    def setup_faculty_content(self):
        faculty_layout = QtWidgets.QHBoxLayout(self.faculty_content)
        faculty_layout.setContentsMargins(0, 0, 0, 0)
        faculty_layout.setSpacing(8)

        # ----- Left Panel: Categories -----
        self.setup_left_panel(faculty_layout)

        # ----- Center Panel: Messages -----
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

        # Create label
        label_header = QtWidgets.QLabel("Message Categories")
        label_header.setFont(QtGui.QFont("Arial", 14))
        label_header.setStyleSheet("color: #084924;")  # Set text color
        layout.addWidget(label_header)

        # Add horizontal line
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        layout.addWidget(line)

        # Buttons
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
        label_actions.setStyleSheet("color: #084924;")  # Set text color
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

        # Search bar
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
        color: black;               /* text color */
        background-color: #f0f0f0;
        border-radius: 10px;
        border: 1px solid #ccc;
        padding: 5px 7px;
        font-size: 14px;
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

        self.comboBox_prio = QtWidgets.QComboBox(); self.comboBox_prio.addItems(["All Priorities", "Urgent", "High", "Normal"])
        self.comboBox_prio.setStyleSheet("""
    QComboBox {
        color: black;               /* text color */
        background-color: #f7f7f7;
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 5px 10px;
        font-size: 14px;
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
        self.comboBox_stat = QtWidgets.QComboBox(); self.comboBox_stat.addItems(["All Status", "Pending", "Sent", "Resolved"])
        self.comboBox_stat.setStyleSheet(self.comboBox_prio.styleSheet())  # reuse same style
        search_layout.addWidget(self.comboBox_stat)

        self.chat_info.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.chat_info.setFixedHeight(64)
        center_layout.addWidget(self.chat_info, 0, QtCore.Qt.AlignmentFlag.AlignTop)

        # Messages container
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
        try:
            faculty = self.data_manager.get_user(self.current_faculty_id)
            if faculty:
                print(f"Faculty logged in: {faculty['name']} ({faculty['department']})")
        except Exception as e:
            print(f"Error loading faculty data: {e}")

    def load_messages(self):
        try:
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
        except Exception as e:
            print(f"Error loading messages: {e}")

    # -------------------- Display --------------------
    def display_items(self):
        layout = self.messages_list_layout
        while layout.count() > 1:
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not getattr(self, 'filtered_items', []):
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
                print(f"Error creating card: {e}")

    # -------------------- Cards --------------------
    def create_message_card(self, item):
        card = QtWidgets.QFrame()
        card.setFrameStyle(QtWidgets.QFrame.Shape.NoFrame)
        card.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        card.setAttribute(QtCore.Qt.WidgetAttribute.WA_Hover, True)
        card.setMouseTracking(True)

        card.setStyleSheet("""
            #message_card { background-color: #ffffff; border: none; padding: 0; }
            #message_card:hover { background-color: #f7f7f7; }
            #message_card * { background: transparent; }
        """)

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
        status_label.setStyleSheet(f"background-color: {status_color}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: bold;")
        header_layout.addWidget(status_label)
        layout.addLayout(header_layout)

        title_label = QtWidgets.QLabel(item['title']); title_label.setWordWrap(True)
        layout.addWidget(title_label)

        content_preview = item['content'][:100] + "..." if len(item['content']) > 100 else item['content']
        content_label = QtWidgets.QLabel(content_preview); content_label.setWordWrap(True)
        layout.addWidget(content_label)

        footer_layout = QtWidgets.QHBoxLayout()
        footer_layout.addWidget(QtWidgets.QLabel(item['date'][:10] if item.get('date') else 'Unknown'))
        footer_layout.addStretch()
        footer_layout.addWidget(QtWidgets.QLabel(item['priority'].upper()))
        layout.addLayout(footer_layout)

        card.mousePressEvent = lambda event, item=item: self.on_message_clicked(item)
        return card

    # -------------------- Message Click --------------------
    def on_message_clicked(self, item):
        try:
            if item.get('type') == 'message':
                self.data_manager.update_message(item['id'], {'is_read': True})
        except Exception as e:
            print(f"Error updating message read status: {e}")

        try:
            dialog = QtWidgets.QDialog(self.window())  # ✅ parent to main window
            ui = Ui_Form()
            ui.setupUi(dialog)
            dialog.setWindowTitle(f"{item.get('type', 'Message').title()} Details")
            dialog.setModal(True)  # modal but attached to main window

            ui.label_header.setText(item.get('title', ''))
            ui.label_recipient.setText(f"From: {item.get('sender', 'Unknown')}")
            ui.label_email.setText(f"({item.get('sender_email', '')})")
            ui.label_day.setText(item.get('date', ''))
            ui.textEdit_body.setPlainText(item.get('content', ''))

            ui.btn_close.clicked.connect(dialog.accept)
            dialog.exec()
        except Exception as e:
            print(f"Error opening dialog: {e}")


    # -------------------- Filters --------------------
    def filter_messages(self, filter_type):
        try:
            if filter_type == "all":
                self.filtered_items = self.all_items.copy()
            elif filter_type == "unread":
                self.filtered_items = [i for i in self.all_items if not i.get('is_read', True)]
            elif filter_type == "academic":
                self.filtered_items = [i for i in self.all_items if i['type'] == 'inquiry']
            elif filter_type == "assignment":
                self.filtered_items = [i for i in self.all_items if 'assignment' in i['title'].lower()]
            elif filter_type == "office":
                self.filtered_items = [i for i in self.all_items if 'office' in i['title'].lower()]
            else:
                self.filtered_items = self.all_items.copy()
            self.apply_filters()
        except Exception as e:
            print(f"Error filtering messages: {e}")

    def apply_filters(self):
        try:
            filtered = self.filtered_items.copy()
            prio = self.comboBox_prio.currentText()
            status = self.comboBox_stat.currentText()

            if prio != "All Priorities":
                priority_map = {"Urgent": "urgent", "High": "high", "Normal": "normal"}
                filtered = [i for i in filtered if i['priority'] == priority_map.get(prio, i['priority'])]

            if status != "All Status":
                status_map = {"Pending": "pending", "Sent": "sent", "Resolved": "resolved"}
                filtered = [i for i in filtered if i['status'] == status_map.get(status, i['status'])]

            self.filtered_items = filtered
            self.display_items()
        except Exception as e:
            print(f"Error applying filters: {e}")

    def search_messages(self, text):
        try:
            s = text.lower().strip()
            self.filtered_items = self.all_items.copy() if not s else [
                i for i in self.all_items if s in i['title'].lower() or s in i['content'].lower() or s in i['sender'].lower()
            ]
            self.apply_filters()
        except Exception as e:
            print(f"Error searching messages: {e}")

    # -------------------- Compose --------------------
    def compose_message(self):
        """Open compose dialog for new message."""
        try:
            dialog = QtWidgets.QDialog(self)
            ui = ComposeUI()
            ui.setupUi(dialog)

            def send_new_message():
                receiver_email = ui.lineEdit_email.text().strip()
                receiver = self.data_manager.get_user_by_email(receiver_email)
                if not receiver:
                    QtWidgets.QMessageBox.warning(dialog, "Invalid Recipient", "Recipient not found.")
                    return

                content = ui.textEdit_body.toPlainText().strip()
                if not content:
                    QtWidgets.QMessageBox.warning(dialog, "Empty Message", "Message content cannot be empty.")
                    return

                # create a new conversation
                new_convo = {
                    "participants": [self.current_faculty_id, receiver["id"]],
                    "title": ui.lineEdit_subject.text().strip() or "No Subject"
                }
                convo = self.data_manager.create_conversation(new_convo)

                # add the message
                self.data_manager.create_message({
                    "conversation_id": convo["id"],
                    "sender_id": self.current_faculty_id,
                    "receiver_id": receiver["id"],
                    "content": content,
                    "status": "sent"
                })

                QtWidgets.QMessageBox.information(dialog, "Sent", "Message sent successfully.")
                self.load_messages()
                dialog.accept()

            ui.btn_send.clicked.connect(send_new_message)
            dialog.exec()
        except Exception as e:
            print(f"Error composing message: {e}")


    
    def reply_message(self, conversation_id: int, receiver_id: int, content: str):
        """Reply to existing conversation."""
        try:
            if not content.strip():
                QtWidgets.QMessageBox.warning(self, "Empty Reply", "Cannot send an empty reply.")
                return

            msg = {
                "conversation_id": conversation_id,
                "sender_id": self.current_faculty_id,
                "receiver_id": receiver_id,
                "content": content.strip(),
                "status": "sent"
            }

            self.data_manager.create_message(msg)
            self.load_messages()
            QtWidgets.QMessageBox.information(self, "Reply Sent", "Reply successfully sent.")
        except Exception as e:
            print(f"Error replying to message: {e}")


    # -------------------- Overlay --------------------
    def show_message_overlay(self, item: dict):
        if not self.isVisible():
            return

        overlay = QtWidgets.QWidget(self)
        overlay.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        overlay.setStyleSheet("#overlay { background: rgba(0, 0, 0, 120); }")
        overlay.setGeometry(self.rect())
        overlay.show()
        overlay.raise_()

        try:
            ui = Ui_Form()
            ui.setupUi(overlay)

            ui.label_header.setText(item.get("title", ""))
            ui.label_recipient.setText(f"From: {item.get('sender', 'Unknown')}")
            ui.label_email.setText(f"({item.get('sender_email', '')})")
            ui.label_day.setText(item.get("date", ""))
            ui.textEdit_body.setPlainText(item.get("content", ""))

            frame = getattr(ui, "message_frame", None)
            if frame:
                frame.adjustSize()
                ow, oh = overlay.width(), overlay.height()
                fw, fh = frame.width(), frame.height()
                frame.move(max(0, (ow - fw) // 2), max(0, (oh - fh) // 2))

            ui.btn_close.clicked.connect(overlay.deleteLater)

            def overlay_mousePressEvent(e):
                if frame and not frame.geometry().contains(e.pos()):
                    overlay.deleteLater()
            overlay.mousePressEvent = overlay_mousePressEvent
        except Exception as e:
            print(f"Error creating overlay: {e}")
