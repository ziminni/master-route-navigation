import sys, os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTableView,
                             QStackedWidget, QComboBox, QHeaderView)
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QIcon, QColor
from .Tagging.classes_page import ClassesPage
from .Tagging.sections_page import SectionsPage



class TaggingMain(QWidget):
    def __init__(self, username, roles, primary_role, token):
        super().__init__()
        self.setWindowTitle("Classroom Tagging System")
        self.setGeometry(100, 100, 1200, 700)
        self.sidebar_expanded = True  # Track sidebar state
        self.init_ui()
    
    def init_ui(self):
        # Main layout for the widget
        main_layout = QHBoxLayout(self)  # Set layout directly on the widget
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(130)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # Hamburger menu
        self.menu_btn = QPushButton("☰")
        self.menu_btn.setFixedHeight(60)
        self.menu_btn.setStyleSheet("""
            QPushButton {
                color: #084924;
                font-size: 24px;
                border: none;
                text-align: center;
                border-bottom: 1px solid #d0d0d0;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.menu_btn.clicked.connect(self.toggle_sidebar)  # Connect to toggle function
        sidebar_layout.addWidget(self.menu_btn)
        
        # Navigation buttons
        self.nav_buttons = []
        
        sections_btn = self.create_nav_button("Sections", "sections")
        classes_btn = self.create_nav_button("Classes", "classes")
        archive_btn = self.create_nav_button("Archive", "archive")
        
        sidebar_layout.addWidget(sections_btn)
        sidebar_layout.addWidget(classes_btn)
        sidebar_layout.addWidget(archive_btn)
        sidebar_layout.addStretch()
        
        self.nav_buttons = [sections_btn, classes_btn, archive_btn]
        
        main_layout.addWidget(self.sidebar)
        
        # Content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Top header
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("background-color: white; border-bottom: 1px solid #d0d0d0;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        header_title = QLabel("CLASSROOM TAGGING")
        header_title.setFont(QFont("Segoe UI", 14, QFont.Weight.DemiBold))
        header_title.setStyleSheet("color: #1e5631; margin-left: 15px;")
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        
        content_layout.addWidget(header)
        
        # Stacked widget for pages
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background-color: #ffffff;")
        
        # Add pages
        self.sections_page = SectionsPage()
        self.classes_page = ClassesPage()
        archive_page = QLabel("Archive")
        archive_page.setAlignment(Qt.AlignmentFlag.AlignCenter)
        archive_page.setFont(QFont("Segoe UI", 16))
        
        self.stacked_widget.addWidget(self.sections_page)
        self.stacked_widget.addWidget(self.classes_page)
        self.stacked_widget.addWidget(archive_page)
        
        content_layout.addWidget(self.stacked_widget)
        main_layout.addWidget(content_widget)
        
        # Set initial active button
        self.set_active_nav_button(sections_btn)
    
    def toggle_sidebar(self):
        """Toggle sidebar between collapsed and expanded states"""
        if self.sidebar_expanded:
            # Collapse sidebar
            self.animate_sidebar(60)  # Collapse to show only hamburger menu
            self.sidebar_expanded = False
        else:
            # Expand sidebar
            self.animate_sidebar(130)  # Expand to full width
            self.sidebar_expanded = True
    
    def animate_sidebar(self, target_width):
        """Animate the sidebar width change"""
        self.animation = QPropertyAnimation(self.sidebar, b"minimumWidth")
        self.animation.setDuration(250)  # Animation duration in milliseconds
        self.animation.setStartValue(self.sidebar.width())
        self.animation.setEndValue(target_width)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # Also animate maximum width
        self.animation2 = QPropertyAnimation(self.sidebar, b"maximumWidth")
        self.animation2.setDuration(250)
        self.animation2.setStartValue(self.sidebar.width())
        self.animation2.setEndValue(target_width)
        self.animation2.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        self.animation.start()
        self.animation2.start()
    
    def create_nav_button(self, text, page_id):
        btn = QPushButton(text)
        btn.setFixedHeight(50)
        btn.setProperty("page_id", page_id)
        btn.setStyleSheet("""
            QPushButton {
                color: white;
                text-align: left;
                padding-left: 20px;
                border: none;
                font-size: 13px;
                background-color: red;
            }
        """)
        btn.clicked.connect(lambda: self.switch_page(btn))
        return btn
    
    def switch_page(self, button):
        page_id = button.property("page_id")
        if page_id == "sections":
            self.stacked_widget.setCurrentIndex(0)
        elif page_id == "classes":
            self.stacked_widget.setCurrentIndex(1)
        elif page_id == "archive":
            self.stacked_widget.setCurrentIndex(2)
        
        self.set_active_nav_button(button)
    
    def set_active_nav_button(self, active_button):
        for btn in self.nav_buttons:
            if btn == active_button:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ffffff;
                        color: #084924;
                        text-align: left;
                        padding-left: 20px;
                        border: none;
                        font-size: 13px;
                        border-left: 4px solid #1e5631;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ffffff;
                        color: #084924;
                        text-align: left;
                        padding-left: 20px;
                        border: none;
                        font-size: 13px;
                    }
                    QPushButton:hover {
                        background-color: #BDBDBD;
                        color: white;
                    }
                """)


def main():
    app = QApplication(sys.argv)
    window = TaggingMain("username", "roles", "primary_role", "token")
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()