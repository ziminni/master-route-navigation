from PyQt6.QtWidgets import QGridLayout, QWidget
from PyQt6.QtCore import Qt
from widgets.sidebar import Sidebar

class LayoutManager:
    def __init__(self, main_layout, content, router, user_role):
        self.main_layout = main_layout  # QGridLayout of the main widget
        self.content = content          # QStackedWidget for pages
        self.router = router            # Router instance
        self.user_role = user_role      # Store user role
        self.navbar = None              # Sidebar will be created when needed
        self.breakpoint = [600]         # Resolution threshold (pixels)
        self.main_layout.setContentsMargins(0, 0, 0, 0)  # No margins
        self.main_layout.setSpacing(0)                  # No spacing
        print(f"LayoutManager: Initialized with user_role '{user_role}', content widget: {type(self.content).__name__}, visible: {self.content.isVisible()}")

        # Initialize sidebar
        self.navbar = Sidebar(self.router, self.user_role)
        print(f"LayoutManager: Created Sidebar, visible: {self.navbar.isVisible()}, collapsed: {self.navbar.is_collapsed}")

        # Apply initial desktop layout
        self.apply_desktop_layout()

    def update_layout(self, width):
        """Update the layout based on window width."""
        print(f"LayoutManager: Updating layout with window_width {width}")
        current_is_mobile = self.main_layout.itemAtPosition(1, 0) is not None
        should_be_mobile = width <= self.breakpoint[0]

        if current_is_mobile != should_be_mobile:
            # Clear layout only when switching modes
            while self.main_layout.count():
                item = self.main_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.setParent(None)
                    print(f"LayoutManager: Removed widget {type(widget).__name__} from layout")

            if should_be_mobile:
                self.apply_mobile_layout()
            else:
                self.apply_desktop_layout()
        else:
            # Adjust desktop layout for sidebar collapse state
            if not should_be_mobile:
                self.apply_desktop_layout()
            print("LayoutManager: No layout mode change needed")

        self.content.update()
        self.navbar.update()
        print(f"LayoutManager: Updated layout, content visible: {self.content.isVisible()}, navbar visible: {self.navbar.isVisible()}")

    def apply_desktop_layout(self):
        """Apply layout for larger screens (navbar on left)."""
        print("LayoutManager: Applying desktop layout")
        if not self.navbar:
            self.navbar = Sidebar(self.router, self.user_role)
            self.navbar.setContentsMargins(0, 0, 0, 0)
            print(f"LayoutManager: Created Sidebar, visible: {self.navbar.isVisible()}, collapsed: {self.navbar.is_collapsed}")

        self.main_layout.addWidget(self.navbar, 0, 0, 2, 1)
        self.main_layout.addWidget(self.content, 0, 1, 2, 1)
        
        # Adjust column widths based on sidebar collapse state
        if self.navbar.is_collapsed:
            self.main_layout.setColumnMinimumWidth(0, 70)
            self.main_layout.setColumnStretch(0, 0)
            self.main_layout.setColumnStretch(1, 1)
            print("LayoutManager: Adjusted for collapsed sidebar (70px)")
        else:
            self.main_layout.setColumnMinimumWidth(0, 280)
            self.main_layout.setColumnStretch(0, 0)
            self.main_layout.setColumnStretch(1, 1)
            print("LayoutManager: Adjusted for expanded sidebar (280px)")

        self.content.setStyleSheet("background: #ffffff;")
        self.main_layout.invalidate()
        print("LayoutManager: Desktop layout applied")

    def apply_mobile_layout(self):
        """Apply layout for smaller screens (navbar at bottom)."""
        print("LayoutManager: Applying mobile layout")
        if not self.navbar:
            self.navbar = Sidebar(self.router, self.user_role)
            self.navbar.setContentsMargins(0, 0, 0, 0)
            print(f"LayoutManager: Created Sidebar, visible: {self.navbar.isVisible()}, collapsed: {self.navbar.is_collapsed}")

        self.main_layout.addWidget(self.content, 0, 0, 1, 1)
        self.main_layout.addWidget(self.navbar, 1, 0, 1, 1)
        self.main_layout.setRowStretch(0, 3)
        self.main_layout.setRowStretch(1, 1)
        self.navbar.setFixedHeight(100)
        self.content.setStyleSheet("background: #ffffff;")
        print("LayoutManager: Mobile layout applied")