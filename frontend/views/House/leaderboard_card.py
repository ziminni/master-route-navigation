from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QFrame, QSpacerItem, QSizePolicy
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt
import os


class LowerLeaderboardCard(QFrame):
    def __init__(self, rank, name, house, points, avatar="avatar1.png", column="left"):
        """
        column: "left" or "right" — for slight alignment adjustment
        """
        super().__init__()

        # === CARD CONTAINER ===
        self.setFixedHeight(40)
        self.setFixedWidth(370)
        self.setStyleSheet("""
            QFrame {
                background-color: #D9D9D9;
                border-radius: 6px;
            }
        """)

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
        avatar_path = os.path.join("frontend", "assets", "images", "avatars", avatar)
        if not os.path.exists(avatar_path):
            avatar_path = os.path.join("frontend", "assets", "images", "avatars", "man1.png")

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
