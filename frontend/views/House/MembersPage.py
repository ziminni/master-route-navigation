import os
import urllib.request
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QMenu, QGridLayout
from PyQt6.QtGui import QPixmap, QIcon, QAction, QFontDatabase
from PyQt6.QtCore import Qt, QSize, QPoint
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                            QLineEdit, QMenu, QGridLayout, QGraphicsDropShadowEffect, 
                            QSizePolicy)
from PyQt6.QtGui import QPixmap, QIcon, QAction, QFontDatabase, QColor
from PyQt6.QtCore import Qt, QSize, QPoint, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect

from controller.HouseController import HouseController
from utils.smooth_scroll import SmoothScrollArea
from .members_card import MemberCard

def load_fonts():
    fonts = {
        "Poppins-Regular": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf",
        "Poppins-Bold": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf",
        "Inter-Regular": "https://github.com/google/fonts/raw/main/ofl/inter/Inter-Regular.ttf",
        "Inter-Bold": "https://github.com/google/fonts/raw/main/ofl/inter/Inter-Bold.ttf",
    }
    for name, url in fonts.items():
        try:
            with urllib.request.urlopen(url) as response:
                font_data = response.read()
                font_id = QFontDatabase.addApplicationFontFromData(font_data)
                if font_id == -1:
                    print(f"Could not load font: {name}")
                else:
                    loaded_families = QFontDatabase.applicationFontFamilies(font_id)
                    print(f"Loaded {name}: {loaded_families}")
        except Exception as e:
            print(f"Failed to load {name} from {url}: {e}")

