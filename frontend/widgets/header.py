from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGraphicsDropShadowEffect, QMenu, QListWidget, QListWidgetItem, QApplication
)
from PyQt6.QtGui import QPixmap, QFont, QIcon, QAction
from PyQt6.QtCore import Qt, QSize, QEvent
from PyQt6 import QtCore, QtWidgets
from views.Feedback.FeedbackPage import FeedbackBox  # Import FeedbackBox

# Custom notification popup with filtering
class NotificationPopup(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.Popup)
        self.setFixedWidth(320)
        self.setStyleSheet("""
            background-color: #ffffff; 
            border: 1px solid #d1d5db;
            border-radius: 8px;
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Filter buttons area
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(8, 8, 8, 8)
        filter_layout.setSpacing(8)
        
        self.all_btn = QPushButton("All")
        self.unread_btn = QPushButton("Unread")

        button_style = """
            QPushButton {
                background-color: #f3f4f6;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                color: #374151;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #e5e7eb; }
            QPushButton:checked {
                background-color: #e0f2fe;
                color: #0c4a6e;
            }
        """
        self.all_btn.setStyleSheet(button_style)
        self.unread_btn.setStyleSheet(button_style)

        for btn in [self.all_btn, self.unread_btn]:
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.all_btn.setChecked(True)

        filter_layout.addWidget(self.all_btn)
        filter_layout.addWidget(self.unread_btn)
        filter_layout.addStretch()

        # Notification list
        self.notification_list = QListWidget()
        self.notification_list.setStyleSheet("""
            QListWidget { border: none; }
            QListWidget::item { padding: 8px 15px; }
            QListWidget::item:selected { background: #f3f4f6; }
        """)

        main_layout.addWidget(filter_widget)
        main_layout.addWidget(QFrame(frameShape=QFrame.Shape.HLine, styleSheet="color:#e5e7eb;"))
        main_layout.addWidget(self.notification_list)

        # Placeholder data
        self.notifications = [
            {"text": "New message from Admin", "read": False},
            {"text": "Schedule updated", "read": True},
            {"text": "Event starts tomorrow!", "read": False},
            {"text": "Your profile was updated.", "read": True},
        ]

        # Connect signals
        self.all_btn.clicked.connect(lambda: self.filter_notifications("all"))
        self.unread_btn.clicked.connect(lambda: self.filter_notifications("unread"))

        self.filter_notifications("all")

    def filter_notifications(self, category):
        self.all_btn.setChecked(category == "all")
        self.unread_btn.setChecked(category == "unread")

        self.notification_list.clear()
        
        if category == "all":
            filtered = self.notifications
        elif category == "unread":
            filtered = [n for n in self.notifications if not n["read"]]
        else:
            filtered = []

        for notif in filtered:
            item = QListWidgetItem(notif["text"])
            if not notif["read"]:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            self.notification_list.addItem(item)


# Custom mail popup with filtering
class MailPopup(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.Popup)
        self.setFixedWidth(320)
        self.setStyleSheet("""
            background-color: #ffffff; 
            border: 1px solid #d1d5db;
            border-radius: 8px;
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Filter buttons area
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(8, 8, 8, 8)
        filter_layout.setSpacing(8)
        
        self.all_btn = QPushButton("All")
        self.unread_btn = QPushButton("Unread")
        self.groups_btn = QPushButton("Groups")

        button_style = """
            QPushButton {
                background-color: #f3f4f6;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                color: #374151;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #e5e7eb; }
            QPushButton:checked {
                background-color: #e0f2fe;
                color: #0c4a6e;
            }
        """
        self.all_btn.setStyleSheet(button_style)
        self.unread_btn.setStyleSheet(button_style)
        self.groups_btn.setStyleSheet(button_style)

        for btn in [self.all_btn, self.unread_btn, self.groups_btn]:
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.all_btn.setChecked(True)

        filter_layout.addWidget(self.all_btn)
        filter_layout.addWidget(self.unread_btn)
        filter_layout.addWidget(self.groups_btn)
        filter_layout.addStretch()

        # Message list
        self.message_list = QListWidget()
        self.message_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.message_list.setStyleSheet("""
            QListWidget { border: none; }
            QListWidget::item { padding: 8px 15px; }
            QListWidget::item:selected { background: #f3f4f6; }
        """)

        main_layout.addWidget(filter_widget)
        main_layout.addWidget(QFrame(frameShape=QFrame.Shape.HLine, styleSheet="color:#e5e7eb;"))
        main_layout.addWidget(self.message_list)

        # Placeholder data
        self.messages = [
            {"text": "Welcome to CISC Hub!", "type": "all", "read": True},
            {"text": "Assignment due tomorrow", "type": "all", "read": False},
            {"text": "Meeting at 3 PM", "type": "all", "read": True},
            {"text": "[Group Chat] Project Update", "type": "groups", "read": True},
            {"text": "Re: Your inquiry", "type": "all", "read": False},
            {"text": "[Group Chat] Lunch plans", "type": "groups", "read": False},
        ]

        # Connect signals
        self.all_btn.clicked.connect(lambda: self.filter_messages("all"))
        self.unread_btn.clicked.connect(lambda: self.filter_messages("unread"))
        self.groups_btn.clicked.connect(lambda: self.filter_messages("groups"))

        self.filter_messages("all")

    def filter_messages(self, category):
        self.all_btn.setChecked(category == "all")
        self.unread_btn.setChecked(category == "unread")
        self.groups_btn.setChecked(category == "groups")

        self.message_list.clear()
        
        if category == "all":
            filtered = self.messages
        elif category == "unread":
            filtered = [m for m in self.messages if not m["read"]]
        elif category == "groups":
            filtered = [m for m in self.messages if m["type"] == "groups"]
        else:
            filtered = []

        for msg in filtered:
            item = QListWidgetItem(msg["text"])
            if not msg["read"]:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            self.message_list.addItem(item)


class Header(QWidget):
    profileRequested = QtCore.pyqtSignal()
    logoutRequested  = QtCore.pyqtSignal()
    def __init__(self, parent=None, session: dict | None = None, user: dict | None = None):
        super().__init__(parent)
        self.session = session or {}
        self.user    = user or {}
        self.setFixedHeight(100)
        self.setObjectName("HeaderRoot")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.setStyleSheet("""
            QWidget#HeaderRoot { 
                background-color: #FFFFFF; 
                border-bottom-left-radius: 12px; 
                border-bottom-right-radius: 12px; 
            }
            QLabel { background: transparent; }
            QPushButton { background: transparent; border:none; }
            QPushButton#DropdownArrow:hover { color:#1f2937; }
        """)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 0)
        shadow.setColor(Qt.GlobalColor.lightGray)
        self.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Image paths (mimicking LoginWidget)
        BASE_DIR = Path(__file__).resolve().parents[2]  # projectname/
        ASSETS_DIR = BASE_DIR / "frontend" /"assets" / "images"    # projectname/frontend/assets/images/

        # Debug paths
        print(f"Current working directory: {Path.cwd()}")
        print(f"Script directory: {Path(__file__).resolve().parent}")
        print(f"Assets directory: {ASSETS_DIR}")

        # Image filenames (adjust if needed based on actual files)
        cisc_path = ASSETS_DIR / "cisc.png"
        mail_path = ASSETS_DIR / "mail.png"
        bell_path = ASSETS_DIR / "bell.png"
        cmu_path = ASSETS_DIR / "cmu.png"
        new_button_path = ASSETS_DIR / "new_icon.png"  # Placeholder for new button icon

        # Debug image existence
        for path in [cisc_path, mail_path, bell_path, cmu_path, new_button_path]:
            print(f"Checking image: {path}, Exists: {path.exists()}")

        # --- Logo + Title ---
        logo = QLabel()
        if cisc_path.exists():
            pixmap = QPixmap(str(cisc_path))
            if pixmap.isNull():
                print(f"Error: Failed to load {cisc_path} (possibly corrupt or not a valid image)")
                logo.setText("CISC Logo Error")
                logo.setStyleSheet("color: red; font-size: 12px;")
            else:
                logo.setPixmap(pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation))
        else:
            print(f"Error: {cisc_path} not found")
            logo.setText("CISC Logo Missing")
            logo.setStyleSheet("color: red; font-size: 12px;")

        title_box = QVBoxLayout()
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.setSpacing(-2)
        t1 = QLabel("College of Information Sciences & Computing")
        t1.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        t1.setStyleSheet("color:#1f2937;")
        t2 = QLabel("Virtual Hub System")
        t2.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        t2.setStyleSheet("color:#1f2937;")
        title_box.addWidget(t1)
        title_box.addWidget(t2)

        title_widget = QWidget()
        title_widget.setLayout(title_box)

        layout.addWidget(logo)
        layout.addWidget(title_widget)
        layout.addStretch(1)

        # Separator
        def vline():
            line = QFrame()
            line.setFrameShape(QFrame.Shape.VLine)
            line.setStyleSheet("color:#e5e7eb;")
            return line

        layout.addWidget(vline())

        # --- Icons ---
        self.new_button = self._icon_button(new_button_path)  # New button
        self.mail_button = self._icon_button(mail_path)
        self.bell_button = self._icon_button(bell_path)
        layout.addWidget(self.new_button)  # Add new button before mail button
        layout.addWidget(self.mail_button)
        layout.addWidget(self.bell_button)
        layout.addWidget(vline())

        # --- User profile ---
        profile = self._build_profile()
        layout.addWidget(profile)

        # Build menus
        self._build_profile_menu()
        self._build_notification_menu()
        self._build_mail_menu()

        # Connect buttons
        self.dropdown_button.clicked.connect(self.show_profile_menu)
        self.bell_button.clicked.connect(self.show_notifications)
        self.mail_button.clicked.connect(self.show_mail)
        self.new_button.clicked.connect(self.show_new_menu)  # Connect new button

        # Install global event filter for auto-close dropdowns anywhere
        app = QApplication.instance()
        if app:
            app.installEventFilter(self)

        self.set_user(session=self.session, user=self.user)

    def _build_profile(self):
        profile_widget = QWidget()
        layout = QHBoxLayout(profile_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # avatar
        self.avatar_lbl = QLabel()
        self.avatar_lbl.setFixedSize(36, 36)
        self.avatar_lbl.setStyleSheet("border-radius:18px;")
        self._set_default_avatar()

        # name + role
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(0)

        self.name_lbl = QLabel("—")
        self.name_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.name_lbl.setStyleSheet("color:#111827;")

        self.role_lbl = QLabel("—")
        self.role_lbl.setFont(QFont("Segoe UI", 8))
        self.role_lbl.setStyleSheet("color:#6b7280;")

        info_layout.addWidget(self.name_lbl)
        info_layout.addWidget(self.role_lbl)

        # dropdown
        self.dropdown_button = QPushButton("▼")
        self.dropdown_button.setObjectName("DropdownArrow")
        self.dropdown_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.dropdown_button.setFixedSize(28, 28)

        layout.addWidget(self.avatar_lbl)
        layout.addWidget(info_widget)
        layout.addWidget(self.dropdown_button)
        return profile_widget

    
    def set_user(self, session: dict | None = None, user: dict | None = None):
        if session is not None:
            self.session = session
        if user is not None:
            self.user = user
        self._apply_user_to_ui()

    def _apply_user_to_ui(self):
        s = self.session or {}
        data = (s.get("user") or self.user or {})
        # fall back to top-level session fields if needed
        if not data:
            data = {
                "full_name": s.get("full_name"),
                "username":  s.get("username"),
                "primary_role": s.get("primary_role"),
                "profile_picture": s.get("profile_picture"),
            }

        name = (data.get("full_name") or data.get("username") or "User").strip() or "User"
        role = (data.get("primary_role") or "—").title()
        self.name_lbl.setText(name)
        self.role_lbl.setText(role)

        url = data.get("profile_picture")
        if url:
            # make relative URLs work too
            if not url.startswith(("http://","https://")):
                base = (s.get("api_base") or "http://127.0.0.1:8000").rstrip("/")
                url = f"{base}{url if url.startswith('/') else f'/Uploads/{url}'}"
            self._set_avatar_from_url(url)
        else:
            self._set_default_avatar()

    def _set_default_avatar(self):
        cmu_path = Path(__file__).resolve().parents[2] / "frontend" / "assets" / "images" / "cmu.png"
        pix = QPixmap(str(cmu_path)) if cmu_path.exists() else QPixmap()
        self._set_avatar_pixmap(pix)

    def _set_avatar_from_url(self, url: str):
        try:
            import requests, time
            # tiny cache-bust
            sep = "&" if "?" in url else "?"
            r = requests.get(f"{url}{sep}v={int(time.time())}", timeout=6)
            r.raise_for_status()
            pix = QPixmap(); pix.loadFromData(r.content)
            self._set_avatar_pixmap(pix)
        except Exception:
            self._set_default_avatar()

    def _set_avatar_pixmap(self, pix: QPixmap):
        if pix and not pix.isNull():
            pix = pix.scaled(
                36, 36,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.avatar_lbl.setPixmap(pix)


    # Icon button utility
    def _icon_button(self, path):
        btn = QPushButton()
        if path.exists():
            icon = QIcon(str(path))
            if icon.isNull():
                print(f"Error: Failed to load {path} (possibly corrupt or not a valid image)")
                btn.setText("X")
                btn.setStyleSheet("color: red; font-size: 12px;")
            else:
                btn.setIcon(icon)
        else:
            print(f"Error: {path} not found")
            btn.setText("X")
            btn.setStyleSheet("color: red; font-size: 12px;")
        btn.setIconSize(QSize(18, 18))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedSize(36, 36)
        btn.setStyleSheet("""
            QPushButton { background:#f3f4f6; border:none; border-radius:18px; }
            QPushButton:hover { background:#e5e7eb; }
        """)
        return btn

    # User profile widget
    # def _build_profile(self):
    #     profile_widget = QWidget()
    #     layout = QHBoxLayout(profile_widget)
    #     layout.setContentsMargins(0, 0, 0, 0)
    #     layout.setSpacing(10)
    #     layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

    #     avatar = QLabel()
    #     cmu_path = Path(__file__).resolve().parents[2] /"frontend" / "assets" / "images" / "cmu.png"
    #     if cmu_path.exists():
    #         pixmap = QPixmap(str(cmu_path))
    #         if pixmap.isNull():
    #             print(f"Error: Failed to load {cmu_path} (possibly corrupt or not a valid image)")
    #             avatar.setText("CMU Logo Error")
    #             avatar.setStyleSheet("color: red; font-size: 12px;")
    #         else:
    #             avatar.setPixmap(pixmap.scaled(36, 36,
    #                                         Qt.AspectRatioMode.KeepAspectRatioByExpanding,
    #                                         Qt.TransformationMode.SmoothTransformation))
    #     else:
    #         print(f"Error: {cmu_path} not found")
    #         avatar.setText("CMU Logo Missing")
    #         avatar.setStyleSheet("color: red; font-size: 12px;")
    #     avatar.setFixedSize(36, 36)
    #     avatar.setStyleSheet("border-radius:18px;")

    #     info_widget = QWidget()
    #     info_layout = QVBoxLayout(info_widget)
    #     info_layout.setContentsMargins(0, 0, 0, 0)
    #     info_layout.setSpacing(0)

    #     name = QLabel("CARLOS FIDEL CASTRO")
    #     name.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
    #     name.setStyleSheet("color:#111827;")
    #     role = QLabel("Student")
    #     role.setFont(QFont("Segoe UI", 8))
    #     role.setStyleSheet("color:#6b7280;")

    #     info_layout.addWidget(name)
    #     info_layout.addWidget(role)

    #     self.dropdown_button = QPushButton("▼")
    #     self.dropdown_button.setObjectName("DropdownArrow")
    #     self.dropdown_button.setCursor(Qt.CursorShape.PointingHandCursor)
    #     self.dropdown_button.setFixedSize(28, 28)

    #     layout.addWidget(avatar)
    #     layout.addWidget(info_widget)
    #     layout.addWidget(self.dropdown_button)
    #     return profile_widget

    def _build_profile_menu(self):
        self.profile_menu = QtWidgets.QMenu(self)
        self.profile_menu.setStyleSheet("""
            QMenu { background-color:#FFFFFF; border:1px solid #d1d5db; }
            QMenu::item { padding:10px 20px; color:#374151; }
            QMenu::item:selected { background-color:#f3f4f6; }
        """)
        act_profile = self.profile_menu.addAction("Profile")
        act_logout  = self.profile_menu.addAction("Logout")
        act_profile.triggered.connect(self.profileRequested.emit)
        act_logout.triggered.connect(self.logoutRequested.emit)

    # Notification menu
    def _build_notification_menu(self):
        self.notif_menu = NotificationPopup()

    # Mail menu
    def _build_mail_menu(self):
        self.mail_menu = MailPopup()

    # Show menus
    def show_profile_menu(self):
        pos = self.dropdown_button.mapToGlobal(self.dropdown_button.rect().bottomLeft())
        self.profile_menu.exec(pos)

    def show_notifications(self):
        pos = self.bell_button.mapToGlobal(self.bell_button.rect().bottomLeft())
        self.notif_menu.move(pos)
        self.notif_menu.show()
        self.notif_menu.raise_()

    def show_mail(self):
        pos = self.mail_button.mapToGlobal(self.mail_button.rect().bottomLeft())
        self.mail_menu.move(pos)
        self.mail_menu.show()
        self.mail_menu.raise_()

    def show_new_menu(self):
        print("Showing FeedbackBox")  # Debug
        self.feedback_popup = FeedbackBox()  # No parent to make it top-level
        self.feedback_popup.show()
        self.feedback_popup.center_on_screen()  # Use screen centering
        self.feedback_popup.raise_()  # Ensure it appears on top
        self.feedback_popup.activateWindow()  # Focus the popup

    # Auto-close dropdowns on any click anywhere
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            click_pos = event.globalPosition().toPoint()
            # Hide notifications if click is outside
            if self.notif_menu.isVisible() and not self.notif_menu.geometry().contains(click_pos):
                self.notif_menu.hide()
            # Hide mail if click is outside
            if self.mail_menu.isVisible() and not self.mail_menu.geometry().contains(click_pos):
                self.mail_menu.hide()
            # Hide profile menu if click is outside
            if self.profile_menu.isVisible() and not self.profile_menu.geometry().contains(click_pos):
                self.profile_menu.hide()
            # Hide feedback popup if click is outside
            if hasattr(self, 'feedback_popup') and self.feedback_popup.isVisible() and not self.feedback_popup.geometry().contains(click_pos):
                self.feedback_popup.close()
        return super().eventFilter(obj, event)