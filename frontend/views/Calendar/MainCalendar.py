# MainCalendar.py - UPDATED to Handle Search Query Transfer and Fix Upcoming Events
import json
import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QStackedWidget, QMessageBox
from PyQt6.QtGui import QFont
from datetime import datetime
from .Calendar import Calendar
from .AdminActivities import AdminActivities
from .StudentActivities import StudentActivities
from .Staff_FacultyActivities import StaffFacultyActivities
from .AddEvent import AddEvent
from .EditEvent import EditEvent
from .SearchView import SearchView

class MainCalendar(QWidget):
    def __init__(self, username, roles, primary_role, token):
        super().__init__()
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        
        # Path to events.json - in the same directory as this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.events_file = os.path.join(current_dir, "events.json")
        
        # Load events from JSON file
        self.sample_events = self.load_events_from_json()

        # Initialize layout with stacked widget
        layout = QVBoxLayout()
        self.stacked_widget = QStackedWidget()

        # Create calendar widget - same for both admin and student
        self.calendar_widget = Calendar(username, roles, primary_role, token)
        
        # Set reference to MainCalendar for filtering
        self.calendar_widget.main_calendar = self
        
        # Create activities widget based on role
        role_lower = primary_role.lower()
        if role_lower == "admin":
            self.activities_widget = AdminActivities(username, roles, primary_role, token)
            # Set reference to MainCalendar for filtering (admin only)
            self.activities_widget.main_calendar = self
        elif role_lower == "student":
            self.activities_widget = StudentActivities(username, roles, primary_role, token)
        
        elif role_lower in ["staff", "faculty"]:
            self.activities_widget = StaffFacultyActivities(username, roles, primary_role, token)
            # Set reference to MainCalendar for filtering
            self.activities_widget.main_calendar = self
        else:
            # Fallback for other roles
            self.activities_widget = self._create_default_widget(
                "Invalid Role", f"No activities available for role: {primary_role}"
            )

        
        # Load events into activities widget
        if hasattr(self.activities_widget, 'load_events'):
            self.activities_widget.load_events(self.sample_events)
        
        # Load events into calendar widget (month and day views)
        if hasattr(self.calendar_widget, 'load_events'):
            self.calendar_widget.load_events(self.sample_events)
        
        # CRITICAL: Set main_calendar reference for day view AFTER loading events
        if hasattr(self.calendar_widget, 'day_view_container'):
            self.calendar_widget.day_view_container.main_calendar = self
        
        # Create search widget
        self.search_widget = SearchView(username, roles, primary_role, token)
        self.search_widget.main_calendar = self
        self.search_widget.load_events(self.sample_events)
        
        # Create add event widget (admin, staff, faculty) and edit event widget (admin only)
        if role_lower in ["admin", "staff", "faculty"]:
            self.add_event_widget = AddEvent(username, roles, primary_role, token)
            self.add_event_widget.main_calendar = self
            
            # Edit widget is admin only
            if role_lower == "admin":
                self.edit_event_widget = EditEvent(username, roles, primary_role, token)
                self.edit_event_widget.main_calendar = self
            else:
                self.edit_event_widget = None
        else:
            self.add_event_widget = None
            self.edit_event_widget = None

        # Set navigation callbacks
        self.calendar_widget.navigate_to_activities = self.show_activities
        self.calendar_widget.navigate_to_search = self.show_search  # UPDATED: Now accepts query parameter
        
        if hasattr(self.activities_widget, 'navigate_back_to_calendar'):
            self.activities_widget.navigate_back_to_calendar = self.show_calendar
        
        # Set search navigation
        self.search_widget.navigate_back_to_calendar = self.show_calendar
        
        # Connect add event button in activities widget (admin, staff, and faculty)
        if role_lower in ["admin", "staff", "faculty"] and hasattr(self.activities_widget, 'btn_add_event'):
            try:
                self.activities_widget.btn_add_event.clicked.disconnect()
            except:
                pass
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
        self.stacked_widget.addWidget(self.search_widget)         # Index 2 - Search
        if self.add_event_widget:
            self.stacked_widget.addWidget(self.add_event_widget)  # Index 3 - Add Event (admin only)
        if self.edit_event_widget:
            self.stacked_widget.addWidget(self.edit_event_widget) # Index 4 - Edit Event (admin only)
        
        # Start with calendar view
        self.stacked_widget.setCurrentIndex(0)
        
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

    def load_events_from_json(self):
        """Load events from events.json file"""
        try:
            if os.path.exists(self.events_file):
                with open(self.events_file, 'r') as f:
                    data = json.load(f)
                    events = data.get('events', [])
                    print(f"MainCalendar: Loaded {len(events)} events from JSON")
                    return events
            else:
                # Create empty events file if it doesn't exist
                print("MainCalendar: events.json not found, creating empty file")
                self.save_events_to_json([])
                return []
        except Exception as e:
            print(f"MainCalendar: Error loading events: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to load events: {str(e)}")
            return []
    
    def save_events_to_json(self, events=None):
        """Save events to events.json file"""
        try:
            if events is None:
                events = self.sample_events
            
            data = {"events": events}
            with open(self.events_file, 'w') as f:
                json.dump(data, f, indent=4)
            print(f"MainCalendar: Saved {len(events)} events to JSON")
            return True
        except Exception as e:
            print(f"MainCalendar: Error saving events: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to save events: {str(e)}")
            return False

    def show_calendar(self):
        """Switch to calendar view"""
        self.stacked_widget.setCurrentIndex(0)
    
    def show_activities(self):
        """Switch to activities view"""
        self.stacked_widget.setCurrentIndex(1)
    
    def show_search(self, search_query=""):
        """Switch to search view with optional search query"""
        self.stacked_widget.setCurrentIndex(2)
        # Refresh search view with latest events
        self.search_widget.load_events(self.sample_events)
        
        # UPDATED: If search query is provided, set it and execute search
        if search_query:
            self.search_widget.search_bar.setText(search_query)
            self.search_widget.on_search_clicked()
    
    def show_add_event(self):
        """Switch to add event view (admin only)"""
        if self.add_event_widget:
            self.add_event_widget.clear_form()  # Clear form before showing
            self.stacked_widget.setCurrentIndex(3)
    
    def show_edit_event(self, event_data=None):
        """Switch to edit event view (admin only)"""
        if self.edit_event_widget:
            # Update event data if provided
            if event_data:
                self.edit_event_widget.event_data = event_data
                self.edit_event_widget.load_event_data()
            self.stacked_widget.setCurrentIndex(4)
    
    def add_new_event(self, event_data):
        """Add a new event to the events list and save to JSON"""
        self.sample_events.append(event_data)
        
        # Save to JSON file
        if self.save_events_to_json():
            # Refresh all widgets
            if hasattr(self.activities_widget, 'load_events'):
                self.activities_widget.load_events(self.sample_events)
            if hasattr(self.calendar_widget, 'load_events'):
                self.calendar_widget.load_events(self.sample_events)
            if hasattr(self.search_widget, 'load_events'):
                self.search_widget.load_events(self.sample_events)
            return True
        return False
    
    def update_event(self, old_event_name, new_event_data):
        """Update an existing event and save to JSON"""
        for i, event in enumerate(self.sample_events):
            if event['event'] == old_event_name:
                self.sample_events[i] = new_event_data
                break
        
        # Save to JSON file
        if self.save_events_to_json():
            # Refresh all widgets
            if hasattr(self.activities_widget, 'load_events'):
                self.activities_widget.load_events(self.sample_events)
            if hasattr(self.calendar_widget, 'load_events'):
                self.calendar_widget.load_events(self.sample_events)
            if hasattr(self.search_widget, 'load_events'):
                self.search_widget.load_events(self.sample_events)
            return True
        return False
    
    def delete_event(self, event_name):
        """Delete an event from the events list and save to JSON"""
        self.sample_events = [e for e in self.sample_events if e['event'] != event_name]
        
        # Save to JSON file
        if self.save_events_to_json():
            # Refresh all widgets
            if hasattr(self.activities_widget, 'load_events'):
                self.activities_widget.load_events(self.sample_events)
            if hasattr(self.calendar_widget, 'load_events'):
                self.calendar_widget.load_events(self.sample_events)
            if hasattr(self.search_widget, 'load_events'):
                self.search_widget.load_events(self.sample_events)
            return True
        return False
    
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