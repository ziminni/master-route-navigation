from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QDialog, QSizePolicy, QSpacerItem, QPushButton, QScrollArea,
)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt, QSize, QEvent
import os

class OverviewPage(QWidget):
    def __init__(self, username, roles, primary_role, token, house_name="House of Java"):
        super().__init__()
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        self.house_name = house_name

        # Path for assets (base_dir resolves to the 'frontend' folder)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.assets_path = os.path.join(base_dir, "assets", "images") + os.sep
        self.avatars_path = os.path.join(self.assets_path, "avatars") + os.sep
        
        # Build the UI on construction so the page is visible when navigated to
        self.init_ui()
        
    def show_rules_dialog(self, event):
        self.rules_dialog = RulesDialog(self.assets_path)
        self.rules_dialog.exec()
        
    def show_announcements_dialog(self, event):
        self.announcements_dialog = AnnouncementsDialog(self.assets_path)
        self.announcements_dialog.exec()


    def init_ui(self):
        # === MAIN LAYOUT (HORIZONTAL SECTIONS) ===
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 5, 30, 50)
        main_layout.setSpacing(10)

        # ----------------------------------------------------------
        # LEFT SECTION: HOUSE NAME + BANNER + ICON STATS
        # ----------------------------------------------------------
        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        left_layout.setContentsMargins(0, -10, 0, 80)


        #Title
        title_label = QLabel(self.house_name.upper())
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            font-family: 'Poppins', sans-serif;
            font-size: 30px;
            font-weight: 900;
            font-style: italic;
            color: #004C25;
            background: transparent;
        """)
        left_layout.addWidget(title_label)

        banner_label = QLabel()
        banner_label.setStyleSheet("background: transparent;")
        banner_pixmap = QPixmap(self.assets_path + "banner.png")
        if banner_pixmap.isNull():
            banner_label.setText("[ Banner ]")
            banner_label.setStyleSheet("""
                background-color: #e5e7eb;
                color: #6b7280;
                border-radius: 8px;
                padding: 100px 80px;
                font-size: 24px;
                font-family: 'Inter', sans-serif;
            """)
        else:
            banner_label.setPixmap(
                banner_pixmap.scaled(150, 430, Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation)
            )
        banner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(banner_label)
        left_layout.addSpacing(5)


        # Stats Icons Row
        stats_layout = QHBoxLayout()

        stats = [
            ("members.png", "257"),
            ("events.png", "20"),
            ("awards.png", "5"),
        ]

        for icon_name, count in stats:
            icon_label = QLabel()
            icon_label.setStyleSheet("background: transparent;")
            pixmap = QPixmap(self.assets_path + icon_name)
            if not pixmap.isNull():
                icon_label.setPixmap(pixmap.scaled(45, 45, Qt.AspectRatioMode.KeepAspectRatio,
                                                   Qt.TransformationMode.SmoothTransformation))
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            count_label = QLabel(count)
            count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            count_label.setStyleSheet("""
                font-family: 'Inter', sans-serif;
                font-size: 18px;
                color: #004C25;
                background: transparent;
                font-weight: 800;
            """)

            box = QVBoxLayout()
            box.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
            box.addWidget(count_label, alignment=Qt.AlignmentFlag.AlignCenter)
            stats_layout.addLayout(box)

        left_layout.addLayout(stats_layout)


        # ----------------------------------------------------------
        # CENTER SECTION: ARROW ON TOP + AVATARS AT BOTTOM
        # ----------------------------------------------------------
        center_layout = QVBoxLayout()
        center_layout.setContentsMargins(0, 0, 0, 0)

        # Arrow (top border)
        arrow_label = QLabel()
        arrow_label.setStyleSheet("background: transparent;")
        arrow_pixmap = QPixmap(self.assets_path + "expander_arrow.png")
        if arrow_pixmap.isNull():
            arrow_label.setText("▼")
            arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            arrow_label.setStyleSheet("""
                font-size: 28px;
                color: #004C25;
                font-family: 'Inter', sans-serif;
                background: transparent;
            """)
        else:
            arrow_label.setPixmap(arrow_pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio,
                                                      Qt.TransformationMode.SmoothTransformation))
        arrow_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        center_layout.addWidget(arrow_label, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        arrow_label.mousePressEvent = self.show_announcements_dialog

        #push avatars to bottom
        center_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Avatars Row
        avatar_layout = QHBoxLayout()
        avatar_layout.setSpacing(20)
        avatar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        avatar_files = ["man1.png", "woman1.png", "woman2.png"]
        for avatar_file in avatar_files:
            avatar = QLabel()
            avatar.setStyleSheet("background: transparent; border-radius: 50px;")
            avatar_pix = QPixmap(self.avatars_path + avatar_file)
            if not avatar_pix.isNull():
                avatar.setPixmap(
                    avatar_pix.scaled(72, 72, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)
                )
            avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
            avatar_layout.addWidget(avatar)

        center_layout.addLayout(avatar_layout)

        # Underline Bar
        underline = QFrame()
        underline.setFixedHeight(5)
        underline.setStyleSheet("background-color: #084924; border-radius: 2px;")
        underline.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        underline.setFixedWidth(260)
        center_layout.addWidget(underline)
    

        # ----------------------------------------------------------
        # RIGHT SECTION: TOP MESSAGE + BOTTOM POINTS BOX
        # ----------------------------------------------------------
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)

        congrats_label = QLabel("Congratulations on winning 1st place!")
        congrats_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        congrats_label.setStyleSheet("""
            border: 2px solid #004C25;
            border-radius: 6px;
            padding: 6px 12px;
            font-size: 14px;
            font-weight: 500;
            font-family: 'Inter', sans-serif;
            color: #004C25;
            background: transparent;
        """)
        right_layout.addWidget(congrats_label, alignment=Qt.AlignmentFlag.AlignRight)

        right_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        

                # === Right Icons (Members Online + Rules) ===
        right_icons_layout = QVBoxLayout()
        right_icons_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        right_icons_layout.setSpacing(25)
        right_icons_layout.setContentsMargins(0, 120, 0, 0)  # position matches your screenshot

        # --- Members Online (hover text) ---
        members_container = QWidget()
        members_container.setStyleSheet("background: transparent;")
        members_layout = QHBoxLayout(members_container)
        members_layout.setContentsMargins(0, 0, 0, 0)
        members_layout.setSpacing(6)

        members_text = QLabel("Members online: 99")
        members_text.setVisible(False)
        members_text.setStyleSheet("font-family: 'Inter'; font-size: 15px; color: #004C25; background: transparent;")

        members_icon = QLabel()
        members_icon.setPixmap(QPixmap(self.assets_path + "members_online.png").scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio))
        members_icon.setStyleSheet("background: transparent;")

        members_layout.addWidget(members_text)
        members_layout.addWidget(members_icon)

        # Hover toggle
        members_container.enterEvent = lambda e: members_text.setVisible(True)
        members_container.leaveEvent = lambda e: members_text.setVisible(False)

        # --- Rules icon ---
        rules_icon = QLabel()
        rules_icon.setPixmap(QPixmap(self.assets_path + "rules.png").scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio))
        rules_icon.setStyleSheet("background: transparent;")
        rules_icon.mousePressEvent = self.show_rules_dialog


        # Add both icons
        right_icons_layout.addWidget(members_container, alignment=Qt.AlignmentFlag.AlignRight)
        right_icons_layout.addWidget(rules_icon, alignment=Qt.AlignmentFlag.AlignRight)

        right_layout.addLayout(right_icons_layout)



        # Points box (bottom)
        points_frame = QFrame()
        points_frame.setFixedWidth(300)
        points_frame.setStyleSheet("""
            QFrame {
                border: 2px solid #084924;
                border-radius: 10px;
                padding: 14px;
                background: transparent;
            }
            QLabel {
                border: none;
                color: #004C25;
                font-family: 'Inter', sans-serif;
                font-size: 14px;
                background: transparent;
            }
        """)

        # Layout
        layout = QVBoxLayout()
        layout.setSpacing(6)

        # Top row
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("<div align='center'><b>3,500</b><br><i>Behavioral</i></div>"))
        top_row.addWidget(QLabel("<div align='center'><b>3,500</b><br><i>Competitive</i></div>"))
        layout.addLayout(top_row)

        # Divider line
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background-color: #084924; height: 1px;")
        layout.addWidget(divider)

        # Bottom row
        bottom_row = QHBoxLayout()
        bottom_row.addWidget(QLabel("<div align='center'><b>3,500</b><br><i>Year Points</i></div>"))
        bottom_row.addWidget(QLabel("<div align='center'><b>7,438</b><br><i>Total Accumulated</i></div>"))
        layout.addLayout(bottom_row)

        points_frame.setLayout(layout)

        right_layout.addWidget(points_frame, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)


        # ----------------------------------------------------------
        # COMBINE ALL SECTIONS
        # ----------------------------------------------------------
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(center_layout, 1)
        main_layout.addLayout(right_layout, 1)

        self.setLayout(main_layout)
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                font-family: 'Inter', sans-serif;
            }
        """)

