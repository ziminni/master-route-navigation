import json
import os
import requests
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QGridLayout
)
from PyQt6.QtGui import QPixmap, QFont, QPalette, QBrush, QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt

from .leaderboard_card import LowerLeaderboardCard

class LeaderboardPage(QWidget):
    def __init__(self, username, roles, primary_role, token, house_name, house_id=None, api_base="http://127.0.0.1:8000"):
        super().__init__()
        self.setWindowTitle("Leaderboards")
        self.token = token
        self.house_id = house_id
        self.api_base = api_base
        self.setup_ui()

    def load_leaderboard_from_api(self):
        """Load leaderboard data from backend API."""
        leaderboard_data = []
        try:
            headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
            # Fetch memberships for this house, sorted by points
            url = f"{self.api_base}/api/house/memberships/"
            if self.house_id:
                url += f"?house={self.house_id}"
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                memberships = response.json()
                if isinstance(memberships, dict) and "results" in memberships:
                    memberships = memberships["results"]
                
                # Sort by points descending
                memberships = sorted(memberships, key=lambda x: x.get("points", 0), reverse=True)
                
                # Transform to leaderboard format
                for idx, membership in enumerate(memberships, start=1):
                    user_display = membership.get("user_display", "Unknown")
                    # Try to extract username from user_display or use user ID
                    username = user_display.split("@")[0] if "@" in str(user_display) else str(membership.get("user", ""))
                    
                    leaderboard_data.append({
                        "rank": idx,
                        "name": user_display,
                        "username": username,
                        "score": membership.get("points", 0),
                        "avatar": membership.get("avatar", "man1.png") or "man1.png",
                    })
            else:
                print(f"Failed to load leaderboard: {response.status_code}")
        except Exception as e:
            print(f"Error loading leaderboard from API: {e}")
        
        return leaderboard_data

    def setup_ui(self):
        # === PATHS ===
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        bg_path = os.path.join(base_dir, "assets", "images" , "bg.png")
        avatars_path = os.path.join(base_dir, "assets", "images" , "avatars")

        # === LOAD DATA FROM API ===
        leaderboard_data = self.load_leaderboard_from_api()

        # Split data
        top5 = leaderboard_data[:5]
        bottom_ranks = leaderboard_data[5:]

        # === MAIN LAYOUT ===
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 2, 20, 2)
        main_layout.setSpacing(2)  # Adjust this number to control podium-to-lowerboard spacing

        # === PODIUM FRAME ===
        podium_frame = QFrame()
        podium_frame.setObjectName("podiumFrame")
        podium_frame.setFixedHeight(250)
        podium_frame.setFixedWidth(730)
        podium_frame.setStyleSheet("""
            QFrame#podiumFrame {
                border-radius: 15px;
                background-color: #084924;
            }
        """)

        # Background image inside podium frame
        if os.path.exists(bg_path):
            bg_url = bg_path.replace("\\", "/")
            podium_frame.setStyleSheet(f"""
                QFrame#podiumFrame {{
                    border-radius: 5px;
                    background-image: url("{bg_url}");
                    background-repeat: no-repeat;
                    background-position: center;
                    background-size: contain;
                }}
            """)
        else:
            podium_frame.setStyleSheet("""
                QFrame#podiumFrame {
                    border-radius: 5px;
                    background-color: #084924;
                }
            """)

        # PODIUM LAYOUT - BOTTOM ALIGNED
        podium_layout = QHBoxLayout(podium_frame)
        podium_layout.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        podium_layout.setSpacing(0)
        podium_layout.setContentsMargins(30, 0, 30, 0)

        # Safely retrieve podium ranks
        podium_order = []
        default_entry = {"name": "Unknown", "score": 0, "avatar": "", "rank": None}
        for rank in [4, 2, 1, 3, 5]:  # Order: 4th, 2nd, 1st, 3rd, 5th
            entry = next((d for d in top5 if d.get("rank") == rank), default_entry.copy())
            if entry["rank"] is None:
                entry["rank"] = rank
            podium_order.append(entry)

        height_by_rank = {1: 170, 2: 150, 3: 130, 4: 115, 5: 100}
        color_by_rank = {
            1: "#297762",
            2: "#51B69A",
            3: "#81CBB0",
            4: "#269E59",
            5: "#238C50"
        }

        for data in podium_order:
            rank_number = data["rank"]
            rank_text = {1: "1st", 2: "2nd", 3: "3rd"}.get(rank_number, f"{rank_number}th")

            # Vertical stack for avatar + bar
            container = QVBoxLayout()
            container.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
            container.setSpacing(0)
            container.setContentsMargins(0, 0, 0, 0)

            # Bar frame
            bar_height = height_by_rank[rank_number]
            bar_frame = QFrame()
            bar_frame.setFixedSize(20, bar_height)
            bar_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {color_by_rank[rank_number]};
                    border-top-left-radius: 8px;
                    border-top-right-radius: 8px;
                }}
            """)
            
            # Add shadow to bar frame (sides only)
            bar_shadow = QGraphicsDropShadowEffect()
            bar_shadow.setBlurRadius(40)
            bar_shadow.setXOffset(0)
            bar_shadow.setYOffset(0)
            bar_shadow.setColor(QColor(0, 0, 0, 60))
            bar_frame.setGraphicsEffect(bar_shadow)

            # Inner layout for text content
            bar_layout = QVBoxLayout(bar_frame)
            bar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Name
            name_label = QLabel(data["name"])
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_label.setStyleSheet("""
                color: white; 
                font-weight: 600;
                background-color: transparent;
            """)
            name_label.setFont(QFont("Poppins", 8, QFont.Weight.Bold))
            
            # Add subtle text shadow - small blur and offset to appear as text shadow, not box
            name_shadow = QGraphicsDropShadowEffect()
            name_shadow.setBlurRadius(4)
            name_shadow.setXOffset(1)
            name_shadow.setYOffset(1)
            name_shadow.setColor(QColor(0, 0, 0, 120))
            name_label.setGraphicsEffect(name_shadow)

            # Subtitle / House of...
            house_label = QLabel(f"@{data.get('username', 'Unknown')}")
            house_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            house_label.setStyleSheet("color: #d9f9e8; font-style: italic;")
            house_label.setFont(QFont("Poppins", 6))

            # Rank and Points section
            rank_label = QLabel(rank_text)
            rank_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            rank_label.setStyleSheet("""
                color: white; 
                font-weight: 500; 
                font-style: italic;
                background-color: transparent;
            """)
            rank_label.setFont(QFont("Poppins", 7))
            
            # Add subtle text shadow to rank label
            rank_shadow = QGraphicsDropShadowEffect()
            rank_shadow.setBlurRadius(4)
            rank_shadow.setXOffset(1)
            rank_shadow.setYOffset(1)
            rank_shadow.setColor(QColor(0, 0, 0, 120))
            rank_label.setGraphicsEffect(rank_shadow)

            points_label = QLabel(f"Points\n{data['score']}")
            points_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            points_label.setStyleSheet("color: white; font-weight: bold;")
            points_label.setFont(QFont("Poppins", 7, QFont.Weight.Bold))

            bar_layout.addWidget(name_label)
            bar_layout.addWidget(house_label)
            bar_layout.addStretch()
            bar_layout.addWidget(rank_label)
            bar_layout.addWidget(points_label)

            avatar_label = QLabel()
            avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            avatar_label.setFixedSize(60, 60)
            avatar_label.setStyleSheet("border-radius: 35px; background-color: transparent;")

            avatar_path = os.path.join(avatars_path, data["avatar"]) if data.get("avatar") else ""
            if avatar_path and os.path.exists(avatar_path):
                pixmap = QPixmap(avatar_path).scaled(
                    60, 60,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                avatar_label.setPixmap(pixmap)
            else:
                # Fallback to default avatar if not found
                default_avatar = os.path.join(avatars_path, "man1.png")
                if os.path.exists(default_avatar):
                    pixmap = QPixmap(default_avatar).scaled(
                        60, 60,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    avatar_label.setPixmap(pixmap)
                else:
                    print(f"Error: Avatar image not found at {avatar_path}")

            # Ensure the bar has same width as avatar
            bar_frame.setFixedWidth(80)

            # Create vertical layout for avatar + bar
            avatar_container = QVBoxLayout()
            avatar_container.setSpacing(10)
            avatar_container.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            avatar_container.addWidget(avatar_label, alignment=Qt.AlignmentFlag.AlignHCenter)
            avatar_container.addWidget(bar_frame, alignment=Qt.AlignmentFlag.AlignHCenter)
            
            # Add to parent container
            container.addLayout(avatar_container)
            podium_layout.addLayout(container)

        main_layout.addWidget(podium_frame, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        # Add specific spacing between podium and lower leaderboard
        main_layout.addSpacing(5)  # Reduced spacing for better fit when not full screen

        # === LOWER LEADERBOARD (6–15) ===
        lower_frame = QFrame()
        lower_layout = QGridLayout(lower_frame)
        lower_layout.setSpacing(8)  # Reduced spacing between cards
        lower_layout.setContentsMargins(20, 10, 20, 10)  # Reduced top/bottom margins

        row, col = 0, 0
        for data in bottom_ranks:
            card = LowerLeaderboardCard(
                f"{data['rank']}th", data["name"], f"@{data.get('username', 'Unknown')}", data["score"], data["avatar"]
            )
            lower_layout.addWidget(card, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1

        main_layout.addWidget(lower_frame, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.setLayout(main_layout)