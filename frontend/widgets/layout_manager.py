from PyQt6.QtWidgets import QGridLayout, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
from widgets.sidebar import Sidebar
from widgets import header  # Assuming header module contains the Header class

class LayoutManager:
    def __init__(self, main_layout, content, router, user_role):
        self.main_layout = main_layout
        self.content = content
        self.router = router
        self.user_role = user_role
        self.navbar = None
        self.header = None
        self.breakpoint = [600]
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        print(f"LayoutManager: Initialized with user_role '{user_role}', content widget: {type(self.content).__name__}, visible: {self.content.isVisible()}")

        self.navbar = Sidebar(self.router, self.user_role)
        print(f"LayoutManager: Created Sidebar, visible: {self.navbar.isVisible()}, collapsed: {self.navbar.is_collapsed}")

        self.header = header.Header()
        print(f"LayoutManager: Created Header, visible: {self.header.isVisible()}")

        self.apply_desktop_layout()

    def update_layout(self, width):
        print(f"LayoutManager: Updating layout with window_width {width}")
        current_is_mobile = self.main_layout.itemAtPosition(1, 0) is not None
        should_be_mobile = width <= self.breakpoint[0]

        if current_is_mobile != should_be_mobile:
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
            if not should_be_mobile:
                self.apply_desktop_layout()
            print("LayoutManager: No layout mode change needed")

        self.content.update()
        self.navbar.update()
        self.header.update()
        print(f"LayoutManager: Updated layout, content visible: {self.content.isVisible()}, navbar visible: {self.navbar.isVisible()}, header visible: {self.header.isVisible()}")

    def apply_desktop_layout(self):
        print("LayoutManager: Applying desktop layout")
        if not self.navbar:
            self.navbar = Sidebar(self.router, self.user_role)
            self.navbar.setContentsMargins(0, 0, 0, 0)
            print(f"LayoutManager: Created Sidebar, visible: {self.navbar.isVisible()}, collapsed: {self.navbar.is_collapsed}")

        if not self.header:
            self.header = header.Header()
            print(f"LayoutManager: Created Header, visible: {self.header.isVisible()}")

        # Create content container with header and stacked widget
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(10, 0, 10, 10)  # sidebar & header margin
        content_layout.setSpacing(10)

        # Add header with its own container for styling
        header_container = QWidget()
        header_container.setStyleSheet("background: transparent;")
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(12, 0, 12, 12)  # Add padding for shadow
        header_layout.addWidget(self.header)
        content_layout.addWidget(header_container)

        # Add stacked widget
        stack_container = QWidget()
        stack_layout = QVBoxLayout(stack_container)
        stack_layout.setContentsMargins(20, 0, 0, 0)
        stack_layout.setSpacing(0)
        stack_layout.addWidget(self.content)
        content_layout.addWidget(stack_container, 1)

        # Add widgets to main layout
        self.main_layout.addWidget(self.navbar, 0, 0, 2, 1)
        self.main_layout.addWidget(content_container, 0, 1, 2, 1)

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

        content_container.setStyleSheet("background: #ffffff;")
        self.main_layout.invalidate()
        print("LayoutManager: Desktop layout applied")

    def apply_mobile_layout(self):
        print("LayoutManager: Applying mobile layout")
        if not self.navbar:
            self.navbar = Sidebar(self.router, self.user_role)
            self.navbar.setContentsMargins(0, 0, 0, 0)
            print(f"LayoutManager: Created Sidebar, visible: {self.navbar.isVisible()}, collapsed: {self.navbar.is_collapsed}")

        if not self.header:
            self.header = header.Header()
            print(f"LayoutManager: Created Header, visible: {self.header.isVisible()}")

        # Create content container with header and stacked widget
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 12, 20, 20)  # Add top padding for shadow
        content_layout.setSpacing(20)

        # Add header with its own container for styling
        header_container = QWidget()
        header_container.setStyleSheet("background: transparent;")
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(12, 12, 12, 12)  # Add padding for shadow
        header_layout.addWidget(self.header)
        content_layout.addWidget(header_container)

        # Add stacked widget
        stack_container = QWidget()
        stack_layout = QVBoxLayout(stack_container)
        stack_layout.setContentsMargins(20, 0, 0, 0)
        stack_layout.setSpacing(0)
        stack_layout.addWidget(self.content)
        content_layout.addWidget(stack_container, 1)

        # Add widgets to main layout
        self.main_layout.addWidget(content_container, 0, 0, 1, 1)
        self.main_layout.addWidget(self.navbar, 1, 0, 1, 1)
        self.main_layout.setRowStretch(0, 3)
        self.main_layout.setRowStretch(1, 1)
        self.navbar.setFixedHeight(100)
        content_container.setStyleSheet("background: #ffffff;")
        print("LayoutManager: Mobile layout applied")