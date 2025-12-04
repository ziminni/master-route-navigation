from datetime import datetime, timedelta


class DayEventsHelper:
    """Pure logic helpers for filtering and organizing day-view events."""

    def __init__(self):
        self.current_date = datetime.now()
        self.all_events = []

    # -------- core state setters --------

    def set_all_events(self, events):
        self.all_events = events or []

    def set_current_date(self, date_obj):
        """date_obj is a datetime.date or datetime"""
        if isinstance(date_obj, datetime):
            self.current_date = date_obj
        else:
            self.current_date = datetime.combine(date_obj, datetime.min.time())

    def go_prev_day(self):
        self.current_date -= timedelta(days=1)

    def go_next_day(self):
        self.current_date += timedelta(days=1)

    def go_today(self):
        self.current_date = datetime.now()

    # -------- internal date parsing --------

    @staticmethod
    def _parse_event_date(date_time_str: str):
        """
        Parse just the date part from various formats:
        - 'MM/DD/YYYY\\nHH:MM AM'
        - 'MM/DD/YYYY'
        - ISO 'YYYY-MM-DDTHH:MM:SS[.fff][Z or +offset]'
        Returns datetime.date or raises.
        """
        if not date_time_str:
            raise ValueError("Empty date string")

        # Legacy format with newline, first line is date
        if "\n" in date_time_str:
            date_part = date_time_str.split("\n")[0].strip()
            return datetime.strptime(date_part, "%m/%d/%Y").date()

        # Try ISO 8601 from backend
        try:
            # Python 3.11+ can handle 'Z' directly; if not, you can replace Z with +00:00
            dt = datetime.fromisoformat(date_time_str.replace("Z", "+00:00"))
            return dt.date()
        except ValueError:
            # Fallback: assume plain MM/DD/YYYY
            return datetime.strptime(date_time_str.strip(), "%m/%d/%Y").date()

    # -------- filtering helpers --------

    def filter_upcoming_events(self):
        """Return upcoming events from today onwards, sorted by date."""
        today = datetime.now().date()
        upcoming = []

        for event in self.all_events:
            date_str = event.get("date_time", "")
            try:
                event_date = self._parse_event_date(date_str)
                if event_date >= today:
                    upcoming.append(event)
            except Exception:
                continue

        def get_event_date(ev):
            ds = ev.get("date_time", "")
            try:
                return self._parse_event_date(ds)
            except Exception:
                return datetime.max.date()

        upcoming.sort(key=get_event_date)
        return upcoming

    def filter_events_by_current_date(self):
        """Return events that match helper.current_date."""
        current_date = self.current_date.date()
        filtered = []

        for event in self.all_events:
            date_str = event.get("date_time", "")
            try:
                event_date = self._parse_event_date(date_str)
                if event_date == current_date:
                    filtered.append(event)
            except Exception:
                continue

        return filtered

    # -------- time parsing --------

    @staticmethod
    def parse_hour_from_time(time_str):
        """Parse hour from time string like '9:00 AM' or '2:00 PM'."""
        try:
            time_str = time_str.strip()
            parts = time_str.split()
            if len(parts) < 2:
                return None

            time_part = parts[0]
            period = parts[1].upper()

            hour = int(time_part.split(":")[0])

            if period == "PM" and hour != 12:
                hour += 12
            elif period == "AM" and hour == 12:
                hour = 0

            return hour
        except Exception:
            return None
