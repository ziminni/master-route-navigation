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
                    {"title": title, "type": etype}
                )
            except Exception:
                continue
        self.update()

    def paintCell(self, painter, rect, date):
        events = self.events_by_date.get(date, [])
        has_events = len(events) > 0

        type_color_map = {
            "Academic": QColor("#4CAF50"),
            "Organizational": QColor("#2196F3"),
            "Deadline": QColor("#FF9800"),
            "Holiday": QColor("#F44336"),
        }

        # ---------- 1) background ----------
        painter.save()

        # base background
        if date == QDate.currentDate():
            base_color = QColor("#FFF3C0")  # light gold
        else:
            base_color = QColor("#FFFFFF")

        if has_events:
            first_type = events[0]["type"]
            etype_color = type_color_map.get(first_type, QColor("#9E9E9E"))
            # very light tint of event color
            base_color = QColor(
                (etype_color.red() + 255) // 2,
                (etype_color.green() + 255) // 2,
                (etype_color.blue() + 255) // 2,
            )

        painter.setBrush(base_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(rect)
        painter.restore()

        # ---------- 2) day number ----------
        painter.save()
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("#084924"))
        day_rect = rect.adjusted(2, 0, -2, -rect.height() // 2 + 4)
        painter.drawText(
            day_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
            str(date.day()),
        )
        painter.restore()

        # ---------- 3) event titles ----------
        if has_events:
            painter.save()
            font = painter.font()
            font.setPointSize(max(font.pointSize() - 2, 7))
            painter.setFont(font)

            top_offset = rect.top() + 18
            line_height = painter.fontMetrics().height()
            max_lines = 2

            for i, ev in enumerate(events[:max_lines]):
                title = ev["title"]
                etype = ev["type"]
                title = painter.fontMetrics().elidedText(
                    title, Qt.TextElideMode.ElideRight, rect.width() - 4
                )
                color = type_color_map.get(etype, QColor("#555555"))
                painter.setPen(color)
                text_rect = rect.adjusted(
                    2, top_offset + i * line_height, -2, 0
                )
                painter.drawText(
                    text_rect,
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    title,
                )

            extra = len(events) - max_lines
            if extra > 0:
                more_text = f"+{extra} more"
                painter.setPen(QColor("#666666"))
                text_rect = rect.adjusted(
                    2, top_offset + (max_lines - 1) * line_height, -2, 0
                )
                painter.drawText(
                    text_rect,
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                    more_text,
                )

            painter.restore()

        # ---------- 4) gold border for today ----------
        if date == QDate.currentDate():
            painter.save()
            pen = painter.pen()
            pen.setColor(QColor("#red"))
            pen.setWidth(2)
            painter.setPen(pen)
            r = rect.adjusted(1, 1, -1, -1)
            painter.drawRect(r)
            painter.restore()
