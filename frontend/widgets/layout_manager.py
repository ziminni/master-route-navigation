from PyQt6.QtWidgets import QGridLayout, QWidget, QVBoxLayout, QStackedWidget
from PyQt6.QtCore import Qt
from widgets.sidebar import Sidebar
from widgets import header

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
        self.pages = {}
        
        # CRITICAL FIX: Create container widgets ONCE
        self.content_container = None
        self.header_container = None
        self.stack_container = None
        self.current_layout_mode = None  # Track current mode
        
        self._init_stack(content)  
        
        print(f"LayoutManager: Initialized with user_role '{user_role}', content widget: {type(self.content).__name__}, visible: {self.content.isVisible()}")

        self.navbar = Sidebar(self.router, self.user_role)
        print(f"LayoutManager: Created Sidebar, visible: {self.navbar.isVisible()}, collapsed: {self.navbar.is_collapsed}")

        self.header = header.Header(
            session=getattr(self.router, "user_session", {}),
            user=getattr(self.router, "user", {}),
        )
        print(f"LayoutManager: Created Header, visible: {self.header.isVisible()}")
        self.header.profileRequested.connect(self._open_profile)
        self.header.logoutRequested.connect(self._logout)

        self.apply_desktop_layout()
        
        # Connect sidebar toggle AFTER desktop layout is applied
        # This ensures content_container exists before we try to update it
        self.navbar.toggled.connect(self.on_sidebar_toggled)

    def _init_stack(self, content):
        """Ensure we have a QStackedWidget to add pages into."""
        if isinstance(content, QStackedWidget):
            self.stack = content
        else:
            self.stack = QStackedWidget()
            self.stack.addWidget(content)
            self.content = self.stack

    def update_layout(self, width):
        """FIXED: Update layout without recreating widgets"""
        print(f"LayoutManager: Updating layout with window_width {width}")
        
        # Determine target mode
        should_be_mobile = width <= self.breakpoint[0]
        target_mode = "mobile" if should_be_mobile else "desktop"
        
        # Only rebuild if mode actually changed
        if self.current_layout_mode == target_mode:
            print(f"LayoutManager: Already in {target_mode} mode, no rebuild needed")
            # Just update sidebar width if needed
            if not should_be_mobile and self.navbar:
                if self.navbar.is_collapsed:
                    self.main_layout.setColumnMinimumWidth(0, 70)
                else:
                    self.main_layout.setColumnMinimumWidth(0, 280)
            return
        
        print(f"LayoutManager: Switching from {self.current_layout_mode} to {target_mode}")
        
        # Clear layout safely
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)  # Unparent but don't delete
                print(f"LayoutManager: Removed widget {type(widget).__name__} from layout")

        # Apply new layout
        if should_be_mobile:
            self.apply_mobile_layout()
        else:
            self.apply_desktop_layout()
        
        self.current_layout_mode = target_mode
        
        # Force update
        self.content.update()
        if self.navbar:
            self.navbar.update()
        if self.header:
            self.header.update()
        
        print(f"LayoutManager: Layout updated to {target_mode}, content visible: {self.content.isVisible()}, navbar visible: {self.navbar.isVisible()}, header visible: {self.header.isVisible()}")

    def apply_desktop_layout(self):
        """FIXED: Reuse containers instead of recreating them"""
        print("LayoutManager: Applying desktop layout")
        
        if not self.navbar:
            self.navbar = Sidebar(self.router, self.user_role)
            self.navbar.setContentsMargins(0, 0, 0, 0)
            print(f"LayoutManager: Created Sidebar")

        if not self.header:
            self.header = header.Header(
                session=getattr(self.router, "user_session", {}),
                user=getattr(self.router, "user", {}),
            )
            self.header.profileRequested.connect(self._open_profile)
            self.header.logoutRequested.connect(self._logout)
            print(f"LayoutManager: Created Header")

        # Create or reuse content container
        if self.content_container is None:
            self.content_container = QWidget()
            content_layout = QVBoxLayout(self.content_container)
            # FIXED: Use consistent margins regardless of sidebar state
            content_layout.setContentsMargins(10, 0, 10, 10)
            content_layout.setSpacing(10)
            
            # Header container
            self.header_container = QWidget()
            self.header_container.setStyleSheet("background: transparent;")
            header_layout = QVBoxLayout(self.header_container)
            header_layout.setContentsMargins(12, 0, 12, 12)
            header_layout.addWidget(self.header)
            content_layout.addWidget(self.header_container)
            
            # Stack container
            self.stack_container = QWidget()
            stack_layout = QVBoxLayout(self.stack_container)
            # FIXED: Keep consistent left margin
            stack_layout.setContentsMargins(20, 0, 0, 0)
            stack_layout.setSpacing(0)
            stack_layout.addWidget(self.content)
            content_layout.addWidget(self.stack_container, 1)
            
            self.content_container.setStyleSheet("background: #ffffff;")
        else:
            # Ensure widgets are properly parented (in case they were unparented)
            if self.header.parent() != self.header_container:
                layout = self.header_container.layout()
                if layout and layout.count() == 0:
                    layout.addWidget(self.header)
            
            if self.content.parent() != self.stack_container:
                layout = self.stack_container.layout()
                if layout and layout.count() == 0:
                    layout.addWidget(self.content)
            
            # FIXED: Reset margins to consistent values
            self.content_container.layout().setContentsMargins(10, 0, 10, 10)

        # Add widgets to main layout
        self.main_layout.addWidget(self.navbar, 0, 0, 2, 1)
        self.main_layout.addWidget(self.content_container, 0, 1, 2, 1)

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

        # Remove spacing between columns
        self.main_layout.setHorizontalSpacing(0)
        self.main_layout.setVerticalSpacing(0)

        # Ensure everything is visible
        self.navbar.show()
        self.content_container.show()
        self.header.show()
        self.content.show()
        
        self.main_layout.invalidate()
        print("LayoutManager: Desktop layout applied")

    def apply_mobile_layout(self):
        """FIXED: Reuse containers instead of recreating them"""
        print("LayoutManager: Applying mobile layout")
        
        if not self.navbar:
            self.navbar = Sidebar(self.router, self.user_role)
            self.navbar.setContentsMargins(0, 0, 0, 0)
            print(f"LayoutManager: Created Sidebar")

        if not self.header:
            self.header = header.Header(
                session=getattr(self.router, "user_session", {}),
                user=getattr(self.router, "user", {}),
            )
            self.header.profileRequested.connect(self._open_profile)
            self.header.logoutRequested.connect(self._logout)
            print(f"LayoutManager: Created Header")

        # Create or reuse content container
        if self.content_container is None:
            self.content_container = QWidget()
            content_layout = QVBoxLayout(self.content_container)
            content_layout.setContentsMargins(0, 12, 20, 20)
            content_layout.setSpacing(20)
            
            # Header container
            self.header_container = QWidget()
            self.header_container.setStyleSheet("background: transparent;")
            header_layout = QVBoxLayout(self.header_container)
            header_layout.setContentsMargins(12, 12, 12, 12)
            header_layout.addWidget(self.header)
            content_layout.addWidget(self.header_container)
            
            # Stack container
            self.stack_container = QWidget()
            stack_layout = QVBoxLayout(self.stack_container)
            stack_layout.setContentsMargins(20, 0, 0, 0)
            stack_layout.setSpacing(0)
            stack_layout.addWidget(self.content)
            content_layout.addWidget(self.stack_container, 1)
            
            self.content_container.setStyleSheet("background: #ffffff;")
        else:
            # Ensure widgets are properly parented
            if self.header.parent() != self.header_container:
                layout = self.header_container.layout()
                if layout and layout.count() == 0:
                    layout.addWidget(self.header)
            
            if self.content.parent() != self.stack_container:
                layout = self.stack_container.layout()
                if layout and layout.count() == 0:
                    layout.addWidget(self.content)

        # Add widgets to main layout
        self.main_layout.addWidget(self.content_container, 0, 0, 1, 1)
        self.main_layout.addWidget(self.navbar, 1, 0, 1, 1)
        self.main_layout.setRowStretch(0, 3)
        self.main_layout.setRowStretch(1, 1)
        self.navbar.setFixedHeight(100)
        
        # Ensure everything is visible
        self.navbar.show()
        self.content_container.show()
        self.header.show()
        self.content.show()
        
        print("LayoutManager: Mobile layout applied")

    def on_sidebar_toggled(self, is_collapsed):
        """Handle sidebar collapse/expand - dynamically adjust spacing"""
        print(f"LayoutManager: Sidebar toggled, collapsed={is_collapsed}")
        
        if self.current_layout_mode == "desktop":
            # FIXED: Only adjust column width, keep margins consistent
            if is_collapsed:
                self.main_layout.setColumnMinimumWidth(0, 70)
                print("LayoutManager: Adjusted for collapsed sidebar")
            else:
                self.main_layout.setColumnMinimumWidth(0, 280)
                print("LayoutManager: Adjusted for expanded sidebar")
            
            # Force layout update without changing margins
            self.main_layout.update()
        else:
            print("LayoutManager: Not in desktop mode, skipping adjustment")

    def _open_profile(self):
        try:
            from views.Login.user_profile import ProfileWidget
        except Exception:
            from frontend.views.Login.user_profile import ProfileWidget

        session = getattr(self.router, "user_session", {}) or {}
        user = getattr(self.router, "user", {}) or {}

        w = getattr(self, "pages", {}).get("profile")
        if w is None:
            if not hasattr(self, "pages"):
                self.pages = {}
            w = ProfileWidget(session=session, user=user)
            self.stack.addWidget(w)
            self.pages["profile"] = w
        else:
            if w.session.get("token") != session.get("token"):
                w.session = session
            w._populate_from_session_then_me()
            w.load_resume()

        self.stack.setCurrentWidget(w)

    def _logout(self):
        try:
            self.header.profile_menu.hide()
        except Exception:
            pass
        self.router.request_full_logout()