# AdminActivities.py
import requests
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QMessageBox, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QListWidget
)
from PyQt6.QtCore import Qt

class AdminActivities(QWidget):
    def __init__(self, username, roles, primary_role, token, parent=None):
        super().__init__(parent)
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token

        # ---- config your API base + endpoints here ----
        self.api_base = "http://127.0.0.1:8000/api/"
        self.activities_url = self.api_base + "activities/"

        self.headers = {"Authorization": f"Bearer {self.token}"}

        # Add navigation callback attributes
        self.navigate_back_to_calendar = None  # Will be set by Calendar.py
        self.navigate_to_edit_event = None  # Will be set by Calendar.py

        self.setWindowTitle("Activities")
        self.resize(1200, 700)

        # Top Controls (Filters and Buttons)
        controls = QHBoxLayout()
        
        # Filter section
        filter_label = QLabel("Filter by:")
        filter_label.setStyleSheet("font-weight: bold; color: #084924; font-size: 14px;")
        
        self.combo_activity_type = QComboBox()
        self.combo_activity_type.setMinimumWidth(150)
        self.combo_activity_type.addItems([
            "All Events",
            "Academic",
            "Organizational",
            "Deadline",
            "Holiday"
        ])
        self.combo_activity_type.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                font-size: 12px;
                color: #084924;
                font-weight: bold;
            }
            QComboBox:hover {
                border-color: #FDC601;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 1px solid #ccc;
                selection-background-color: #FDC601;
                selection-color: #084924;
            }
        """)
        
        controls.addWidget(filter_label)
        controls.addWidget(self.combo_activity_type)
        controls.addStretch()
        
        # Action buttons (only show for admin)
        button_style = """
            QPushButton {
                background-color: #084924;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #FDC601;
                color: #084924;
            }
            QPushButton:pressed {
                background-color: #d4a000;
            }
        """
        
        # Add Event button (admin only)
        self.btn_add_event = QPushButton("+ Add Event")
        self.btn_add_event.setStyleSheet(button_style)
        if self.primary_role.lower() != "admin":
            self.btn_add_event.setVisible(False)
        controls.addWidget(self.btn_add_event)
        
        # Back to Calendar button
        self.btn_back = QPushButton("← Back to Calendar")
        self.btn_back.setStyleSheet("""
            QPushButton {
                background-color: #FDC601;
                color: #084924;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #e6b400;
                border: 2px solid #084924;
            }
            QPushButton:pressed {
                background-color: #cc9f00;
            }
        """)
        controls.addWidget(self.btn_back)

        # Main content area - split between upcoming events and activities table
        content_layout = QHBoxLayout()
        
        # Left side - Upcoming Events Panel
        self.setup_upcoming_events_panel()
        content_layout.addWidget(self.upcoming_events_widget)
        
        # Right side - Activities Table
        self.setup_activities_table()
        content_layout.addWidget(self.activities_widget)

        # Main Layout
        root = QVBoxLayout(self)
        root.addLayout(controls)
        root.addLayout(content_layout)

        # Signals
        self.btn_back.clicked.connect(self.back_to_calendar)
        self.btn_add_event.clicked.connect(self.add_event)
        self.combo_activity_type.currentTextChanged.connect(self.filter_activities)

        # Initial data
        self.activities_data = []

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
        self.combo_upcoming_filter.currentTextChanged.connect(self.on_upcoming_filter_changed)
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

    def setup_activities_table(self):
        """Setup the activities table on the right side"""
        self.activities_widget = QWidget()
        self.activities_widget.setStyleSheet("background-color: white;")
        
        table_layout = QVBoxLayout(self.activities_widget)
        table_layout.setContentsMargins(10, 10, 10, 10)
        
        # Table title
        table_title = QLabel("Daily Activities")
        table_title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #084924;
            padding: 10px;
        """)
        table_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        table_layout.addWidget(table_title)
        
        # Activities Table
        self.activities_table = QTableWidget(0, 6)
        self.activities_table.setMinimumSize(600, 400)
        
        # Set column headers
        headers = ["Date & Time", "Event", "Type", "Location", "Status", "Action"]
        self.activities_table.setHorizontalHeaderLabels(headers)
        
        # Style the table
        self.activities_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 2px solid #FDC601;
                border-radius: 8px;
                gridline-color: #e0e0e0;
                font-size: 12px;
                alternate-background-color: #f8f9fa;
            }
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #f0f0f0;
                color: #333;
            }
            QTableWidget::item:selected {
                background-color: #FDC601;
                color: #084924;
                font-weight: bold;
            }
            QTableWidget::item:hover {
                background-color: #f8f9fa;
            }
            QHeaderView::section {
                background-color: #084924;
                color: white;
                border: 1px solid #FDC601;
                padding: 12px;
                font-weight: bold;
                font-size: 11px;
            }
            QHeaderView::section:hover {
                background-color: #0a5228;
            }
            QScrollBar:vertical {
                background-color: #f0f0f0;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #084924;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #FDC601;
            }
        """)
        
        # Set column widths - more compact
        self.activities_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.activities_table.setColumnWidth(0, 120)  # Date & Time
        self.activities_table.setColumnWidth(1, 190)  # Event
        self.activities_table.setColumnWidth(2, 90)   # Type
        self.activities_table.setColumnWidth(3, 100)  # Location
        self.activities_table.setColumnWidth(4, 100)  # Status
        self.activities_table.setColumnWidth(5, 150)  # Action
        
        # Set row height
        self.activities_table.verticalHeader().setDefaultSectionSize(60)
        
        # Additional settings
        self.activities_table.verticalHeader().setVisible(False)
        self.activities_table.setAlternatingRowColors(True)
        self.activities_table.setSortingEnabled(False)  # DISABLED to maintain custom sort order
        
        table_layout.addWidget(self.activities_table)

    def load_events(self, events):
        """Load events from MainCalendar"""
        self.activities_data = events
        self.populate_table(events)
        self.populate_upcoming_events(events)

    def create_action_buttons(self, row):
        """Create Edit/Delete action buttons for a table row (admin only)"""
        if self.primary_role.lower() != "admin":
            return None
        
        button_widget = QWidget()
        button_widget.setStyleSheet("background-color: white;")
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(5, 2, 5, 2)
        button_layout.setSpacing(5)
        
        # Edit button
        edit_btn = QPushButton("Edit")
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #084924;
                border: 1px solid #084924;
                border-radius: 4px;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 10px;
                min-width: 40px;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border: 2px solid #084924;
            }
        """)
        
        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #dc3545;
                border: 1px solid #dc3545;
                border-radius: 4px;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 10px;
                min-width: 40px;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border: 2px solid #dc3545;
            }
        """)
        
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addStretch()
        
        # Connect buttons
        edit_btn.clicked.connect(lambda checked, r=row: self.edit_event(r))
        delete_btn.clicked.connect(lambda checked, r=row: self.delete_event(r))
        
        return button_widget
    
    def populate_table(self, activities):
        """Populate the table with activity data - SORTED by priority"""
        # Disable sorting while populating
        self.activities_table.setSortingEnabled(False)
        self.activities_table.setRowCount(0)
        
        # Sort activities using custom sorting function
        sorted_activities = self._sort_activities_by_priority(activities)
        
        for activity in sorted_activities:
            row_position = self.activities_table.rowCount()
            self.activities_table.insertRow(row_position)
            
            # Add data to columns
            self.activities_table.setItem(row_position, 0, QTableWidgetItem(activity["date_time"]))
            self.activities_table.setItem(row_position, 1, QTableWidgetItem(activity["event"]))
            self.activities_table.setItem(row_position, 2, QTableWidgetItem(activity["type"]))
            self.activities_table.setItem(row_position, 3, QTableWidgetItem(activity["location"]))
            self.activities_table.setItem(row_position, 4, QTableWidgetItem(activity["status"]))
            
            # Add action buttons (admin only)
            if self.primary_role.lower() == "admin":
                action_buttons = self.create_action_buttons(row_position)
                if action_buttons:
                    self.activities_table.setCellWidget(row_position, 5, action_buttons)
            
            # Center align all cells
            for col in range(5):
                item = self.activities_table.item(row_position, col)
                if item:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # KEEP SORTING DISABLED to maintain our custom sort order
        # If you want users to be able to sort by columns, comment out this line:
        # self.activities_table.setSortingEnabled(True)
    
    def populate_upcoming_events(self, activities):
        """Populate the upcoming events list with activity data - FIXED to filter and sort"""
        self.list_upcoming.clear()
        
        # Define emoji icons for each event type
        type_icons = {
            "Academic": "🟢",
            "Organizational": "🔵",
            "Deadline": "🟠",
            "Holiday": "🔴"
        }
        
        # Filter and sort upcoming events
        upcoming_events = self._filter_upcoming_events(activities)
        
        for activity in upcoming_events:
            icon = type_icons.get(activity["type"], "⚪")
            event_text = f"{icon} {activity['event']}\n    {activity['date_time'].replace(chr(10), ' - ')}"
            self.list_upcoming.addItem(event_text)

    # ========== SORTING AND FILTERING FUNCTIONS ==========
    
    def _sort_activities_by_priority(self, events):
        """
        Sort events by priority:
        1. Current month events from today onwards 
        2. Future month events 
        3. Past events from current month 
        4. Past events from previous months 
        """
        today = datetime.now().date()
        current_month = today.month
        current_year = today.year
        
        current_month_upcoming = []
        future_months = []
        current_month_past = []
        old_past_events = []
        
        for event in events:
            date_str = event.get('date_time', '')
            
            try:
                # Parse the date
                if '\n' in date_str:
                    date_part = date_str.split('\n')[0].strip()
                else:
                    date_part = date_str.strip()
                
                event_date = datetime.strptime(date_part, "%m/%d/%Y").date()
                
                # Update status based on date
                if event_date < today:
                    event['status'] = "Finished"
                elif event.get('status') == "Finished":
                    event['status'] = "Upcoming"
                
                # Categorize events
                if event_date.month == current_month and event_date.year == current_year:
                    # Current month events
                    if event_date >= today:
                        current_month_upcoming.append((event_date, event))
                    else:
                        current_month_past.append((event_date, event))
                elif event_date > today:
                    # Future months
                    future_months.append((event_date, event))
                else:
                    # Past events from previous months
                    old_past_events.append((event_date, event))
                    
            except (ValueError, IndexError) as e:
                print(f"Warning: Could not parse date for event '{event.get('event', 'Unknown')}': {date_str}")
                # Put unparseable events at the very end
                old_past_events.append((datetime.max.date(), event))
                continue
        
        # Sort each category by date
        current_month_upcoming.sort(key=lambda x: x[0])
        current_month_past.sort(key=lambda x: x[0])
        future_months.sort(key=lambda x: x[0])
        old_past_events.sort(key=lambda x: x[0])
        
        # Combine: current month upcoming → future months → current month past → old past events
        sorted_events = (
            [event for _, event in current_month_upcoming] +
            [event for _, event in future_months] +
            [event for _, event in current_month_past] +
            [event for _, event in old_past_events]
        )
        
        return sorted_events
    
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
    
    # ========== EVENT HANDLERS ==========
    
    def edit_event(self, row):
        """Handle edit event button click"""
        event_data = {
            'date_time': self.activities_table.item(row, 0).text(),
            'event': self.activities_table.item(row, 1).text(),
            'type': self.activities_table.item(row, 2).text(),
            'location': self.activities_table.item(row, 3).text(),
            'status': self.activities_table.item(row, 4).text(),
        }
        
        if self.navigate_to_edit_event:
            self.navigate_to_edit_event(event_data)
        else:
            self._info(f"Edit event: {event_data['event']}")
    
    def delete_event(self, row):
        """Handle delete event button click - FIXED to actually delete from JSON"""
        event_name = self.activities_table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{event_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Call MainCalendar's delete_event method to remove from JSON
            if hasattr(self, 'main_calendar'):
                success = self.main_calendar.delete_event(event_name)
                if success:
                    QMessageBox.information(self, "Success", f"Event '{event_name}' deleted successfully")
                else:
                    QMessageBox.warning(self, "Error", f"Failed to delete event '{event_name}'")
            else:
                # Fallback: just remove from table if main_calendar not available
                self.activities_table.removeRow(row)
                self._info(f"Event '{event_name}' removed from table")

    def back_to_calendar(self):
        """Handle back to calendar button click"""
        if self.navigate_back_to_calendar:
            self.navigate_back_to_calendar()
        else:
            self._info("Navigation not configured")

    def add_event(self):
        """Handle add event button click"""
        pass

    def filter_activities(self, filter_text):
        """Filter activities table based on selected type"""
        if hasattr(self, 'main_calendar'):
            filtered_events = self.main_calendar.filter_events(filter_text)
            # Update both the table and the upcoming events list
            self.populate_table(filtered_events)
            self.populate_upcoming_events(filtered_events)
    
    def on_upcoming_filter_changed(self, filter_text):
        """Handle filter change in upcoming events list - FIXED to use filtered upcoming events"""
        if hasattr(self, 'main_calendar'):
            filtered_events = self.main_calendar.filter_events(filter_text)
            # Update only the upcoming events list (with date filtering)
            self.populate_upcoming_events(filtered_events)

    # ========== UI HELPERS ==========
    
    def _info(self, msg):
        QMessageBox.information(self, "Info", str(msg))

    def _error(self, msg):
        QMessageBox.critical(self, "Error", str(msg))
        