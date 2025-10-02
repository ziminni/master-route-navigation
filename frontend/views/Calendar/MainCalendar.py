# MainCalendar.py  MAIN ENTRY POINT
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QStackedWidget
from PyQt6.QtGui import QFont
from .Calendar import Calendar
from .AdminActivities import AdminActivities
from .StudentActivities import StudentActivities
from .AddEvent import AddEvent
from .EditEvent import EditEvent

class MainCalendar(QWidget):
    def __init__(self, username, roles, primary_role, token):
        super().__init__()
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token

        # Initialize sample events data
        self.sample_events = [
             {
                "date_time": "10/2/2025\n9:00 AM",
                "event": "TeSTING",
                "type": "Academic",
                "location": "TEST",
                "status": "Patya ko",
            },
            {
                "date_time": "10/15/2025\n9:00 AM",
                "event": "Database Systems Lecture",
                "type": "Academic",
                "location": "Room 301",
                "status": "Upcoming",
            },
            {
                "date_time": "10/20/2025\n2:00 PM",
                "event": "Student Council Meeting",
                "type": "Organizational",
                "location": "Conference Hall",
                "status": "Upcoming",
            },
            {
                "date_time": "10/25/2025\n11:59 PM",
                "event": "Project Submission",
                "type": "Deadline",
                "location": "Online Portal",
                "status": "Pending",
            },
            {
                "date_time": "11/01/2025\nAll Day",
                "event": "All Saints' Day",
                "type": "Holiday",
                "location": "N/A",
                "status": "Holiday",
            },
            {
                "date_time": "10/18/2025\n10:00 AM",
                "event": "Software Engineering Workshop",
                "type": "Academic",
                "location": "Lab 204",
                "status": "Upcoming",
            }
        ]

        # Initialize layout with stacked widget
        layout = QVBoxLayout()
        self.stacked_widget = QStackedWidget()

        # Create calendar widget - same for both admin and student
        self.calendar_widget = Calendar(username, roles, primary_role, token)
        
        # Set reference to MainCalendar for filtering
        self.calendar_widget.main_calendar = self
        
        # Also set reference for day view (inside calendar widget)
        if hasattr(self.calendar_widget, 'day_view_container'):
            self.calendar_widget.day_view_container.main_calendar = self
        
        # Create activities widget based on role
        role_lower = primary_role.lower()
        if role_lower == "admin":
            self.activities_widget = AdminActivities(username, roles, primary_role, token)
            # Set reference to MainCalendar for filtering (admin only)
            self.activities_widget.main_calendar = self
        elif role_lower == "student":
            self.activities_widget = StudentActivities(username, roles, primary_role, token)
        else:
            # Fallback for other roles
            self.activities_widget = self._create_default_widget(
                "Invalid Role", f"No activities available for role: {primary_role}"
            )
        
        # Load sample events into activities widget
        if hasattr(self.activities_widget, 'load_events'):
            self.activities_widget.load_events(self.sample_events)
        
        # Load sample events into calendar widget (month and day views)
        if hasattr(self.calendar_widget, 'load_events'):
            self.calendar_widget.load_events(self.sample_events)
        
        # Create add event and edit event widgets (only for admin)
        if role_lower == "admin":
            self.add_event_widget = AddEvent(username, roles, primary_role, token)
            self.edit_event_widget = EditEvent(username, roles, primary_role, token)
        else:
            self.add_event_widget = None
            self.edit_event_widget = None
        
        # Set navigation callbacks
        self.calendar_widget.navigate_to_activities = self.show_activities
        
        if hasattr(self.activities_widget, 'navigate_back_to_calendar'):
            self.activities_widget.navigate_back_to_calendar = self.show_calendar
        
        # Connect add event button in activities widget (admin only)
        if role_lower == "admin" and hasattr(self.activities_widget, 'btn_add_event'):
            self.activities_widget.btn_add_event.clicked.disconnect()  # Remove any existing connection
            self.activities_widget.btn_add_event.clicked.connect(self.show_add_event)
        
        # Connect edit event navigation (admin only)
        if role_lower == "admin" and hasattr(self.activities_widget, 'navigate_to_edit_event'):
            self.activities_widget.navigate_to_edit_event = self.show_edit_event
        
        # Connect add event and edit event widget navigation (admin only)
        if self.add_event_widget:
            self.add_event_widget.navigate_back_to_activities = self.show_activities
        
        if self.edit_event_widget:
            self.edit_event_widget.navigate_back_to_activities = self.show_activities
        
        # Add widgets to stack
        self.stacked_widget.addWidget(self.calendar_widget)      # Index 0 - Calendar
        self.stacked_widget.addWidget(self.activities_widget)     # Index 1 - Activities
        if self.add_event_widget:
            self.stacked_widget.addWidget(self.add_event_widget)  # Index 2 - Add Event (admin only)
        if self.edit_event_widget:
            self.stacked_widget.addWidget(self.edit_event_widget) # Index 3 - Edit Event (admin only)
        
        # Start with calendar view
        self.stacked_widget.setCurrentIndex(0)
        
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

    def show_calendar(self):
        """Switch to calendar view"""
        self.stacked_widget.setCurrentIndex(0)
    
    def show_activities(self):
        """Switch to activities view"""
        self.stacked_widget.setCurrentIndex(1)
    
    def show_add_event(self):
        """Switch to add event view (admin only)"""
        if self.add_event_widget:
            self.stacked_widget.setCurrentIndex(2)
    
    def show_edit_event(self, event_data=None):
        """Switch to edit event view (admin only)"""
        if self.edit_event_widget:
            # Update event data if provided
            if event_data:
                self.edit_event_widget.event_data = event_data
                self.edit_event_widget.load_event_data()
            self.stacked_widget.setCurrentIndex(3)
    
    def add_new_event(self, event_data):
        """Add a new event to the events list"""
        self.sample_events.append(event_data)
        # Refresh all widgets
        if hasattr(self.activities_widget, 'load_events'):
            self.activities_widget.load_events(self.sample_events)
        if hasattr(self.calendar_widget, 'load_events'):
            self.calendar_widget.load_events(self.sample_events)
    
    def update_event(self, old_event_name, new_event_data):
        """Update an existing event"""
        for i, event in enumerate(self.sample_events):
            if event['event'] == old_event_name:
                self.sample_events[i] = new_event_data
                break
        # Refresh all widgets
        if hasattr(self.activities_widget, 'load_events'):
            self.activities_widget.load_events(self.sample_events)
        if hasattr(self.calendar_widget, 'load_events'):
            self.calendar_widget.load_events(self.sample_events)
    
    def delete_event(self, event_name):
        """Delete an event from the events list"""
        self.sample_events = [e for e in self.sample_events if e['event'] != event_name]
        # Refresh all widgets
        if hasattr(self.activities_widget, 'load_events'):
            self.activities_widget.load_events(self.sample_events)
        if hasattr(self.calendar_widget, 'load_events'):
            self.calendar_widget.load_events(self.sample_events)
    
    def filter_events(self, filter_type):
        """
        Filter events by type
        
        Args:
            filter_type (str): Type to filter by. Options:
                - "All Events": Returns all events
                - "Academic" or "Academic Activities": Returns only Academic events
                - "Organizational" or "Organizational Activities": Returns only Organizational events
                - "Deadline" or "Deadlines": Returns only Deadline events
                - "Holiday" or "Holidays": Returns only Holiday events
        
        Returns:
            list: Filtered list of events
        """
        # Normalize filter type
        filter_map = {
            "All Events": None,
            "Academic": "Academic",
            "Academic Activities": "Academic",
            "Organizational": "Organizational",
            "Organizational Activities": "Organizational",
            "Deadline": "Deadline",
            "Deadlines": "Deadline",
            "Holiday": "Holiday",
            "Holidays": "Holiday"
        }
        
        event_type = filter_map.get(filter_type)
        
        # Return all events if no filter or "All Events"
        if event_type is None:
            return self.sample_events
        
        # Filter by type
        return [event for event in self.sample_events if event.get("type") == event_type]

    def _create_default_widget(self, title, desc):
        """Create a fallback widget for invalid roles."""
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