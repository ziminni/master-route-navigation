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

        # # ===== Sidebar placeholder =====
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
        self.label_2.setStyleSheet("color: black;")
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
                color: #333;
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
        self.label_8.setStyleSheet("color: black;")
        self.label_8.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        message_layout.addWidget(self.label_8)

        content_layout.addWidget(self.message_widget)
        self.message_widget.show()

        # ===== Load MainChatWidget =====
        try:
            self.chat_box = MainChatWidget(parent=content_widget, chat_name="Welcome Chat")
            content_layout.addWidget(self.chat_box)
            
            self.chat_box.hide()
            self.chat_info.setFixedWidth(260)
        except Exception as e:
            print(f"Error loading chat widget: {e}")
            error_label = QtWidgets.QLabel(f"Failed to load chat: {e}")
            error_label.setStyleSheet("color: red; font-weight: bold;")
            content_layout.addWidget(error_label)

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
        self.label_9.setStyleSheet("color: black;")
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
