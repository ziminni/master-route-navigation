from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QDialog, QSizePolicy, QSpacerItem, QPushButton, QScrollArea,
    QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QPixmap, QIcon, QPainter, QColor
from PyQt6.QtCore import Qt, QSize, QEvent, QTimer
import os
import threading
import requests
import hashlib

from .HouseServices import HouseService


class RulesDialog(QDialog):
    """Dialog to display house rules."""
    def __init__(self, assets_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("House Rules")
        self.setFixedSize(500, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a2e;
                border-radius: 10px;
            }
            QLabel {
                color: white;
                font-family: 'Inter', sans-serif;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("House Rules")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #4CAF50;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        rules_text = QLabel("""
1. Respect all house members and their opinions.

2. Participate actively in house events and activities.

3. Maintain good academic standing.

4. Support fellow house members in their endeavors.

5. Represent the house with pride and integrity.

6. Attend house meetings regularly.

7. Contribute positively to the house community.
        """)
        rules_text.setWordWrap(True)
        rules_text.setStyleSheet("font-size: 14px; line-height: 1.6;")
        layout.addWidget(rules_text)
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 30px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)


class OverviewPage(QWidget):
    def __init__(self, username, roles, primary_role, token, house_name="House of Java"):
        super().__init__()
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        self.house_name = house_name

        # HouseService instance (re-usable)
        self.house_service = HouseService()

        # Store backend data
        self.house_data = None
        self.members_data = []
        self.events_data = []

        # Path for assets (base_dir resolves to the 'frontend' folder)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.assets_path = os.path.join(base_dir, "assets", "images") + os.sep
        self.avatars_path = os.path.join(self.assets_path, "avatars") + os.sep

        # Build the UI on construction so the page is visible when navigated to
        self.init_ui()

        # Fetch data in background
        threading.Thread(target=self._fetch_all_data, daemon=True).start()

    def show_rules_dialog(self, event):
        self.rules_dialog = RulesDialog(self.assets_path)
        self.rules_dialog.exec()

    def _set_logo_image(self, image_bytes: bytes):
        """Set logo image from bytes data (adapted from HouseCard.set_image)"""
        try:
            if not hasattr(self, 'logo_label'):
                return
                
            pix = QPixmap()
            if pix.loadFromData(image_bytes):
                # Scale to appropriate size for the logo area
                # Change this value to make logo bigger/smaller (e.g., 180, 220, 250, 300)
                logo_size = 350
                pix = pix.scaled(logo_size, logo_size, Qt.AspectRatioMode.KeepAspectRatio, 
                               Qt.TransformationMode.SmoothTransformation)
                self.logo_label.setPixmap(pix)
                self.logo_label.setText("")  # Clear the placeholder text
                print(f"[OverviewPage] Logo loaded successfully, size: {pix.width()}x{pix.height()}")
        except Exception as e:
            print(f"[ERROR] Failed to set logo image: {e}")

    def _fetch_all_data(self):
        """Background thread: fetch all data from backend."""
        try:
            self._fetch_house_data()
            if self.house_data and self.house_data.get("id"):
                house_id = self.house_data["id"]
                self._fetch_members(house_id)
                self._fetch_events(house_id)

                # Load logo if available - USE THE HOUSE SERVICE'S load_image_async
                logo_field = self.house_data.get("logo") or self.house_data.get("banner") or ""
                if logo_field:
                    print(f"[OverviewPage] Found logo field: {logo_field}")
                    
                    # Create a simple adapter object that has a set_image method
                    class LogoAdapter:
                        def __init__(self, page):
                            self.page = page
                        
                        def set_image(self, image_bytes: bytes):
                            # Call the page's _set_logo_image method
                            self.page._set_logo_image(image_bytes)
                    
                    # Create adapter and use the service's load_image_async
                    adapter = LogoAdapter(self)
                    self.house_service.load_image_async(logo_field, adapter)

        except Exception as e:
            print(f"[ERROR] Failed to fetch all data: {e}")
        finally:
            # Ensure UI is refreshed even if some fetches failed or house not found
            try:
                self._update_ui_from_data()
            except Exception as e:
                print(f"[ERROR] Failed to update UI after fetch attempts: {e}")

    def _fetch_house_data(self):
        """Fetch house object by matching name/slug."""
        try:
            url = "http://127.0.0.1:8000/api/house/houses/"
            headers = {}
            if getattr(self, "token", None):
                headers["Authorization"] = f"Bearer {self.token}"
            r = requests.get(url, headers=headers, timeout=6)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict) and "results" in data:
                    items = data["results"]
                else:
                    items = data
                for h in items:
                    if str(h.get("name", "")).lower() == str(self.house_name).lower() or \
                       str(h.get("slug", "")).lower() == str(self.house_name).lower():
                        self.house_data = h
                        print(f"[DEBUG] Found house data: {h.get('name')} (id={h.get('id')})")
                        return
        except Exception as e:
            print(f"[ERROR] Failed to fetch house data: {e}")

    def _fetch_members(self, house_id):
        """Fetch house members."""
        try:
            url = f"http://127.0.0.1:8000/api/house/memberships/?house={house_id}"
            headers = {}
            if getattr(self, "token", None):
                headers["Authorization"] = f"Bearer {self.token}"
            r = requests.get(url, headers=headers, timeout=6)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict) and "results" in data:
                    self.members_data = data["results"]
                else:
                    self.members_data = data
                print(f"[DEBUG] Fetched {len(self.members_data)} members")
        except Exception as e:
            print(f"[ERROR] Failed to fetch members: {e}")

    def _fetch_events(self, house_id):
        """Fetch house events."""
        try:
            url = f"http://127.0.0.1:8000/api/house/events/?house={house_id}"
            headers = {}
            if getattr(self, "token", None):
                headers["Authorization"] = f"Bearer {self.token}"
            r = requests.get(url, headers=headers, timeout=6)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict) and "results" in data:
                    self.events_data = data["results"]
                else:
                    self.events_data = data
                # compute awards count (events marked as competitions)
                try:
                    self._awards_count = len([e for e in self.events_data if e.get("is_competition")])
                except Exception:
                    self._awards_count = 0
                print(f"[DEBUG] Fetched {len(self.events_data)} events (awards={self._awards_count})")
        except Exception as e:
            print(f"[ERROR] Failed to fetch events: {e}")

    def _update_ui_from_data(self):
        """Update UI labels with real data from backend."""
        try:
            # Debug: Print what data we have
            print(f"[OverviewPage] Updating UI with house_data: {self.house_data}")
            print(f"[OverviewPage] Members count: {len(self.members_data) if self.members_data else 0}")
            
            # Update member count
            if hasattr(self, "count_label_members") and self.count_label_members:
                member_count = len(self.members_data) if self.members_data else (self.house_data.get("members_count", 0) if self.house_data else 0)
                print(f"[OverviewPage] Setting members count to: {member_count}")
                QTimer.singleShot(0, lambda mc=member_count: self.count_label_members.setText(str(mc)))

            # Update event count
            if hasattr(self, "count_label_events") and self.count_label_events:
                event_count = len(self.events_data) if self.events_data else 0
                QTimer.singleShot(0, lambda ec=event_count: self.count_label_events.setText(str(ec)))
            
            # Update awards count (derived from events marked as competition)
            if hasattr(self, "count_label_awards") and self.count_label_awards:
                awards = getattr(self, "_awards_count", 0) or 0
                QTimer.singleShot(0, lambda a=awards: self.count_label_awards.setText(str(a)))

            # Update member online text
            if hasattr(self, "members_text") and self.members_text:
                members_online = len([m for m in self.members_data if m.get("is_active")]) if self.members_data else 0
                QTimer.singleShot(0, lambda mo=members_online: self.members_text.setText(f"Members online: {mo}"))

            # Update points breakdown
            if self.house_data:
                points_total = self.house_data.get("points_total", 0)
                behavioral = self.house_data.get("behavioral_points", 0)
                competitive = self.house_data.get("competitive_points", 0)
                print(f"[OverviewPage] Points - Total: {points_total}, Behavioral: {behavioral}, Competitive: {competitive}")
                if hasattr(self, "points_labels") and self.points_labels:
                    QTimer.singleShot(0, lambda pt=points_total: self._update_points_display(pt))

            # Update top members avatars
            if self.members_data and hasattr(self, "top_member_labels") and self.top_member_labels:
                QTimer.singleShot(0, self._update_top_members)

        except Exception as e:
            print(f"[ERROR] Failed to update UI: {e}")
            import traceback
            traceback.print_exc()

    def _update_points_display(self, total_points):
        """Update the points breakdown display."""
        try:
            if not hasattr(self, "points_labels") or not self.points_labels:
                return
            # Prefer explicit fields from backend if present
            behavioral = 0
            competitive = 0
            if self.house_data:
                behavioral = int(self.house_data.get("behavioral_points", 0) or 0)
                competitive = int(self.house_data.get("competitive_points", 0) or 0)
            # If backend provided behavioral/competitive use them; otherwise distribute evenly
            if behavioral == 0 and competitive == 0:
                behavioral = total_points // 4
                competitive = total_points // 4
                year = total_points // 4
            else:
                year = max(0, total_points - behavioral - competitive)
            accumulated = total_points

            values = [behavioral, competitive, year, accumulated]
            for i, label in enumerate(self.points_labels):
                if i < len(values):
                    label.setText(f"<div align='center'><b>{values[i]:,}</b><br><i>{['Behavioral', 'Competitive', 'Year Points', 'Total Accumulated'][i]}</i></div>")
        except Exception as e:
            print(f"[ERROR] Failed to update points: {e}")

    def _update_top_members(self):
        """Update top members avatars and names."""
        try:
            if not self.members_data or not hasattr(self, "top_member_labels"):
                return
            # Sort by points (descending) and take top 3
            sorted_members = sorted(self.members_data, key=lambda m: m.get("points", 0), reverse=True)[:3]

            for i, label in enumerate(self.top_member_labels):
                if i < len(sorted_members):
                    member = sorted_members[i]
                    # Try to load avatar from backend or use placeholder
                    avatar_file = member.get("avatar") or "man1.png"
                    if avatar_file and not avatar_file.startswith("/") and not avatar_file.startswith("http"):
                        avatar_path = self.avatars_path + avatar_file
                    else:
                        avatar_path = avatar_file if avatar_file else self.avatars_path + "man1.png"

                    pix = QPixmap(avatar_path)
                    if pix.isNull() or len(sorted_members) == 0:
                        # Generate color-based placeholder
                        pix = self._generate_avatar_placeholder(member.get("user_display", "?"))

                    label.setPixmap(pix.scaled(72, 72, Qt.AspectRatioMode.KeepAspectRatio,
                                                Qt.TransformationMode.SmoothTransformation))
        except Exception as e:
            print(f"[ERROR] Failed to update top members: {e}")

    def _generate_avatar_placeholder(self, name):
        """Generate a colored placeholder avatar based on name."""
        pix = QPixmap(72, 72)
        # Generate color from name hash
        color_hash = hashlib.md5(name.encode()).hexdigest()
        r = int(color_hash[0:2], 16)
        g = int(color_hash[2:4], 16)
        b = int(color_hash[4:6], 16)
        pix.fill(Qt.GlobalColor.white)
        # For now just fill with white; could add letter in center
        return pix

    def init_ui(self):
        def _set_scaled_pixmap(label, pixmap, base_size, scale=1.0):
            """Helper to consistently scale icons for hover animations."""
            if pixmap.isNull():
                return
            width = max(1, int(base_size[0] * scale))
            height = max(1, int(base_size[1] * scale))
            label.setPixmap(
                pixmap.scaled(
                    width,
                    height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        def _add_hover_scale(label, pixmap, base_size, hover_scale=1.15):
            """Attach hover enter/leave scaling behavior to a QLabel icon."""
            if pixmap.isNull():
                return

            _set_scaled_pixmap(label, pixmap, base_size, 1.0)

            def enter_event(event):
                _set_scaled_pixmap(label, pixmap, base_size, hover_scale)

            def leave_event(event):
                _set_scaled_pixmap(label, pixmap, base_size, 1.0)

            label.enterEvent = enter_event
            label.leaveEvent = leave_event

        # === MAIN LAYOUT (HORIZONTAL SECTIONS) ===
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 5, 30, 5)
        main_layout.setSpacing(10)

        # ----------------------------------------------------------
        # LEFT SECTION: HOUSE NAME + LOGO + ICON STATS
        # ----------------------------------------------------------
        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        left_layout.setContentsMargins(0, -10, 0, 80)

        # Title
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

        # Add subtle shadow to title
        title_shadow = QGraphicsDropShadowEffect()
        title_shadow.setBlurRadius(5)
        title_shadow.setXOffset(2)
        title_shadow.setYOffset(2)
        title_shadow.setColor(Qt.GlobalColor.darkGreen)
        title_label.setGraphicsEffect(title_shadow)

        left_layout.addWidget(title_label)

        # === LOGO (REPLACING BANNER) ===
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("background: transparent;")
        self.logo_label = logo_label  # Store reference for logo updates

        # Placeholder text (will be replaced when logo loads)
        logo_label.setText("[ Logo ]")

        # Drop shadow (same style as before)
        logo_shadow = QGraphicsDropShadowEffect()
        logo_shadow.setBlurRadius(15)
        logo_shadow.setXOffset(5)
        logo_shadow.setYOffset(5)
        logo_shadow.setColor(Qt.GlobalColor.black)
        logo_label.setGraphicsEffect(logo_shadow)

        left_layout.addWidget(logo_label)
        left_layout.addSpacing(5)

        # Stats Icons Row
        stats_layout = QHBoxLayout()

        stats = [
            ("members.png", "0", "Members"),
            ("events.png", "0", "Events"),
            ("awards.png", "0", "Awards"),
        ]

        # Store references to count labels for later updates
        self.count_label_members = None
        self.count_label_events = None
        self.count_label_awards = None

        for icon_name, count, label_text in stats:
            # Create container widget for shadow effect
            stat_container = QWidget()
            stat_container.setStyleSheet("background: transparent;")

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

            # Store references to specific count labels
            if label_text == "Members":
                self.count_label_members = count_label
            elif label_text == "Events":
                self.count_label_events = count_label
            elif label_text == "Awards":
                self.count_label_awards = count_label

            # Add text label below count
            text_label = QLabel(label_text)
            text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            text_label.setStyleSheet("""
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                color: #004C25;
                background: transparent;
                font-weight: 500;
            """)

            box = QVBoxLayout(stat_container)
            box.setContentsMargins(0, 0, 0, 0)
            box.setSpacing(2)
            box.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
            box.addWidget(count_label, alignment=Qt.AlignmentFlag.AlignCenter)
            box.addWidget(text_label, alignment=Qt.AlignmentFlag.AlignCenter)

            # Add shadow effect to stat container
            stat_shadow = QGraphicsDropShadowEffect()
            stat_shadow.setBlurRadius(8)
            stat_shadow.setXOffset(2)
            stat_shadow.setYOffset(2)
            stat_shadow.setColor(Qt.GlobalColor.black)
            stat_container.setGraphicsEffect(stat_shadow)

            stats_layout.addWidget(stat_container)

        left_layout.addLayout(stats_layout)
        
        # ----------------------------------------------------------
        # CENTER SECTION: TOP MEMBERS (at bottom)
        # ----------------------------------------------------------
        center_layout = QVBoxLayout()
        center_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        # Bottom margin (4th value) pushes content UP - adjust this value to move Top Members up/down
        # Increase = move up, Decrease = move down
        center_layout.setContentsMargins(0, 0, 0, 10)
        
        # Add spacer to push content to bottom
        center_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Top Members Title
        top_members_label = QLabel("Top Members")
        top_members_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_members_label.setStyleSheet("""
            font-family: 'Inter', sans-serif;
            font-size: 16px;
            font-weight: 600;
            color: #004C25;
            background: transparent;
            margin-bottom: 10px;
        """)
        center_layout.addWidget(top_members_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Avatars Row
        avatar_layout = QHBoxLayout()
        avatar_layout.setSpacing(20)
        avatar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Store avatar labels for updates
        self.top_member_labels = []

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

            # Add shadow effect to avatars
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(8)
            shadow.setXOffset(2)
            shadow.setYOffset(2)
            shadow.setColor(Qt.GlobalColor.black)
            avatar.setGraphicsEffect(shadow)

            # Store reference for later updates
            self.top_member_labels.append(avatar)
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


        right_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # === Right Icons (Members Online + Rules) ===
        right_icons_layout = QVBoxLayout()
        right_icons_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        right_icons_layout.setSpacing(25)
        right_icons_layout.setContentsMargins(0, 120, 0, 0)

        # --- Members Online (hover text) ---
        members_container = QWidget()
        members_container.setStyleSheet("background: transparent;")
        members_layout = QHBoxLayout(members_container)
        members_layout.setContentsMargins(0, 0, 0, 0)
        members_layout.setSpacing(2)

        # Use 0 as default so UI doesn't show misleading placeholder
        members_text = QLabel("Members online: 0")
        members_text.setVisible(False)
        members_text.setStyleSheet("font-family: 'Inter'; font-size: 15px; color: #004C25; background: transparent;")

        # Store reference for updates
        self.members_text = members_text

        members_icon = QLabel()
        members_icon.setStyleSheet("background: transparent;")
        members_pixmap = QPixmap(self.assets_path + "members_online.png")
        members_base_size = (35, 35)
        _set_scaled_pixmap(members_icon, members_pixmap, members_base_size)

        members_layout.addWidget(members_text)
        members_layout.addWidget(members_icon)

        # Hover toggle with animation
        def members_enter(event):
            members_text.setVisible(True)
            _set_scaled_pixmap(members_icon, members_pixmap, members_base_size, 1.15)

        def members_leave(event):
            members_text.setVisible(False)
            _set_scaled_pixmap(members_icon, members_pixmap, members_base_size, 1.0)

        members_container.enterEvent = members_enter
        members_container.leaveEvent = members_leave

        # --- Rules icon ---
        rules_icon = QLabel()
        rules_icon.setStyleSheet("background: transparent;")
        rules_pixmap = QPixmap(self.assets_path + "rules.png")
        rules_base_size = (35, 35)
        _add_hover_scale(rules_icon, rules_pixmap, rules_base_size, hover_scale=1.15)
        rules_icon.mousePressEvent = self.show_rules_dialog

        # Add both icons
        right_icons_layout.addWidget(members_container, alignment=Qt.AlignmentFlag.AlignRight)
        right_icons_layout.addWidget(rules_icon, alignment=Qt.AlignmentFlag.AlignRight)

        right_layout.addLayout(right_icons_layout)

        # House Points Summary Title
        points_title_label = QLabel("House Points Summary")
        points_title_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        points_title_label.setStyleSheet("""
            font-family: 'Inter', sans-serif;
            font-size: 16px;
            font-weight: 600;
            color: #004C25;
            background: transparent;
            margin-bottom: 8px;
        """)
        right_layout.addWidget(points_title_label, alignment=Qt.AlignmentFlag.AlignRight)

        # Points box (bottom)
        points_frame = QFrame()
        points_frame.setFixedWidth(300)
        points_frame.setStyleSheet("""
            QFrame {
                border: 2px solid #084924;
                border-radius: 10px;
                padding: 14px;
                background: #FFFFFF;
            }
            QLabel {
                border: none;
                color: #004C25;
                font-family: 'Inter', sans-serif;
                font-size: 14px;
                background: transparent;
            }
        """)

        # Add shadow effect to points frame
        points_shadow = QGraphicsDropShadowEffect()
        points_shadow.setBlurRadius(12)
        points_shadow.setXOffset(4)
        points_shadow.setYOffset(4)
        points_shadow.setColor(Qt.GlobalColor.black)
        points_frame.setGraphicsEffect(points_shadow)

        # Layout
        layout = QVBoxLayout()
        layout.setSpacing(6)

        # Store points labels for updates
        self.points_labels = []

        # Top row
        top_row = QHBoxLayout()
        label1 = QLabel("<div align='center'><b>0</b><br><i>Behavioral</i></div>")
        label2 = QLabel("<div align='center'><b>0</b><br><i>Competitive</i></div>")
        self.points_labels.extend([label1, label2])
        top_row.addWidget(label1)
        top_row.addWidget(label2)
        layout.addLayout(top_row)

        # Divider line
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background-color: #084924; height: 1px;")
        layout.addWidget(divider)

        # Bottom row
        bottom_row = QHBoxLayout()
        label3 = QLabel("<div align='center'><b>0</b><br><i>Year Points</i></div>")
        label4 = QLabel("<div align='center'><b>0</b><br><i>Total Accumulated</i></div>")
        self.points_labels.extend([label3, label4])
        bottom_row.addWidget(label3)
        bottom_row.addWidget(label4)
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