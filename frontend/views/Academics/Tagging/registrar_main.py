import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTableView,
                             QStackedWidget, QComboBox, QHeaderView)
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QFont, QIcon, QColor
from ..test.classes_page import ClassesPage
from ..test.sections_page import SectionsPage

class ClassroomTaggingSystem(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Classroom Tagging System")
        self.setGeometry(100, 100, 1200, 700)
        self.init_ui()
    
    def init_ui(self):
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(130)
        # sidebar.setStyleSheet("background-color: #2d2d2d;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # Hamburger menu
        menu_btn = QPushButton("☰")
        menu_btn.setFixedHeight(60)
        menu_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: white;
                font-size: 24px;
                border: none;
                border-bottom: 1px solid #3d3d3d;
            }
        """)
        sidebar_layout.addWidget(menu_btn)
        
        # Navigation buttons
        self.nav_buttons = []
        
        sections_btn = self.create_nav_button("🏠  Sections", "sections")
        classes_btn = self.create_nav_button("🏠  Classes", "classes")
        archive_btn = self.create_nav_button("📚  Archive", "archive")
        
        sidebar_layout.addWidget(sections_btn)
        sidebar_layout.addWidget(classes_btn)
        sidebar_layout.addWidget(archive_btn)
        sidebar_layout.addStretch()
        
        self.nav_buttons = [sections_btn, classes_btn, archive_btn]
        
        main_layout.addWidget(sidebar)
        
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
        
        # header_menu = QLabel("☰")
        # header_menu.setStyleSheet("color: #666666; font-size: 20px;")
        # header_layout.addWidget(header_menu)
        
        header_title = QLabel("CLASSROOM TAGGING")
        header_title.setFont(QFont("Segoe UI", 14, QFont.Weight.DemiBold))
        header_title.setStyleSheet("color: #1e5631; margin-left: 15px;")
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        
        content_layout.addWidget(header)
        
        # Stacked widget for pages
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background-color: #f0f0f0;")
        
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
            }
            QPushButton:hover {
                background-color: #3d3d3d;
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
                        background-color: #3d3d3d;
                        color: white;
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
                        background-color: #2d2d2d;
                        color: white;
                        text-align: left;
                        padding-left: 20px;
                        border: none;
                        font-size: 13px;
                    }
                    QPushButton:hover {
                        background-color: #3d3d3d;
                    }
                """)


def main():
    app = QApplication(sys.argv)
    window = ClassroomTaggingSystem()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()