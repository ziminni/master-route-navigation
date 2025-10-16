import json
import os
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QGridLayout
)
from PyQt6.QtGui import QPixmap, QFont, QPalette, QBrush
from PyQt6.QtCore import Qt

from .leaderboard_card import LowerLeaderboardCard

class LeaderboardPage(QWidget):
    def __init__(self, username, roles, primary_role, token, house_name):
        super().__init__()
        self.setWindowTitle("Leaderboards")
        self.setup_ui()

    def setup_ui(self):
        # === PATHS ===
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        data_path = os.path.join(base_dir , "Mock", "leaderboards.json")
        bg_path = os.path.join(base_dir, "assets", "images" , "bg.png")
        avatars_path = os.path.join(base_dir, "assets", "images" , "avatars")

        # === LOAD DATA ===
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                leaderboard_data = json.load(f)
        except FileNotFoundError:
            print(f"Error: leaderboards.json not found at {data_path}. Using empty leaderboard.")
            leaderboard_data = []
        except Exception as e:
            print(f"Could not load leaderboard data: {e}")
            leaderboard_data = []

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

            # Inner layout for text content
            bar_layout = QVBoxLayout(bar_frame)
            bar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Name
            name_label = QLabel(data["name"])
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_label.setStyleSheet("color: white; font-weight: 600;")
            name_label.setFont(QFont("Poppins", 8, QFont.Weight.Bold))

            # Subtitle / House of...
            house_label = QLabel(f"@{data.get('username', 'Unknown')}")
            house_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            house_label.setStyleSheet("color: #d9f9e8; font-style: italic;")
            house_label.setFont(QFont("Poppins", 6))

            # Rank and Points section
            rank_label = QLabel(rank_text)
            rank_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            rank_label.setStyleSheet("color: white; font-weight: 500; font-style: italic;")
            rank_label.setFont(QFont("Poppins", 7))

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

            avatar_path = os.path.join("frontend", "assets", "images", "avatars", data["avatar"]) if data["avatar"] else ""
            if os.path.exists(avatar_path):
                pixmap = QPixmap(avatar_path).scaled(
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
        main_layout.addSpacing(10)  # Adjust this number for precise control

        # === LOWER LEADERBOARD (6–15) ===
        lower_frame = QFrame()
        lower_layout = QGridLayout(lower_frame)
        lower_layout.setSpacing(10)
        lower_layout.setContentsMargins(20, 20, 20, 20)

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