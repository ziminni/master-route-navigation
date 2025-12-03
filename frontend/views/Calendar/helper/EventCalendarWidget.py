from datetime import datetime

from PyQt6.QtWidgets import QCalendarWidget
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtCore import Qt, QDate


class EventCalendarWidget(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # map: QDate -> list of {"event": str, "type": str}
        self.events_by_date = {}

    def _parse_event_date(self, date_time_str: str):
        """
        Parse a date from either:
        - legacy 'MM/DD/YYYY\\nHH:MM AM'
        - ISO datetime 'YYYY-MM-DDTHH:MM:SS[+offset]'
        - plain 'MM/DD/YYYY'
        Returns a datetime.date or raises.
        """
        if not date_time_str:
            raise ValueError("Empty date string")

        # Legacy format with newline
        if "\n" in date_time_str:
            date_part = date_time_str.split("\n")[0].strip()
            return datetime.strptime(date_part, "%m/%d/%Y").date()

        # Try ISO 8601 from API
        try:
            normalized = date_time_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(normalized)
            return dt.date()
        except ValueError:
            # Fallback: plain MM/DD/YYYY
            return datetime.strptime(date_time_str.strip(), "%m/%d/%Y").date()

    def set_events(self, events):
        """Store events grouped by QDate."""
        self.events_by_date.clear()
        for ev in events:
            date_str = ev.get("date_time", "")
            title = ev.get("event", "")
            etype = ev.get("type", "")
            try:
                dt = self._parse_event_date(date_str)
                qd = QDate(dt.year, dt.month, dt.day)
                self.events_by_date.setdefault(qd, []).append(
                    {"event": title, "type": etype}
                )
                # Debug print
                print(f"Added event: {title} on {qd.toString('MM/dd/yyyy')}")
            except Exception as e:
                print(f"Error parsing date '{date_str}': {e}")
                continue
        print(f"Total dates with events: {len(self.events_by_date)}")
        self.updateCells()

    def paintCell(self, painter, rect, date):
        # Get events for this date
        events = self.events_by_date.get(date, [])
        has_events = len(events) > 0

        # Debug: print when painting cells with events
        if has_events:
            print(f"Painting cell for {date.toString('MM/dd/yyyy')} with {len(events)} events")

        # Type colors
        type_color_map = {
            "Academic": QColor("#90EE90"),       # Light green
            "Organizational": QColor("#ADD8E6"), # Light blue
            "Deadline": QColor("#FFD700"),       # Gold
            "Holiday": QColor("#FFB6C1"),        # Light pink
        }

        # 1) Background
        painter.save()

        if has_events:
            first_type = events[0].get("type", "")
            bg_color = type_color_map.get(first_type, QColor("#FFFFFF"))
        elif date == QDate.currentDate():
            bg_color = QColor("#FFF3C0")  # Light gold for today
        else:
            bg_color = QColor("#FFFFFF")

        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(rect)
        painter.restore()

        # 2) Day number
        painter.save()
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)
        painter.setPen(QColor("#000000"))

        day_rect = rect.adjusted(2, 2, -2, -rect.height() + 16)
        painter.drawText(
            day_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
            str(date.day())
        )
        painter.restore()

        # 3) Event title (first event)
        if has_events:
            painter.save()
            font = QFont()
            font.setPointSize(7)
            font.setBold(False)
            painter.setFont(font)
            painter.setPen(QColor("#000000"))

            title = events[0].get("event", "")
            title = painter.fontMetrics().elidedText(
                title,
                Qt.TextElideMode.ElideRight,
                rect.width() - 6
            )

            title_rect = rect.adjusted(2, 18, -2, -2)
            painter.drawText(
                title_rect,
                Qt.AlignmentFlag.AlignLeft
                | Qt.AlignmentFlag.AlignTop
                | Qt.TextFlag.TextWordWrap,
                title,
            )
            painter.restore()

        # 4) Border for today
        if date == QDate.currentDate():
            painter.save()
            pen = painter.pen()
            pen.setColor(QColor("#000000"))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(rect.adjusted(1, 1, -2, -2))
            painter.restore()