class MembersPage(QWidget):
    def __init__(self, username, roles, primary_role, token, house_name):
        super().__init__()
        self.setMinimumSize(600, 500)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(32, 24, 32, 24)
        self.main_layout.setSpacing(20)

        # Initialize controller
        self.controller = HouseController(self)
        self.controller.members_updated.connect(self.update_member_grid)

        # Top area
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(12)

        # Title
        title_label = QLabel("Team Members")
        title_label.setStyleSheet("""
            QLabel {
                font-family: 'Inter';
                font-weight: 800;
                font-size: 28px;
                color: #084924;
                letter-spacing: -0.5px;
            }
        """)
        top_layout.addWidget(title_label)

        # Search and filter row
        search_row = QHBoxLayout()
        search_row.setContentsMargins(0, 0, 0, 0)
        search_row.setSpacing(12)

        # Search box with icon
        self.search_container = QWidget()
        self.search_container.setObjectName("searchContainer")
        search_container_layout = QHBoxLayout(self.search_container)
        search_container_layout.setContentsMargins(16, 12, 16, 12)
        search_container_layout.setSpacing(10)
        self.search_container.setFixedHeight(52)

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        search_icon = QLabel()
        search_icon_path = os.path.join(project_root, "frontend", "assets", "images", "search.png")
        if os.path.exists(search_icon_path):
            search_icon.setPixmap(
                QPixmap(search_icon_path).scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            )
        else:
            print(f"Search icon not found at: {search_icon_path}")
        search_icon.setStyleSheet("background: transparent;")
        search_container_layout.addWidget(search_icon)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchBar")
        self.search_input.setPlaceholderText("Search members by name or role...")
        self.search_input.setFrame(False)
        self.search_input.textChanged.connect(self.controller.search_members)
        search_container_layout.addWidget(self.search_input)

        search_row.addWidget(self.search_container, 1)

        # Filter button
        self.filter_btn = QPushButton(" Filter")
        self.filter_btn.setObjectName("filterButton")
        filter_icon_path = os.path.join(project_root, "frontend", "assets", "images", "filter.png")
        if os.path.exists(filter_icon_path):
            pixmap = QPixmap(filter_icon_path).scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.filter_btn.setIcon(QIcon(pixmap))
            self.filter_btn.setIconSize(QSize(20, 20))
        else:
            print(f"Filter icon not found at: {filter_icon_path}")
        self.filter_btn.setFixedHeight(52)
        self.filter_btn.setFixedWidth(120)
        self.filter_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.filter_btn.clicked.connect(lambda: self.show_filter_menu(self.filter_btn))
        search_row.addWidget(self.filter_btn)

        top_layout.addLayout(search_row)
        self.main_layout.addWidget(top_widget)

        # Members area
        members_area = QWidget()
        members_layout_outer = QVBoxLayout(members_area)
        members_layout_outer.setContentsMargins(0, 0, 0, 0)

        self.scroll = SmoothScrollArea()
        self.scroll.setObjectName("membersScroll")
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_content = QWidget()
        
        self.grid = QGridLayout(self.scroll_content)
        self.grid.setContentsMargins(20, 20, 20, 20)
        self.grid.setHorizontalSpacing(20)
        self.grid.setVerticalSpacing(20)
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 1)

        # Initial population of the grid
        self.update_member_grid(self.controller.get_filtered_members())
        print("Initial grid population completed")

        self.scroll_content.setLayout(self.grid)
        self.scroll.setWidget(self.scroll_content)
        members_layout_outer.addWidget(self.scroll)
        self.main_layout.addWidget(members_area)

        self.main_layout.setStretch(0, 0)
        self.main_layout.setStretch(1, 1)

        # Enhanced stylesheet (unchanged)
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fafafa, stop:1 #f0f0f0);
            }
            
            QWidget#searchContainer {
                background-color: white;
                border: 2px solid rgba(8, 73, 36, 0.15);
                border-radius: 12px;
            }
            
            QWidget#searchContainer:focus-within {
                border: 2px solid #084924;
            }
            
            QLineEdit#searchBar {
                border: none;
                font-family: "Inter", "Segoe UI", Arial, sans-serif;
                font-size: 14px;
                color: #1a1a1a;
                background: transparent;
                font-weight: 500;
            }
            
            QLineEdit#searchBar::placeholder {
                color: #999999;
                font-weight: 400;
            }
            
            QPushButton#filterButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #084924, stop:1 #0a6030);
                border: none;
                border-radius: 12px;
                color: white;
                font-family: "Inter", "Segoe UI", Arial, sans-serif;
                font-weight: 700;
                font-size: 14px;
                padding-left: 16px;
                padding-right: 16px;
            }
            
            QPushButton#filterButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0a6030, stop:1 #084924);
            }
            
            QMenu {
                background-color: white;
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 12px;
                padding: 8px;
            }
            
            QMenu::item {
                padding: 12px 24px;
                font-family: "Inter", "Segoe UI", Arial, sans-serif;
                font-weight: 600;
                color: #084924;
                border-radius: 8px;
                margin: 2px;
            }
            
            QMenu::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(253, 198, 1, 0.3), stop:1 rgba(8, 73, 36, 0.1));
            }
            
            QScrollBar:vertical {
                background: rgba(0, 0, 0, 0.05);
                width: 10px;
                margin: 4px;
                border-radius: 5px;
            }
            
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #084924, stop:1 #0a6030);
                min-height: 40px;
                border-radius: 5px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #084924;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            
            QScrollBar::page:vertical {
                background: transparent;
            }
            
            QWidget#membersScroll {
                background-color: rgba(255, 255, 255, 0.6);
                border: 1px solid rgba(0, 0, 0, 0.06);
                border-radius: 20px;
            }
        """)

    def update_member_grid(self, members):
        """Update the grid with the provided members."""
        print(f"Updating grid with {len(members)} members")
        # Clear existing grid
        for i in reversed(range(self.grid.count())):
            widget = self.grid.itemAt(i).widget()
            if widget:
                self.grid.removeWidget(widget)
                widget.deleteLater()

        # Populate grid with new members
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        avatars_base_path = os.path.join(project_root, "frontend", "assets", "images", "avatars")
        row = 0
        col = 0
        for m in members:
            avatar_filename = m.get("avatar", "man1.png") if m.get("avatar") else "man1.png"
            full_avatar_path = os.path.join(avatars_base_path, avatar_filename)
            if not os.path.exists(full_avatar_path):
                full_avatar_path = os.path.join(avatars_base_path, "man1.png")
                print(f"Avatar not found, using default: {full_avatar_path}")
            card = MemberCard(m["name"], m["role"], avatar_path=full_avatar_path)
            card.setMaximumWidth(306)
            self.grid.addWidget(card, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1
        self.grid.update()
        self.scroll_content.update()
        self.scroll.update()
        print("Grid update completed")

    def show_filter_menu(self, button):
        menu = QMenu(self)
        menu.setFixedWidth(220)
        for label in ["Year Level", "Position", "A-Z", "Z-A"]:
            act = QAction(label, self)
            act.triggered.connect(lambda checked, l=label: self.controller.filter_members(l))
            menu.addAction(act)
        global_pos = button.mapToGlobal(button.rect().bottomLeft())
        offset = QPoint(0, 8)
        menu.exec(global_pos + offset)