# item_widget.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QMenu, QSpacerItem, QSizePolicy
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QFont, QPixmap
import os
from utils.date_utils import format_date_display

class ItemWidget(QWidget):
    def __init__(self, post, controller, user_role, parent=None):
        super().__init__(parent)
        self.post = post
        self.controller = controller
        self.user_role = user_role
        self.setup_ui()

    def _load_document_icon(self):
        """Load document icon matching Stream layout"""
        try:
            icon_path = "frontend/assets/icons/document.svg"
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                # Scale to match Stream icon size (24x24 inside 42x42 circle)
                return pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, 
                                   Qt.TransformationMode.SmoothTransformation)
        except:
            pass
        return None

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(15)  # Same spacing as Stream
        layout.setContentsMargins(15, 12, 15, 12)  # Same padding as Stream

        # # Icon - Matching Stream layout exactly
        # icon_label = QLabel(self)
        # icon_label.setFixedSize(40, 40)  # Same size as Stream (42x42 instead of 50x50)
        # icon_label.setStyleSheet("""
        #     QLabel {
        #         background-color: #084924;
        #         border-radius: 20px;  /* Half of 42px for perfect circle */
        #         border: 2px solid white;
        #         min-width: 42px;
        #         min-height: 42px;
        #         padding: 0px;
        #         margin: 5px;
        #         margin-top: -10px;
        #     }
        # """)
        
        # # Load document icon like Stream
        # document_pixmap = self._load_document_icon()
        # if document_pixmap and not document_pixmap.isNull():
        #     icon_label.setPixmap(document_pixmap)
        #     icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # else:
        #     # Fallback to document emoji (same as Stream fallback)
        #     icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        #     icon_label.setText("📄")
        #     icon_label.setStyleSheet(icon_label.styleSheet() + """
        #         QLabel {
        #             color: white;
        #             font-size: 16px;
        #         }
        #     """)
        
        # layout.addWidget(icon_label)

        # Title Label - Stream style (title only, no author)
        title_text = self.post.get("title", "")
        title_label = QLabel(title_text, self)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                border: none;
                color: #333;
                margin: 0px;
                padding: 0px;
                font-family: "Poppins", Arial, sans-serif;
            }
        """)
        title_label.setWordWrap(True)
        # title_label.setMinimumHeight(20)
        title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        title_label.setMinimumWidth(100)  # Give it some minimum width
        layout.addWidget(title_label, 1)


        # Spacer
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout.addItem(spacer)

        # Date Label - Stream style
        date_text = self.format_date(self.post.get("date", ""))
        date_label = QLabel(date_text, self)
        date_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                border: none;
                color: #666;
                margin: 0px;
                padding: 0px;
                font-family: "Poppins", Arial, sans-serif;
            }
        """)
        # date_label.setMinimumHeight(16)
        date_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        layout.addWidget(date_label)

        # Menu Button (for faculty/admin)
        if self.user_role in ["faculty", "admin"]:
            self.menu_button = QPushButton("⋮", self)
            self.menu_button.setFixedSize(30, 30)
            menu_font = QFont("Poppins")
            menu_font.setPointSize(16)
            self.menu_button.setFont(menu_font)
            self.menu_button.setStyleSheet("""
                QPushButton {
                    border: none;
                    background-color: transparent;
                    color: #656d76;
                    border-radius: 15px;
                    font-weight: bold;
                    font-family: "Poppins", Arial, sans-serif;
                }
                QPushButton:hover {
                    background-color: #F3F4F6;
                }
            """)
            layout.addWidget(self.menu_button)
            self.menu_button.clicked.connect(self.show_menu)

    def format_date(self, date_str):
        return format_date_display(date_str)

    def show_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 4px 0px;
                font-family: "Poppins", Arial, sans-serif;
            }
            QMenu::item {
                padding: 8px 16px;
                font-size: 16px;
            }
            QMenu::item:selected {
                background-color: #f5f5f5;
            }
        """)
        edit_action = QAction("Edit", self)
        delete_action = QAction("Delete", self)
        edit_action.triggered.connect(lambda: self.controller.edit_post(self.post))
        delete_action.triggered.connect(lambda: self.controller.delete_post(self.post))
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        button_pos = self.menu_button.mapToGlobal(self.menu_button.rect().bottomLeft())
        menu.exec(button_pos)