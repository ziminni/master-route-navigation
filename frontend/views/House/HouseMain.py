import sys
import os
import json
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.append(project_root)
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QFont, QFontDatabase, QFontMetrics
import urllib.request

from .HousesPage import HousesPage, HouseCard

# Import OverviewPage
try:
    from .OverviewPage import OverviewPage
except ImportError:
    class OverviewPage(QWidget):
        def __init__(self, username, roles, primary_role, token, house_name):
            super().__init__()
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel(f"Overview Page for {house_name}"))

try:
    from .EventsPage import EventsPage
except ImportError:
    class EventsPage(QWidget):
        def __init__(self, username, roles, primary_role, token, house_name):
            super().__init__()
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel(f"Events Page for {house_name}"))

try:
    from .MembersPage import MembersPage
except ImportError as e:
    class MembersPage(QWidget):
        def __init__(self, username, roles, primary_role, token, house_name):
            super().__init__()
            layout = QVBoxLayout(self)  
            layout.addWidget(QLabel(f"Members Page for {house_name}"))

try:
    from .HistoryPage import HistoryPage
except ImportError:
    class HistoryPage(QWidget):
        def __init__(self, username, roles, primary_role, token, house_name):
            super().__init__()
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel(f"History Page for {house_name}"))


from .LeaderboardPage import LeaderboardPage

try:
    from .AdminCreateHousePage import AdminCreateHousePage
except Exception:
    class AdminCreateHousePage(QWidget):
        def __init__(self, token=None, api_base=None, parent=None):
            super().__init__(parent)
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Admin Create House (missing module)"))


class NavigationBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Nav container
        self.nav_container = QWidget()
        self.nav_container.setObjectName("navContainer")
        self.nav_container.setFixedHeight(50)
        nav_row = QHBoxLayout(self.nav_container)
        nav_row.setContentsMargins(0, 0, 0, 0)
        nav_row.setSpacing(20)

        # Load nav items
        navjson_path = os.path.join("data", "navbar.json")
        try:
            with open(navjson_path, "r", encoding="utf-8") as f:
                navdata = json.load(f)
        except Exception:
            navdata = {"tabs": ["Overview", "Events", "Members", "History", "Leaderboards"], "active": "Overview"}

        active_tab = navdata.get("active", "Overview")
        self.nav_buttons = {}
        # Calculate button widths based on text content
        temp_font = QFont("Poppins", 18, QFont.Weight.Normal)
        temp_metrics = QFontMetrics(temp_font)
        
        for tab in navdata.get("tabs", []):
            btn = QPushButton(tab)
            btn.setCheckable(True)
            btn.setChecked(tab == active_tab)
            btn.setObjectName("navButton")
            # Calculate width needed for text + padding
            text_width = temp_metrics.horizontalAdvance(tab)
            btn.setMinimumWidth(text_width + 20)  # Add 20px padding
            btn.setMaximumWidth(text_width + 20)
            self.nav_buttons[tab] = btn
            nav_row.addWidget(btn)

        nav_row.addStretch()

        # Divider line
        self.divider = QWidget()
        self.divider.setFixedHeight(2)
        self.divider.setObjectName("dividerLine")
        self.divider.setStyleSheet("""
            QWidget#dividerLine {
                background-color: #084924;
                border: none;
            }
        """)

        self.layout.addWidget(self.nav_container)
        self.layout.addWidget(self.divider)

        # Yellow underline
        self.nav_highlight = QWidget(self)
        self.nav_highlight.setObjectName("navHighlight")
        self.nav_highlight.setFixedHeight(12)
        self.nav_highlight.setStyleSheet("""
            QWidget#navHighlight {
                background-color: #FDC601;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
        """)
        self.nav_highlight.hide()
        self._current_anim = None  # Track current animation

        # Apply styles
        self.setStyleSheet("""
            QPushButton#navButton {
                height: 31px;
                font-family: 'Poppins';
                font-weight: 310;
                font-style: normal;
                font-size: 18px;
                line-height: 52.8px;
                letter-spacing: 0%;
                color: #084924;
                text-align: center;
                background: transparent;
                border: none;
            }

            QPushButton#navButton:checked {
                font-weight: 600;
            }

            QPushButton#navButton:hover {
                color: #0B6630;
            }
        """)

    def set_active_tab(self, tab_name):
        # Show the yellow bar if it was hidden
        if not self.nav_highlight.isVisible():
            self.nav_highlight.show()
            self.nav_highlight.raise_()

        active_button = None
        for name, btn in self.nav_buttons.items():
            is_active = (name == tab_name)
            btn.setChecked(is_active)
            if is_active:
                active_button = btn
        
        if active_button:
            # Use QTimer.singleShot to ensure layout is complete before animating
            from PyQt6.QtCore import QTimer
            # Capture active_button in a default argument to avoid closure issues
            QTimer.singleShot(10, lambda btn=active_button: self._animate_underline(btn))

    def _animate_underline(self, active_button):
        # Ensure the widget is properly laid out before calculating positions
        if not self.isVisible():
            return
        
        # Force layout update to ensure accurate positions
        self.update()
        QWidget.repaint(self)
        
        # Get button position relative to the main NavigationBar
        # Use mapToGlobal then mapFromGlobal for more accurate positioning
        btn_global_pos = active_button.mapToGlobal(active_button.rect().topLeft())
        btn_pos = self.mapFromGlobal(btn_global_pos)
        
        metrics = active_button.fontMetrics()
        text_width = metrics.horizontalAdvance(active_button.text())
        
        # Calculate position - place it between the nav container and divider
        container_bottom = self.nav_container.geometry().bottom()
        underline_y = container_bottom - 8
        
        # Calculate x position to center under the text
        # Account for button padding/margins
        text_x = btn_pos.x() + (active_button.width() - text_width) / 2

        # Stop any existing animation
        if hasattr(self, '_current_anim') and self._current_anim:
            self._current_anim.stop()
        
        # Create animation
        anim = QPropertyAnimation(self.nav_highlight, b"geometry")
        anim.setDuration(250)
        anim.setStartValue(self.nav_highlight.geometry())
        anim.setEndValue(QRect(
            int(text_x),
            int(underline_y),
            int(text_width),
            self.nav_highlight.height()
        ))
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        anim.start()
        self._current_anim = anim  # Store reference to prevent garbage collection

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Reposition yellow bar when navbar is resized
        if self.nav_highlight.isVisible():
            active_button = None
            for name, btn in self.nav_buttons.items():
                if btn.isChecked():
                    active_button = btn
                    break
            if active_button:
                # Delay to ensure layout is updated
                from PyQt6.QtCore import QTimer
                # Capture active_button in a default argument to avoid closure issues
                QTimer.singleShot(10, lambda btn=active_button: self._animate_underline(btn))

    def showEvent(self, event):
        super().showEvent(event)
        # Initialize the yellow bar position when navbar first becomes visible
        if not self.nav_highlight.isVisible():
            # Position it under the first button but keep hidden initially
            first_btn = list(self.nav_buttons.values())[0]
            btn_pos = first_btn.mapTo(self, first_btn.rect().topLeft())
            metrics = first_btn.fontMetrics()
            text_width = metrics.horizontalAdvance(first_btn.text())
            container_bottom = self.nav_container.geometry().bottom()
            underline_y = container_bottom - 8
            text_x = btn_pos.x() + (first_btn.width() - text_width) / 2
            
            self.nav_highlight.setGeometry(QRect(
                int(text_x),
                int(underline_y),
                int(text_width),
                self.nav_highlight.height()
            ))

