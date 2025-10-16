import sys
import os
import json
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
        self.setModal(True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(parent.width(), parent.height())

        overlay = QVBoxLayout(self)
        overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overlay.setContentsMargins(0, 0, 0, 0)

        bg = QWidget()
        bg.setStyleSheet("background-color: rgba(8, 73, 36, 250);")
        bg_layout = QVBoxLayout(bg)
        bg_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Popup card
        card = QFrame()
        card.setFixedSize(600, 500)
        card.setStyleSheet("""
            background: white;
            border-radius: 12px;
            padding: 20px;
        """)
        vbox = QVBoxLayout(card)
        vbox.setSpacing(10)

        title = QLabel(details["title"])
        title.setFont(QFont("Poppins", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #084924;")
        vbox.addWidget(title)

        # Date/Time/Location
        date_label = QLabel(f"{details['date']} | {details['time']}\n {details['location']}")
        date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        date_label.setStyleSheet("font-family: 'Inter'; font-size: 13px; color: #333;")
        vbox.addWidget(date_label)

        # Description
        desc = QLabel(details["details"])
        desc.setWordWrap(True)
        desc.setStyleSheet("font-family: 'Inter'; font-size: 12px; color: #222;")
        vbox.addWidget(desc)

        # Adviser
        adviser = QLabel(f"Adviser: {details['adviser']}")
        adviser.setStyleSheet("font-family: 'Inter'; font-size: 13px; color: #084924; font-weight: bold;")
        vbox.addWidget(adviser)

        # Participants
        participants_label = QLabel("Participants:\n" + ", ".join(details["participants"]))
        participants_label.setWordWrap(True)
        participants_label.setStyleSheet("font-family: 'Inter'; font-size: 12px; color: #333;")
        vbox.addWidget(participants_label)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #084924;
                color: white;
                border-radius: 8px;
                padding: 6px 12px;
                font-family: 'Inter';
            }
            QPushButton:hover {
                background-color: #0b6b34;
            }
        """)
        close_btn.clicked.connect(self.accept)
        vbox.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        bg_layout.addWidget(card)
        overlay.addWidget(bg)

    def mousePressEvent(self, event):
        child = self.childAt(event.pos())
        if not isinstance(child, QFrame):
            self.close()


class HistoryCard(QWidget):
    clicked = pyqtSignal(dict)

    def __init__(self, data):
        super().__init__()
        self.data = data
        self.setFixedSize(220, 460)  # Smaller card
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
            background: white;
            border-bottom-left-radius: 10px;
            border-bottom-right-radius: 10px;
            border-top: 1px solid #ccc;
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # --- Placement Label ---
        placement_map = {1: "1st Place", 2: "2nd Place", 3: "3rd Place"}
        placement_text = placement_map.get(self.data.get("placement"), "Participant")

        place_label = QLabel(placement_text)
        place_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        place_label.setStyleSheet("color: #084924; font-family: 'Poppins'; font-weight: bold;")
        place_label.setFont(QFont("Poppins", 14, QFont.Weight.Bold))
        layout.addWidget(place_label)

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
            label.setWordWrap(True)  # ✅ allows wrapping of long text like dates
            label.setMinimumWidth(80)  # ✅ ensures enough space to display
            label.setStyleSheet("color: #084924; font-family: 'Inter'; font-size: 11px;")
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            container.addWidget(icon)
            container.addWidget(label)

            wrapper = QWidget()
            wrapper.setLayout(container)
            wrapper.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            return wrapper

        icon_grid.addWidget(create_icon_text(icons["members"], self.data["membersO"]), 0, 0)
        icon_grid.addWidget(create_icon_text(icons["points"], self.data["points"]), 0, 1)
        icon_grid.addWidget(create_icon_text(icons["date"], self.data["date"]), 1, 0)
        icon_grid.addWidget(create_icon_text(icons["category"], self.data["type"]), 1, 1)

        layout.addLayout(icon_grid)


        # --- Description ---
        desc_label = QLabel(self.data["desc"])
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            color: #084924;
            font-family: 'Inter';
            font-size: 11px;
            font-style: italic;
            text-decoration: underline;
        """)
        layout.addWidget(desc_label)
        main_layout.addWidget(frame)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.data)





class HistoryPage(QWidget):
    def __init__(self, username, roles, primary_role, token, house_name):
        super().__init__()
        self.setWindowTitle("History - House System")
        self.resize(1100, 650)

        main_layout = QVBoxLayout(self)

        # --- Quote section ---
        quote = QLabel("“Match History records every battle you’ve played — tracking placements, scores, and rankings so you can see your growth.”")
        quote.setWordWrap(True)
        quote.setAlignment(Qt.AlignmentFlag.AlignCenter)
        quote.setStyleSheet("""
            font-family: 'Inter';
            font-style: italic;
            background: white;
            border: 1px solid #ccc;
            padding: 6px;
            border-radius: 6px;
        """)
        main_layout.addWidget(quote)

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
                background: white;
                border-radius: 7px;
                margin: 3px;
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

        # --- Load JSON ---
        base_dir = os.path.dirname(os.path.abspath(__file__))
        history_path = os.path.join(base_dir, "..", "..", "..", "frontend", "Mock", "history.json")
        with open(history_path, "r", encoding="utf-8") as f:
            history_data = json.load(f)
        with open(os.path.join(base_dir, "..", "..", "..", "frontend", "Mock", "history_details.json"), "r", encoding="utf-8") as f:
            self.details_data = json.load(f)

        # --- Add cards ---
        for record in history_data:
            card = HistoryCard(record)
            card.clicked.connect(self.show_details)
            hbox.addWidget(card)

        # Add a stretch so cards align left
        hbox.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def show_details(self, data):
        match = next((d for d in self.details_data if d["id"] == data["id"]), None)
        if match:
            popup = EventDetailsPopup(self, data, match)
            popup.exec()