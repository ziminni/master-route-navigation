import sys
import json
import os
import requests
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, 
    QScrollArea, QFrame, QMessageBox, QDialog, QLineEdit, QMenu, QSizePolicy, QGraphicsDropShadowEffect, QStackedWidget
)
from PyQt6.QtGui import QPixmap, QFont, QPainterPath, QRegion, QFontMetrics, QPainter, QIcon, QColor
from PyQt6.QtCore import Qt, QRectF, QSize


# Helper function to get the project root directory
def get_project_root():
    current_dir = os.path.dirname(__file__)
    # Navigate up from [projectname]/frontend/views/House to [projectname]
    return os.path.abspath(os.path.join(current_dir, "..", "..", ".."))


class RoundedTopImageLabel(QLabel):
    """QLabel subclass with only top-left and top-right rounded corners."""
    def __init__(self, radius=12):
        super().__init__()
        self.radius = radius
        self._pixmap = None

    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        super().setPixmap(pixmap)
        self.update_mask()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_mask()

    def update_mask(self):
        if not self._pixmap:
            return
        path = QPainterPath()
        rect = QRectF(self.rect())
        # Only round the top corners
        path.moveTo(rect.left(), rect.bottom())
        path.lineTo(rect.left(), rect.top() + self.radius)
        path.quadTo(rect.left(), rect.top(), rect.left() + self.radius, rect.top())
        path.lineTo(rect.right() - self.radius, rect.top())
        path.quadTo(rect.right(), rect.top(), rect.right(), rect.top() + self.radius)
        path.lineTo(rect.right(), rect.bottom())
        path.lineTo(rect.left(), rect.bottom())
        path.closeSubpath()
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)


