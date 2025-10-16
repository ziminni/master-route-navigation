from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)


# ============================================================
# Collapsible Nav Section
# - Represents a sidebar section with a main button
# - Can expand/collapse to show its sub-items
# ============================================================
class CollapsibleSection(QFrame):
    def __init__(self, icon, text, sub_items=None, parent_sidebar=None):
        super().__init__()
        self.parent_sidebar = parent_sidebar   # reference to Sidebar
        self.is_open = False                   # state (expanded/collapsed)
        self.sub_items = sub_items or []       # optional sub-item list

        # ---------------- Main Button ----------------
        self.main_btn = QPushButton(f"{icon}  {text}")
        self.main_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.main_btn.setStyleSheet(
            "QPushButton {background:transparent;color:white;font-weight:bold;font-size:14px;text-align:left;padding:10px;}"
            "QPushButton:hover {background:rgba(255,255,255,40);}"
        )
        self.main_btn.clicked.connect(self.toggle)

        # ---------------- Sub-Items Container ----------------
        self.sub_container = QFrame()
        self.sub_layout = QVBoxLayout(self.sub_container)
        self.sub_layout.setContentsMargins(40, 0, 0, 0)  # indent sub-items
        self.sub_layout.setSpacing(0)

        # Create sub-item buttons
        for sub in self.sub_items:
            btn = QPushButton(sub)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                "QPushButton {background:transparent;color:#b8c5ba;font-size:13px;text-align:left;padding:6px;}"
                "QPushButton:hover {background:rgba(255,255,255,30);}"
            )
            self.sub_layout.addWidget(btn)

        self.sub_container.setVisible(False)  # hidden by default

        # ---------------- Layout for Section ----------------
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.main_btn)
        lay.addWidget(self.sub_container)

    # ========================================================
    # Expand/Collapse logic
    # ========================================================
    def toggle(self):
        if self.parent_sidebar.is_collapsed:
            # If sidebar is collapsed, expand it automatically
            self.parent_sidebar.toggleDrawer(force_open=True)
            self.open()
        else:
            # Toggle sub-container visibility
            self.is_open = not self.is_open
            self.sub_container.setVisible(self.is_open)

    def open(self):
        """Force open the sub-items"""
        self.is_open = True
        self.sub_container.setVisible(True)

    def close(self):
        """Force close the sub-items"""
        self.is_open = False
        self.sub_container.setVisible(False)


# ============================================================
# Sidebar
# - Contains header (logo + toggle button)
# - Contains multiple CollapsibleSections
# - Can expand/collapse as a whole drawer
# ============================================================
class Sidebar(QFrame):
    def __init__(self):
        super().__init__()
        self.is_collapsed = False  # drawer state (expanded by default)

        # ---------------- Sidebar Style ----------------
        self.setFixedWidth(280)               # default width
        self.setStyleSheet("background:#1e4d2b;")

        # Main vertical layout for sidebar
        self.v = QVBoxLayout(self)
        self.v.setContentsMargins(0, 0, 0, 0)
        self.v.setSpacing(0)
        self.v.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ---------------- Header Section ----------------
        top = QFrame()
        top.setFixedHeight(50)  # Reduced from 60 to 50 pixels for a more compact header
        top.setStyleSheet("""
            background: #ffc107;
            border-bottom: 1px solid #e0a800;  /* Add a subtle border at the bottom */
        """)

        h = QHBoxLayout(top)
        h.setContentsMargins(15, 0, 15, 0)

        # Drawer toggle button (hamburger ☰)
        self.toggle_btn = QPushButton("☰")
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setStyleSheet(
            "QPushButton {background:transparent;font-size:18px;}"
            "QPushButton:hover {color:#333;}"
        )
        self.toggle_btn.clicked.connect(self.toggleDrawer)

        # Header content (toggle + title)
        h.addWidget(self.toggle_btn)
        h.addWidget(QLabel("Virtual Hub"))

        # Add header to sidebar
        self.v.addWidget(top)

        # ---------------- Sidebar Sections ----------------
        self.sections = []
        self.sections.append(CollapsibleSection("🏠", "Dashboard", ["Dashboard"], self))
        self.sections.append(CollapsibleSection("📚", "Academics", ["Classes", "Schedule", "Progress", "Appointments"], self))
        self.sections.append(CollapsibleSection("👥", "Organizations", ["Browser", "Membership", "Events"], self))
        self.sections.append(CollapsibleSection("🏫", "Campus", ["Calendar", "Announcement", "House System", "Showcase"], self))
        self.sections.append(CollapsibleSection("🛠️", "Tools", ["Documents", "Messages", "Student Service"], self))

        # Add sections to sidebar
        for section in self.sections:
            self.v.addWidget(section)


    # ========================================================
    # Sidebar Toggle Logic
    # - Expands/collapses drawer
    # ========================================================
    def toggleDrawer(self, force_open=False):
        if self.is_collapsed or force_open:
            # ---------------- Expand Drawer ----------------
            self.setFixedWidth(280)
            self.is_collapsed = False
            for section in self.sections:
                section.close()  # close dropdowns
                section.main_btn.setText(section.main_btn.text())  # restore text
        else:
            # ---------------- Collapse Drawer ----------------
            self.setFixedWidth(70)
            self.is_collapsed = True
            for section in self.sections:
                section.close()
                # Keep only the icon (first character before space)
                icon = section.main_btn.text().split()[0]
                section.main_btn.setText(icon)
