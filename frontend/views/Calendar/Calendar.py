from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QStackedWidget,
    QPushButton, QLineEdit, QListWidget, QGridLayout, QCalendarWidget,
    QComboBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from .DayView import DayView
from .role.AdminActivities import AdminActivities
from .role.StudentActivities import StudentActivities
from .role.Staff_FacultyActivities import StaffFacultyActivities
from .CRUD.AddEvent import AddEvent
from .CRUD.EditEvent import EditEvent
from .CRUD.SearchView import SearchView
from .helper.EventCalendarWidget import EventCalendarWidget


class Calendar(QWidget):
    """Main calendar layout with all views"""

    def __init__(self, username, roles, primary_role, token):
        super().__init__()
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        self.current_view = "Month"

        # These will be set from MainCalendar
        self.navigate_to_activities = None
        self.navigate_to_search = None
        self.main_calendar = None  # set this externally so on_month_filter_changed can call filter_events()

        self.month_events_list = None
        self.upcoming_events_visible = True
        self.all_events = []

        main_layout = QVBoxLayout(self)

        self.stacked_widget = QStackedWidget()

        # Views
        self.setup_month_view()
        self.setup_day_view()

        # Activities widget based on role
        role_lower = primary_role.lower()
        if role_lower == "admin":
            self.activities_widget = AdminActivities(username, roles, primary_role, token)
        elif role_lower == "student":
            self.activities_widget = StudentActivities(username, roles, primary_role, token)
        elif role_lower in ["staff", "faculty"]:
            self.activities_widget = StaffFacultyActivities(username, roles, primary_role, token)
        else:
            self.activities_widget = self._create_default_widget(
                "Invalid Role", f"No activities available for role: {primary_role}"
            )

        # Add/Edit event widgets
        if role_lower == "admin":
            self.add_event_widget = AddEvent(username, roles, primary_role, token)
            self.edit_event_widget = EditEvent(username, roles, primary_role, token)
        else:
            self.add_event_widget = None
            self.edit_event_widget = None

        # Stack indices:
        # 0 - Month, 1 - Day, 2 - Activities, 3 - Add Event, 4 - Edit Event
        self.stacked_widget.addWidget(self.month_view_container)
        self.stacked_widget.addWidget(self.day_view_container)
        self.stacked_widget.addWidget(self.activities_widget)
        if self.add_event_widget:
            self.stacked_widget.addWidget(self.add_event_widget)
        if self.edit_event_widget:
            self.stacked_widget.addWidget(self.edit_event_widget)

        main_layout.addWidget(self.stacked_widget)

        self.setup_navigation()
        self.connect_signals()

        self.show_month_view()

    # ---------- Month view ----------

    def setup_month_view(self):
        """Setup month calendar view with controls and upcoming events."""
        self.month_view_container = QWidget()
        container_layout = QVBoxLayout(self.month_view_container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(15)

        # Top controls
        self.setup_controls(container_layout)

        # Content: left upcoming panel, right calendar
        self.content_layout = QHBoxLayout()

        self.month_upcoming_panel = self.create_upcoming_events_panel()
        self.calendar_widget = self.create_calendar_grid()

        self.content_layout.addWidget(self.month_upcoming_panel)
        self.content_layout.addWidget(self.calendar_widget)

        container_layout.addLayout(self.content_layout)

    def create_calendar_grid(self):
        """Create calendar grid widget with styled QCalendarWidget."""
        calendar_container = QWidget()
        calendar_layout = QVBoxLayout(calendar_container)
        calendar_layout.setContentsMargins(0, 0, 0, 0)

        self.calendar = EventCalendarWidget()
        self.calendar.setNavigationBarVisible(True)
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)

        self.calendar.clicked.connect(self.on_calendar_date_clicked)

        self.calendar.setStyleSheet("""
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #084924;
                min-height: 50px;
                padding: 5px;
            }
            QCalendarWidget QToolButton {
                color: white;
                background-color: #084924;
                font-size: 16px;
                font-weight: bold;
                padding: 8px;
                margin: 2px;
                border-radius: 4px;
                min-width: 40px;
                min-height: 40px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #FDC601;
                color: #084924;
            }
            QCalendarWidget QToolButton:pressed {
                background-color: #d4a000;
            }
            QCalendarWidget QMenu {
                background-color: white;
                color: #084924;
                border: 1px solid #ddd;
            }
            QCalendarWidget QMenu::item:selected {
                background-color: #FDC601;
                color: white;
            }
            QCalendarWidget QSpinBox {
                color: white;
                background-color: #084924;
                selection-background-color: #FDC601;
                selection-color: white;
                font-size: 16px;
                font-weight: bold;
                border: 1px solid #FDC601;
                border-radius: 4px;
                padding: 5px 10px;
                min-width: 80px;
                min-height: 35px;
            }
            QCalendarWidget QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                background-color: #FDC601;
                border-left: 1px solid #084924;
                width: 20px;
                border-top-right-radius: 3px;
            }
            QCalendarWidget QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                background-color: #FDC601;
                border-left: 1px solid #084924;
                width: 20px;
                border-bottom-right-radius: 3px;
            }
            QCalendarWidget QSpinBox::up-button:hover {
                background-color: #d4a000;
            }
            QCalendarWidget QSpinBox::down-button:hover {
                background-color: #d4a000;
            }
            QCalendarWidget QSpinBox::up-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-bottom: 6px solid #084924;
                width: 0px;
                height: 0px;
            }
            QCalendarWidget QSpinBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #084924;
                width: 0px;
                height: 0px;
            }
            QCalendarWidget QTableView {
                background-color: white;
                selection-background-color: #FDC601;
                selection-color: white;
                border: 1px solid #ddd;
                font-size: 13px;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: #084924;
                background-color: white;
            }
            QCalendarWidget QAbstractItemView:disabled {
                color: #999;
            }
            QCalendarWidget QWidget {
                alternate-background-color: #f8f9fa;
            }
        """)

        calendar_layout.addWidget(self.calendar)
        return calendar_container

    def setup_controls(self, layout):
        """Setup controls section (panel toggle, activities, search)."""
        controls_layout = QHBoxLayout()

        # Toggle upcoming
        self.btn_toggle_upcoming = QPushButton("◀ Hide Panel")
        self.btn_toggle_upcoming.setStyleSheet("""
            QPushButton {
                background-color: #084924;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #FDC601;
                color: #084924;
            }
            QPushButton:pressed {
                background-color: #d4a000;
            }
        """)
        self.btn_toggle_upcoming.clicked.connect(self.toggle_upcoming_events)
        controls_layout.addWidget(self.btn_toggle_upcoming)

        controls_layout.addStretch()

        # View activities
        self.btn_view_activities = QPushButton("View Activities")
        button_style = """
            QPushButton {
                background-color: #084924;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #FDC601;
                color: #084924;
            }
            QPushButton:pressed {
                background-color: #d4a000;
            }
        """
        self.btn_view_activities.setStyleSheet(button_style)
        self.btn_view_activities.clicked.connect(self.show_activities)
        controls_layout.addWidget(self.btn_view_activities)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setFixedWidth(200)
        self.search_bar.setPlaceholderText("Search events...")
        self.search_bar.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px 12px;
                background-color: white;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #FDC601;
            }
        """)
        self.search_bar.returnPressed.connect(self.on_search_triggered)
        controls_layout.addWidget(self.search_bar)

        # Search button
        self.btn_search = QPushButton("🔍")
        self.btn_search.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 14px;
                min-width: 40px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #FDC601;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """)
        self.btn_search.clicked.connect(self.on_search_triggered)
        controls_layout.addWidget(self.btn_search)

        layout.addLayout(controls_layout)

    def toggle_upcoming_events(self):
        """Toggle visibility of upcoming events panel."""
        if self.upcoming_events_visible:
            self.month_upcoming_panel.setVisible(False)
            self.btn_toggle_upcoming.setText("▶ Show Panel")
        else:
            self.month_upcoming_panel.setVisible(True)
            self.btn_toggle_upcoming.setText("◀ Hide Panel")
        self.upcoming_events_visible = not self.upcoming_events_visible

    # ---------- Day view ----------

    def setup_day_view(self):
        self.day_view_container = DayView(self.username, self.roles, self.primary_role, self.token)
        self.day_view_container.navigate_back_to_calendar = self.show_month_view
        self.day_view_container.navigate_to_activities = self.show_activities
        self.day_view_container.navigate_to_search = self.on_search_triggered

    # ---------- Upcoming panel + legend ----------

    def create_upcoming_events_panel(self):
        """Create upcoming events panel with 2x2 legend layout."""
        panel = QWidget()
        panel.setMinimumWidth(300)
        panel.setMaximumWidth(400)
        panel.setStyleSheet("background-color: white;")

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(10, 10, 10, 10)

        frame = QWidget()
        frame.setStyleSheet("""
            QWidget {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: #FFFFFF;
                padding: 10px;
            }
        """)
        frame_layout = QVBoxLayout(frame)

        title = QLabel("Upcoming Events")
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #084924;
            padding: 10px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(title)

        legend_grid = QGridLayout()
        legend_grid.setSpacing(8)
        legend_grid.setContentsMargins(5, 5, 5, 5)

        legend_style = """
            QLabel {
                padding: 5px 8px;
                border-radius: 3px;
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                font-size: 11px;
                font-weight: 500;
            }
        """

        label_academic = QLabel("🟢 Academic")
        label_academic.setStyleSheet(legend_style)
        label_org = QLabel("🔵 Organizational")
        label_org.setStyleSheet(legend_style)
        label_deadline = QLabel("🟠 Deadlines")
        label_deadline.setStyleSheet(legend_style)
        label_holiday = QLabel("🔴 Holidays")
        label_holiday.setStyleSheet(legend_style)

        legend_grid.addWidget(label_academic, 0, 0)
        legend_grid.addWidget(label_org, 0, 1)
        legend_grid.addWidget(label_deadline, 1, 0)
        legend_grid.addWidget(label_holiday, 1, 1)

        frame_layout.addLayout(legend_grid)

        # Filter combo
        self.month_filter_combo = QComboBox()
        self.month_filter_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 6px 12px;
                background-color: white;
                min-width: 150px;
                color: #666;
                font-size: 12px;
                margin: 10px 0px;
            }
            QComboBox:hover {
                border-color: #FDC601;
            }
        """)
        self.month_filter_combo.addItems([
            "All Events",
            "Academic Activities",
            "Organizational Activities",
            "Deadlines",
            "Holidays"
        ])
        self.month_filter_combo.currentTextChanged.connect(self.on_month_filter_changed)
        frame_layout.addWidget(self.month_filter_combo)

        # Events list
        self.month_events_list = QListWidget()
        self.month_events_list.setMinimumHeight(400)
        self.month_events_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                color: black;
                border-radius: 8px;
                padding: 8px;
                border: 1px solid #ddd;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
                margin: 2px;
            }
            QListWidget::item:hover {
                background-color: #f0f0f0;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #FDC601;
                color: white;
                border-radius: 4px;
            }
        """)
        frame_layout.addWidget(self.month_events_list)

        panel_layout.addWidget(frame)
        return panel

    # ---------- Navigation / callbacks ----------

    def setup_navigation(self):
        if hasattr(self.activities_widget, "navigate_back_to_calendar"):
            self.activities_widget.navigate_back_to_calendar = self.show_month_view

        role_lower = self.primary_role.lower()
        if role_lower == "admin":
            if hasattr(self.activities_widget, "btn_add_event"):
                try:
                    self.activities_widget.btn_add_event.clicked.disconnect()
                except Exception:
                    pass
                self.activities_widget.btn_add_event.clicked.connect(self.show_add_event)

            if hasattr(self.activities_widget, "navigate_to_edit_event"):
                self.activities_widget.navigate_to_edit_event = self.show_edit_event

            if self.add_event_widget:
                self.add_event_widget.navigate_back_to_activities = self.show_activities

            if self.edit_event_widget:
                self.edit_event_widget.navigate_back_to_activities = self.show_activities

    def connect_signals(self):
        """Reserved for future signals."""
        pass

    # ---------- Search ----------

    def on_search_triggered(self, query=None):
        """Send search query to SearchView via MainCalendar."""
        if query is None:
            query = self.search_bar.text().strip()
        if self.navigate_to_search and query:
            self.navigate_to_search(query)

    # ---------- View switches ----------

    def show_month_view(self):
        self.stacked_widget.setCurrentIndex(0)
        self.current_view = "Month"

    def show_day_view(self):
        self.stacked_widget.setCurrentIndex(1)
        self.current_view = "Day"

    def show_activities(self):
        if self.navigate_to_activities:
            self.navigate_to_activities()

    def show_add_event(self):
        if self.add_event_widget:
            self.stacked_widget.setCurrentIndex(3)

    def show_edit_event(self, event_data=None):
        if self.edit_event_widget:
            if event_data:
                self.edit_event_widget.event_data = event_data
                self.edit_event_widget.load_event_data()
            self.stacked_widget.setCurrentIndex(4)

    # ---------- Calendar interaction ----------

    def on_calendar_date_clicked(self, qdate):
        """When a date is clicked in month view, open DayView for that date."""
        if not hasattr(self, "day_view_container"):
            return

        selected_date = qdate.toPyDate()

        if hasattr(self.day_view_container, "set_current_date"):
            self.day_view_container.set_current_date(selected_date)

        if hasattr(self.day_view_container, "load_events"):
            self.day_view_container.load_events(self.all_events)

        self.show_day_view()

    # ---------- Events loading/filtering ----------

    def load_events(self, events):
        """Load events into month view, calendar indicators, and day view."""
        self.all_events = events

        if hasattr(self, "calendar"):
            self.calendar.set_events(events)

        if self.month_events_list is not None:
            self.month_events_list.clear()
            type_icons = {
                "Academic": "🟢",
                "Organizational": "🔵",
                "Deadline": "🟠",
                "Holiday": "🔴"
            }

            upcoming_events = self._filter_upcoming_events(events)
            for event in upcoming_events:
                icon = type_icons.get(event.get("type"), "⚪")
                date_text = event.get("date_time", "").replace(chr(10), " - ")
                event_text = f"{icon} {event.get('event', '')}\n    {date_text}"
                self.month_events_list.addItem(event_text)

        if hasattr(self, "day_view_container") and hasattr(self.day_view_container, "load_events"):
            self.day_view_container.load_events(events)

    def _filter_upcoming_events(self, events):
        """Filter to events from today onward, sorted by date."""
        today = datetime.now().date()
        upcoming = []

        for event in events:
            date_str = event.get("date_time", "")
            try:
                if "\n" in date_str:
                    date_part = date_str.split("\n")[0].strip()
                else:
                    date_part = date_str.strip()
                event_date = datetime.strptime(date_part, "%m/%d/%Y").date()
                if event_date >= today:
                    upcoming.append(event)
            except (ValueError, IndexError):
                print(f"Warning: Could not parse date for event '{event.get('event', 'Unknown')}': {date_str}")
                continue

        def get_event_date(ev):
            ds = ev.get("date_time", "")
            try:
                if "\n" in ds:
                    dp = ds.split("\n")[0].strip()
                else:
                    dp = ds.strip()
                return datetime.strptime(dp, "%m/%d/%Y").date()
            except Exception:
                return datetime.max.date()

        upcoming.sort(key=get_event_date)
        return upcoming

    def on_month_filter_changed(self, filter_text):
        """Handle filter change for upcoming events panel."""
        if not hasattr(self, "main_calendar") or self.main_calendar is None:
            return

        filtered_events = self.main_calendar.filter_events(filter_text)
        upcoming_events = self._filter_upcoming_events(filtered_events)

        if self.month_events_list is not None:
            self.month_events_list.clear()
            type_icons = {
                "Academic": "🟢",
                "Organizational": "🔵",
                "Deadline": "🟠",
                "Holiday": "🔴"
            }
            for event in upcoming_events:
                icon = type_icons.get(event.get("type"), "⚪")
                date_text = event.get("date_time", "").replace(chr(10), " - ")
                event_text = f"{icon} {event.get('event', '')}\n    {date_text}"
                self.month_events_list.addItem(event_text)

    # ---------- Fallback widget ----------

    def _create_default_widget(self, title, desc):
        widget = QWidget()
        layout = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        desc_label = QLabel(desc)
        desc_label.setFont(QFont("Arial", 12))
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addStretch()
        widget.setLayout(layout)
        return widget
