import os
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMenu, QScrollArea, QWidget, QSizePolicy
from utils.db_helper import get_all_parents, get_main_by_parent, get_modular_by_main, get_access_level

class CollapsibleSection(QFrame):
    def __init__(self, icon, text, router, user_role, parent_sidebar=None,
                sub_indent=20, sub_spacing=2, sub_button_padding=8):
        super().__init__()
        self.router = router
        self.user_role = user_role
        self.parent_sidebar = parent_sidebar
        self.is_open = False
        self.sub_items = []
        self.full_button_text = f"{icon}  {text}"
        self.icon = icon
        self.sub_button_padding = sub_button_padding

        print(f"CollapsibleSection: Creating section '{text}' with user_role '{user_role}'")

        # Main Button - Full width clickable
        self.main_btn = QPushButton()
        self.main_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.main_btn.setObjectName("sectionMainButton")
        self.main_btn.clicked.connect(self.toggle)
        # Set button text based on sidebar collapse state
        if self.parent_sidebar and self.parent_sidebar.is_collapsed:
            self.main_btn.setText(self.icon)
            print(f"CollapsibleSection: Set button text to icon '{self.icon}' for collapsed sidebar")
        else:
            self.main_btn.setText(self.full_button_text)
            print(f"CollapsibleSection: Set button text to '{self.full_button_text}'")

        # Sub-Items Container
        self.sub_container = QFrame()
        self.sub_container.setObjectName("subContainer")
        self.sub_layout = QVBoxLayout(self.sub_container)
        self.sub_layout.setContentsMargins(0, 5, 0, 5)
        self.sub_layout.setSpacing(1)
        self.sub_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        # Populate sub-items from database, filtered by access
        parents = get_all_parents()
        print(f"CollapsibleSection: Found {len(parents)} parents: {parents}")
        for parent_id, parent_name in parents:
            if parent_name == text:
                mains = get_main_by_parent(parent_id)
                print(f"CollapsibleSection: Found {len(mains)} mains for parent '{parent_name}': {mains}")
                for main_id, main_name, _, access, _ in mains:
                    # Check if user_role is in access (string or list)
                    if (isinstance(access, str) and (access == self.user_role or self.user_role == "super_admin")) or \
                    (isinstance(access, list) and (self.user_role in access or self.user_role == "super_admin")):
                        print(f"CollapsibleSection: Adding main '{main_name}' (ID: {main_id}) to section '{text}'")

                        # Container for the sub-item row
                        row_container = QFrame()
                        row_container.setObjectName("subRowContainer")

                        row_layout = QHBoxLayout(row_container)
                        row_layout.setContentsMargins(0, 0, 0, 0)
                        row_layout.setSpacing(0)

                        # Main clickable button that spans most of the width
                        main_sub_btn = QPushButton(main_name)
                        main_sub_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                        main_sub_btn.setObjectName("subMainButton")
                        main_sub_btn.setStyleSheet(f"padding: {sub_button_padding}px 35px;")
                        main_sub_btn.clicked.connect(lambda checked, id=main_id: self.router.navigate(id))

                        row_layout.addWidget(main_sub_btn, 1)  # Takes up most space

                        # Optional popup button for modulars
                        modulars = get_modular_by_main(main_id)
                        print(f"CollapsibleSection: Found {len(modulars)} modulars for main '{main_name}': {modulars}")
                        if modulars:
                            # Filter modulars by inherited access
                            filtered_modulars = [
                                mod for mod in modulars
                                if (isinstance(access, str) and (access == self.user_role or self.user_role == "super_admin")) or
                                (isinstance(access, list) and (self.user_role in access or self.user_role == "super_admin"))
                            ]
                            print(f"CollapsibleSection: Filtered {len(filtered_modulars)} modulars for main '{main_name}': {filtered_modulars}")
                            if filtered_modulars:
                                popup_btn = QPushButton("▶")
                                popup_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                                popup_btn.setObjectName("popupButton")
                                popup_btn.clicked.connect(lambda _, mods=filtered_modulars, mid=main_id: self.show_house_system_popup(popup_btn, mods, mid))
                                row_layout.addWidget(popup_btn, 0)

                        self.sub_layout.addWidget(row_container)
                        self.sub_items.append(row_container)

        # Keep section closed by default, even with sub-items
        self.sub_container.setVisible(False)
        print(f"CollapsibleSection: Initialized section '{text}' with {len(self.sub_items)} sub-items, closed by default")

        # Main layout
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 2, 0, 2)
        lay.setSpacing(0)
        lay.addWidget(self.main_btn)
        lay.addWidget(self.sub_container)

    def toggle(self):
        if self.parent_sidebar.is_collapsed:
            self.parent_sidebar.toggleDrawer(force_open=True)
            self.open()
        else:
            self.is_open = not self.is_open
            self.sub_container.setVisible(self.is_open)
            print(f"CollapsibleSection: Toggled section '{self.main_btn.text()}' to {'open' if self.is_open else 'closed'}")

    def open(self):
        self.is_open = True
        self.sub_container.setVisible(True)
        self.main_btn.setText(self.full_button_text)
        print(f"CollapsibleSection: Opened section, set text to '{self.full_button_text}'")

    def close(self):
        self.is_open = False
        self.sub_container.setVisible(False)
        if self.parent_sidebar.is_collapsed:
            self.main_btn.setText(self.icon)
            print(f"CollapsibleSection: Closed section, set text to icon '{self.icon}'")
        else:
            self.main_btn.setText(self.full_button_text)
            print(f"CollapsibleSection: Closed section, set text to '{self.full_button_text}'")

    def show_house_system_popup(self, button, modulars, main_id):
        menu = QMenu(self)
        menu.setObjectName("popupMenu")

        for mod_id, mod_name, _, _ in modulars:
            menu.addAction(mod_name, lambda mid=mod_id, parent_id=main_id: self.router.navigate(mid, is_modular=True, parent_main_id=parent_id))
            print(f"CollapsibleSection: Added modular '{mod_name}' (ID: {mod_id}) to popup menu for main ID {main_id}")

        sidebar_pos = self.parent_sidebar.mapToGlobal(QPoint(0, 0))
        sidebar_width = self.parent_sidebar.width()
        button_pos = button.mapToGlobal(button.pos())
        popup_x = sidebar_pos.x() + sidebar_width + 5
        popup_y = button_pos.y()
        menu.exec(QPoint(popup_x, popup_y))

