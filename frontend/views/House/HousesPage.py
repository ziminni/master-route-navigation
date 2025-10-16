import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPixmap

class LogoPlaceholder(QWidget):
    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.color = color
        self.setFixedSize(80, 80)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(self.color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, 80, 80, 8, 8)
        painter.setPen(QColor(255, 255, 255))
        font = painter.font()
        font.setPointSize(12)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "LOGO")

class HouseCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, house_name, description, logo_color, parent=None):
        super().__init__(parent)
        self.house_name = house_name
        self.description = description
        self.logo_color = logo_color
        self.setFixedHeight(110)
        self.default_style = """
            QFrame {
                background-color: #ffffff;
                border: none;
                border-radius: 12px;
            }
        """
        self.clicked_style = """
            QFrame {
                background-color: #f0f0f0;
                border: none;
                border-radius: 12px;
            }
        """
        self.setStyleSheet(self.default_style)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 10))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(25)

        logo = LogoPlaceholder(self.logo_color)
        layout.addWidget(logo)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(8)

        name_label = QLabel(self.house_name)
        name_label.setStyleSheet("""
            font-size: 20px;
            font-weight: 700;
            color: #111827;
        """)
        name_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        desc_label = QLabel(self.description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            font-size: 12px;
            color: #6b7280;
            line-height: 1.5;
        """)
        desc_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        text_layout.addWidget(name_label)
        text_layout.addWidget(desc_label)
        text_layout.addStretch()

        layout.addLayout(text_layout, 1)

        image_label = QLabel()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(script_dir, "../../assets/images/cisc.png")

        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            image_label.setPixmap(pixmap)
        else:
            image_label.setText("Image\nMissing")
            image_label.setStyleSheet("font-size: 12px; color: #ff0000; text-align: center;")

        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(image_label)

        self.setLayout(layout)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.setStyleSheet(self.clicked_style)
        self.clicked.emit(self.house_name)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.setStyleSheet(self.default_style)

    def enterEvent(self, event):
        self.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: none;
                border-radius: 12px;
            }
        """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self.default_style)
        super().leaveEvent(event)

class HousesPage(QWidget):
    house_clicked = pyqtSignal(str)
    
    def __init__(self, username, roles, primary_role, token):
        super().__init__()
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(25)

        title = QLabel("Houses")
        title.setStyleSheet("""
            font-size: 32px;
            font-weight: 300;
            color: #111827;
            margin-bottom: 10px;
        """)
        main_layout.addWidget(title)

        houses = [
            {
                "name": "House of Java",
                "description": "Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. Aenean massa.",
                "color": "#d97706"
            },
            {
                "name": "House of Python",
                "description": "Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. Aenean massa.",
                "color": "#3b82f6"
            },
            {
                "name": "House of Perl",
                "description": "Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. Aenean massa.",
                "color": "#8b5cf6"
            }
        ]

        for house in houses:
            card = HouseCard(
                house["name"],
                house["description"],
                house["color"]
            )
            card.clicked.connect(self.house_clicked.emit)
            main_layout.addWidget(card)

        main_layout.addStretch()
        self.setLayout(main_layout)
        self.setStyleSheet("""
            QWidget {
                background-color: #f9fafb;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
        """)