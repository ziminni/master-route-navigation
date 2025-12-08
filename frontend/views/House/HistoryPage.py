import sys
import os
import json
import requests
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QScrollArea, QFrame, QDialog, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QFont, QPainterPath, QRegion
from PyQt6.QtCore import Qt, QRectF, pyqtSignal


class RoundedTopImageLabel(QLabel):
    """QLabel subclass with only top-left and top-right rounded corners."""
    def __init__(self, radius=12):
        super().__init__()
        self.radius = radius
        self._pixmap = None

    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        super().setPixmap(pixmap)
        self.update_mask()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_mask()

    def update_mask(self):
        if not self._pixmap:
            return
        path = QPainterPath()
        rect = QRectF(self.rect())
        # Round only top corners
        path.moveTo(rect.left(), rect.bottom())
        path.lineTo(rect.left(), rect.top() + self.radius)
        path.quadTo(rect.left(), rect.top(), rect.left() + self.radius, rect.top())
        path.lineTo(rect.right() - self.radius, rect.top())
        path.quadTo(rect.right(), rect.top(), rect.right(), rect.top() + self.radius)
        path.lineTo(rect.right(), rect.bottom())
        path.lineTo(rect.left(), rect.bottom())
        path.closeSubpath()
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)


class EventDetailsPopup(QDialog):
    def __init__(self, parent, data, details):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setModal(False)
        self.resize(900, 600)  # Landscape orientation
        self.setStyleSheet("background: transparent;")

        # Main layout with shadow effect container
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Outer container for green border
        outer_frame = QFrame()
        outer_frame.setStyleSheet("""
            QFrame {
                background: #084924;
                border-radius: 20px;
                padding: 3px;
            }
        """)
        
        # Inner white container
        inner_frame = QFrame()
        inner_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 18px;
            }
        """)
        
        # Setup outer frame layout
        outer_layout = QVBoxLayout(outer_frame)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(inner_frame)
        
        main_layout.addWidget(outer_frame)
        
        # Content layout for inner frame - using HBox for landscape
        content_layout = QHBoxLayout(inner_frame)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        
        # Left side - Image and basic info
        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)
        
        # Header with title only (X button removed)
        header_layout = QHBoxLayout()
        
        # Title
        title_label = QLabel(details["title"])
        title_label.setFont(QFont("Poppins", 18, QFont.Weight.Black))
        title_label.setStyleSheet("color: #084924;")
        title_label.setWordWrap(True)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        left_layout.addLayout(header_layout)
        
        # Event image
        base_dir = os.path.dirname(os.path.abspath(__file__))
        pics_dir = os.path.join(base_dir, "..", "..", "assets", "images", "pics")
        img_filename = os.path.basename(data.get("img", "default.png"))
        img_path = os.path.join(pics_dir, img_filename)
        
        if os.path.exists(img_path):
            image_label = QLabel()
            pixmap = QPixmap(img_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(400, 250, Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                                      Qt.TransformationMode.SmoothTransformation)
                image_label.setPixmap(pixmap)
                image_label.setStyleSheet("border-radius: 12px; border: 2px solid #084924;")
                image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                image_label.setFixedSize(400, 250)
                left_layout.addWidget(image_label)
        
        # Basic info section
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 12px;
                padding: 15px;
                border: 2px solid #e9ecef;
            }
        """)
        info_layout = QVBoxLayout(info_frame)
        
        # Placement with medal
        placement_map = {1: "🥇 1st Place", 2: "🥈 2nd Place", 3: "🥉 3rd Place"}
        placement_text = placement_map.get(data.get("placement"), "🎯 Participant")
        placement_label = QLabel(placement_text)
        placement_label.setFont(QFont("Poppins", 16, QFont.Weight.Bold))
        placement_label.setStyleSheet("color: #f39c12; background-color: #fff9e6; padding: 8px 12px; border-radius: 8px;")
        placement_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(placement_label)
        
        # Quick info
        quick_info = QLabel(f"📅 {details.get('date', 'N/A')}\n⏰ {details.get('time', 'N/A')}\n📍 {details.get('location', 'N/A')}")
        quick_info.setStyleSheet("color: #2c3e50; font-family: 'Inter'; font-size: 13px; font-weight: 600; line-height: 1.6;")
        quick_info.setWordWrap(True)
        info_layout.addWidget(quick_info)
        
        left_layout.addWidget(info_frame)
        left_layout.addStretch()
        
        # Right side - Detailed information
        right_layout = QVBoxLayout()
        right_layout.setSpacing(15)
        
        # Scroll area for detailed content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #053D1D;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: white;
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }
        """)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(12)
        
        # Points and Category
        stats_layout = QHBoxLayout()
        
        points_frame = QFrame()
        points_frame.setStyleSheet("""
            QFrame {
                background-color: #d4edda;
                border-radius: 8px;
                padding: 10px;
                border: 1px solid #c3e6cb;
            }
        """)
        points_layout = QVBoxLayout(points_frame)
        points_label = QLabel(f"🏆 {data.get('points', 'N/A')} Points")
        points_label.setStyleSheet("color: #155724; font-family: 'Inter'; font-size: 14px; font-weight: bold;")
        points_layout.addWidget(points_label)
        
        category_frame = QFrame()
        category_frame.setStyleSheet("""
            QFrame {
                background-color: #d1ecf1;
                border-radius: 8px;
                padding: 10px;
                border: 1px solid #bee5eb;
            }
        """)
        category_layout = QVBoxLayout(category_frame)
        category_label = QLabel(f"📂 {data.get('type', 'N/A')}")
        category_label.setStyleSheet("color: #0c5460; font-family: 'Inter'; font-size: 14px; font-weight: bold;")
        category_layout.addWidget(category_label)
        
        stats_layout.addWidget(points_frame)
        stats_layout.addWidget(category_frame)
        scroll_layout.addLayout(stats_layout)
        
        # Adviser
        adviser_frame = QFrame()
        adviser_frame.setStyleSheet("""
            QFrame {
                background-color: #e2e3e5;
                border-radius: 8px;
                padding: 10px;
                border: 1px solid #d6d8db;
            }
        """)
        adviser_layout = QVBoxLayout(adviser_frame)
        adviser_label = QLabel(f"👨‍🏫 Adviser: {details.get('adviser', 'N/A')}")
        adviser_label.setStyleSheet("color: #383d41; font-family: 'Inter'; font-size: 13px; font-weight: 600;")
        adviser_layout.addWidget(adviser_label)
        scroll_layout.addWidget(adviser_frame)
        
        # Description section
        if "details" in details:
            desc_frame = QFrame()
            desc_frame.setStyleSheet("""
                QFrame {
                    background-color: #f8f9fa;
                    border-radius: 8px;
                    padding: 12px;
                    border: 1px solid #e9ecef;
                }
            """)
            desc_layout = QVBoxLayout(desc_frame)
            
            desc_title = QLabel("📝 Event Description")
            desc_title.setFont(QFont("Poppins", 12, QFont.Weight.Bold))
            desc_title.setStyleSheet("color: #084924; margin-bottom: 6px;")
            desc_layout.addWidget(desc_title)
            
            # Handle details as either string or list
            details_text = details["details"]
            if isinstance(details_text, list):
                details_text = "\n".join(str(item) for item in details_text)
            desc_label = QLabel(str(details_text) if details_text else "No details available")
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #495057; font-family: 'Inter'; font-size: 12px; line-height: 1.4;")
            desc_layout.addWidget(desc_label)
            
            scroll_layout.addWidget(desc_frame)
        
        # Team Members
        members_frame = QFrame()
        members_frame.setStyleSheet("""
            QFrame {
                background-color: #fff3cd;
                border-radius: 8px;
                padding: 12px;
                border: 1px solid #ffeaa7;
            }
        """)
        members_layout = QVBoxLayout(members_frame)
        
        members_title = QLabel("👨‍🎓 Team Members")
        members_title.setFont(QFont("Poppins", 12, QFont.Weight.Bold))
        members_title.setStyleSheet("color: #856404; margin-bottom: 6px;")
        members_layout.addWidget(members_title)
        
        members_label = QLabel(data.get('membersO', 'N/A'))
        members_label.setWordWrap(True)
        members_label.setStyleSheet("color: #856404; font-family: 'Inter'; font-size: 12px; font-weight: 600;")
        members_layout.addWidget(members_label)
        
        scroll_layout.addWidget(members_frame)
        
        # Participants section
        if "participants" in details and details["participants"]:
            parts_frame = QFrame()
            parts_frame.setStyleSheet("""
                QFrame {
                    background-color: #d1ecf1;
                    border-radius: 8px;
                    padding: 12px;
                    border: 1px solid #bee5eb;
                }
            """)
            parts_layout = QVBoxLayout(parts_frame)
            
            parts_title = QLabel("👥 Participants")
            parts_title.setFont(QFont("Poppins", 12, QFont.Weight.Bold))
            parts_title.setStyleSheet("color: #0c5460; margin-bottom: 6px;")
            parts_layout.addWidget(parts_title)
            
            participants_text = " • " + "\n • ".join(details["participants"])
            participants_label = QLabel(participants_text)
            participants_label.setWordWrap(True)
            participants_label.setStyleSheet("color: #0c5460; font-family: 'Inter'; font-size: 11px; line-height: 1.4;")
            parts_layout.addWidget(participants_label)
            
            scroll_layout.addWidget(parts_frame)
        
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        right_layout.addWidget(scroll)
        
        # Action buttons at bottom right
        button_layout = QHBoxLayout()
        
        share_btn = QPushButton("📤 Share")
        share_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 15px;
                border-radius: 6px;
                font-weight: bold;
                font-family: 'Inter';
                font-size: 12px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        close_btn_bottom = QPushButton("Close")
        close_btn_bottom.setStyleSheet("""
            QPushButton {
                background-color: #084924;
                color: white;
                padding: 8px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-family: 'Inter';
                font-size: 12px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0b6b34;
            }
        """)
        close_btn_bottom.clicked.connect(self.close)
        
        button_layout.addWidget(share_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn_bottom)
        
        right_layout.addLayout(button_layout)
        
        # Add both sides to main content
        content_layout.addLayout(left_layout, 45)  # 45% width
        content_layout.addLayout(right_layout, 55)  # 55% width


class HistoryCard(QWidget):
    clicked = pyqtSignal(dict)

    def __init__(self, data):
        super().__init__()
        self.data = data
        self.setFixedSize(220, 460)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- Base directories ---
        base_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(base_dir, "..", "..", "assets", "images")
        icons_dir = os.path.join(assets_dir, "icons")
        pics_dir = os.path.join(assets_dir, "pics")

        # --- Image ---
        img_container = QWidget()
        img_container.setFixedSize(220, 220)
        img_container.setStyleSheet("border: 3px solid #fdd835; border-radius: 10px;")
        img_layout = QVBoxLayout(img_container)
        img_layout.setContentsMargins(0, 0, 0, 0)

        img_label = RoundedTopImageLabel(radius=10)
        img_label.setFixedSize(220, 220)

        img_filename = os.path.basename(self.data.get("img", "default.png"))
        img_path = os.path.join(pics_dir, img_filename)
        pixmap = QPixmap(img_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(220, 220, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                   Qt.TransformationMode.SmoothTransformation)
            rect = pixmap.rect()
            x = (rect.width() - 220) // 2
            y = (rect.height() - 220) // 2
            pixmap = pixmap.copy(x, y, 220, 220)
            img_label.setPixmap(pixmap)
        img_layout.addWidget(img_label)
        main_layout.addWidget(img_container)

        # --- Bottom Frame ---
        frame = QFrame()
        frame.setFixedSize(220, 230)
        frame.setStyleSheet("""
            QFrame {
                background: white;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
                border: 1px solid #ddd;
                border-top: 3px solid #fdd835;
            }
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # --- Placement Label with badge styling ---
        placement_map = {1: "🥇 1st Place", 2: "🥈 2nd Place", 3: "🥉 3rd Place"}
        placement_text = placement_map.get(self.data.get("placement"), "📋 Participant")

        place_label = QLabel(placement_text)
        place_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        place_label.setStyleSheet("""
            color: #084924; 
            font-family: 'Poppins'; 
            font-weight: bold;
            background: #f0f9f4;
            border-radius: 8px;
            padding: 5px;
        """)
        place_label.setFont(QFont("Poppins", 13, QFont.Weight.Bold))
        layout.addWidget(place_label)

        # --- Event Title ---
        title_label = QLabel(self.data.get("title", "Event"))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("color: #084924; font-family: 'Poppins'; font-size: 12px; font-weight: 600;")
        layout.addWidget(title_label)

        # --- Icon Grid ---
        icon_grid = QGridLayout()
        icon_grid.setHorizontalSpacing(6)
        icon_grid.setVerticalSpacing(4)

        icons = {
            "members": os.path.join(icons_dir, "membersP.png"),
            "points": os.path.join(icons_dir, "points.png"),
            "date": os.path.join(icons_dir, "date.png"),
            "category": os.path.join(icons_dir, "category.png")
        }

        def create_icon_text(icon_path, text):
            container = QHBoxLayout()
            container.setSpacing(1)

            icon = QLabel()
            pix = QPixmap(icon_path)
            if not pix.isNull():
                pix = pix.scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                icon.setPixmap(pix)

            label = QLabel(f": {text}")
            label.setWordWrap(True)
            label.setMinimumWidth(80)
            label.setStyleSheet("color: #084924; font-family: 'Inter'; font-size: 11px;")
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            container.addWidget(icon)
            container.addWidget(label)

            wrapper = QWidget()
            wrapper.setLayout(container)
            wrapper.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            return wrapper

        icon_grid.addWidget(create_icon_text(icons["members"], self.data["membersO"]), 0, 0)
        icon_grid.addWidget(create_icon_text(icons["points"], str(self.data.get("points", "0"))), 0, 1)
        icon_grid.addWidget(create_icon_text(icons["date"], self.data.get("date", "N/A")), 1, 0)
        icon_grid.addWidget(create_icon_text(icons["category"], self.data.get("type", "Event")), 1, 1)

        layout.addLayout(icon_grid)

        # --- Description ---
        desc_text = self.data.get("desc", "")
        if len(desc_text) > 40:
            desc_text = desc_text[:40] + "..."
        desc_label = QLabel(desc_text)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            color: #666;
            font-family: 'Inter';
            font-size: 10px;
            font-style: italic;
        """)
        layout.addWidget(desc_label)
        main_layout.addWidget(frame)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.data)





class HistoryPage(QWidget):
    def __init__(self, username, roles, primary_role, token, house_name, house_id=None, api_base="http://127.0.0.1:8000"):
        super().__init__()
        self.setWindowTitle("History - House System")
        self.resize(1100, 650)
        self.token = token
        self.house_id = house_id
        self.api_base = api_base

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(12)

        # --- Header Section with gradient background ---
        header_frame = QFrame()
        header_frame.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #084924, stop:1 #0b6b34); border-radius: 12px;")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 12, 15, 12)
        
        title = QLabel("🏆 Match History")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-family: 'Poppins'; font-size: 22px; font-weight: bold; color: white; background: transparent;")
        header_layout.addWidget(title)
        
        quote = QLabel("\"Track your journey through competitions and events — see placements, points, and achievements.\"")
        quote.setWordWrap(True)
        quote.setAlignment(Qt.AlignmentFlag.AlignCenter)
        quote.setStyleSheet("font-family: 'Inter'; font-style: italic; font-size: 12px; color: rgba(255, 255, 255, 0.85); background: transparent;")
        header_layout.addWidget(quote)
        
        main_layout.addWidget(header_frame)

        # --- Scrollable Area ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:horizontal {
                background: #053D1D;
                height: 14px;
                border-radius: 7px;
            }
            QScrollBar::handle:horizontal {
                background: #fdd835;
                border-radius: 7px;
                margin: 3px;
                min-width: 40px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #ffeb3b;
            }
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width: 0;
            }
        """)



        content = QWidget()
        hbox = QHBoxLayout(content)
        hbox.setSpacing(20)
        hbox.setContentsMargins(10, 10, 10, 10)

        # --- Load from API ---
        history_data, self.details_data = self.load_history_from_api()

        # --- Add cards ---
        for record in history_data:
            card = HistoryCard(record)
            card.clicked.connect(self.show_details)
            hbox.addWidget(card)

        # Add a stretch so cards align left
        hbox.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def load_history_from_api(self):
        """Load history data from mock JSON file (will be replaced with API later)."""
        history_data = []
        details_data = []
        
        try:
            # Load from mock data file
            base_dir = os.path.dirname(os.path.abspath(__file__))
            mock_dir = os.path.join(base_dir, "..", "..", "Mock")
            history_json_path = os.path.join(mock_dir, "history.json")
            details_json_path = os.path.join(mock_dir, "history_details.json")
            
            # Load history data
            if os.path.exists(history_json_path):
                with open(history_json_path, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                print(f"[HistoryPage] Loaded {len(history_data)} history records from mock data")
            
            # Load details data
            if os.path.exists(details_json_path):
                with open(details_json_path, 'r', encoding='utf-8') as f:
                    details_data = json.load(f)
            else:
                # Generate details from history data if details file doesn't exist
                for item in history_data:
                    details_data.append({
                        "id": item.get("id"),
                        "title": item.get("title", ""),
                        "date": item.get("date", "N/A"),
                        "time": "09:00 AM",
                        "location": "CMU Campus",
                        "adviser": "TBA",
                        "category": item.get("type", "Event"),
                        "details": [item.get("desc", "No description available.")],
                        "participants": [],
                    })
                    
        except Exception as e:
            print(f"[HistoryPage] Error loading history data: {e}")
        
        return history_data, details_data

    def show_details(self, data):
        match = next((d for d in self.details_data if d["id"] == data["id"]), None)
        if match:
            popup = EventDetailsPopup(self, data, match)
            popup.exec()