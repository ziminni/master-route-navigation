# MainCalendar.py
# Handles calendar, activities, search, and event persistence (JSON)

import json
import os
from datetime import datetime

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QStackedWidget, QMessageBox
from PyQt6.QtGui import QFont

from .Calendar import Calendar
from .AdminActivities import AdminActivities
from .StudentActivities import StudentActivities
from .Staff_FacultyActivities import StaffFacultyActivities
from .AddEvent import AddEvent
from .EditEvent import EditEvent
from .SearchView import SearchView


class MainCalendar(QWidget):
    """Main container for the calendar module with navigation and event storage."""

    def __init__(self, username, roles, primary_role, token):
        super().__init__()

        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token

        # ---------- JSON storage ----------

        # events.json lives in the same directory as this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.events_file = os.path.join(current_dir, "events.json")

        # Load events from JSON file (creates empty file if missing)
        self.sample_events = self.load_events_from_json()

        # ---------- stacked UI ----------

        layout = QVBoxLayout(self)
        self.stacked_widget = QStackedWidget()

        # Calendar (shared for all roles)
        self.calendar_widget = Calendar(username, roles, primary_role, token)
        self.calendar_widget.main_calendar = self  # for filtering callbacks

        # Activities per role
        role_lower = primary_role.lower()
        if role_lower == "admin":
            self.activities_widget = AdminActivities(username, roles, primary_role, token)
            self.activities_widget.main_calendar = self
        elif role_lower == "student":
            self.activities_widget = StudentActivities(username, roles, primary_role, token)
        elif role_lower in ["staff", "faculty"]:
            self.activities_widget = StaffFacultyActivities(username, roles, primary_role, token)
            self.activities_widget.main_calendar = self
        else:
            self.activities_widget = self._create_default_widget(
                "Invalid Role", f"No activities available for role: {primary_role}"
            )

        # Load events into role activities
        if hasattr(self.activities_widget, "load_events"):
            self.activities_widget.load_events(self.sample_events)

        # Load events into calendar (month + day views)
        if hasattr(self.calendar_widget, "load_events"):
            self.calendar_widget.load_events(self.sample_events)

        # Give DayView access back to MainCalendar (for filters)
        if hasattr(self.calendar_widget, "day_view_container"):
            self.calendar_widget.day_view_container.main_calendar = self

        # Search view
        self.search_widget = SearchView(username, roles, primary_role, token)
        self.search_widget.main_calendar = self
        self.search_widget.load_events(self.sample_events)

        # Add / edit event views
        if role_lower in ["admin", "staff", "faculty"]:
            self.add_event_widget = AddEvent(username, roles, primary_role, token)
            self.add_event_widget.main_calendar = self

            if role_lower == "admin":
                self.edit_event_widget = EditEvent(username, roles, primary_role, token)
                self.edit_event_widget.main_calendar = self
            else:
                self.edit_event_widget = None
        else:
            self.add_event_widget = None
            self.edit_event_widget = None

        # ---------- navigation wiring ----------

        # From calendar
        self.calendar_widget.navigate_to_activities = self.show_activities
        self.calendar_widget.navigate_to_search = self.show_search

        # From activities back to calendar
        if hasattr(self.activities_widget, "navigate_back_to_calendar"):
            self.activities_widget.navigate_back_to_calendar = self.show_calendar

        # From search back to calendar
        self.search_widget.navigate_back_to_calendar = self.show_calendar

        # Add-event button (admin/staff/faculty)
        if role_lower in ["admin", "staff", "faculty"] and hasattr(
            self.activities_widget, "btn_add_event"
        ):
            try:
                self.activities_widget.btn_add_event.clicked.disconnect()
            except Exception:
                pass
            self.activities_widget.btn_add_event.clicked.connect(self.show_add_event)

        # Edit-event navigation (admin only)
        if role_lower == "admin" and hasattr(self.activities_widget, "navigate_to_edit_event"):
            self.activities_widget.navigate_to_edit_event = self.show_edit_event

        # Add/edit widgets back-navigation
        if self.add_event_widget:
            self.add_event_widget.navigate_back_to_activities = self.show_activities
        if self.edit_event_widget:
            self.edit_event_widget.navigate_back_to_activities = self.show_activities

        # ---------- stacked pages ----------

        self.stacked_widget.addWidget(self.calendar_widget)      # 0 - Calendar
        self.stacked_widget.addWidget(self.activities_widget)    # 1 - Activities
        self.stacked_widget.addWidget(self.search_widget)        # 2 - Search
        if self.add_event_widget:
            self.stacked_widget.addWidget(self.add_event_widget) # 3 - Add Event
        if self.edit_event_widget:
            self.stacked_widget.addWidget(self.edit_event_widget) # 4 - Edit Event

        # Start on calendar
        self.stacked_widget.setCurrentIndex(0)

        layout.addWidget(self.stacked_widget)

    # -------------------------------------------------------------------------
    # JSON load/save
    # -------------------------------------------------------------------------

    def load_events_from_json(self):
        """Load events list from events.json, creating an empty file if needed."""
        try:
            if os.path.exists(self.events_file):
                with open(self.events_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    events = data.get("events", [])
                    print(f"MainCalendar: Loaded {len(events)} events from JSON")
                    return events

            # File does not exist: create empty
            print("MainCalendar: events.json not found, creating empty file")
            self.save_events_to_json([])
            return []

        except Exception as e:
            print(f"MainCalendar: Error loading events: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load events: {e}")
            return []

    def save_events_to_json(self, events=None):
        """Save the given events (or current sample_events) to events.json."""
        try:
            if events is None:
                events = self.sample_events

            data = {"events": events}
            with open(self.events_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

            print(f"MainCalendar: Saved {len(events)} events to JSON")
            return True

        except Exception as e:
            print(f"MainCalendar: Error saving events: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save events: {e}")
            return False

    # -------------------------------------------------------------------------
    # View switching
    # -------------------------------------------------------------------------

    def show_calendar(self):
        """Switch to calendar view."""
        self.stacked_widget.setCurrentIndex(0)

    def show_activities(self):
        """Switch to activities view."""
        self.stacked_widget.setCurrentIndex(1)

    def show_search(self, search_query: str = ""):
        """Switch to search view and optionally execute a search."""
        self.stacked_widget.setCurrentIndex(2)

        # Refresh with latest events
        self.search_widget.load_events(self.sample_events)

        # If a query was passed (from Calendar / DayView), run it
        if search_query:
            self.search_widget.search_bar.setText(search_query)
            self.search_widget.on_search_clicked()

    def show_add_event(self):
        """Switch to add-event view (admin/staff/faculty)."""
        if self.add_event_widget:
            self.add_event_widget.clear_form()
            self.stacked_widget.setCurrentIndex(3)

    def show_edit_event(self, event_data=None):
        """Switch to edit-event view (admin only)."""
        if self.edit_event_widget:
            if event_data:
                self.edit_event_widget.event_data = event_data
                self.edit_event_widget.load_event_data()
            self.stacked_widget.setCurrentIndex(4)

    # -------------------------------------------------------------------------
    # Event CRUD
    # -------------------------------------------------------------------------

    def add_new_event(self, event_data):
        """Append a new event and propagate to JSON and all views."""
        self.sample_events.append(event_data)

        if self.save_events_to_json():
            self._reload_all_views()
            return True
        return False

    def update_event(self, old_event_name, new_event_data):
        """Replace an existing event by name and refresh all views."""
        for i, event in enumerate(self.sample_events):
            if event.get("event") == old_event_name:
                self.sample_events[i] = new_event_data
                break

        if self.save_events_to_json():
            self._reload_all_views()
            return True
        return False

    def delete_event(self, event_name):
        """Remove an event by name and refresh all views."""
        self.sample_events = [e for e in self.sample_events if e.get("event") != event_name]

        if self.save_events_to_json():
            self._reload_all_views()
            return True
        return False

    def _reload_all_views(self):
        """Reload events into activities, calendar, and search views."""
        if hasattr(self.activities_widget, "load_events"):
            self.activities_widget.load_events(self.sample_events)
        if hasattr(self.calendar_widget, "load_events"):
            self.calendar_widget.load_events(self.sample_events)
        if hasattr(self.search_widget, "load_events"):
            self.search_widget.load_events(self.sample_events)

    # -------------------------------------------------------------------------
    # Filtering helper
    # -------------------------------------------------------------------------

    def filter_events(self, filter_type):
        """
        Return events filtered by logical type string.

        filter_type options:
            - "All Events"
            - "Academic" / "Academic Activities"
            - "Organizational" / "Organizational Activities"
            - "Deadline" / "Deadlines"
            - "Holiday" / "Holidays"
        """
        filter_map = {
            "All Events": None,
            "Academic": "Academic",
            "Academic Activities": "Academic",
            "Organizational": "Organizational",
            "Organizational Activities": "Organizational",
            "Deadline": "Deadline",
            "Deadlines": "Deadline",
            "Holiday": "Holiday",
            "Holidays": "Holiday",
        }

        event_type = filter_map.get(filter_type)

        if event_type is None:
            return self.sample_events

        return [event for event in self.sample_events if event.get("type") == event_type]

    # -------------------------------------------------------------------------
    # Fallback widget for invalid roles
    # -------------------------------------------------------------------------

    def _create_default_widget(self, title, desc):
        """Create a simple placeholder widget for unsupported roles."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))

        desc_label = QLabel(desc)
        desc_label.setFont(QFont("Arial", 12))

        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addStretch()

        return widget
