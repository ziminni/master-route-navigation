from datetime import datetime

from PyQt6.QtWidgets import QCalendarWidget
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtCore import Qt, QDate


class EventCalendarWidget(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # map: QDate -> list of {"title": str, "type": str}
        self.events_by_date = {}

    def set_events(self, events):
        """Store events grouped by QDate."""
        self.events_by_date.clear()
        for ev in events:
            date_str = ev.get("date_time", "")
            title = ev.get("event", "")
            etype = ev.get("type", "")
            try:
                if "\n" in date_str:
                    date_part = date_str.split("\n")[0].strip()
                else:
                    date_part = date_str.strip()
                dt = datetime.strptime(date_part, "%m/%d/%Y").date()
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
        self.updateCells()  # Use updateCells() instead of update()

    def paintCell(self, painter, rect, date):
        # Get events for this date
        events = self.events_by_date.get(date, [])
        has_events = len(events) > 0
        
        # Debug: print when painting cells with events
        if has_events:
            print(f"Painting cell for {date.toString('MM/dd/yyyy')} with {len(events)} events")

        # Define type colors
        type_color_map = {
            "Academic": QColor("#90EE90"),      # Light green
            "Organizational": QColor("#ADD8E6"), # Light blue
            "Deadline": QColor("#FFD700"),       # Gold
            "Holiday": QColor("#FFB6C1"),        # Light pink
        }

        # ---------- 1) Draw background ----------
        painter.save()
        
        if has_events:
            # Color background based on event type
            first_type = events[0].get("type", "")
            bg_color = type_color_map.get(first_type, QColor("#FFFFFF"))
        elif date == QDate.currentDate():
            bg_color = QColor("#FFF3C0")  # Light gold for today
        else:
            bg_color = QColor("#FFFFFF")  # White for other days

        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(rect)
        painter.restore()

        # ---------- 2) Draw day number ----------
        painter.save()
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)
        painter.setPen(QColor("#000000"))
        
        # Day number in top-left
        day_rect = rect.adjusted(2, 2, -2, -rect.height() + 16)
        painter.drawText(
            day_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
            str(date.day())
        )
        painter.restore()

        # ---------- 3) Draw event title (if exists) ----------
        if has_events:
            painter.save()
            font = QFont()
            font.setPointSize(7)  # Small font size
            font.setBold(False)
            painter.setFont(font)
            painter.setPen(QColor("#000000"))
            
            # Get first event title
            title = events[0].get("event", "")
            
            # Truncate if too long
            title = painter.fontMetrics().elidedText(
                title,
                Qt.TextElideMode.ElideRight,
                rect.width() - 6
            )
            
            # Draw title below day number with word wrap
            title_rect = rect.adjusted(2, 18, -2, -2)
            painter.drawText(
                title_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
                title
            )
            painter.restore()

        # ---------- 4) Border for today ----------
        if date == QDate.currentDate():
            painter.save()
            pen = painter.pen()
            pen.setColor(QColor("#000000"))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(rect.adjusted(1, 1, -2, -2))
            painter.restore()