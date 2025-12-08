from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtGui import QIcon
from pathlib import Path


class CustomMessageBox(QtWidgets.QMessageBox):
        """Custom borderless white QMessageBox with black text"""
        def __init__(self, parent=None):
                super().__init__(parent)
                self.setStyleSheet("""
            QMessageBox {
                background-color: white;
                border: none;
                border-radius: 12px;
            }
            QMessageBox QLabel {
                color: black;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QMessageBox QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 6px;
                color: black;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #e0e0e0;
                border: 1px solid #999;
            }
            QMessageBox QPushButton:pressed {
                background-color: #d0d0d0;
            }
            QMessageBox QPushButton:focus {
                border: 2px solid #084924;
                background-color: #e8f5e8;
            }
        """)


class Ui_MainWindow(object):
        def setupUi(self, MainWindow):
                MainWindow.setObjectName("MainWindow")
                MainWindow.resize(1124, 914)
                self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
                self.centralwidget.setObjectName("centralwidget")

                # Root layout
                root_layout = QtWidgets.QVBoxLayout(self.centralwidget)
                root_layout.setContentsMargins(0, 0, 0, 0)
                root_layout.setSpacing(0)

                # Message container
                self.message_widget = QtWidgets.QWidget(parent=self.centralwidget)
                self.message_widget.setObjectName("message_widget")
                self.message_widget.setStyleSheet("""
            QWidget#message_widget {
                background-color: white;
                border-radius: 16px;
                border: 1px solid #e0e0e0;
                padding: 0px;
            }
        """)

                message_layout = QtWidgets.QVBoxLayout(self.message_widget)
                message_layout.setContentsMargins(0, 0, 0, 0)
                message_layout.setSpacing(0)

                BASE_DIR = Path(__file__).resolve().parent
                ICON_DIR = BASE_DIR / "images"

                # ===== Header widget (green bar) =====
                self.header_widget = QtWidgets.QWidget(parent=self.message_widget)
                self.header_widget.setObjectName("header_widget")
                self.header_widget.setStyleSheet("""
            QWidget#header_widget {
                background-color: #003d1f;
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
            }
            QLabel#name_header {
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QLabel#header2_accesslvl {
                color: #e0f3ea;
                font-size: 11px;
            }
            QToolButton#toolButton {
                background: transparent;
                border: none;
                color: white;
            }
            QToolButton#toolButton::menu-indicator {
                width: 0px;
                height: 0px;
            }
        """)
                header_layout = QtWidgets.QHBoxLayout(self.header_widget)
                header_layout.setContentsMargins(12, 8, 12, 8)
                header_layout.setSpacing(8)

                header_left = QtWidgets.QVBoxLayout()
                header_left.setContentsMargins(0, 0, 0, 0)
                header_left.setSpacing(2)

                self.name_header = QtWidgets.QLabel(parent=self.header_widget)
                self.name_header.setObjectName("name_header")
                font = QtGui.QFont()
                font.setFamily("Arial")
                font.setPointSize(16)
                self.name_header.setFont(font)
                header_left.addWidget(self.name_header)

                self.header2_accesslvl = QtWidgets.QLabel(parent=self.header_widget)
                self.header2_accesslvl.setObjectName("header2_accesslvl")
                font2 = QtGui.QFont()
                font2.setFamily("Arial")
                font2.setPointSize(10)
                self.header2_accesslvl.setFont(font2)
                header_left.addWidget(self.header2_accesslvl)

                header_layout.addLayout(header_left)
                header_layout.addStretch()

                self.toolButton = QtWidgets.QToolButton(parent=self.header_widget)
                self.toolButton.setObjectName("toolButton")
                self.toolButton.setIcon(QIcon(str(ICON_DIR / "dots.png")))
                self.toolButton.setIconSize(QtCore.QSize(24, 24))
                header_layout.addWidget(self.toolButton)

                message_layout.addWidget(self.header_widget)

                # ===== Body (messages + input) =====
                body_widget = QtWidgets.QWidget(parent=self.message_widget)
                body_layout = QtWidgets.QVBoxLayout(body_widget)
                body_layout.setContentsMargins(12, 8, 12, 12)
                body_layout.setSpacing(8)

                self.line_3 = QtWidgets.QFrame(parent=body_widget)
                self.line_3.setFrameShape(QtWidgets.QFrame.Shape.HLine)
                self.line_3.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
                self.line_3.setObjectName("line_3")
                body_layout.addWidget(self.line_3)

                # Scrollable message area
                self.scroll_area = QtWidgets.QScrollArea(parent=body_widget)
                self.scroll_area.setWidgetResizable(True)
                self.scroll_area.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)

                self.messages_container = QtWidgets.QWidget()
                self.messages_layout = QtWidgets.QVBoxLayout(self.messages_container)
                self.messages_layout.setContentsMargins(0, 0, 0, 0)
                self.messages_layout.setSpacing(8)
                self.messages_layout.addStretch()

                self.scroll_area.setWidget(self.messages_container)
                body_layout.addWidget(self.scroll_area, 1)

                # Bottom input bar
                self.line_4 = QtWidgets.QFrame(parent=body_widget)
                self.line_4.setFrameShape(QtWidgets.QFrame.Shape.HLine)
                self.line_4.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
                self.line_4.setObjectName("line_4")
                body_layout.addWidget(self.line_4)

                input_row = QtWidgets.QHBoxLayout()
                input_row.setContentsMargins(0, 0, 0, 0)
                input_row.setSpacing(6)

                self.button_attachments = QtWidgets.QToolButton(parent=body_widget)
                self.button_attachments.setObjectName("button_attachments")
                self.button_attachments.setIcon(QIcon(str(ICON_DIR / "open-folder.png")))
                self.button_attachments.setIconSize(QtCore.QSize(24, 24))
                input_row.addWidget(self.button_attachments)

                self.button_link = QtWidgets.QToolButton(parent=body_widget)
                self.button_link.setObjectName("button_link")
                self.button_link.setIcon(QIcon(str(ICON_DIR / "link.png")))
                self.button_link.setIconSize(QtCore.QSize(24, 24))
                input_row.addWidget(self.button_link)

                self.lineedit_msg = QtWidgets.QLineEdit(parent=body_widget)
                self.lineedit_msg.setObjectName("lineedit_msg")
                self.lineedit_msg.setStyleSheet("""
            QLineEdit#lineedit_msg {
                background-color: #f0f0f0;
                border-radius: 10px;
                border: 1px solid #ccc;
                padding: 5px 7px;
                font-size: 14px;
                color: #333;
            }
            QLineEdit#lineedit_msg:focus {
                border: 1px solid #084924;
            }
            QLineEdit#lineedit_msg:hover {
                border: 1px solid #888;
                background-color: #e9e9e9;
            }
        """)
                input_row.addWidget(self.lineedit_msg, 1)

                self.button_send = QtWidgets.QToolButton(parent=body_widget)
                self.button_send.setObjectName("button_send")
                self.button_send.setIcon(QIcon(str(ICON_DIR / "send.png")))
                self.button_send.setIconSize(QtCore.QSize(24, 24))
                input_row.addWidget(self.button_send)

                body_layout.addLayout(input_row)

                message_layout.addWidget(body_widget)

                root_layout.addWidget(self.message_widget)

                MainWindow.setCentralWidget(self.centralwidget)
                self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
                self.menubar.setGeometry(QtCore.QRect(0, 0, 1124, 22))
                self.menubar.setObjectName("menubar")
                MainWindow.setMenuBar(self.menubar)
                self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
                self.statusbar.setObjectName("statusbar")
                MainWindow.setStatusBar(self.statusbar)

                self.retranslateUi(MainWindow)
                QtCore.QMetaObject.connectSlotsByName(MainWindow)

        def retranslateUi(self, MainWindow):
                _translate = QtCore.QCoreApplication.translate
                MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
                self.name_header.setText(_translate("MainWindow", "Person1"))
                self.header2_accesslvl.setText(_translate("MainWindow", "Access"))
                self.toolButton.setText(_translate("MainWindow", ""))
                self.button_attachments.setText(_translate("MainWindow", ""))
                self.button_link.setText(_translate("MainWindow", ""))
                self.button_send.setText(_translate("MainWindow", ""))