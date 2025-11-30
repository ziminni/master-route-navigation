from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QFrame, QSpacerItem, QSizePolicy, QGraphicsDropShadowEffect
from PyQt6.QtGui import QPixmap, QFont, QColor
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect
import os


class LowerLeaderboardCard(QFrame):
    def __init__(self, rank, name, house, points, avatar="avatar1.png", column="left"):
        """
        column: "left" or "right" — for slight alignment adjustment
        """
        super().__init__()
        self._original_y = None  # Store original Y position

        # === CARD CONTAINER ===
        self.setFixedHeight(40)
        self.setFixedWidth(370)
        self.setStyleSheet("""
            QFrame {
                background-color: #D9D9D9;
                border-radius: 6px;
            }
        """)
        
        # Add shadow effect
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(12)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(3)
        self.shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(self.shadow)
        
        # Enable hover events
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        
        # Hover animation
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Shadow animation
        self.shadow_anim = QPropertyAnimation(self.shadow, b"blurRadius")
        self.shadow_anim.setDuration(200)
        self.shadow_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # === LEFT SIDE (rank, avatar, name, house) ===
        left_layout = QHBoxLayout()
        left_layout.setSpacing(5)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # RANK
        rank_label = QLabel(rank)
        rank_label.setFont(QFont("Poppins", 10, QFont.Weight.DemiBold))
        rank_label.setStyleSheet("font-style: italic; color: #000000;")
        left_layout.addWidget(rank_label)

        # AVATAR
        avatar_label = QLabel()
        # Calculate base directory relative to this file
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        avatars_path = os.path.join(base_dir, "assets", "images", "avatars")
        
        avatar_path = os.path.join(avatars_path, avatar) if avatar else ""
        if not avatar_path or not os.path.exists(avatar_path):
            avatar_path = os.path.join(avatars_path, "man1.png")
            if not os.path.exists(avatar_path):
                # If still not found, try relative path as fallback
                avatar_path = os.path.join("frontend", "assets", "images", "avatars", "man1.png")

        if os.path.exists(avatar_path):
            pixmap = QPixmap(avatar_path).scaled(
                30, 30,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            avatar_label.setPixmap(pixmap)
        avatar_label.setFixedSize(30, 30)
        avatar_label.setStyleSheet("border-radius: 21px; background-color: transparent;")
        left_layout.addWidget(avatar_label)

        # NAME + HOUSE
        info_layout = QVBoxLayout()
        info_layout.setSpacing(0)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        name_label = QLabel(name)
        name_label.setFont(QFont("Poppins", 9, QFont.Weight.DemiBold))
        name_label.setStyleSheet("color: #000000;")

        house_label = QLabel(house)
        house_label.setFont(QFont("Inter", 7))
        house_label.setStyleSheet("font-style: italic; color: #000000;")

        info_layout.addWidget(name_label)
        info_layout.addWidget(house_label)
        left_layout.addLayout(info_layout)
        layout.addLayout(left_layout)

        # === SPACER ===
        layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # === RIGHT SIDE (points) ===
        points_layout = QVBoxLayout()
        points_layout.setSpacing(0)
        points_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        points_label = QLabel("Points")
        points_label.setFont(QFont("Inter", 7))
        points_label.setStyleSheet("color: #000000; text-align: right;")

        points_value = QLabel(str(points))
        points_value.setFont(QFont("Poppins", 9, QFont.Weight.DemiBold))
        points_value.setStyleSheet("color: #000000; text-align: right;")

        points_layout.addWidget(points_label)
        points_layout.addWidget(points_value)
        layout.addLayout(points_layout)

        # Align card to left or right column
        if column == "right":
            layout.setContentsMargins(30, 5, 15, 5)  # slight inward padding for right column
        else:
            layout.setContentsMargins(15, 5, 30, 5)
    
    def showEvent(self, event):
        """Store original position when widget is first shown"""
        super().showEvent(event)
        if self._original_y is None:
            self._original_y = self.y()
    
    def enterEvent(self, event):
        """Handle mouse enter event - lift card up"""
        # Store original position if not already stored
        if self._original_y is None:
            self._original_y = self.y()
        
        geom = self.geometry()
        self.animation.stop()
        self.animation.setStartValue(geom)
        self.animation.setEndValue(QRect(geom.x(), self._original_y - 3, geom.width(), geom.height()))
        self.animation.start()
        self.shadow_anim.setStartValue(12)
        self.shadow_anim.setEndValue(18)
        self.shadow_anim.start()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave event - return card to original position"""
        # Ensure we have original position
        if self._original_y is None:
            self._original_y = self.y()
        
        geom = self.geometry()
        self.animation.stop()
        # Always return to the exact original Y position
        self.animation.setStartValue(geom)
        self.animation.setEndValue(QRect(geom.x(), self._original_y, geom.width(), geom.height()))
        self.animation.start()
        self.shadow_anim.setStartValue(18)
        self.shadow_anim.setEndValue(12)
        self.shadow_anim.start()
        super().leaveEvent(event)