class RulesDialog(QDialog):
    def __init__(self, assets_path):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setModal(True)
        self.resize(850, 600)

        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border: 2px solid #004C25;
                border-radius: 10px;
            }

            QLabel#titleLabel {
                font-size: 26px;
                font-style: italic;
                font-weight: 800;
                color: #004C25;
                font-family: 'Inter';
                padding-bottom: 4px;
                border: none;
            }

            QFrame#line {
                background-color: #004C25;
                height: 3px;
                border: none;
                border-radius: 2px;
            }

            QLabel#contentText {
                color: #004C25;
                background: transparent;
                font-family: 'Inter';
                font-size: 20px;
                line-height: 1.5em;
                border: none;
                padding: 10px;
            }

            QPushButton {
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                opacity: 0.7;
            }
        """)

        # === MAIN CONTAINER ===
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(15)

        # === TITLE ROW (Label + Close Button) ===
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel("RULES & REGULATIONS")
        title_label.setObjectName("titleLabel")

        close_button = QPushButton()
        close_button.setIcon(QIcon(assets_path + "xbutton.png"))
        close_button.setIconSize(QSize(35, 35))
        close_button.setFixedSize(40, 40)
        close_button.clicked.connect(self.close)

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(close_button)
        main_layout.addLayout(title_layout)

        # === UNDERLINE (green bar under title) ===
        underline = QFrame()
        underline.setObjectName("line")
        underline.setFixedHeight(8)
        underline.setFixedWidth(320)
        underline.setStyleSheet("background-color: #004C25; border-radius: 2px;")
        main_layout.addWidget(underline)

        # === SCROLLABLE CONTENT ===
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none; background: transparent;")

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # === Bordered box container ===
        rules_box = QFrame()
        rules_box.setStyleSheet("""
            QFrame {
                border: 2px solid #004C25;
                border-radius: 8px;
                background: transparent;
            }
        """)

        # Text inside the box
        rules_label = QLabel()
        rules_label.setObjectName("contentText")
        rules_label.setWordWrap(True)
        rules_label.setText(
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
            "Aenean commodo ligula eget dolor. Aenean massa. "
            "Cum sociis natoque penatibus et magnis dis parturient montes, "
            "nascetur ridiculus mus. Donec quam felis, ultricies nec, "
            "pellentesque eu, pretium quis, sem. Nulla consequat massa quis enim."
            "Donec pede justo, fringilla vel, aliquet nec, vulputate eget, arcu."
            "In enim justo, rhoncus ut, imperdiet a, venenatis vitae, justo. Nullam dictum felis eu pede mollis pretium."
            "Integer tincidunt. Cras dapibus. Vivamus elementum semper nisi. Aenean vulputate eleifend tellus."
            "Aenean leo ligula, porttitor eu, consequat vitae, eleifend ac, enim. Aliquam lorem ante, dapibus in, viverra quis, feugiat a, tellus."
            "Phasellus viverra nulla ut metus varius laoreet. Quisque rutrum. Aenean imperdiet. Etiam ultricies nisi vel augue."
            "Curabitur ullamcorper ultricies nisi. Nam eget dui. Etiam rhoncus."
        )
        rules_label.setStyleSheet("""
            QLabel#contentText {
                color: #004C25;
                background: transparent;
                font-family: 'Inter';
                font-size: 20px;
                line-height: 1.5em;
                padding: 10px;
                border: none;
            }
        """)

        box_layout = QVBoxLayout(rules_box)
        box_layout.setContentsMargins(10, 10, 10, 10)
        box_layout.addWidget(rules_label)

        content_layout.addWidget(rules_box)
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
class AnnouncementsDialog(QDialog):
    def __init__(self, assets_path):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setModal(True)
        self.resize(850, 600)

        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border: 2px solid #004C25;
                border-radius: 10px;
            }

            QLabel#titleLabel {
                font-size: 26px;
                font-style: italic;
                font-weight: 800;
                color: #004C25;
                font-family: 'Inter';
                padding-bottom: 4px;
                border: none;
            }

            QFrame#line {
                background-color: #004C25;
                height: 3px;
                border: none;
                border-radius: 2px;
            }

            QLabel#contentText {
                color: #004C25;
                background: transparent;
                font-family: 'Inter';
                font-size: 18px;
                line-height: 1.5em;
                padding: 10px;
                border: none;
            }

            QPushButton {
                background: transparent;
                border: none;
            }

            QPushButton:hover {
                opacity: 0.7;
            }
        """)

        # === MAIN CONTAINER ===
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(6)

        # === TITLE + CLOSE BUTTON ===
        title_layout = QHBoxLayout()
        title_label = QLabel("ANNOUNCEMENTS")
        title_label.setObjectName("titleLabel")
        main_layout.addSpacing(2)
        

        close_button = QPushButton()
        close_button.setIcon(QIcon(assets_path + "xbutton.png"))
        close_button.setIconSize(QSize(35, 35))
        close_button.setFixedSize(40, 40)
        close_button.clicked.connect(self.close)

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(close_button)
        main_layout.addLayout(title_layout)

        underline = QFrame()
        underline.setObjectName("line")
        underline.setFixedHeight(8)
        underline.setFixedWidth(250)
        underline.setStyleSheet("background-color: #004C25; border-radius: 2px;")
        main_layout.addSpacing(20)
        main_layout.addWidget(underline)

        major_title = QLabel("MAJOR ANNOUNCEMENT")
        major_title.setStyleSheet("""
            font-family: 'Inter';
            font-size: 18px;
            font-weight: 700;
            color: #004C25;
        """)
        major_title.setContentsMargins(0, 2, 0, 6)  # small top and bottom margin
        main_layout.addSpacing(20)
        main_layout.addWidget(major_title)

        # === SCROLL AREA ===
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QWidget {
                background: transparent;
            }
        """)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        # === Announcement Box 1 ===
        box1 = QFrame()
        box1.setStyleSheet("""
            QFrame {
                border: 2px solid #004C25;
                border-radius: 8px;
                background: transparent;
            }
        """)
        box1_layout = QVBoxLayout(box1)
        box1_layout.setContentsMargins(8, 8, 8, 8)
        text1 = QLabel("Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor."
                       "Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus."
                       "Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem. Nulla consequat massa quis enim.")
        text1.setObjectName("contentText")
        text1.setWordWrap(True)
        text1.setStyleSheet("border: none;")
        box1_layout.addWidget(text1)
        content_layout.addWidget(box1)

        # === Announcement Box 2 ===
        box2 = QFrame()
        box2.setStyleSheet("""
            QFrame {
                border: 2px solid #004C25;
                border-radius: 8px;
                background: transparent;
            }
        """)
        box2_layout = QVBoxLayout(box2)
        box2_layout.setContentsMargins(8, 8, 8, 8)
        text2 = QLabel("Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. Aenean massa."
                       "Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus."
                       "Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem. Nulla consequat massa quis enim."
                       "Donec pede justo, fringilla vel, aliquet nec, vulputate eget, arcu. In enim justo, rhoncus ut, imperdiet a, venenatis vitae, justo."
                       "Nullam dictum felis eu pede mollis pretium. Integer tincidunt. Cras dapibus. Vivamus elementum semper nisi. Aenean vulputate eleifend tellus."
                       "Aenean leo ligula, porttitor eu, consequat vitae, eleifend ac, enim. Aliquam lorem ante, dapibus in, viverra quis, feugiat a, tellus. Phasellus viverra nulla ut metus varius laoreet."
                       "Quisque rutrum. Aenean imperdiet. Etiam ultricies nisi vel augue. Curabitur ullamcorper ultricies nisi. Nam eget dui. Etiam rhoncus."
                       "Maecenas tempus, tellus eget condimentum rhoncus, sem quam semper libero, sit amet adipiscing sem neque sed ipsum. Nam quam nunc, blandit vel, luctus pulvinar, hendrerit id, lorem."
                       "Maecenas nec odio et ante tincidunt tempus. Donec vitae sapien ut libero venenatis faucibus. Nullam quis ante. Etiam sit amet orci eget eros faucibus tincidunt. Duis leo. Sed fringilla mauris sit amet nibh."
                       "Donec sodales sagittis magna. Sed consequat, leo eget bibendum sodales, augue velit cursus nunc,")
        text2.setObjectName("contentText")
        text2.setWordWrap(True)
        text2.setStyleSheet("border: none;")
        box2_layout.addWidget(text2)
        content_layout.addWidget(box2)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
