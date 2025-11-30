from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QDialog, QSizePolicy, QSpacerItem, QPushButton, QScrollArea,
    QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt, QSize, QEvent, QTimer
import os
import threading
import requests
import hashlib

class OverviewPage(QWidget):
    def __init__(self, username, roles, primary_role, token, house_name="House of Java"):
        super().__init__()
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        self.house_name = house_name
        
        # Store backend data
        self.house_data = None
        self.members_data = []
        self.events_data = []
        self.announcements_data = []

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
        
    def show_announcements_dialog(self, event):
        self.announcements_dialog = AnnouncementsDialog(self.assets_path, self.announcements_data)
        self.announcements_dialog.exec()

    def _fetch_all_data(self):
        """Background thread: fetch all data from backend."""
        try:
            self._fetch_house_data()
            if self.house_data and self.house_data.get("id"):
                house_id = self.house_data["id"]
                self._fetch_members(house_id)
                self._fetch_events(house_id)
                self._fetch_announcements(house_id)
        except Exception as e:
            # keep a lightweight log so we can diagnose why UI stayed with placeholders
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

    def _fetch_announcements(self, house_id):
        """Fetch house announcements."""
        try:
            url = f"http://127.0.0.1:8000/api/house/announcements/?house={house_id}"
            headers = {}
            if getattr(self, "token", None):
                headers["Authorization"] = f"Bearer {self.token}"
            r = requests.get(url, headers=headers, timeout=6)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict) and "results" in data:
                    self.announcements_data = data["results"]
                else:
                    self.announcements_data = data
                print(f"[DEBUG] Fetched {len(self.announcements_data)} announcements")
        except Exception as e:
            print(f"[ERROR] Failed to fetch announcements: {e}")

    def _update_ui_from_data(self):
        """Update UI labels with real data from backend."""
        try:
            # Update member count
            if hasattr(self, "count_label_members"):
                member_count = len(self.members_data) if self.members_data else self.house_data.get("members_count", 0) if self.house_data else 0
                QTimer.singleShot(0, lambda: self.count_label_members.setText(str(member_count)))
            
            # Update event count
            if hasattr(self, "count_label_events"):
                event_count = len(self.events_data) if self.events_data else 0
                QTimer.singleShot(0, lambda: self.count_label_events.setText(str(event_count)))
            # Update awards count (derived from events marked as competition)
            if hasattr(self, "count_label_awards"):
                awards = getattr(self, "_awards_count", None)
                if awards is None:
                    # fallback: 0 if not computed
                    awards = 0
                QTimer.singleShot(0, lambda a=awards: self.count_label_awards.setText(str(a)))
            
            # Update member online text
            if hasattr(self, "members_text"):
                members_online = len([m for m in self.members_data if m.get("is_active")]) if self.members_data else 0
                QTimer.singleShot(0, lambda: self.members_text.setText(f"Members online: {members_online}"))
            
            # Update points breakdown
            if self.house_data:
                points_total = self.house_data.get("points_total", 0)
                if hasattr(self, "points_labels"):
                    QTimer.singleShot(0, lambda: self._update_points_display(points_total))
            
            # Update top members avatars
            if self.members_data and hasattr(self, "top_member_labels"):
                QTimer.singleShot(0, self._update_top_members)
            
            # Update congrats message
            if hasattr(self, "congrats_label"):
                congrats_msg = f"Congratulations, {self.house_name}! You are building a great house!"
                QTimer.singleShot(0, lambda: self.congrats_label.setText(congrats_msg))
        except Exception as e:
            print(f"[ERROR] Failed to update UI: {e}")

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
                    avatar_file = member.get("avatar", "man1.png")
                    if not avatar_file.startswith("/") and not avatar_file.startswith("http"):
                        avatar_path = self.avatars_path + avatar_file
                    else:
                        avatar_path = avatar_file
                    
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
        
        # Add subtle shadow to title
        title_shadow = QGraphicsDropShadowEffect()
        title_shadow.setBlurRadius(5)
        title_shadow.setXOffset(2)
        title_shadow.setYOffset(2)
        title_shadow.setColor(Qt.GlobalColor.darkGreen)
        title_label.setGraphicsEffect(title_shadow)
        
        left_layout.addWidget(title_label)
        
        # Tagline
        tagline_label = QLabel("Code.Create.Conquer.")
        tagline_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline_label.setStyleSheet("""
            font-family: 'Inter', sans-serif;
            font-size: 18px;
            font-weight: 400;
            font-style: italic;
            color: #004C25;
            background: transparent;
            margin-top: -5px;
        """)
        left_layout.addWidget(tagline_label)

        banner_label = QLabel()
        banner_label.setStyleSheet("background: transparent;")
        self.banner_label = banner_label
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
        
        # Add shadow effect to banner
        banner_shadow = QGraphicsDropShadowEffect()
        banner_shadow.setBlurRadius(15)
        banner_shadow.setXOffset(5)
        banner_shadow.setYOffset(5)
        banner_shadow.setColor(Qt.GlobalColor.black)
        banner_label.setGraphicsEffect(banner_shadow)
        
        left_layout.addWidget(banner_label)
        left_layout.addSpacing(5)

        # Try to fetch the banner image for this house from backend in background
        def _fetch_banner():
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
                    target = None
                    for h in items:
                        # match by name or slug (case-insensitive)
                        if str(h.get("name", "")).lower() == str(self.house_name).lower() or str(h.get("slug", "")).lower() == str(self.house_name).lower():
                            target = h
                            break
                    if target:
                        img_url = target.get("banner") or target.get("logo")
                        if img_url:
                            if img_url.startswith("/"):
                                img_url = f"http://127.0.0.1:8000{img_url}"
                            try:
                                r2 = requests.get(img_url, headers=headers, timeout=6)
                                if r2.status_code == 200:
                                    data_bytes = r2.content
                                    pix = QPixmap()
                                    if pix.loadFromData(data_bytes):
                                        pix = pix.scaled(150, 430, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                                        # update UI in main thread via Qt event
                                        def _apply():
                                            try:
                                                self.banner_label.setPixmap(pix)
                                            except Exception:
                                                pass

                                        # Use Qt: invoke via single-shot timer to run on main thread
                                        from PyQt6.QtCore import QTimer
                                        QTimer.singleShot(0, _apply)
                            except Exception:
                                pass
            except Exception:
                pass

        threading.Thread(target=_fetch_banner, daemon=True).start()


        # Stats Icons Row
        stats_layout = QHBoxLayout()

        stats = [
            ("members.png", "257", "Members"),
            ("events.png", "20", "Events"),
            ("awards.png", "5", "Awards"),
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
        # CENTER SECTION: ARROW ON TOP + AVATARS AT BOTTOM
        # ----------------------------------------------------------
        center_layout = QVBoxLayout()
        center_layout.setContentsMargins(0, 0, 0, 0)

        # Arrow (top border)
        arrow_label = QLabel()
        arrow_label.setStyleSheet("background: transparent;")
        arrow_pixmap = QPixmap(self.assets_path + "expander_arrow.png")
        arrow_base_size = (32, 32)
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
            _set_scaled_pixmap(arrow_label, arrow_pixmap, arrow_base_size)
            _add_hover_scale(arrow_label, arrow_pixmap, arrow_base_size, hover_scale=1.2)
        arrow_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        center_layout.addWidget(arrow_label, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        arrow_label.mousePressEvent = self.show_announcements_dialog

        #push avatars to bottom
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

        # Create a frame container for the congratulatory message
        congrats_frame = QFrame()
        congrats_frame.setStyleSheet("""
            QFrame {
                border: 2px solid #084924;
                border-radius: 6px;
                background: transparent;
            }
        """)
        
        congrats_layout = QVBoxLayout(congrats_frame)
        congrats_layout.setContentsMargins(8, 8, 8, 8)
        
        congrats_label = QLabel("Congratulations, House of Java! You are currently 1st Place among all houses!")
        congrats_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        congrats_label.setWordWrap(True)
        congrats_label.setStyleSheet("""
            border: none;
            font-size: 13px;
            font-weight: 500;
            font-family: 'Inter', sans-serif;
            color: #084924;
            background: transparent;
        """)
        
        # Store reference for updates
        self.congrats_label = congrats_label
        
        congrats_layout.addWidget(congrats_label)
        
        # Add subtle shadow effect that appears only on the border
        # Using small blur and minimal offset to create border-only shadow effect
        congrats_shadow = QGraphicsDropShadowEffect()
        congrats_shadow.setBlurRadius(2)
        congrats_shadow.setXOffset(1)
        congrats_shadow.setYOffset(1)
        congrats_shadow.setColor(Qt.GlobalColor.black)
        congrats_frame.setGraphicsEffect(congrats_shadow)
        
        right_layout.addWidget(congrats_frame, alignment=Qt.AlignmentFlag.AlignRight)

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
        label1 = QLabel("<div align='center'><b>3,500</b><br><i>Behavioral</i></div>")
        label2 = QLabel("<div align='center'><b>3,500</b><br><i>Competitive</i></div>")
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
        label3 = QLabel("<div align='center'><b>3,500</b><br><i>Year Points</i></div>")
        label4 = QLabel("<div align='center'><b>7,438</b><br><i>Total Accumulated</i></div>")
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
        
        # Add shadow effect to RulesDialog
        dialog_shadow = QGraphicsDropShadowEffect()
        dialog_shadow.setBlurRadius(20)
        dialog_shadow.setXOffset(0)
        dialog_shadow.setYOffset(0)
        dialog_shadow.setColor(Qt.GlobalColor.black)
        self.setGraphicsEffect(dialog_shadow)
        
class AnnouncementsDialog(QDialog):
    def __init__(self, assets_path, announcements_data=None):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setModal(True)
        self.resize(850, 600)
        self.announcements_data = announcements_data or []

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

        # === Dynamic Announcement Boxes ===
        if self.announcements_data:
            for ann in self.announcements_data:
                box = QFrame()
                box.setStyleSheet("""
                    QFrame {
                        border: 2px solid #004C25;
                        border-radius: 8px;
                        background: transparent;
                    }
                """)
                box_layout = QVBoxLayout(box)
                box_layout.setContentsMargins(8, 8, 8, 8)
                
                # Title if available
                if ann.get("title"):
                    title = QLabel(f"<b>{ann.get('title')}</b>")
                    title.setStyleSheet("color: #004C25; font-family: 'Inter'; font-size: 14px; font-weight: bold; border: none;")
                    box_layout.addWidget(title)
                
                # Content
                content = QLabel(ann.get("content", "No content"))
                content.setObjectName("contentText")
                content.setWordWrap(True)
                content.setStyleSheet("border: none;")
                box_layout.addWidget(content)
                
                content_layout.addWidget(box)
        else:
            # Fallback if no data
            no_data_label = QLabel("No announcements available")
            no_data_label.setStyleSheet("color: #004C25; font-family: 'Inter'; font-size: 14px;")
            content_layout.addWidget(no_data_label)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        # Add shadow effect to AnnouncementsDialog
        dialog_shadow = QGraphicsDropShadowEffect()
        dialog_shadow.setBlurRadius(20)
        dialog_shadow.setXOffset(0)
        dialog_shadow.setYOffset(0)
        dialog_shadow.setColor(Qt.GlobalColor.black)
        self.setGraphicsEffect(dialog_shadow)
