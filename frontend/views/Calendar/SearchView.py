# SearchView.py - Complete search view with new layout style
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QLineEdit, QScrollArea, QListWidget
)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime
from PyQt6.QtGui import QFont

class SearchView(QWidget):
    """Search view matching the Calendar.py layout style"""
    
    def __init__(self, username, roles, primary_role, token):
        super().__init__()
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        
        # Callback for navigation (set by MainCalendar)
        self.navigate_back_to_calendar = None
        
        # Store all events for searching
        self.all_events = []
        
        # Initialize UI
        self.init_ui()
    
    def init_ui(self):
        """Initialize the search UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # Header
        self.setup_header(main_layout)
        
        # Controls
        self.setup_controls(main_layout)
        
        # Content area with upcoming events and search results
        content_layout = QHBoxLayout()
        
        # Upcoming events panel (left side)
        self.upcoming_panel = self.create_upcoming_events_panel()
        
        # Search results panel (right side)
        self.results_panel = self.create_search_results_panel()
        
        content_layout.addWidget(self.upcoming_panel)
        content_layout.addWidget(self.results_panel)
        
        main_layout.addLayout(content_layout)
    
    def setup_header(self, layout):
        """Setup header section"""
        header_layout = QVBoxLayout()
        
        title = QLabel("Search Events")
        title.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold; 
            color: #084924;
            padding: 10px 0px;
        """)
        header_layout.addWidget(title)
        
        subtitle = QLabel(f"Welcome, {self.username}")
        subtitle.setStyleSheet("font-size: 14px; color: #666;")
        header_layout.addWidget(subtitle)
        
        layout.addLayout(header_layout)
    
    def setup_controls(self, layout):
        """Setup controls section"""
        controls_layout = QHBoxLayout()
        
        # Back button
        self.btn_back = QPushButton("← Back")
        self.btn_back.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
        """)
        self.btn_back.clicked.connect(self.on_back_clicked)
        controls_layout.addWidget(self.btn_back)
        
        controls_layout.addStretch()
            
        
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
        self.search_bar.returnPressed.connect(self.on_search_clicked)
        controls_layout.addWidget(self.search_bar)
        
        # Search button
        self.btn_search = QPushButton("Search")
        self.btn_search.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px 16px;
                color: #666;
                font-size: 12px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """)
        self.btn_search.clicked.connect(self.on_search_clicked)
        controls_layout.addWidget(self.btn_search)
        
        layout.addLayout(controls_layout)
    
    def create_upcoming_events_panel(self):
        """Create upcoming events panel (same as Calendar.py)"""
        panel = QWidget()
        panel.setMinimumWidth(300)
        panel.setMaximumWidth(400)
        panel.setStyleSheet("background-color: white;")
        
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(10, 10, 10, 10)
        
        # Frame
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
        
        # Title
        title = QLabel("Upcoming Events")
        title.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: #084924; 
            padding: 10px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(title)
        
        # Legend
        legend_layout = QHBoxLayout()
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
        for text in ["🟢 Academic", "🔵 Organizational", "🟠 Deadlines", "🔴 Holidays"]:
            label = QLabel(text)
            label.setStyleSheet(legend_style)
            legend_layout.addWidget(label)
        frame_layout.addLayout(legend_layout)
        
        # Filter
        self.filter_combo = QComboBox()
        self.filter_combo.setStyleSheet("""
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
        self.filter_combo.addItems([
            "All Events",
            "Academic Activities",
            "Organizational Activities",
            "Deadlines",
            "Holidays"
        ])
        self.filter_combo.currentTextChanged.connect(self.on_filter_changed)
        frame_layout.addWidget(self.filter_combo)
        
        # Events list
        self.events_list = QListWidget()
        self.events_list.setMinimumHeight(400)
        self.events_list.setStyleSheet("""
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
        
        frame_layout.addWidget(self.events_list)
        panel_layout.addWidget(frame)
        
        return panel
    
    def create_search_results_panel(self):
        """Create search results panel"""
        panel = QWidget()
        panel.setStyleSheet("background-color: white;")
        
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(20, 20, 20, 20)
        panel_layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.label_results = QLabel("Search Results")
        self.label_results.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: #084924;
        """)
        header_layout.addWidget(self.label_results)
        header_layout.addStretch()
        
        panel_layout.addLayout(header_layout)
        
        # Table header
        table_header = QWidget()
        table_header.setFixedHeight(40)
        table_header.setStyleSheet("""
            background-color: #084924; 
            border-radius: 6px;
        """)
        
        header_layout = QHBoxLayout(table_header)
        header_layout.setContentsMargins(15, 0, 15, 0)
        
        date_label = QLabel("Date")
        date_label.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
        header_layout.addWidget(date_label)
        
        header_layout.addStretch()
        
        event_label = QLabel("Event")
        event_label.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
        header_layout.addWidget(event_label)
        
        panel_layout.addWidget(table_header)
        
        # Results scroll area
        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: white;
            }
            QScrollBar:vertical {
                background-color: #f1f1f1;
                width: 14px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical {
                background-color: #c1c1c1;
                border-radius: 7px;
                min-height: 25px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #a8a8a8;
            }
        """)
        
        # Content widget
        self.results_content = QWidget()
        self.results_layout = QVBoxLayout(self.results_content)
        self.results_layout.setContentsMargins(10, 10, 10, 10)
        self.results_layout.setSpacing(8)
        
        # Initial message
        self.show_initial_message()
        
        self.results_scroll.setWidget(self.results_content)
        panel_layout.addWidget(self.results_scroll)
        
        return panel
    
    def show_initial_message(self):
        """Show initial search message"""
        self.clear_results()
        msg = QLabel("Enter a search query to find events")
        msg.setStyleSheet("""
            color: #999; 
            padding: 20px; 
            font-size: 14px;
        """)
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.results_layout.addWidget(msg)
    
    def clear_results(self):
        """Clear search results"""
        for i in reversed(range(self.results_layout.count())):
            widget = self.results_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
    
    def load_events(self, events):
        """Load events from MainCalendar - FIXED VERSION"""
        self.all_events = events  # Store all events for searching
        
        # Filter and sort upcoming events for sidebar
        upcoming_events = self._filter_upcoming_events(events)
        
        # Populate upcoming events list
        self.populate_upcoming_events(upcoming_events)

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

    def populate_upcoming_events(self, events):
        """Populate the upcoming events list - FIXED with date filtering"""
        self.events_list.clear()
        
        type_icons = {
            "Academic": "🟢",
            "Organizational": "🔵",
            "Deadline": "🟠",
            "Holiday": "🔴"
        }
        
        for event in events:
            icon = type_icons.get(event["type"], "⚪")
            event_text = f"{icon} {event['event']}\n    {event['date_time'].replace(chr(10), ' - ')}"
            self.events_list.addItem(event_text)

    def on_filter_changed(self, filter_text):
        """Handle filter change in upcoming events - FIXED with date filtering"""
        if hasattr(self, 'main_calendar'):
            filtered_events = self.main_calendar.filter_events(filter_text)
            # Apply date filtering and sorting
            upcoming_events = self._filter_upcoming_events(filtered_events)
            self.populate_upcoming_events(upcoming_events)
    
    def on_search_clicked(self):
        """Execute search - case insensitive"""
        # Get the search query and convert to lowercase for case-insensitive search
        query = self.search_bar.text().strip().lower()
        
        print(f"SearchView: Search clicked with query: '{query}'")
        print(f"SearchView: Total events available: {len(self.all_events)}")
        
        if not query:
            self.show_initial_message()
            return
        
        # Search through events - case insensitive
        results = []
        for event in self.all_events:
            # Convert all search fields to lowercase for comparison
            event_name = str(event.get('event', '')).lower()
            event_type = str(event.get('type', '')).lower()
            event_location = str(event.get('location', '')).lower()
            event_status = str(event.get('status', '')).lower()
            event_datetime = str(event.get('date_time', '')).lower()
            
            # Check if query matches any field
            if (query in event_name or 
                query in event_type or 
                query in event_location or
                query in event_status or
                query in event_datetime):
                results.append(event)
        
        print(f"SearchView: Found {len(results)} matching results")
        
        # Display results
        self.display_search_results(results, query)
    
    def display_search_results(self, results, query):
        """Display search results"""
        print(f"SearchView: Displaying {len(results)} results")
        self.clear_results()
        
        # Update header
        self.label_results.setText(f"Search Results ({len(results)} found)")
        
        if not results:
            no_results = QLabel(f"No events found matching '{query}'")
            no_results.setStyleSheet("""
                color: #666; 
                font-style: italic; 
                padding: 20px;
            """)
            no_results.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.results_layout.addWidget(no_results)
            print("SearchView: No results widget added")
            return
        
        # Color map
        color_map = {
            "Academic": "#28a745",
            "Organizational": "#007bff",
            "Deadline": "#fd7e14",
            "Holiday": "#dc3545"
        }
        
        # Add result items
        for i, event in enumerate(results):
            print(f"SearchView: Creating result item {i+1}: {event.get('event', 'Unknown')}")
            result_item = self.create_result_item(
                event['date_time'],
                event['event'],
                event['type'],
                event.get('location', 'N/A'),
                color_map.get(event['type'], "#6c757d")
            )
            self.results_layout.addWidget(result_item)
        
        self.results_layout.addStretch()
        print("SearchView: All result items added")
    
    def create_result_item(self, date_time, event_name, event_type, location, color):
        """Create a single result item"""
        item = QWidget()
        item.setFixedHeight(70)
        item.setStyleSheet(f"""
            QWidget {{
                background-color: {color};
                border-radius: 6px;
                margin: 3px;
            }}
            QWidget:hover {{
                background-color: {self.adjust_brightness(color, -20)};
            }}
        """)
        
        layout = QHBoxLayout(item)
        layout.setContentsMargins(15, 8, 15, 8)
        
        # Date column
        date_label = QLabel(date_time.replace('\n', ' - '))
        date_label.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
        date_label.setFixedWidth(150)
        layout.addWidget(date_label)
        
        # Event details
        details_layout = QVBoxLayout()
        details_layout.setSpacing(4)
        
        name_label = QLabel(event_name)
        name_label.setStyleSheet("color: white; font-weight: bold; font-size: 13px;")
        details_layout.addWidget(name_label)
        
        info_label = QLabel(f"{event_type} • {location}")
        info_label.setStyleSheet("color: white; font-size: 11px;")
        details_layout.addWidget(info_label)
        
        layout.addLayout(details_layout)
        
        return item
    
    def adjust_brightness(self, hex_color, percent):
        """Adjust color brightness"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        rgb = tuple(max(0, min(255, int(c + (255 - c) * percent / 100))) for c in rgb)
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    
    def on_back_clicked(self):
        """Handle back button"""
        if self.navigate_back_to_calendar:
            self.navigate_back_to_calendar()