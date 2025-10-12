import os
import sys
from PyQt6 import uic
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHeaderView, QWidget, QPushButton, QTableWidget, QTableWidgetItem
)
from datetime import datetime

def ui_path(filename):
    # Returns the absolute path to the shared ui file under frontend/ui/Event Manager
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "ui", "Event Manager", filename))

# Ensure project root on sys.path so 'controller.*' imports work when running directly
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

class EventManagerStudent(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), "EventManager-Student.ui"), self)

        # Wire common table sizing and signals via controller
        try:
            from controller.module6.event_manager_controller import wire_org_officer_signals
            wire_org_officer_signals(self, ui_path)
        except Exception as e:
            print(f"Error wiring Module 6 student signals: {e}")
            # Fallback: manually connect the attendance button
            if hasattr(self, "ViewAttendanceButton"):
                # Fallback loads Attendance UI and populates from JSON
                from PyQt6 import uic as _fallback_uic
                # Avoid importing controller in fallback; populate directly from attendance_service
                try:
                    from services.attendance_service import load_attendance
                except Exception:
                    def load_attendance(event_name=None):
                        return {"records": []}
                def _fallback_open():
                    attendance_widget = QWidget()
                    _fallback_uic.loadUi(ui_path("Attendance.ui"), attendance_widget)
                    # Populate combos
                    data = load_attendance()
                    combo_event = attendance_widget.findChild(QWidget, "comboBox")
                    if combo_event and hasattr(combo_event, "clear") and hasattr(combo_event, "addItem"):
                        try:
                            combo_event.clear()
                            ev = data.get("event") or "Event: Event Name"
                            combo_event.addItem(ev)
                        except Exception:
                            pass
                    combo_filter = attendance_widget.findChild(QWidget, "comboBox_2")
                    if combo_filter and hasattr(combo_filter, "clear") and hasattr(combo_filter, "addItem"):
                        try:
                            combo_filter.clear()
                            for f in (data.get("filters") or ["All"]):
                                combo_filter.addItem(f)
                        except Exception:
                            pass
                    # Populate table
                    table = attendance_widget.findChild(QTableWidget, "tableWidget")
                    if table:
                        headers = [
                            "Student ID", "Name", "Year", "Section", "Course",
                            "Gender/Sex", "Attendance Status", "Time IN", "Time OUT"
                        ]
                        table.setColumnCount(len(headers))
                        for c, h in enumerate(headers):
                            table.setHorizontalHeaderItem(c, QTableWidgetItem(h))
                        recs = data.get("records", [])
                        table.setRowCount(len(recs))
                        for r, rec in enumerate(recs):
                            table.setItem(r, 0, QTableWidgetItem(rec.get("studentId", "")))
                            table.setItem(r, 1, QTableWidgetItem(rec.get("name", "")))
                            table.setItem(r, 2, QTableWidgetItem(rec.get("year", "")))
                            table.setItem(r, 3, QTableWidgetItem(rec.get("section", "")))
                            table.setItem(r, 4, QTableWidgetItem(rec.get("course", "")))
                            table.setItem(r, 5, QTableWidgetItem(rec.get("gender", "")))
                            table.setItem(r, 6, QTableWidgetItem(rec.get("status", "")))
                            table.setItem(r, 7, QTableWidgetItem(str(rec.get("timeIn", ""))))
                            table.setItem(r, 8, QTableWidgetItem(str(rec.get("timeOut", ""))))
                    # Insert into stacked widget at index 1
                    if hasattr(self, "stackedWidget"):
                        if self.stackedWidget.count() > 1:
                            self.stackedWidget.removeWidget(self.stackedWidget.widget(1))
                            self.stackedWidget.insertWidget(1, attendance_widget)
                        else:
                            self.stackedWidget.insertWidget(1, attendance_widget)
                    self.stackedWidget.setCurrentIndex(1)
                self.ViewAttendanceButton.clicked.connect(_fallback_open)

        # Attendance will be lazy-loaded by the controller when needed

        # Fit tables if present
        if hasattr(self, "EventT_Table") and hasattr(self.EventT_Table, "horizontalHeader"):
            self.EventT_Table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        if hasattr(self, "Events_table") and hasattr(self.Events_table, "horizontalHeader"):
            self.Events_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Apply UI helpers to prevent clipping (buttons/tables)
        try:
            from services.ui_utils import fit_all_buttons, auto_resize_all_tables
            fit_all_buttons(self)
            auto_resize_all_tables(self)
        except Exception:
            pass

        self._load_and_render_schedules()
        # If there's an Upcoming Events button, repurpose it to switch events if multiple proposals exist
        try:
            if hasattr(self, "pushButton_2"):
                self.pushButton_2.setText("Refresh from Proposals")
                self.pushButton_2.clicked.connect(self._load_and_render_schedules)
        except Exception:
            pass

        # Apply QSS to this widget only (use json_paths helper to find project root)
        try:
            from services.json_paths import get_project_root
            project_root = get_project_root()
            qss_path = os.path.join(project_root, "assets", "qss", "module6_styles.qss")
            if os.path.exists(qss_path):
                with open(qss_path, 'r', encoding='utf-8') as f:
                    self.setStyleSheet(f.read())
        except Exception:
            pass

    def show_attendance_page(self):
        self.stackedWidget.setCurrentIndex(1)  # Show attendance page

    def show_main_page(self):
        self.stackedWidget.setCurrentIndex(0)  # Show main page

    # --- Internal helpers for schedules ---
    def _load_and_render_schedules(self) -> None:
        try:
            from services.event_timeline_service import load_timeline
            from services.event_proposal_service import list_proposals
        except Exception:
            load_timeline = None
            list_proposals = None
        # Always show all events from the global timeline
        data = load_timeline() if load_timeline else {"timeline": []}
        timeline_items = data.get("timeline", []) if isinstance(data, dict) else []
        self._populate_weekly_from_timeline(timeline_items)
        self._populate_today_from_timeline(timeline_items)
        # After rendering, ensure table columns/rows fit their contents
        try:
            from services.ui_utils import auto_resize_all_tables
            auto_resize_all_tables(self)
        except Exception:
            pass

    def _populate_weekly_from_timeline(self, items: list[dict]) -> None:
        table = getattr(self, "EventT_Table", None)
        if not isinstance(table, QTableWidget):
            return
        days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        times = [
            "7:00 AM", "8:00 AM", "9:00 AM", "10:00 AM", "11:00 AM",
            "12:00 PM", "1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM",
            "5:00 PM", "6:00 PM", "7:00 PM",
        ]
        # Set headers
        table.setRowCount(len(times))
        table.setColumnCount(len(days))
        for r, label in enumerate(times):
            table.setVerticalHeaderItem(r, QTableWidgetItem(label))
            for c in range(len(days)):
                table.setItem(r, c, QTableWidgetItem(""))
        for c, d in enumerate(days):
            table.setHorizontalHeaderItem(c, QTableWidgetItem(d))
        # Place activities (show event name and activity)
        for it in items:
            day = it.get("day")
            time24 = it.get("time")
            activity = it.get("activity", "")
            event_name = it.get("eventName", "")
            if not (day and time24 and activity and day in days):
                continue
            try:
                label = datetime.strptime(time24, "%H:%M").strftime("%I:%M %p").lstrip("0")
            except Exception:
                label = time24
            if label not in times:
                continue
            r = times.index(label)
            c = days.index(day)
            cell_text = f"{event_name}: {activity}" if event_name else activity
            table.setItem(r, c, QTableWidgetItem(cell_text))

    def _populate_today_from_timeline(self, items: list[dict]) -> None:
        table = getattr(self, "Events_table", None)
        if not isinstance(table, QTableWidget):
            return
        times = [
            "7:00 AM", "8:00 AM", "9:00 AM", "10:00 AM", "11:00 AM",
            "12:00 PM", "1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM",
            "5:00 PM", "6:00 PM", "7:00 PM",
        ]
        today_name = datetime.now().strftime("%A")
        table.setRowCount(len(times))
        table.setColumnCount(1)
        for r, label in enumerate(times):
            table.setVerticalHeaderItem(r, QTableWidgetItem(label))
            table.setItem(r, 0, QTableWidgetItem(""))
        # Filter today's items
        todays = [it for it in items if it.get("day") == today_name]
        for it in todays:
            time24 = it.get("time")
            activity = it.get("activity", "")
            event_name = it.get("eventName", "")
            if not time24:
                continue
            try:
                label = datetime.strptime(time24, "%H:%M").strftime("%I:%M %p").lstrip("0")
            except Exception:
                label = time24
            if label in times:
                r = times.index(label)
                cell_text = f"{event_name}: {activity}" if event_name else activity
                table.setItem(r, 0, QTableWidgetItem(cell_text))

if __name__ == "__main__":
    app = QApplication([])
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    style_qss = os.path.join(project_root, "styles", "style.qss")
    if os.path.exists(style_qss):
        with open(style_qss, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    window = EventManagerStudent()
    window.show()
    app.exec()