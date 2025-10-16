import sys
import json
import os
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea, QFrame, QMessageBox, QDialog, QLineEdit, QMenu
)
from PyQt6.QtGui import QPixmap, QFont, QPainterPath, QRegion, QFontMetrics, QPainter, QIcon
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

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- Image Section (only top corners rounded) ---
        img_label = RoundedTopImageLabel(radius=12)
        img_label.setFixedSize(288, 288)

        # Load image relative to [projectname]/frontend/assets/images/pics
        project_root = get_project_root()
        img_path = os.path.join(project_root, "frontend", "assets", "images", "pics", self.event_data.get("img", ""))
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
            QMessageBox.warning(self, "Image Not Found", f"Image {img_path} not found.")

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
            background: transparent;
            border: none;
        """)

        # Start with a max font size
        font = QFont("Poppins", 20, QFont.Weight.Bold)
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
        # --- Path setup (same as MembersPage) ---
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
        dialog.setModal(True)
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

        # --- Search Bar ---
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
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
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

        from PyQt6.QtWidgets import QMenu

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

        # --- Add filter options ---
        filter_menu.addAction("Filter by Year Level", lambda: apply_filter("year"))
        filter_menu.addAction("Filter by Position", lambda: apply_filter("position"))
        filter_menu.addSeparator()
        filter_menu.addAction("Sort A–Z", lambda: apply_filter("az"))
        filter_menu.addAction("Sort Z–A", lambda: apply_filter("za"))

        # --- Connect the button to show the menu ---
        filter_btn.setMenu(filter_menu)


        # Add to main layout
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

        # --- Popup for selected participants (shown beside main dialog) ---
        selected_popup = QDialog(dialog)
        selected_popup.setWindowTitle("Selected Participants")
        selected_popup.resize(420, 700)
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
            # Clear layout
            for i in reversed(range(selected_scroll_layout.count())):
                item = selected_scroll_layout.itemAt(i).widget()
                if item:
                    item.deleteLater()

            # Add selected participants
            for idx, (name, info) in enumerate(selected_members.items(), start=1):
                frame = QFrame()
                frame.setStyleSheet("""
                    background: white;
                    border-radius: 10px;
                    border: 2px solid #3bb54a;
                """)
                h = QHBoxLayout(frame)
                h.setContentsMargins(8, 8, 8, 8)

                # Avatar
                avatar_path = os.path.join(avatars_base_path, info["avatar"])
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
                h.addWidget(avatar_lbl)

                # Name & role
                v = QVBoxLayout()
                name_lbl = QLabel(f"{idx}. {name}")
                name_lbl.setStyleSheet("font-weight: bold; color: #084924; font-size: 13px;")
                role_lbl = QLabel(info["role"])
                role_lbl.setStyleSheet("color: #666; font-size: 12px;")
                v.addWidget(name_lbl)
                v.addWidget(role_lbl)
                h.addLayout(v)
                h.addStretch()

                # Remove button
                remove_btn = QPushButton("✕")
                remove_btn.setFixedSize(30, 30)
                remove_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #e53935;
                        color: white;
                        border-radius: 15px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #c62828;
                    }
                """)
                remove_btn.clicked.connect(lambda _, n=name: remove_participant(n))
                h.addWidget(remove_btn)

                selected_scroll_layout.addWidget(frame)

            selected_content.setLayout(selected_scroll_layout)
            selected_scroll.setWidget(selected_content)
            selected_popup.show()

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
        for idx, m in enumerate(members_data, start=1):
            frame = QFrame()
            frame.setStyleSheet("""
                QFrame {
                    background: white;
                    border-radius: 10px;
                    border: 2px solid #3bb54a;
                }
            """)
            frame_layout = QHBoxLayout(frame)
            frame_layout.setContentsMargins(8, 8, 8, 8)
            frame_layout.setSpacing(12)

            # Avatar
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
            frame_layout.addWidget(avatar_lbl)

            # Name & Role
            v = QVBoxLayout()
            name_lbl = QLabel(f"{idx}. {m['name']}")
            name_lbl.setStyleSheet("font-weight: bold; color: #084924; font-size: 13px;")
            role_lbl = QLabel(m["role"])
            role_lbl.setStyleSheet("color: #666; font-size: 12px;")
            v.addWidget(name_lbl)
            v.addWidget(role_lbl)
            frame_layout.addLayout(v)
            frame_layout.addStretch()

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
            frame_layout.addWidget(add_btn)

            scroll_layout.addWidget(frame)

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

        def apply_filter(mode):
            # Extract all frames (each represents a member)
            member_frames = []
            for i in range(scroll_layout.count()):
                w = scroll_layout.itemAt(i).widget()
                if w:
                    member_frames.append(w)

            if mode == "year":
                # Sort by year level text inside QLabel (if available)
                member_frames.sort(key=lambda frame: next(
                    (lbl.text() for lbl in frame.findChildren(QLabel) if "Year" in lbl.text()), ""
                ))
            elif mode == "position":
                # Sort by role label
                member_frames.sort(key=lambda frame: next(
                    (lbl.text() for lbl in frame.findChildren(QLabel) if lbl.text() not in ["+", "✓"]), ""
                ))
            elif mode == "az":
                member_frames.sort(key=lambda frame: next(
                    (lbl.text() for lbl in frame.findChildren(QLabel) if ". " in lbl.text()), ""
                ))
            elif mode == "za":
                member_frames.sort(key=lambda frame: next(
                    (lbl.text() for lbl in frame.findChildren(QLabel) if ". " in lbl.text()), ""
                ), reverse=True)

            # Clear layout
            for i in reversed(range(scroll_layout.count())):
                item = scroll_layout.takeAt(i)
                if item.widget():
                    item.widget().setParent(None)

            # Re-add sorted frames
            for frame in member_frames:
                scroll_layout.addWidget(frame)


        # --- Confirm button saves JSON ---
        def confirm_selection():
            try:
                with open(participants_json, "w", encoding="utf-8") as f:
                    json.dump({"participants": selected_members}, f, indent=2)
                QMessageBox.information(dialog, "Saved", "Participants successfully saved!")
                selected_popup.close()
                dialog.close()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to save participants:\n{e}")

        confirm_btn.clicked.connect(confirm_selection)

        # --- Position selected_popup beside dialog ---
        geo = dialog.geometry()
        selected_popup.move(geo.x() + geo.width() + 20, geo.y())
        selected_popup.show()
        dialog.exec()




    def show_details(self):
        # Load event details from external JSON file
        project_root = get_project_root()
        details_path = os.path.join(project_root, "frontend", "Mock", "event_details.json")
        print(f"Attempting to load event_details.json: {details_path}")  # Debug log
        try:
            with open(details_path, "r", encoding="utf-8") as f:
                details_data = json.load(f)
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", f"event_details.json file not found at {details_path}.")
            return

        # Normalize poster paths in details_data (so they reference Mock/pics/<basename>)
        for d in details_data:
            if "poster" in d and d["poster"]:
                # ensure poster is a list
                if isinstance(d["poster"], str):
                    d["poster"] = [d["poster"]]
                normalized = []
                for p in d["poster"]:
                    # always use basename and place under 'pics' so the UI path join works
                    normalized.append(os.path.join(os.path.basename(p)))
                d["poster"] = normalized

        # Find matching event by id
        detail = next((d for d in details_data if d["id"] == self.event_data["id"]), None)
        if not detail:
            QMessageBox.warning(self, "Not Found", "No details found for this event.")
            return

        # --- Popup Dialog ---
        dialog = QDialog(self)
        dialog.setWindowTitle(detail["title"])
        dialog.setModal(True)
        dialog.resize(600, 750)  # Fixed height

        # --- Gradient Border Frame (Outer) ---
        outer_frame = QFrame(dialog)
        outer_frame.setStyleSheet("""
            QFrame {
                border-radius: 12px;
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #084924,
                    stop: 0.33 #077336,
                    stop: 1 #078F41
                );
                padding: 4px;
            }
        """)

        # --- Inner Frame (Content Background) ---
        inner_frame = QFrame()
        inner_frame.setStyleSheet("""
            QFrame {
                background-color: #f3f3f3;
                border-radius: 8px;
            }
        """)

        outer_layout = QVBoxLayout(dialog)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(outer_frame)

        inner_layout = QVBoxLayout(outer_frame)
        inner_layout.setContentsMargins(4, 4, 4, 4)
        inner_layout.addWidget(inner_frame)

        # --- Scroll Area (With Scrollbars) ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
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
            QScrollBar:horizontal {
                background: #053D1D;
                height: 14px;
                border: none;
                margin: 0;
                border-radius: 7px;
            }
            QScrollBar::handle:horizontal {
                background: white;
                border-radius: 7px;
                min-width: 30px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #f2f2f2;
            }
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width: 0;
                background: none;
                border: none;
            }
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {
                background: #053D1D;
                border-radius: 7px;
            }
        """)

        # --- Scrollable Content ---
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(20, 20, 20, 20)
        scroll_layout.setSpacing(15)

        # --- Title ---
        title_label = QLabel(detail["title"])
        title_label.setFont(QFont("Poppins", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #084924;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_layout.addWidget(title_label)

        # --- Description ---
        desc_label = QLabel(detail["content"])
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #084924; font-size: 13px;")
        scroll_layout.addWidget(desc_label)

        # --- Details ---
        for line in detail["details"]:
            lbl = QLabel(line)
            lbl.setWordWrap(True)
            lbl.setStyleSheet("color: rgba(8, 73, 36, 0.8); font-size: 12px;")
            scroll_layout.addWidget(lbl)

        # --- Poster Images ---
        posters = detail.get("poster")
        if isinstance(posters, str):
            posters = [posters]

        if posters:
            poster_frame = QFrame()
            poster_frame.setStyleSheet("""
                background: #084924;
                border-radius: 12px;
                padding: 10px;
            """)
            poster_layout = QHBoxLayout(poster_frame)
            poster_layout.setContentsMargins(10, 10, 10, 10)
            poster_layout.setSpacing(10)

            for img_path in posters[:2]:
                lbl = QLabel()
                # img_path is normalized to 'pics/<basename>' earlier
                full_img_path = os.path.join(project_root, "frontend", "assets", "images", "pics", img_path)
                print(f"Attempting to load poster image: {full_img_path}")  # Debug log
                pix = QPixmap(full_img_path)
                if pix.isNull():
                    pix = QPixmap(300, 250)
                    pix.fill(Qt.GlobalColor.darkGreen)
                    QMessageBox.warning(self, "Image Not Found", f"Poster image {full_img_path} not found.")
                else:
                    pix = pix.scaled(
                        300, 250,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                lbl.setPixmap(pix)
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                poster_layout.addWidget(lbl)

            scroll_layout.addWidget(poster_frame)

        scroll.setWidget(scroll_content)
        inner_frame_layout = QVBoxLayout(inner_frame)
        inner_frame_layout.setContentsMargins(0, 0, 0, 0)
        inner_frame_layout.addWidget(scroll)

                # --- Participate Button ---
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
        scroll_layout.addWidget(participate_btn, alignment=Qt.AlignmentFlag.AlignCenter)


        dialog.exec()




class EventsPage(QWidget):
    def __init__(self, username, role, primary_role, token, house_name):
        super().__init__()
        self.username = username
        self.role = role
        self.primary_role = primary_role
        self.token = token
        self.house_name = house_name

        main_layout = QVBoxLayout(self)

        # --- Scrollable Event Cards ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
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
            QScrollBar:horizontal {
                background: #053D1D;
                height: 14px;
                border: none;
                margin: 0;
                border-radius: 7px;
            }
            QScrollBar::handle:horizontal {
                background: white;
                border-radius: 7px;
                min-width: 30px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #f2f2f2;
            }
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width: 0;
                background: none;
                border: none;
            }
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {
                background: #053D1D;
                border-radius: 7px;
            }
            QScrollBar::corner {
                background: #053D1D;
                border-radius: 7px;
            }
        """)

        content = QWidget()
        layout = QHBoxLayout(content)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)


        # Load events.json
        project_root = get_project_root()
        events_path = os.path.join(project_root, "frontend", "Mock", "events.json")
        print(f"Attempting to load events.json: {events_path}")  # Debug log
        try:
            with open(events_path, "r", encoding="utf-8") as f:
                events = json.load(f)
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", f"events.json file not found at {events_path}.")
            events = []

        # Normalize event image paths to 'pics/<basename>' so the existing path joins work
        for e in events:
            if "img" in e and e["img"]:
                e["img"] = os.path.join( os.path.basename(e["img"]))

        # Add cards to grid — automatically based on the JSON length
        for event in events:
            card = EventCard(event)
            layout.addWidget(card)


        scroll_area.setWidget(content)
        layout.addStretch()
        main_layout.addWidget(scroll_area)