class Sidebar(QFrame):
    def __init__(self, router, user_role):
        super().__init__()
        self.is_collapsed = True  # Start collapsed
        self.router = router
        self.user_role = user_role

        print(f"Sidebar: Initializing with user_role '{user_role}', collapsed: {self.is_collapsed}")

        self.setFixedWidth(70)  # Collapsed width
        self.setObjectName("sidebarMain")

        # Load stylesheet
        self.load_stylesheet()

        # Main layout for the entire sidebar
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header - Fixed at top
        self.header = QFrame()
        self.header.setFixedHeight(65)
        self.header.setObjectName("sidebarHeader")

        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(15, 0, 15, 0)
        header_layout.setSpacing(10)

        self.toggle_btn = QPushButton("☰")
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setFixedSize(40, 40)
        self.toggle_btn.setObjectName("toggleButton")
        self.toggle_btn.clicked.connect(self.toggleDrawer)
        print(f"Sidebar: Created toggle button, visible: {self.toggle_btn.isVisible()}")

        self.header_label = QLabel("Virtual Hub")
        self.header_label.setObjectName("sidebarHeaderLabel")
        self.header_label.setVisible(False)  # Hidden when collapsed

        header_layout.addWidget(self.toggle_btn)
        header_layout.addWidget(self.header_label)
        header_layout.addStretch()

        # Create a green background frame that will fill remaining space
        self.green_background = QFrame()
        self.green_background.setObjectName("sidebarGreenBackground")

        # Layout for the green background
        green_layout = QVBoxLayout(self.green_background)
        green_layout.setContentsMargins(0, 0, 0, 0)
        green_layout.setSpacing(0)

        # Scrollable content area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setObjectName("sidebarScrollArea")

        # Content widget inside scroll area
        self.content_widget = QWidget()
        self.content_widget.setObjectName("sidebarContent")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 8, 0, 20)
        self.content_layout.setSpacing(0)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Add sections to content
        self.sections = []
        parents = get_all_parents()
        print(f"Sidebar: Found {len(parents)} parents: {parents}")
        for parent_id, parent_name in parents:
            mains = get_main_by_parent(parent_id)
            print(f"Sidebar: Found {len(mains)} mains for parent '{parent_name}': {mains}")
            has_accessible_main = any(
                (isinstance(access, str) and (access == self.user_role or self.user_role == "super_admin")) or
                (isinstance(access, list) and (self.user_role in access or self.user_role == "super_admin"))
                for _, _, _, access, _ in mains
            )
            if has_accessible_main:
                icon_map = {
                    "Dashboard": "🏠",
                    "Academics": "📚", 
                    "Organizations": "👥",
                    "Campus": "🏫",
                }
                icon = icon_map.get(parent_name, "🛠️")

                section = CollapsibleSection(icon, parent_name, self.router, self.user_role, self)
                self.sections.append(section)
                self.content_layout.addWidget(section)
                print(f"Sidebar: Added section '{parent_name}' with icon '{icon}'")

        self.content_layout.addStretch()

        # Set content widget to scroll area
        self.scroll_area.setWidget(self.content_widget)

        # Add scroll area to green background
        green_layout.addWidget(self.scroll_area)

        # Add header and green background to main layout
        main_layout.addWidget(self.header)
        main_layout.addWidget(self.green_background, 1)  # Expand to fill remaining space

    def load_stylesheet(self):
        """Load the QSS stylesheet from file"""
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            qss_path = os.path.join(project_root, 'assets', 'qss', 'sidebar_styles.qss')
            with open(qss_path, 'r', encoding='utf-8') as file:
                stylesheet = file.read()
                print("Sidebar: Loaded stylesheet from sidebar_styles.qss")

            mapped_stylesheet = stylesheet.replace('.sidebar-main', '#sidebarMain') \
                                        .replace('.sidebar-green-background', '#sidebarGreenBackground') \
                                        .replace('.sidebar-header', '#sidebarHeader') \
                                        .replace('.sidebar-header-label', '#sidebarHeaderLabel') \
                                        .replace('.toggle-button', '#toggleButton') \
                                        .replace('.section-main-button', '#sectionMainButton') \
                                        .replace('.sub-container', '#subContainer') \
                                        .replace('.sub-row-container', '#subRowContainer') \
                                        .replace('.sub-main-button', '#subMainButton') \
                                        .replace('.popup-button', '#popupButton') \
                                        .replace('.sidebar-scroll-area', '#sidebarScrollArea') \
                                        .replace('.sidebar-content', '#sidebarContent') \
                                        .replace('.popup-menu', '#popupMenu')

            self.setStyleSheet(mapped_stylesheet)
            print("Sidebar: Applied mapped stylesheet")

        except FileNotFoundError:
            print(f"Warning: Could not find sidebar_styles.qss at {qss_path}")
            print("Using fallback inline styles...")
            self.setStyleSheet("""
                #sidebarMain { background: #1e4d2b; border: none; }
                #sidebarHeader { background: #ffc107; border-bottom: 2px solid #e6ac00; }
                #sidebarHeaderLabel { background: transparent; color: #333333; font-size: 16px; font-weight: bold; }
                #toggleButton { background: transparent; color: #333; font-size: 18px; border-radius: 6px; }
                #toggleButton:hover { background: rgba(51,51,51,0.1); }
                #sectionMainButton { color: white; text-align: left; padding: 10px; }
                #subContainer { background: transparent; }
                #subRowContainer { background: transparent; }
                #subMainButton { color: white; text-align: left; }
                #popupButton { color: white; }
                #sidebarScrollArea { background: transparent; }
                #sidebarContent { background: transparent; }
            """)
        except Exception as e:
            print(f"Error loading stylesheet: {e}")
            self.setStyleSheet("#sidebarMain { background: #1e4d2b; }")

    def toggleDrawer(self, force_open=False):
        if self.is_collapsed or force_open:
            # Expand
            self.setFixedWidth(280)
            self.is_collapsed = False
            self.header_label.setVisible(True)
            for section in self.sections:
                section.close()
                section.main_btn.setText(section.full_button_text)
            print("Sidebar: Expanded")
        else:
            # Collapse
            self.setFixedWidth(70)
            self.is_collapsed = True
            self.header_label.setVisible(False)
            for section in self.sections:
                section.close()
                section.main_btn.setText(section.icon)
            print("Sidebar: Collapsed")

        # Notify parent to update layout
        self.updateGeometry()
        if self.parentWidget() and self.parentWidget().layout():
            self.parentWidget().layout().invalidate()
            self.parentWidget().updateGeometry()
            self.parentWidget().update()