class HouseMain(QWidget):
    def __init__(self, username, roles, primary_role, token):
        super().__init__()
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        self.current_house = None
        self.pages = {}

        # Create main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 14, 24, 18)
        self.layout.setSpacing(10)

        # Initialize NavigationBar
        self.nav_bar = NavigationBar(self)
        self.nav_bar.setVisible(False)
        
        # Connect nav buttons
        for page_name, button in self.nav_bar.nav_buttons.items():
            button.clicked.connect(lambda checked, pn=page_name: self.navigate_to(pn))

        # Initialize QStackedWidget
        self.stack = QStackedWidget(self)
        self.stack.setStyleSheet("background-color: #f9fafb;")

        # Initialize HousesPage
        self.houses_page = HousesPage(username, roles, primary_role, token)
        self.stack.addWidget(self.houses_page)

        # Check if user is admin and show AdminCreateHousePage instead
        is_admin = False
        if isinstance(self.roles, (list, tuple)):
            is_admin = any((str(r).lower() == "admin") for r in self.roles)
        if not is_admin and isinstance(self.primary_role, str):
            is_admin = (self.primary_role.lower() == "admin")

        if is_admin:
            try:
                self.admin_page = AdminCreateHousePage(token=self.token, api_base="http://127.0.0.1:8000")
                self.stack.addWidget(self.admin_page)
                self.stack.setCurrentWidget(self.admin_page)
                self.nav_bar.setVisible(False)
            except Exception:
                pass

        # Add widgets to layout
        self.layout.addWidget(self.nav_bar)
        self.layout.addWidget(self.stack)

        # Connect signals
        self.houses_page.house_clicked.connect(self.handle_house_click)

    def handle_house_click(self, house_name):
        self.current_house = house_name
        self.nav_bar.setVisible(True)

        # Clear previous pages
        while self.stack.count() > 1:
            widget = self.stack.widget(1)
            self.stack.removeWidget(widget)
            widget.deleteLater()

        # Initialize pages
        self.pages = {
            "Overview": OverviewPage(self.username, self.roles, self.primary_role, self.token, house_name),
            "Events": EventsPage(self.username, self.roles, self.primary_role, self.token, house_name),
            "Members": MembersPage(self.username, self.roles, self.primary_role, self.token, house_name),
            "History": HistoryPage(self.username, self.roles, self.primary_role, self.token, house_name),
            "Leaderboards": LeaderboardPage(self.username, self.roles, self.primary_role, self.token, house_name),
        }

        # Add pages to stack
        for page in self.pages.values():
            self.stack.addWidget(page)

        # Navigate to Overview and trigger yellow bar animation
        self.navigate_to("Overview")

    def navigate_to(self, page_name):
        if page_name in self.pages and self.current_house:
            self.stack.setCurrentWidget(self.pages[page_name])
            self.nav_bar.set_active_tab(page_name)  # This will animate the yellow bar

    def navigate_to_houses(self):
        self.current_house = None
        self.pages = {}
        self.nav_bar.setVisible(False)
        
        self.stack.setCurrentWidget(self.houses_page)