class EventCard(QWidget):
    def __init__(self, event_data):
        super().__init__()
        self.event_data = event_data
        self.setFixedSize(288, 490)

        self.setCursor(Qt.CursorShape.ArrowCursor)

        # --- Drop shadow ---
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)             # Soft blur for shadow
        shadow.setXOffset(8)                 # Horizontal offset
        shadow.setYOffset(8)                 # Vertical offset
        shadow.setColor(QColor(0, 0, 0, 100))  # Slightly transparent black
        self.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- Image Section (only top corners rounded) ---
        img_label = RoundedTopImageLabel(radius=12)
        img_label.setFixedSize(288, 288)

        # Load image relative to [projectname]/frontend/assets/images/pics
        project_root = get_project_root()
        img_filename = self.event_data.get("img", "") or "default.png"
        img_path = os.path.join(project_root, "frontend", "assets", "images", "pics", img_filename)
        print(f"Attempting to load image: {img_path}")  # Debug log
        pixmap = QPixmap(img_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(
                288, 288,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            rect = pixmap.rect()
            x = (rect.width() - 288) // 2
            y = (rect.height() - 288) // 2
            pixmap = pixmap.copy(x, y, 288, 288)
            img_label.setPixmap(pixmap)
        else:
            # Set placeholder background instead of showing warning
            img_label.setStyleSheet("background-color: #e0e0e0; border-radius: 12px;")
            print(f"Image not found, using placeholder: {img_path}")

        main_layout.addWidget(img_label)

        # --- White Rectangle Section (attached below) ---
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            background: white;
            border-bottom-left-radius: 12px;
            border-bottom-right-radius: 12px;
            border-top-left-radius: 0px;
            border-top-right-radius: 0px;
            border: 1px solid #ccc;
        """)
        content_frame.setFixedSize(288, 202)

        content_layout = QVBoxLayout(content_frame)
        content_layout.setSpacing(5)
        content_layout.setContentsMargins(10, 10, 10, 10)

        # --- Title (Auto-Fitting Font) ---
        title_label = QLabel(self.event_data.get("title", ""))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("""
            color: #084924;
            border: none;
        """)

        # Start with a max font size
        font = QFont("Poppins", 20, QFont.Weight.Bold,)
        fm = QFontMetrics(font)
        max_width = 260  # inside the 288px card with padding
        text_width = fm.horizontalAdvance(self.event_data.get("title", ""))

        # Reduce font size until it fits within the rectangle
        while text_width > max_width and font.pointSize() > 10:
            font.setPointSize(font.pointSize() - 1)
            fm = QFontMetrics(font)
            text_width = fm.horizontalAdvance(self.event_data.get("title", ""))

        title_label.setFont(font)
        content_layout.addWidget(title_label)

        # Event Type
        event_type_label = QLabel("COMPETITION EVENT")
        event_font = QFont("Inter", 14)
        event_font.setItalic(True)
        event_type_label.setFont(event_font)
        event_type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        event_type_label.setStyleSheet("color: rgba(8, 73, 36, 0.64); background: transparent; border: none;")
        content_layout.addWidget(event_type_label)

        # Description
        desc_label = QLabel(self.event_data.get("desc", ""))
        desc_font = QFont("Inter", 13)
        desc_font.setItalic(True)
        desc_label.setFont(desc_font)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(
            "color: rgba(8, 73, 36, 0.64); background: transparent; border: none; text-decoration: underline;"
        )
        content_layout.addWidget(desc_label)

        # Button
        btn = QPushButton("See Details")
        btn.setFixedWidth(100)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            "background-color: #fdd835; color: black; padding: 6px; border-radius: 8px; font-weight: bold;"
        )
        btn.clicked.connect(self.show_details)
        content_layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignRight)

        main_layout.addWidget(content_frame)



    def open_participate_popup(self, event_title):
        # --- Path setup ---
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        members_path = os.path.join(project_root, "frontend", "Mock", "members.json")
        avatars_base_path = os.path.join(project_root, "frontend", "assets", "images", "avatars")
        participants_json = os.path.join(project_root, "frontend", "Mock", "participants.json")

        # --- Load members data ---
        try:
            with open(members_path, "r", encoding="utf-8") as f:
                members_data = json.load(f).get("members", [])
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to load members.json:\n{e}")
            return

        # --- Main dialog for members list ---
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Participate in {event_title}")
        dialog.resize(420, 700)
        dialog.setModal(False)  # CHANGED: Non-modal so other windows can be interacted with
        dialog.setStyleSheet("background-color: white; border-radius: 12px;")

        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Header ---
        header = QLabel("Select Members to Participate")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("""
            background-color: #084924;
            color: white;
            font: bold 16px 'Poppins';
            padding: 12px;
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
        """)
        main_layout.addWidget(header)

        # --- Search and filter row ---
        search_row = QHBoxLayout()
        search_row.setContentsMargins(0, 0, 0, 0)
        search_row.setSpacing(12)

        # Search container
        search_container = QWidget()
        search_container.setObjectName("searchContainer")
        search_container_layout = QHBoxLayout(search_container)
        search_container_layout.setContentsMargins(16, 12, 16, 12)
        search_container_layout.setSpacing(10)
        search_container.setFixedHeight(52)

        # Search icon
        search_icon = QLabel()
        search_icon_path = os.path.join(project_root, "frontend", "assets", "images", "search.png")
        if os.path.exists(search_icon_path):
            search_icon.setPixmap(
                QPixmap(search_icon_path).scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            )
        search_icon.setStyleSheet("background: transparent;")
        search_container_layout.addWidget(search_icon)

        # Search input
        search_bar = QLineEdit()
        search_bar.setObjectName("searchBar")
        search_bar.setPlaceholderText("Search members by name or role...")
        search_bar.setFrame(False)
        search_container_layout.addWidget(search_bar)
        search_row.addWidget(search_container, 1)

        # Filter button
        filter_btn = QPushButton(" Filter")
        filter_btn.setObjectName("filterButton")
        filter_icon_path = os.path.join(project_root, "frontend", "assets", "images", "filter.png")
        if os.path.exists(filter_icon_path):
            pixmap = QPixmap(filter_icon_path).scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            filter_btn.setIcon(QIcon(pixmap))
            filter_btn.setIconSize(QSize(20, 20))
        filter_btn.setFixedHeight(52)
        filter_btn.setFixedWidth(120)
        filter_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        search_row.addWidget(filter_btn)

        # --- Filter Menu Setup ---
        filter_menu = QMenu()
        filter_menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #084924;
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 16px;
                color: #084924;
                font-family: 'Inter';
            }
            QMenu::item:selected {
                background-color: #e8f5e9;
                color: #053D1D;
                border-radius: 6px;
            }
        """)

        main_layout.addLayout(search_row)

        # --- Scroll Area for members ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: #e8f5e9;")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(12, 12, 12, 12)
        scroll_layout.setSpacing(10)
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        # --- Popup for selected participants ---
        selected_popup = QDialog(self)
        selected_popup.setWindowTitle("Selected Participants")
        selected_popup.resize(420, 700)
        selected_popup.setWindowModality(Qt.WindowModality.NonModal)
        selected_popup.setWindowFlags(selected_popup.windowFlags() | Qt.WindowType.Window)
        selected_popup.setStyleSheet("""
            background-color: #084924;
            border-radius: 12px;
        """)
        selected_layout = QVBoxLayout(selected_popup)
        selected_layout.setContentsMargins(12, 12, 12, 12)
        selected_layout.setSpacing(10)

        selected_title = QLabel("Participants List")
        selected_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        selected_title.setStyleSheet("color: white; font: bold 16px 'Poppins'; margin-bottom: 8px;")
        selected_layout.addWidget(selected_title)

        selected_scroll = QScrollArea()
        selected_scroll.setWidgetResizable(True)
        selected_scroll.setStyleSheet("border: none; background: transparent;")
        selected_content = QWidget()
        selected_scroll_layout = QVBoxLayout(selected_content)
        selected_scroll_layout.setSpacing(10)
        selected_scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        selected_scroll.setWidget(selected_content)
        selected_layout.addWidget(selected_scroll)

        confirm_btn = QPushButton("Confirm")
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #3bb54a;
                color: white;
                border-radius: 8px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2e8b3e;
            }
        """)
        selected_layout.addWidget(confirm_btn)

        selected_members = {}  # store selected members dict

        # --- Function: update selected participants popup ---
        def update_selected_popup():
            # Clear previous widgets
            for i in reversed(range(selected_scroll_layout.count())):
                item = selected_scroll_layout.itemAt(i).widget()
                if item:
                    item.deleteLater()

            # Add selected participants
            for idx, (name, info) in enumerate(selected_members.items(), start=1):
                frame = QFrame()
                frame.setFixedHeight(80)
                frame.setStyleSheet("background: white;")
                frame_layout = QHBoxLayout(frame)
                frame_layout.setContentsMargins(8, 8, 8, 8)
                frame_layout.setSpacing(12)

                # Avatar
                avatar_path = os.path.join(avatars_base_path, info["avatar"])
                pix = QPixmap(avatar_path)
                if pix.isNull():
                    pix = QPixmap(50, 50)
                    pix.fill(Qt.GlobalColor.lightGray)
                pix = pix.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                circ = QPixmap(50, 50)
                circ.fill(Qt.GlobalColor.transparent)
                painter = QPainter(circ)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                path = QPainterPath()
                path.addEllipse(0, 0, 50, 50)
                painter.setClipPath(path)
                painter.drawPixmap(0, 0, pix)
                painter.end()
                avatar_lbl = QLabel()
                avatar_lbl.setPixmap(circ)
                avatar_lbl.setFixedSize(50, 50)
                frame_layout.addWidget(avatar_lbl)

                # Name & Role
                v = QVBoxLayout()
                v.setContentsMargins(0, 0, 0, 0)
                v.setSpacing(-3)

                name_lbl = QLabel(f"{idx}. {name}")
                name_font = QFont("Poppins", 11, QFont.Weight.Bold)
                name_lbl.setFont(name_font)
                name_lbl.setStyleSheet("color: #084924; padding: 0px; margin: 0px;")
                name_lbl.setContentsMargins(0, 0, 0, 0)

                role_lbl = QLabel(info["role"])
                role_font = QFont("Inter", 10)
                role_lbl.setFont(role_font)
                role_lbl.setStyleSheet("color: #666; padding: 0px; margin: 0px;")
                role_lbl.setContentsMargins(0, 0, 0, 0)

                v.addWidget(name_lbl)
                v.addWidget(role_lbl)
                frame_layout.addLayout(v)
                frame_layout.addStretch()

                # Remove button
                remove_btn = QPushButton("✕")
                remove_btn.setFixedSize(30, 30)
                remove_btn.setStyleSheet("""
                    QPushButton { background-color: #e53935; color: white; border-radius: 15px; font-weight: bold; }
                    QPushButton:hover { background-color: #c62828; }
                """)
                remove_btn.clicked.connect(lambda _, n=name: remove_participant(n))
                frame_layout.addWidget(remove_btn)

                selected_scroll_layout.addWidget(frame)

        # --- Function: remove participant ---
        def remove_participant(name):
            if name in selected_members:
                del selected_members[name]
            update_selected_popup()

        # --- Function: toggle selection ---
        def toggle_selection(mem, btn):
            name = mem["name"]
            if name not in selected_members:
                selected_members[name] = {
                    "role": mem["role"],
                    "avatar": mem["avatar"]
                }
                btn.setText("✓")
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3bb54a;
                        color: white;
                        border-radius: 15px;
                        font-weight: bold;
                        font-size: 16px;
                    }
                    QPushButton:hover {
                        background-color: #2e8b3e;
                    }
                """)
            else:
                remove_participant(name)
                btn.setText("+")
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3bb54a;
                        color: white;
                        border-radius: 15px;
                        font-weight: bold;
                        font-size: 16px;
                    }
                    QPushButton:hover {
                        background-color: #2e8b3e;
                    }
                """)
            update_selected_popup()

        # --- Build members list ---
        member_frames = []
        for idx, m in enumerate(members_data, start=1):
            frame = QFrame()
            frame.setFixedHeight(80)
            frame.setStyleSheet("QFrame { background: white; }")
            frame_layout = QHBoxLayout(frame)
            frame_layout.setContentsMargins(8, 8, 8, 8)
            frame_layout.setSpacing(12)

            frame.meta = m  # attach the member dict directly to the frame


            # --- Avatar ---
            avatar_path = os.path.join(avatars_base_path, m["avatar"])
            pix = QPixmap(avatar_path)
            if pix.isNull():
                pix = QPixmap(50, 50)
                pix.fill(Qt.GlobalColor.lightGray)
            pix = pix.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)

            size = min(pix.width(), pix.height())
            circ = QPixmap(size, size)
            circ.fill(Qt.GlobalColor.transparent)
            painter = QPainter(circ)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            path = QPainterPath()
            path.addEllipse(0, 0, size, size)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, pix)
            painter.end()

            avatar_lbl = QLabel()
            avatar_lbl.setPixmap(circ)
            avatar_lbl.setFixedSize(50, 50)
            avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            frame_layout.addWidget(avatar_lbl)

            # --- Name & Role ---
            v = QVBoxLayout()
            v.setContentsMargins(0, 0, 0, 0)
            v.setSpacing(-3)

            name_lbl = QLabel(f"{idx}. {m['name']}")
            name_font = QFont("Poppins", 11, QFont.Weight.Bold)
            name_lbl.setFont(name_font)
            name_lbl.setStyleSheet("color: #084924; padding: 0px; margin: 0px;")
            name_lbl.setContentsMargins(0, 0, 0, 0)

            role_lbl = QLabel(m["role"])
            role_font = QFont("Inter", 10)
            role_lbl.setFont(role_font)
            role_lbl.setStyleSheet("color: #666; padding: 0px; margin: 0px;")
            role_lbl.setContentsMargins(0, 0, 0, 0)

            v.addWidget(name_lbl)
            v.addWidget(role_lbl)
            frame_layout.addLayout(v)
            frame_layout.addStretch()

            # --- Add/Remove Button + Chat Icon ---
            buttons_layout = QHBoxLayout()
            buttons_layout.setSpacing(5)

            # Chat icon button
            chat_btn = QPushButton()
            chat_btn.setFixedSize(30, 30)
            chat_icon_path = os.path.join(project_root, "frontend", "assets", "images", "icons", "chat.png")
            if os.path.exists(chat_icon_path):
                chat_btn.setIcon(QIcon(chat_icon_path))
                chat_btn.setIconSize(QSize(20, 20))
            chat_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    border-radius: 15px;
                }
                QPushButton:hover {
                    background-color: #dcdcdc;
                }
            """)
            buttons_layout.addWidget(chat_btn)

            # Add button
            add_btn = QPushButton("+")
            add_btn.setFixedSize(30, 30)
            add_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3bb54a;
                    color: white;
                    border-radius: 15px;
                    font-weight: bold;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #2e8b3e;
                }
            """)
            add_btn.clicked.connect(lambda _, m=m, b=add_btn: toggle_selection(m, b))
            buttons_layout.addWidget(add_btn)

            frame_layout.addLayout(buttons_layout)
            frame.meta = {"name": m["name"], "role": m["role"], "year": m.get("year", "")}
            scroll_layout.addWidget(frame)
            member_frames.append(frame)
            

        # --- Search filter ---
        def filter_members(text):
            for i in range(scroll_layout.count()):
                item = scroll_layout.itemAt(i).widget()
                if not item:
                    continue
                labels = item.findChildren(QLabel)
                visible = any(text.lower() in lbl.text().lower() for lbl in labels)
                item.setVisible(visible)

        search_bar.textChanged.connect(filter_members)

        # --- Add filter actions ---
        filter_menu.addAction("Filter by Year Level", lambda: apply_filter("year"))
        filter_menu.addAction("Filter by Position", lambda: apply_filter("position"))
        filter_menu.addSeparator()
        filter_menu.addAction("Sort A–Z", lambda: apply_filter("az"))
        filter_menu.addAction("Sort Z–A", lambda: apply_filter("za"))
        filter_btn.setMenu(filter_menu)

        # --- Filter function ---
        def apply_filter(mode):
            # Copy original frames
            frames = member_frames.copy()

            if mode == "year":
                frames.sort(key=lambda f: int(f.meta.get("year", 0)), reverse=True)

            elif mode == "position":
                ROLE_ORDER = {
                    "House leader": 0,
                    "Vice-house leader": 1,
                    "Member": 2
                }
                frames.sort(key=lambda f: ROLE_ORDER.get(f.meta.get("role", ""), 999))

            elif mode == "az":
                # Sort by last name ascending
                frames.sort(key=lambda f: f.meta.get("name", "").split()[-1].lower())
            elif mode == "za":
                # Sort by last name descending
                frames.sort(key=lambda f: f.meta.get("name", "").split()[-1].lower(), reverse=True)

            # Clear layout
            for i in reversed(range(scroll_layout.count())):
                item = scroll_layout.takeAt(i)
                if item.widget():
                    item.widget().setParent(None)

            # Re-add frames in new order
            for f in frames:
                scroll_layout.addWidget(f)

        # --- Confirm button saves JSON ---
        def confirm_selection():
            try:
                # Load existing participants if file exists
                if os.path.exists(participants_json):
                    with open(participants_json, "r", encoding="utf-8") as f:
                        existing_data = json.load(f)
                else:
                    existing_data = {}

                # Ensure a dictionary for events
                if not isinstance(existing_data, dict):
                    existing_data = {}

                # Update current event
                existing_data[str(self.event_data["id"])] = {
                    "event_title": event_title,
                    "participants": list(selected_members.keys())
                }

                # Save back
                with open(participants_json, "w", encoding="utf-8") as f:
                    json.dump(existing_data, f, indent=2)

                QMessageBox.information(dialog, "Saved", "Participants successfully saved!")
                selected_popup.close()
                dialog.close()

            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to save participants:\n{e}")


        confirm_btn.clicked.connect(confirm_selection)

        # --- Twin dialog positioning ---
        # Calculate screen position (optional: center on screen)
        screen = self.screen().availableGeometry()
        main_width = 420
        main_height = 700
        spacing = 20  # gap between the dialogs

        # Position main dialog on left
        dialog.move(screen.center().x() - main_width - spacing//2, screen.center().y() - main_height//2)

        # Position selected_popup to the right of main dialog
        selected_popup.move(dialog.x() + main_width + spacing, dialog.y())

        # Make both visible
        selected_popup.show()
        dialog.show()

        # Use exec() only on main dialog to block   
        dialog.exec()





    def show_details(self):
        project_root = get_project_root()
        details_path = os.path.join(project_root, "frontend", "Mock", "event_details.json")
        try:
            with open(details_path, "r", encoding="utf-8") as f:
                details_data = json.load(f)
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", f"event_details.json file not found at {details_path}.")
            return

        # Normalize poster field
        for d in details_data:
            if "poster" in d and d["poster"]:
                if isinstance(d["poster"], str):
                    d["poster"] = [d["poster"]]
                d["poster"] = [os.path.basename(p) for p in d["poster"]]

        detail = next((d for d in details_data if d["id"] == self.event_data["id"]), None)
        if not detail:
            QMessageBox.warning(self, "Not Found", "No details found for this event.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(detail["title"])
        dialog.resize(900, 600)
        dialog.setModal(False)
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.Window)

        # Green gradient background
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(
                    spread:pad,
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #00512E,
                    stop:1 #00813C
                );
            }
        """)

        outer_layout = QVBoxLayout(dialog)
        outer_layout.setContentsMargins(20, 20, 20, 20)
        outer_layout.setSpacing(15)

        # Main horizontal layout for 2 columns
        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)
        outer_layout.addLayout(main_layout)

        # -----------------------------
        # Left Column: Logo/Title/Date + Poster Images
        # -----------------------------
        left_column = QVBoxLayout()
        left_column.setSpacing(15)

        # 1️⃣ Logo + Title + Date container (compact)
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 12px;
                padding: 8px;  /* smaller padding for compact look */
            }
        """)
        info_layout = QHBoxLayout(info_frame)
        info_layout.setSpacing(10)  # less spacing for compactness
        info_layout.setContentsMargins(5, 5, 5, 5)  # smaller margins

        # Logo
        logo_label = QLabel()
        logo_path = os.path.join(project_root, "frontend", "assets", "images", "csco_logo.png")
        logo_pix = QPixmap(logo_path)
        if not logo_pix.isNull():
            logo_pix = logo_pix.scaledToHeight(50, Qt.TransformationMode.SmoothTransformation)  # slightly smaller
        logo_label.setPixmap(logo_pix)
        logo_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        info_layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        # Title + Date & Time
        title_date_layout = QVBoxLayout()
        title_date_layout.setSpacing(2)  # smaller gap between title and datetime

        title_label = QLabel(detail["title"])
        title_label.setFont(QFont("Poppins", 12, QFont.Weight.Bold))  # slightly smaller font
        title_label.setStyleSheet("color: #084924;")
        title_label.setWordWrap(True)
        title_date_layout.addWidget(title_label)

        datetime_label = QLabel(f"{detail.get('dateofpost')} at {detail.get('timeofpost')}")
        datetime_label.setFont(QFont("Inter", 11))
        datetime_label.setStyleSheet("color: #084924;")
        title_date_layout.addWidget(datetime_label)

        info_layout.addLayout(title_date_layout)

        # Set a fixed height for compactness
        info_frame.setFixedHeight(150)  # adjust as needed
        left_column.addWidget(info_frame)


        # Poster Images container with proper scaling
        posters = detail.get("poster", [])
        if posters:
            poster_frame = QFrame()
            poster_frame.setStyleSheet("""
                QFrame {
                    background: white;
                    border-radius: 12px;
                    padding: 10px;
                }
            """)
            poster_layout = QVBoxLayout(poster_frame)
            poster_layout.setSpacing(6)
            poster_layout.setContentsMargins(10, 10, 10, 10)

            stacked_widget = QStackedWidget()
            stacked_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            poster_layout.addWidget(stacked_widget)

            # Add images
            for img_path in posters:
                lbl = QLabel()
                full_img_path = os.path.join(project_root, "frontend", "assets", "images", "pics", img_path)
                pix = QPixmap(full_img_path)
                if pix.isNull():
                    pix = QPixmap(500, 300)
                    pix.fill(Qt.GlobalColor.darkGreen)
                else:
                    # Scale image to take most of the container
                    max_width, max_height = 500, 300  # container size
                    pix = pix.scaled(
                        max_width, max_height,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                lbl.setPixmap(pix)
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                stacked_widget.addWidget(lbl)

            # Navigation only if multiple images
            if len(posters) > 1:
                # Circle indicators
                indicators_layout = QHBoxLayout()
                indicators_layout.setSpacing(4)  # compact spacing
                indicators = []
                for i in range(len(posters)):
                    circle = QLabel("●")
                    circle.setStyleSheet("color: #066c27; font-size: 12px;")  # green
                    indicators_layout.addWidget(circle, alignment=Qt.AlignmentFlag.AlignCenter)
                    indicators.append(circle)
                indicators[0].setStyleSheet("color: #fdd835; font-size: 12px;")  # highlight first

                # Navigation buttons
                nav_layout = QHBoxLayout()
                nav_layout.setSpacing(10)
                prev_btn = QPushButton("◀")
                next_btn = QPushButton("▶")
                for btn in [prev_btn, next_btn]:
                    btn.setFixedSize(30, 30)
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #084924;
                            color: white;
                            border-radius: 15px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #066c27;
                        }
                    """)
                nav_layout.addWidget(prev_btn)
                nav_layout.addStretch()
                nav_layout.addLayout(indicators_layout)
                nav_layout.addStretch()
                nav_layout.addWidget(next_btn)

                poster_layout.addLayout(nav_layout)

                # Navigation logic
                def update_indicators(index):
                    for i, circle in enumerate(indicators):
                        circle.setStyleSheet(
                            "color: #fdd835; font-size: 12px;" if i == index else "color: #066c27; font-size: 12px;"
                        )

                def show_prev():
                    idx = stacked_widget.currentIndex()
                    idx = (idx - 1) % stacked_widget.count()
                    stacked_widget.setCurrentIndex(idx)
                    update_indicators(idx)

                def show_next():
                    idx = stacked_widget.currentIndex()
                    idx = (idx + 1) % stacked_widget.count()
                    stacked_widget.setCurrentIndex(idx)
                    update_indicators(idx)

                prev_btn.clicked.connect(show_prev)
                next_btn.clicked.connect(show_next)

            left_column.addWidget(poster_frame)


        main_layout.addLayout(left_column, 1)

        # -----------------------------
        # Right Column: Scrollable Event Details
        # -----------------------------
        right_column = QVBoxLayout()

        details_frame = QFrame()
        details_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 12px;
                padding: 10px;
            }
        """)
        details_layout = QVBoxLayout(details_frame)
        details_layout.setContentsMargins(5, 5, 5, 5)
        details_layout.setSpacing(10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(8)
        scroll_layout.setContentsMargins(0, 0, 0, 0)

        for line in detail["details"]:
            lbl = QLabel(line)
            lbl.setWordWrap(True)
            lbl.setStyleSheet("color: #084924; font-size: 12px; font-weight: 700;")
            scroll_layout.addWidget(lbl)

        scroll_content.setLayout(scroll_layout)
        scroll.setWidget(scroll_content)
        details_layout.addWidget(scroll)
        right_column.addWidget(details_frame)

        main_layout.addLayout(right_column, 2)

        # -----------------------------
        # Participate Button
        # -----------------------------
        participate_btn = QPushButton("Participate")
        participate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        participate_btn.setStyleSheet("""
            QPushButton {
                background-color: #fdd835;
                color: black;
                padding: 8px 14px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffeb3b;
            }
        """)
        participate_btn.clicked.connect(lambda: self.open_participate_popup(detail["title"]))
        outer_layout.addWidget(participate_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        dialog.show()

class EventsPage(QWidget):
    def __init__(self, username, role, primary_role, token, house_name, house_id=None, api_base="http://127.0.0.1:8000"):
        super().__init__()
        self.username = username
        self.role = role
        self.primary_role = primary_role
        self.token = token
        self.house_name = house_name
        self.house_id = house_id
        self.api_base = api_base

        self.setup_ui()

    def load_events_from_api(self):
        """Load events from backend API."""
        events = []
        try:
            headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
            url = f"{self.api_base}/api/house/events/"
            if self.house_id:
                url += f"?house={self.house_id}"
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                api_events = response.json()
                if isinstance(api_events, dict) and "results" in api_events:
                    api_events = api_events["results"]
                
                # Transform API data to expected format
                for event in api_events:
                    events.append({
                        "id": event.get("id"),
                        "title": event.get("title", "Untitled Event"),
                        "desc": event.get("description", ""),
                        "img": event.get("img", "") or "",
                        "start_date": event.get("start_date", ""),
                        "end_date": event.get("end_date", ""),
                        "is_competition": event.get("is_competition", False),
                    })
            else:
                print(f"Failed to load events: {response.status_code}")
        except Exception as e:
            print(f"Error loading events from API: {e}")
        
        return events

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Scrollable Event Cards ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # disable horizontal scroll
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #053D1D;
                width: 14px;
                border: none;
                margin: 0;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical {
                background: white;
                border-radius: 7px;
                min-height: 30px;
                margin: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #f2f2f2;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
                background: none;
                border: none;
            }
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: #053D1D;
                border-radius: 7px;
            }
        """)


        # Load events from API
        project_root = get_project_root()
        events = self.load_events_from_api()

        # Normalize event image paths to 'pics/<basename>'
        for e in events:
            if "img" in e and e["img"]:
                e["img"] = os.path.join(os.path.basename(e["img"]))

        # --- Container for event cards ---
        content = QWidget()
        grid_layout = QGridLayout(content)
        grid_layout.setSpacing(20)
        grid_layout.setContentsMargins(20, 20, 20, 20)

        # Number of columns
        columns = 3

        # Add cards in a grid
        for idx, event in enumerate(events):
            row = idx // columns
            col = idx % columns
            card = EventCard(event)
            grid_layout.addWidget(card, row, col)

        # Optional: add stretch to bottom row to push cards up if needed
        grid_layout.setRowStretch((len(events)-1)//columns + 1, 1)

        # Scroll area
        scroll_area.setWidget(content)
        main_layout.addWidget(scroll_area)
