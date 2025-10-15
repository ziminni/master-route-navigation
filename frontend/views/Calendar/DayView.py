# DayView.py DAY VIEW LAYOUT
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QComboBox, QFrame, QListWidget, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from datetime import datetime, timedelta

class DayView(QWidget):
    def __init__(self, username, roles, primary_role, token):
        super().__init__()
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        self.current_date = datetime.now()
        self.navigate_back_to_calendar = None  # Will be set by parent
        self.navigate_to_activities = None  # Will be set by parent
        self.navigate_to_search = None  # NEW: Navigation callback for search
        self.all_events = []  # Store all events
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the day view UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
    
        # View selector at the top
        self.setup_view_selector(main_layout)
        
        # Content layout - split between upcoming events (left) and day schedule (right)
        content_layout = QHBoxLayout()
        
        # Left side - Upcoming Events Panel
        self.setup_upcoming_events_panel()
        content_layout.addWidget(self.upcoming_events_widget)
        
        # Right side - Day Schedule
        self.setup_day_schedule()
        content_layout.addWidget(self.day_schedule_widget)
        
        main_layout.addLayout(content_layout)
        
    def setup_view_selector(self, layout):
        """Setup view selector at the top with search bar and activities button"""
        view_layout = QHBoxLayout()
        view_layout.setSpacing(10)
        
        view_label = QLabel("View:")
        view_label.setStyleSheet("font-weight: bold; color: #084924; font-size: 14px;")
        
        self.combo_view = QComboBox()
        self.combo_view.setMinimumWidth(100)
        self.combo_view.addItems(["Day", "Month"])
        self.combo_view.setCurrentText("Day")
        self.combo_view.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                font-size: 12px;
            }
            QComboBox:hover {
                border-color: #FDC601;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
        """)
        self.combo_view.currentTextChanged.connect(self.on_view_changed)
        
        view_layout.addWidget(view_label)
        view_layout.addWidget(self.combo_view)
        view_layout.addStretch()
        
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
        view_layout.addWidget(self.btn_view_activities)
        
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
        # Connect Enter key to trigger search with query
        self.search_bar.returnPressed.connect(self.on_search_triggered)
        view_layout.addWidget(self.search_bar)
        
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
        view_layout.addWidget(self.btn_search)
        
        layout.addLayout(view_layout)
    
    def setup_upcoming_events_panel(self):
        """Setup the upcoming events panel on the left side"""
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
        """Setup the day schedule on the right side"""
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
        """Setup date navigation buttons"""
        # Previous and Next buttons
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
        """Setup scrollable time slots"""
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
        
        # Container for time slots
        self.slots_widget = QWidget()
        self.slots_layout = QVBoxLayout(self.slots_widget)
        self.slots_layout.setContentsMargins(0, 0, 0, 0)
        self.slots_layout.setSpacing(0)
        
        # Create time slots from 7 AM to 7 PM
        for hour in range(7, 20):
            time_slot = self.create_time_slot(hour)
            self.slots_layout.addWidget(time_slot)
        
        self.scroll_area.setWidget(self.slots_widget)
        layout.addWidget(self.scroll_area)
    
    def create_time_slot(self, hour):
        """Create a single time slot"""
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
        
        # Time label
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
        
        # Event area
        event_area = QWidget()
        event_area.setStyleSheet("""
            QWidget {
                background-color: #fafafa;
            }
        """)
        event_layout = QVBoxLayout(event_area)
        event_layout.setContentsMargins(15, 8, 15, 8)
        
        # Placeholder for events
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
    
    def format_hour(self, hour):
        """Format hour to 12-hour format with AM/PM"""
        if hour == 0:
            return "12:00 AM"
        elif hour < 12:
            return f"{hour}:00 AM"
        elif hour == 12:
            return "12:00 PM"
        else:
            return f"{hour-12}:00 PM"
    
    def update_date_label(self):
        """Update the date label with current date"""
        self.date_label.setText(
            self.current_date.strftime("%A\n%B %d, %Y")
        )
    
    def load_events(self, events):
        """Load events from MainCalendar - FIXED VERSION"""
        self.all_events = events  # Store all events
        
        # Filter and sort upcoming events
        upcoming_events = self._filter_upcoming_events(events)
        
        # Populate upcoming events list
        self.populate_upcoming_events(upcoming_events)
        
        # Populate time slots with events for current date
        current_date_events = self.filter_events_by_current_date(events)
        self.populate_time_slots_with_events(current_date_events)

    def _filter_upcoming_events(self, events):
        """
        Filter events to show only upcoming events (today onwards) and sort by date.
        Events that ended before today are excluded.
        
        Returns:
            list: Sorted list of upcoming events (nearest date first)
        """
        today = datetime.now().date()
        upcoming = []
        
        for event in events:
            # Parse the date_time field
            date_str = event.get('date_time', '')
            
            try:
                # Your format: "10/2/2025\n9:00 AM" or "10/15/2025\n2:00 PM"
                # Split by newline to get just the date part
                if '\n' in date_str:
                    date_part = date_str.split('\n')[0].strip()  # "10/2/2025"
                else:
                    date_part = date_str.strip()
                
                # Parse the date in MM/DD/YYYY format
                event_date = datetime.strptime(date_part, "%m/%d/%Y").date()
                
                # Include event if date is today or in the future
                if event_date >= today:
                    upcoming.append(event)
                    
            except (ValueError, IndexError) as e:
                # If date parsing fails, print warning and skip
                print(f"Warning: Could not parse date for event '{event.get('event', 'Unknown')}': {date_str}")
                continue
        
        # Sort by date (earliest first)
        def get_event_date(event):
            """Extract date from event for sorting"""
            date_str = event.get('date_time', '')
            try:
                if '\n' in date_str:
                    date_part = date_str.split('\n')[0].strip()
                else:
                    date_part = date_str.strip()
                
                return datetime.strptime(date_part, "%m/%d/%Y").date()
            except:
                return datetime.max.date()  # Put unparseable dates at the end
        
        upcoming.sort(key=get_event_date)
        
        return upcoming

    def filter_events_by_current_date(self, events):
        """Filter events that match the current displayed date"""
        current_date_str = self.current_date.strftime("%m/%d/%Y")
        filtered = []
        
        for event in events:
            date_str = event.get('date_time', '')
            try:
                if '\n' in date_str:
                    date_part = date_str.split('\n')[0].strip()
                else:
                    date_part = date_str.strip()
                
                if date_part == current_date_str:
                    filtered.append(event)
            except:
                continue
        
        return filtered
    
    def populate_time_slots_with_events(self, events):
        """Populate time slots with events based on their scheduled time"""
        # First, clear all existing events from time slots
        self.clear_time_slot_events()
        
        # Process each event
        for event in events:
            try:
                # Parse the time from date_time (e.g., "10/15/2025\n9:00 AM")
                time_str = event['date_time'].split('\n')[1] if '\n' in event['date_time'] else event['date_time']
                hour = self.parse_hour_from_time(time_str)
                
                if hour is not None and 7 <= hour <= 19:  # Only show events within day view hours
                    self.add_event_to_time_slot(hour, event['event'], event['type'])
            except Exception as e:
                print(f"Error processing event {event.get('event', 'Unknown')}: {e}")
    
    def parse_hour_from_time(self, time_str):
        """Parse hour from time string like '9:00 AM' or '2:00 PM'"""
        try:
            # Remove any whitespace
            time_str = time_str.strip()
            
            # Split by space to get time and AM/PM
            parts = time_str.split()
            if len(parts) < 2:
                return None
            
            time_part = parts[0]  # e.g., "9:00"
            period = parts[1].upper()  # e.g., "AM" or "PM"
            
            # Extract hour
            hour = int(time_part.split(':')[0])
            
            # Convert to 24-hour format
            if period == 'PM' and hour != 12:
                hour += 12
            elif period == 'AM' and hour == 12:
                hour = 0
            
            return hour
        except:
            return None
    
    def clear_time_slot_events(self):
        """Clear all events from time slots"""
        if not hasattr(self, 'slots_layout'):
            return
        
        # Iterate through all time slots
        for i in range(self.slots_layout.count()):
            time_slot = self.slots_layout.itemAt(i).widget()
            if time_slot:
                # Get the horizontal layout of the time slot
                h_layout = time_slot.layout()
                if h_layout and h_layout.count() > 1:
                    # Get the event area (second widget in horizontal layout)
                    event_area = h_layout.itemAt(1).widget()
                    if event_area:
                        # Clear the event area layout
                        event_layout = event_area.layout()
                        while event_layout.count():
                            child = event_layout.takeAt(0)
                            if child.widget():
                                child.widget().deleteLater()
                        
                        # Add back the placeholder
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
        """Add an event to a specific time slot"""
        if not hasattr(self, 'slots_layout'):
            return
        
        # Calculate the slot index (hour 7 is at index 0)
        slot_index = hour - 7
        
        if slot_index < 0 or slot_index >= self.slots_layout.count():
            return
        
        # Get the time slot container
        time_slot = self.slots_layout.itemAt(slot_index).widget()
        if not time_slot:
            return
        
        # Get the horizontal layout
        h_layout = time_slot.layout()
        if not h_layout or h_layout.count() < 2:
            return
        
        # Get the event area (second widget)
        event_area = h_layout.itemAt(1).widget()
        if not event_area:
            return
        
        # Get the event area layout
        event_layout = event_area.layout()
        if not event_layout:
            return
        
        # Remove placeholder if it exists
        if event_layout.count() > 0:
            first_widget = event_layout.itemAt(0).widget()
            if first_widget and isinstance(first_widget, QLabel):
                if first_widget.text() == "No events scheduled":
                    first_widget.deleteLater()
                    # Also remove the stretch if it exists
                    if event_layout.count() > 0:
                        stretch_item = event_layout.itemAt(event_layout.count() - 1)
                        if stretch_item:
                            event_layout.removeItem(stretch_item)
        
        # Get category color
        color_map = {
            "Academic": "#4CAF50",
            "Organizational": "#2196F3",
            "Deadline": "#FF9800",
            "Holiday": "#F44336"
        }
        color = color_map.get(category, "#9E9E9E")
        
        # Create event widget
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
        
        # Event title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 11px;
            }
        """)
        title_label.setWordWrap(True)
        
        # Event category
        category_label = QLabel(category)
        category_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 9px;
            }
        """)
        
        event_layout_inner.addWidget(title_label)
        event_layout_inner.addWidget(category_label)
        
        # Add the event widget to the time slot
        event_layout.addWidget(event_widget)
    
    def populate_upcoming_events(self, events):
        """Populate the upcoming events list - FIXED with date filtering"""
        self.list_upcoming.clear()
        
        # Define emoji icons for each event type
        type_icons = {
            "Academic": "🟢",
            "Organizational": "🔵",
            "Deadline": "🟠",
            "Holiday": "🔴"
        }
        
        for event in events:
            # Get the icon for the event type
            icon = type_icons.get(event["type"], "⚪")
            
            # Format the display text
            event_text = f"{icon} {event['event']}\n    {event['date_time'].replace(chr(10), ' - ')}"
            
            # Add to list
            self.list_upcoming.addItem(event_text)
    
    def previous_day(self):
        """Navigate to previous day"""
        self.current_date -= timedelta(days=1)
        self.update_date_label()
        # Reload events for the new date
        current_date_events = self.filter_events_by_current_date(self.all_events)
        self.clear_time_slot_events()
        self.populate_time_slots_with_events(current_date_events)
    
    def next_day(self):
        """Navigate to next day"""
        self.current_date += timedelta(days=1)
        self.update_date_label()
        # Reload events for the new date
        current_date_events = self.filter_events_by_current_date(self.all_events)
        self.clear_time_slot_events()
        self.populate_time_slots_with_events(current_date_events)
    
    def go_to_today(self):
        """Navigate to today"""
        self.current_date = datetime.now()
        self.update_date_label()
        # Reload events for today
        current_date_events = self.filter_events_by_current_date(self.all_events)
        self.clear_time_slot_events()
        self.populate_time_slots_with_events(current_date_events)
    
    def on_view_changed(self, view):
        """Handle view change"""
        if view == "Month" and self.navigate_back_to_calendar:
            self.navigate_back_to_calendar()
    
    def on_day_filter_changed(self, filter_text):
        """Handle filter change in day view upcoming events - FIXED with date filtering"""
        if hasattr(self, 'main_calendar'):
            filtered_events = self.main_calendar.filter_events(filter_text)
            # Apply date filtering and sorting
            upcoming_events = self._filter_upcoming_events(filtered_events)
            self.populate_upcoming_events(upcoming_events)
    
    def show_activities(self):
        """Navigate to activities view"""
        if self.navigate_to_activities:
            self.navigate_to_activities()
    
    def on_search_triggered(self, query=None):
        """Handle search button click or Enter press - transfer query to SearchView"""
        if query is None:
            query = self.search_bar.text().strip()
        
        if self.navigate_to_search:
            # Pass the search query to the navigation callback
            self.navigate_to_search(query)