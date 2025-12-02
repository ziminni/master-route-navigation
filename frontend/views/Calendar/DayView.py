# DayView.py DAY VIEW LAYOUT
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QListWidget, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from .DayEventsHelper import DayEventsHelper


class DayView(QWidget):
    def __init__(self, username, roles, primary_role, token):
        super().__init__()
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token

        # navigation callbacks (set by parent)
        self.navigate_back_to_calendar = None
        self.navigate_to_activities = None
        self.navigate_to_search = None

        # helper for all event/date logic
        self.helper = DayEventsHelper()

        self.init_ui()

    # ---------- UI setup ----------

    def init_ui(self):
        """Initialize the day view UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # Top bar (Back, Activities, Search)
        self.setup_top_bar(main_layout)

        # Content layout - split between upcoming events (left) and day schedule (right)
        content_layout = QHBoxLayout()

        # Left side - Upcoming Events Panel
        self.setup_upcoming_events_panel()
        content_layout.addWidget(self.upcoming_events_widget)

        # Right side - Day Schedule
        self.setup_day_schedule()
        content_layout.addWidget(self.day_schedule_widget)

        main_layout.addLayout(content_layout)

    def setup_top_bar(self, layout):
        """Top bar with Back to Month, Activities, and Search."""
        bar_layout = QHBoxLayout()
        bar_layout.setSpacing(10)

        # Back to Month View
        self.btn_back_month = QPushButton("◀ Back to Month View")
        self.btn_back_month.setStyleSheet("""
            QPushButton {
                background-color: #084924;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #FDC601;
                color: #084924;
            }
            QPushButton:pressed {
                background-color: #d4a000;
            }
        """)
        self.btn_back_month.clicked.connect(self.on_back_to_month_clicked)
        bar_layout.addWidget(self.btn_back_month)

        bar_layout.addStretch()

        # View Activities button
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
        bar_layout.addWidget(self.btn_view_activities)

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
        bar_layout.addWidget(self.search_bar)

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
        bar_layout.addWidget(self.btn_search)

        layout.addLayout(bar_layout)

    def setup_upcoming_events_panel(self):
        """Setup the upcoming events panel on the left side."""
        self.upcoming_events_widget = QWidget()
        self.upcoming_events_widget.setMinimumWidth(300)
        self.upcoming_events_widget.setMaximumWidth(400)
        self.upcoming_events_widget.setStyleSheet("background-color: white;")

        upcoming_layout = QVBoxLayout(self.upcoming_events_widget)
        upcoming_layout.setContentsMargins(10, 10, 10, 10)

        # Upcoming Events Frame
        upcoming_frame = QWidget()
        upcoming_frame.setStyleSheet("""
            QWidget {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: #FFFFFF;
                padding: 10px;
            }
        """)
        frame_layout = QVBoxLayout(upcoming_frame)

        # Title
        title_label = QLabel("Upcoming Events")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #084924;
            padding: 10px;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(title_label)

        # Legend
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(8)

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

        legend_layout.addWidget(label_academic)
        legend_layout.addWidget(label_org)
        legend_layout.addWidget(label_deadline)
        legend_layout.addWidget(label_holiday)

        frame_layout.addLayout(legend_layout)

        # Filter dropdown
        from PyQt6.QtWidgets import QComboBox  # local import, only used here
        self.combo_upcoming_filter = QComboBox()
        self.combo_upcoming_filter.setStyleSheet("""
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
            QComboBox::drop-down {
                border: 0px;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 1px solid #ccc;
                selection-background-color: #FDC601;
                selection-color: white;
                color: #084924;
            }
        """)
        self.combo_upcoming_filter.addItems([
            "All Events",
            "Academic Activities",
            "Organizational Activities",
            "Deadlines",
            "Holidays"
        ])
        self.combo_upcoming_filter.currentTextChanged.connect(self.on_day_filter_changed)
        frame_layout.addWidget(self.combo_upcoming_filter)

        # Upcoming events list
        self.list_upcoming = QListWidget()
        self.list_upcoming.setMinimumHeight(400)
        self.list_upcoming.setStyleSheet("""
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
        frame_layout.addWidget(self.list_upcoming)

        upcoming_layout.addWidget(upcoming_frame)

    def setup_day_schedule(self):
        """Setup the day schedule on the right side."""
        self.day_schedule_widget = QWidget()
        self.day_schedule_widget.setStyleSheet("background-color: white;")

        schedule_layout = QVBoxLayout(self.day_schedule_widget)
        schedule_layout.setContentsMargins(10, 10, 10, 10)
        schedule_layout.setSpacing(15)

        # Title
        title_label = QLabel("Daily Schedule")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #084924;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        schedule_layout.addWidget(title_label)

        # Current date display
        self.date_label = QLabel()
        self.update_date_label()
        self.date_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #084924;
            text-align: center;
            margin: 5px 0px;
            padding: 8px;
            border: 2px solid #FDC601;
            border-radius: 6px;
            background-color: #fffef7;
        """)
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        schedule_layout.addWidget(self.date_label)

        # Navigation buttons
        self.setup_navigation_buttons(schedule_layout)

        # Time slots (scrollable)
        self.setup_time_slots(schedule_layout)

    def setup_navigation_buttons(self, layout):
        """Setup date navigation buttons."""
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(10)

        button_style = """
            QPushButton {
                background-color: #084924;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FDC601;
                color: #084924;
            }
        """

        self.btn_prev = QPushButton("◀ Previous Day")
        self.btn_prev.setStyleSheet(button_style)
        self.btn_prev.clicked.connect(self.previous_day)

        self.btn_next = QPushButton("Next Day ▶")
        self.btn_next.setStyleSheet(button_style)
        self.btn_next.clicked.connect(self.next_day)

        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.btn_next)

        layout.addLayout(nav_layout)

        # Today button
        self.btn_today = QPushButton("Today")
        self.btn_today.setStyleSheet("""
            QPushButton {
                background-color: #FDC601;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
                margin-top: 5px;
            }
            QPushButton:hover {
                background-color: #084924;
            }
        """)
        self.btn_today.clicked.connect(self.go_to_today)
        layout.addWidget(self.btn_today)

    def setup_time_slots(self, layout):
        """Setup scrollable time slots."""
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: white;
            }
        """)

        self.slots_widget = QWidget()
        self.slots_layout = QVBoxLayout(self.slots_widget)
        self.slots_layout.setContentsMargins(0, 0, 0, 0)
        self.slots_layout.setSpacing(0)

        # 7 AM to 7 PM
        for hour in range(7, 20):
            time_slot = self.create_time_slot(hour)
            self.slots_layout.addWidget(time_slot)

        self.scroll_area.setWidget(self.slots_widget)
        layout.addWidget(self.scroll_area)

    def create_time_slot(self, hour):
        """Create a single time slot."""
        slot_container = QFrame()
        slot_container.setFixedHeight(100)
        slot_container.setStyleSheet("""
            QFrame {
                border-bottom: 1px solid #e0e0e0;
                background-color: white;
            }
            QFrame:hover {
                background-color: #f9f9f9;
            }
        """)

        slot_layout = QHBoxLayout(slot_container)
        slot_layout.setContentsMargins(0, 0, 0, 0)
        slot_layout.setSpacing(0)

        time_str = self.format_hour(hour)
        time_label = QLabel(time_str)
        time_label.setFixedWidth(100)
        time_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 12px;
                font-weight: bold;
                padding: 8px;
                border-right: 2px solid #e0e0e0;
                background-color: #f8f9fa;
            }
        """)
        time_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)

        event_area = QWidget()
        event_area.setStyleSheet("""
            QWidget {
                background-color: #fafafa;
            }
        """)
        event_layout = QVBoxLayout(event_area)
        event_layout.setContentsMargins(15, 8, 15, 8)

        placeholder = QLabel("No events scheduled")
        placeholder.setStyleSheet("""
            QLabel {
                color: #999;
                font-style: italic;
                font-size: 12px;
            }
        """)
        event_layout.addWidget(placeholder)
        event_layout.addStretch()

        slot_layout.addWidget(time_label)
        slot_layout.addWidget(event_area, 1)

        return slot_container

    # ---------- helpers & logic integration ----------

    def format_hour(self, hour):
        """Format hour to 12-hour format with AM/PM."""
        if hour == 0:
            return "12:00 AM"
        elif hour < 12:
            return f"{hour}:00 AM"
        elif hour == 12:
            return "12:00 PM"
        else:
            return f"{hour-12}:00 PM"

    def update_date_label(self):
        """Update the date label with current date."""
        self.date_label.setText(
            self.helper.current_date.strftime("%A\n%B %d, %Y")
        )

    def load_events(self, events):
        """Load events from MainCalendar - uses helper for logic."""
        self.helper.set_all_events(events)

        upcoming_events = self.helper.filter_upcoming_events()
        self.populate_upcoming_events(upcoming_events)

        current_date_events = self.helper.filter_events_by_current_date()
        self.populate_time_slots_with_events(current_date_events)

    def populate_time_slots_with_events(self, events):
        """Populate time slots with events based on their scheduled time."""
        self.clear_time_slot_events()

        for event in events:
            try:
                dt = event.get("date_time", "")
                time_str = dt.split("\n")[1] if "\n" in dt else dt
                hour = self.helper.parse_hour_from_time(time_str)
                if hour is not None and 7 <= hour <= 19:
                    self.add_event_to_time_slot(hour, event["event"], event["type"])
            except Exception as e:
                print(f"Error processing event {event.get('event', 'Unknown')}: {e}")

    def clear_time_slot_events(self):
        """Clear all events from time slots."""
        if not hasattr(self, "slots_layout"):
            return

        for i in range(self.slots_layout.count()):
            time_slot = self.slots_layout.itemAt(i).widget()
            if time_slot:
                h_layout = time_slot.layout()
                if h_layout and h_layout.count() > 1:
                    event_area = h_layout.itemAt(1).widget()
                    if event_area:
                        event_layout = event_area.layout()
                        while event_layout.count():
                            child = event_layout.takeAt(0)
                            if child.widget():
                                child.widget().deleteLater()

                        placeholder = QLabel("No events scheduled")
                        placeholder.setStyleSheet("""
                            QLabel {
                                color: #999;
                                font-style: italic;
                                font-size: 12px;
                            }
                        """)
                        event_layout.addWidget(placeholder)
                        event_layout.addStretch()

    def add_event_to_time_slot(self, hour, title, category):
        """Add an event to a specific time slot."""
        if not hasattr(self, "slots_layout"):
            return

        slot_index = hour - 7
        if slot_index < 0 or slot_index >= self.slots_layout.count():
            return

        time_slot = self.slots_layout.itemAt(slot_index).widget()
        if not time_slot:
            return

        h_layout = time_slot.layout()
        if not h_layout or h_layout.count() < 2:
            return

        event_area = h_layout.itemAt(1).widget()
        if not event_area:
            return

        event_layout = event_area.layout()
        if not event_layout:
            return

        # remove placeholder
        if event_layout.count() > 0:
            first_widget = event_layout.itemAt(0).widget()
            if first_widget and isinstance(first_widget, QLabel):
                if first_widget.text() == "No events scheduled":
                    first_widget.deleteLater()
                    if event_layout.count() > 0:
                        stretch_item = event_layout.itemAt(event_layout.count() - 1)
                        if stretch_item:
                            event_layout.removeItem(stretch_item)

        color_map = {
            "Academic": "#4CAF50",
            "Organizational": "#2196F3",
            "Deadline": "#FF9800",
            "Holiday": "#F44336",
        }
        color = color_map.get(category, "#9E9E9E")

        event_widget = QFrame()
        event_widget.setMaximumHeight(70)
        event_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 4px;
                padding: 4px 8px;
                margin: 2px 0px;
            }}
        """)

        event_layout_inner = QVBoxLayout(event_widget)
        event_layout_inner.setContentsMargins(6, 4, 6, 4)
        event_layout_inner.setSpacing(1)

        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 11px;
            }
        """)
        title_label.setWordWrap(True)

        category_label = QLabel(category)
        category_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 9px;
            }
        """)

        event_layout_inner.addWidget(title_label)
        event_layout_inner.addWidget(category_label)

        event_layout.addWidget(event_widget)

    def populate_upcoming_events(self, events):
        """Populate the upcoming events list."""
        self.list_upcoming.clear()

        type_icons = {
            "Academic": "🟢",
            "Organizational": "🔵",
            "Deadline": "🟠",
            "Holiday": "🔴",
        }

        for event in events:
            icon = type_icons.get(event["type"], "⚪")
            event_text = f"{icon} {event['event']}\n    {event['date_time'].replace(chr(10), ' - ')}"
            self.list_upcoming.addItem(event_text)

    # ---------- navigation & filters ----------

    def previous_day(self):
        """Navigate to previous day."""
        self.helper.go_prev_day()
        self.update_date_label()
        current_date_events = self.helper.filter_events_by_current_date()
        self.clear_time_slot_events()
        self.populate_time_slots_with_events(current_date_events)

    def next_day(self):
        """Navigate to next day."""
        self.helper.go_next_day()
        self.update_date_label()
        current_date_events = self.helper.filter_events_by_current_date()
        self.clear_time_slot_events()
        self.populate_time_slots_with_events(current_date_events)

    def go_to_today(self):
        """Navigate to today."""
        self.helper.go_today()
        self.update_date_label()
        current_date_events = self.helper.filter_events_by_current_date()
        self.clear_time_slot_events()
        self.populate_time_slots_with_events(current_date_events)

    def on_back_to_month_clicked(self):
        """Back to month view via parent callback."""
        if self.navigate_back_to_calendar:
            self.navigate_back_to_calendar()

    def on_day_filter_changed(self, filter_text):
        """Handle filter change in day view upcoming events."""
        if hasattr(self, "main_calendar"):
            filtered_events = self.main_calendar.filter_events(filter_text)
            self.helper.set_all_events(filtered_events)
            upcoming_events = self.helper.filter_upcoming_events()
            self.populate_upcoming_events(upcoming_events)

    def show_activities(self):
        """Navigate to activities view."""
        if self.navigate_to_activities:
            self.navigate_to_activities()

    def on_search_triggered(self, query=None):
        """Transfer search query to SearchView."""
        if query is None:
            query = self.search_bar.text().strip()

        if self.navigate_to_search:
            self.navigate_to_search(query)

    # used by Calendar.on_calendar_date_clicked
    def set_current_date(self, date_obj):
        """
        Set the current date from Month view and refresh the schedule
        for that specific day.
        """
        self.helper.set_current_date(date_obj)
        self.update_date_label()

        if self.helper.all_events:
            current_date_events = self.helper.filter_events_by_current_date()
            self.clear_time_slot_events()
            self.populate_time_slots_with_events(current_date_events)
