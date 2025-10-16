import os
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QSizePolicy, QGraphicsDropShadowEffect
from PyQt6.QtGui import QPixmap, QIcon, QColor
from PyQt6.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve, pyqtSignal, QSize


class MemberCard(QWidget):
    profile_clicked = pyqtSignal()
    chat_clicked = pyqtSignal()

    def __init__(self, name: str, role: str, avatar_path: str = "", parent=None):
        super().__init__(parent)
        self.name = name
        self.role = role
        self.avatar_path = avatar_path
        self.setStyleSheet("background: transparent;")
        self.setFixedHeight(120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumWidth(500)

        # Card background with shadow
        self.card_bg = QWidget(self)
        self.card_bg.setObjectName("memberCard")

        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(4)
        self.shadow.setColor(QColor(0, 0, 0, 30))
        self.card_bg.setGraphicsEffect(self.shadow)

        self._setup_widgets()

        # Hover animation
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        self.shadow_anim = QPropertyAnimation(self.shadow, b"blurRadius")
        self.shadow_anim.setDuration(200)
        self.shadow_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _setup_widgets(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        assets_base_path = os.path.join(base_dir, "..", "..", "..", "frontend", "assets", "images")

        self.card_bg.setStyleSheet("""
            QWidget#memberCard {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: 1px solid rgba(0, 0, 0, 0.06);
            }
        """)

        # Avatar
        self.avatar_container = QWidget(self.card_bg)
        self.avatar_container.setGeometry(20, 30, 60, 60)
        self.avatar_container.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #084924, stop:1 #0a6030);
            border-radius: 30px;
        """)

        self.avatar_label = QLabel(self.avatar_container)
        avatar_full_path = self.avatar_path or os.path.join(assets_base_path, "avatars", "man1.png")
        if not os.path.exists(avatar_full_path):
            avatar_full_path = os.path.join(assets_base_path, "avatars", "man1.png")
        pixmap = QPixmap(avatar_full_path)
        self.avatar_label.setPixmap(pixmap.scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatio,
                                                 Qt.TransformationMode.SmoothTransformation))
        self.avatar_label.setStyleSheet("border-radius: 28px; background: transparent;")
        self.avatar_label.setGeometry(2, 2, 56, 56)

        self.name_label = QLabel(self.card_bg)
        self.name_label.setText(self.name)
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet("""
            QLabel {
                color: #1a1a1a;
                font-family: 'Inter';
                font-weight: 700;
                font-size: 15px;
                letter-spacing: -0.3px;
                background: transparent;
            }
        """)

        self.role_container = QWidget(self.card_bg)
        self.role_container.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(8, 73, 36, 0.08), stop:1 rgba(253, 198, 1, 0.08));
            border-radius: 10px;
        """)

        self.role_label = QLabel(self.role_container)
        self.role_label.setText(self.role)
        self.role_label.setWordWrap(True)
        self.role_label.setStyleSheet("""
            QLabel {
                color: #084924;
                font-family: 'Inter';
                font-weight: 600;
                font-size: 12px;
                background: transparent;
                padding: 4px 8px;
            }
        """)

        self.actions_widget = QWidget(self.card_bg)
        actions_layout = QVBoxLayout(self.actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(12)

        profile_icon_path = os.path.join(assets_base_path, "Resume.png")
        self.profile_button = QPushButton()
        if os.path.exists(profile_icon_path):
            self.profile_button.setIcon(QIcon(QPixmap(profile_icon_path).scaled(37, 37,
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)))
            self.profile_button.setIconSize(QSize(37, 37))
        self.profile_button.setFixedSize(45, 45)
        self.profile_button.setStyleSheet("""
            QPushButton {
                border: none;
                background: rgba(255, 255, 255, 0.8);
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #084924, stop:1 #0a6030);
            }
        """)
        self.profile_button.clicked.connect(self.profile_clicked)
        actions_layout.addWidget(self.profile_button, alignment=Qt.AlignmentFlag.AlignCenter)

        chat_icon_path = os.path.join(assets_base_path, "chat.png")
        self.chat_button = QPushButton()
        if os.path.exists(chat_icon_path):
            self.chat_button.setIcon(QIcon(QPixmap(chat_icon_path).scaled(37, 37,
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)))
            self.chat_button.setIconSize(QSize(37, 37))
        self.chat_button.setFixedSize(45, 45)
        self.chat_button.setStyleSheet("""
            QPushButton {
                border: none;
                background: rgba(255, 255, 255, 0.8);
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FDC601, stop:1 #fdd13a);
            }
        """)
        self.chat_button.clicked.connect(self.chat_clicked)
        actions_layout.addWidget(self.chat_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self._update_geometry()

    def _update_geometry(self):
        card_width = max(self.width(), 300)
        self.card_bg.setGeometry(0, 0, card_width, 120)
        content_width = card_width - 183
        if content_width < 100:
            content_width = 100
            card_width = content_width + 183
            self.setMinimumWidth(card_width)
        self.name_label.setGeometry(95, 30, content_width, 28)
        self.role_container.setGeometry(95, 62, content_width, 28)
        self.role_label.setGeometry(8, 0, content_width - 16, 28)
        self.actions_widget.setGeometry(card_width - 98, 15, 88, 90)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_geometry()

    def enterEvent(self, event):
        geom = self.geometry()
        self.animation.stop()
        self.animation.setStartValue(geom)
        self.animation.setEndValue(QRect(geom.x(), geom.y() - 4, geom.width(), geom.height()))
        self.animation.start()
        self.shadow_anim.setStartValue(20)
        self.shadow_anim.setEndValue(28)
        self.shadow_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        geom = self.geometry()
        self.animation.stop()
        self.animation.setStartValue(geom)
        self.animation.setEndValue(QRect(geom.x(), geom.y() + 4, geom.width(), geom.height()))
        self.animation.start()
        self.shadow_anim.setStartValue(28)
        self.shadow_anim.setEndValue(20)
        self.shadow_anim.start()
        super().leaveEvent(event)
