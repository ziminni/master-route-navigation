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

    # -------- filtering helpers --------

    def filter_upcoming_events(self):
        """Return upcoming events from today onwards, sorted by date."""
        today = datetime.now().date()
        upcoming = []

        for event in self.all_events:
            date_str = event.get('date_time', '')
            try:
                if '\n' in date_str:
                    date_part = date_str.split('\n')[0].strip()
                else:
                    date_part = date_str.strip()
                event_date = datetime.strptime(date_part, "%m/%d/%Y").date()
                if event_date >= today:
                    upcoming.append(event)
            except (ValueError, IndexError):
                continue

        def get_event_date(ev):
            ds = ev.get('date_time', '')
            try:
                if '\n' in ds:
                    dp = ds.split('\n')[0].strip()
                else:
                    dp = ds.strip()
                return datetime.strptime(dp, "%m/%d/%Y").date()
            except Exception:
                return datetime.max.date()

        upcoming.sort(key=get_event_date)
        return upcoming

    def filter_events_by_current_date(self):
        """Return events that match helper.current_date."""
        current_date_str = self.current_date.strftime("%m/%d/%Y")
        filtered = []

        for event in self.all_events:
            date_str = event.get('date_time', '')
            try:
                if '\n' in date_str:
                    date_part = date_str.split('\n')[0].strip()
                else:
                    date_part = date_str.strip()
                if date_part == current_date_str:
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

            hour = int(time_part.split(':')[0])

            if period == 'PM' and hour != 12:
                hour += 12
            elif period == 'AM' and hour == 12:
                hour = 0

            return hour
        except Exception:
            return None
