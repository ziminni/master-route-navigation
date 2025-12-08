# Handles calendar, activities, search, and event persistence (via API)

import os
from datetime import datetime

import requests
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QStackedWidget, QMessageBox
from PyQt6.QtGui import QFont

from .Calendar import Calendar
from .role.AdminActivities import AdminActivities
from .role.StudentActivities import StudentActivities
from .role.Staff_FacultyActivities import StaffFacultyActivities
from .CRUD.AddEvent import AddEvent
from .CRUD.EditEvent import EditEvent
from .CRUD.SearchView import SearchView


class MainCalendar(QWidget):
    """Main container for the calendar module with navigation and event storage."""

    def __init__(self, username, roles, primary_role, token):
        super().__init__()

        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token

        # ---------- API storage ----------

        self.api_base = "http://127.0.0.1:8000/api/calendar/calendar-entries/"
        self.headers = {"Authorization": f"Bearer {self.token}"}

        # Load events from backend API
        self.sample_events = self.load_events_from_api()

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
            self.activities_widget.main_calendar = self
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

        self.stacked_widget.addWidget(self.calendar_widget)       # 0 - Calendar
        self.stacked_widget.addWidget(self.activities_widget)     # 1 - Activities
        self.stacked_widget.addWidget(self.search_widget)         # 2 - Search
        if self.add_event_widget:
            self.stacked_widget.addWidget(self.add_event_widget)  # 3 - Add Event
        if self.edit_event_widget:
            self.stacked_widget.addWidget(self.edit_event_widget) # 4 - Edit Event

        # Start on calendar
        self.stacked_widget.setCurrentIndex(0)

        layout.addWidget(self.stacked_widget)

    # -------------------------------------------------------------------------
    # API load
    # -------------------------------------------------------------------------

    def load_events_from_api(self):
        """Load calendar entries from Django API and map them to UI event dicts."""
        try:
            r = requests.get(self.api_base, headers=self.headers, timeout=10)
            r.raise_for_status()
            data = r.json()

            if isinstance(data, dict):
                items = data.get("results", [])
            elif isinstance(data, list):
                items = data
            else:
                items = []

            events = []
            for item in items:
                start_iso = item.get("start_at")
                # Keep ISO string; your widgets can format if needed
                date_time_str = start_iso or ""

                events.append({
                    "id": item["id"],
                    "date_time": date_time_str,
                    "event": item["title"],
                    "type": self._map_tags_to_type(item.get("tags", [])),
                    "location": item.get("location") or "N/A",
                    "status": "Upcoming",
                })

            print(f"MainCalendar: Loaded {len(events)} events from API")
            return events

        except Exception as e:
            print(f"MainCalendar: Error loading events from API: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load events: {e}")
            return []

    def _map_tags_to_type(self, tags):
        """Convert CalendarEntry.tags to existing UI type labels."""
        if "class" in tags or "Academic" in tags:
            return "Academic"
        if "org_event" in tags or "Organizational" in tags:
            return "Organizational"
        if "deadline" in tags or "Deadline" in tags:
            return "Deadline"
        if "holiday" in tags or "Holiday" in tags:
            return "Holiday"
        return "Academic"

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
    # Event CRUD (via API)
    # -------------------------------------------------------------------------

    def _event_to_payload(self, event_data):
        """
        Map UI event dict -> CalendarEntry POST/PUT payload.
        Adjust parsing if you use formatted date_time strings.
        """
        date_time_str = event_data.get("date_time", "")
        start_iso = None
        if date_time_str:
            # If your UI stores ISO strings, just pass them through
            try:
                # validate and normalize
                dt = datetime.fromisoformat(date_time_str.replace("Z", "+00:00"))
                start_iso = dt.isoformat()
            except ValueError:
                start_iso = None

        t = event_data.get("type")
        tags = []
        if t == "Academic":
            tags.append("class")
        elif t == "Organizational":
            tags.append("org_event")
        elif t == "Deadline":
            tags.append("deadline")
        elif t == "Holiday":
            tags.append("holiday")

        return {
            "source_ct_id": 1,   # temporary; set up properly in backend later
            "source_id": 0,
            "title": event_data.get("event"),
            "start_at": start_iso,
            "end_at": None,
            "all_day": False,
            "location": event_data.get("location") or "",
            "is_public": True,
            "tags": tags,
            "org_status": "",
            "org_id": None,
            "section_id": None,
            "semester_id": None,
        }

    def add_new_event(self, event_data):
        """Create a CalendarEntry via API and refresh all views."""
        try:
            payload = self._event_to_payload(event_data)
            r = requests.post(self.api_base, json=payload, headers=self.headers, timeout=10)
            r.raise_for_status()
            self.sample_events = self.load_events_from_api()
            self._reload_all_views()
            return True
        except Exception as e:
            print(f"MainCalendar: Error creating event via API: {e}")
            QMessageBox.critical(self, "Error", f"Failed to create event: {e}")
            return False

    def update_event(self, old_event_name, new_event_data):
        """Update corresponding CalendarEntry via API and refresh."""
        event_id = None
        for e in self.sample_events:
            if e.get("event") == old_event_name:
                event_id = e.get("id")
                break
        if event_id is None:
            QMessageBox.warning(self, "Error", "Event not found.")
            return False

        try:
            payload = self._event_to_payload(new_event_data)
            url = f"{self.api_base}{event_id}/"
            r = requests.put(url, json=payload, headers=self.headers, timeout=10)
            r.raise_for_status()
            self.sample_events = self.load_events_from_api()
            self._reload_all_views()
            return True
        except Exception as e:
            print(f"MainCalendar: Error updating event via API: {e}")
            QMessageBox.critical(self, "Error", f"Failed to update event: {e}")
            return False

    def delete_event(self, event_name):
        """Delete CalendarEntry via API and refresh."""
        event_id = None
        for e in self.sample_events:
            if e.get("event") == event_name:
                event_id = e.get("id")
                break
        if event_id is None:
            QMessageBox.warning(self, "Error", "Event not found.")
            return False

        try:
            url = f"{self.api_base}{event_id}/"
            r = requests.delete(url, headers=self.headers, timeout=10)
            if r.status_code not in (200, 204):
                raise Exception(f"HTTP {r.status_code} {r.text[:200]}")
            self.sample_events = self.load_events_from_api()
            self._reload_all_views()
            return True
        except Exception as e:
            print(f"MainCalendar: Error deleting event via API: {e}")
            QMessageBox.critical(self, "Error", f"Failed to delete event: {e}")
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
