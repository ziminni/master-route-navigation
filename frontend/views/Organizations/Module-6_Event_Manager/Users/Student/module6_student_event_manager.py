import os
import sys
from PyQt6 import uic
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHeaderView, QWidget, QPushButton, QTableWidget, QTableWidgetItem
)

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

    def show_attendance_page(self):
        self.stackedWidget.setCurrentIndex(1)  # Show attendance page

    def show_main_page(self):
        self.stackedWidget.setCurrentIndex(0)  # Show main page

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