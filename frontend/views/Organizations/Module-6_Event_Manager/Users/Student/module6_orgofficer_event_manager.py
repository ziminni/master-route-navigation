import os
import sys
from PyQt6 import uic
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHeaderView, QDialog, QWidget, QPushButton, QInputDialog, QTableWidgetItem, QTableWidget, QHBoxLayout
)

def ui_path(filename):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "ui", "Event Manager", filename))

# Ensure project root is importable for 'controller.*' modules when running directly
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

class EventTimelineDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(ui_path("Event Timeline.ui"), self)
        if hasattr(self, "WeekTable_2"):
            self.WeekTable_2.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # Hook Add to persist with requested event name if available
        try:
            from services.event_timeline_service import add_timeline_item, load_timeline, update_timeline_item, delete_timeline_item
            from services.event_proposal_service import list_proposals
        except Exception:
            add_timeline_item = None
            load_timeline = None
            update_timeline_item = None
            delete_timeline_item = None
            list_proposals = None
        # Default to first saved proposal as the current event
        self._requested_event = None
        if list_proposals:
            proposals = list_proposals() or []
            if proposals:
                self._requested_event = proposals[0].get("eventName")
        if hasattr(self, "Event_Add") and add_timeline_item:
            self.Event_Add.clicked.connect(lambda: self._open_add_activity_dialog(add_timeline_item))
        if hasattr(self, "Event_Edit") and update_timeline_item:
            self.Event_Edit.clicked.connect(lambda: self._edit_timeline(update_timeline_item))
        if hasattr(self, "Event_Delete") and delete_timeline_item:
            self.Event_Delete.clicked.connect(lambda: self._delete_timeline(delete_timeline_item))
        # Render existing timeline for current event
        if load_timeline and hasattr(self, "WeekTable_2") and self._requested_event:
            data = load_timeline(self._requested_event)
            self._render_timeline_table(data)

    def _open_add_activity_dialog(self, add_func):
        table = getattr(self, "WeekTable_2", None)
        if table is None:
            return
        row = table.currentRow()
        col = table.currentColumn()
        if row < 0 or col < 0:
            return
        v_item = table.verticalHeaderItem(row)
        h_item = table.horizontalHeaderItem(col)
        time_label = v_item.text() if v_item else ""
        day_label = h_item.text() if h_item else ""
        if not time_label or not day_label:
            return
        dialog = QDialog(self)
        uic.loadUi(ui_path("addactivity.ui"), dialog)
        # Apply button closes dialog
        try:
            apply_btn = getattr(dialog, "ApplyActivity", None)
            if apply_btn and hasattr(apply_btn, "clicked"):
                apply_btn.clicked.connect(dialog.accept)
        except Exception:
            pass
        # Populate building/rooms
        try:
            from services.events_metadata_service import load_buildings, load_rooms
            if hasattr(dialog, "building"):
                for b in load_buildings():
                    dialog.building.addItem(b.get("name", ""), b.get("id"))
            def refresh_rooms_for_dialog():
                if not hasattr(dialog, "roomname"):
                    return
                dialog.roomname.clear()
                sel_building_id = None
                if hasattr(dialog, "building") and hasattr(dialog.building, "currentData"):
                    sel_building_id = dialog.building.currentData()
                for r in load_rooms(sel_building_id):
                    dialog.roomname.addItem(r.get("name", ""))
            if hasattr(dialog, "building") and hasattr(dialog.building, "currentIndexChanged"):
                dialog.building.currentIndexChanged.connect(lambda _: refresh_rooms_for_dialog())
            refresh_rooms_for_dialog()
        except Exception:
            pass
        if dialog.exec() == dialog.DialogCode.Accepted:
            try:
                time_hhmm = self._to_24h(time_label)
                activity = "Activity"
                building = getattr(dialog.building, "currentText", lambda: "")() if hasattr(dialog, "building") else ""
                room = getattr(dialog.roomname, "currentText", lambda: "")() if hasattr(dialog, "roomname") else ""
                if day_label and time_hhmm and activity:
                    add_func(day_label, time_hhmm, activity, self._requested_event, building=building, room=room)
                    self._place_activity_at(table, day_label, time_hhmm, activity)
            except Exception:
                pass

    def _to_24h(self, label: str) -> str:
        try:
            from datetime import datetime
            dt = datetime.strptime(label.replace("\u200f", "").strip(), "%I:%M %p")
            return dt.strftime("%H:%M")
        except Exception:
            return label

    def _render_timeline_table(self, data):
        table = getattr(self, "WeekTable_2", None)
        if table is None:
            return
        items = data.get("timeline", [])
        for item in items:
            day = item.get("day")
            time = item.get("time")
            activity = item.get("activity", "")
            try:
                from datetime import datetime
                label = datetime.strptime(time, "%H:%M").strftime("%I:%M %p").lstrip("0")
            except Exception:
                label = time
            row = -1
            col = -1
            for r in range(table.rowCount()):
                vh = table.verticalHeaderItem(r)
                if vh and vh.text() == label:
                    row = r
                    break
            for c in range(table.columnCount()):
                hh = table.horizontalHeaderItem(c)
                if hh and hh.text() == day:
                    col = c
                    break
            if row >= 0 and col >= 0:
                table.setItem(row, col, QTableWidgetItem(activity))
    def _place_activity_at(self, table, day: str, time_hhmm: str, activity: str):
        try:
            from datetime import datetime
            label = datetime.strptime(time_hhmm, "%H:%M").strftime("%I:%M %p").lstrip("0")
        except Exception:
            label = time_hhmm
        row = -1
        col = -1
        for r in range(table.rowCount()):
            vh = table.verticalHeaderItem(r)
            if vh and vh.text() == label:
                row = r
                break
        for c in range(table.columnCount()):
            hh = table.horizontalHeaderItem(c)
            if hh and hh.text() == day:
                col = c
                break
        if row >= 0 and col >= 0:
            table.setItem(row, col, QTableWidgetItem(activity))

    def _edit_timeline(self, update_func):
        table = getattr(self, "WeekTable_2", None)
        if table is None:
            return
        row = table.currentRow()
        col = table.currentColumn()
        if row < 0 or col < 0:
            return
        v_item = table.verticalHeaderItem(row)
        h_item = table.horizontalHeaderItem(col)
        time_label = v_item.text() if v_item else ""
        day_label = h_item.text() if h_item else ""
        if not time_label or not day_label:
            return
        current_item = table.item(row, col)
        current_text = current_item.text() if current_item else ""
        text, ok = QInputDialog.getText(self, "Edit Timeline Item", f"Edit activity for {day_label} @ {time_label}:", text=current_text)
        if not ok:
            return
        hhmm = self._to_24h(time_label)
        if update_func(day_label, hhmm, text, self._requested_event):
            table.setItem(row, col, QTableWidgetItem(text))

    def _delete_timeline(self, delete_func):
        table = getattr(self, "WeekTable_2", None)
        if table is None:
            return
        row = table.currentRow()
        col = table.currentColumn()
        if row < 0 or col < 0:
            return
        v_item = table.verticalHeaderItem(row)
        h_item = table.horizontalHeaderItem(col)
        time_label = v_item.text() if v_item else ""
        day_label = h_item.text() if h_item else ""
        if not time_label or not day_label:
            return
        hhmm = self._to_24h(time_label)
        if delete_func(day_label, hhmm, self._requested_event):
            table.setItem(row, col, QTableWidgetItem(""))

class RequestProposalDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(ui_path("Request Event Proposal.ui"), self)
        if hasattr(self, "ViewEventTimeline"):
            self.ViewEventTimeline.clicked.connect(self._save_and_open_event_timeline)
        self._populate_dropdowns()
        # Add Save/Update and Delete buttons
        try:
            container = getattr(self, "verticalLayoutWidget", None)
            layout = container.layout() if container and hasattr(container, "layout") else None
            if layout:
                btn_row = QHBoxLayout()
                save_btn = QPushButton("Save/Update Proposal", self)
                del_btn = QPushButton("Delete Proposal", self)
                save_btn.clicked.connect(self._save_only)
                del_btn.clicked.connect(self._delete_current)
                btn_row.addWidget(save_btn)
                btn_row.addWidget(del_btn)
                layout.addLayout(btn_row)
        except Exception:
            pass

    def _populate_dropdowns(self):
        try:
            from services.events_metadata_service import load_buildings, load_rooms, load_organizers
        except Exception:
            return
        if hasattr(self, "comboBox"):
            self.comboBox.clear()
            for b in load_buildings():
                self.comboBox.addItem(b.get("name", ""), b.get("id"))
        def refresh_rooms():
            if not hasattr(self, "comboBox_3"):
                return
            self.comboBox_3.clear()
            sel_building_id = None
            if hasattr(self, "comboBox") and hasattr(self.comboBox, "currentData"):
                sel_building_id = self.comboBox.currentData()
            for r in load_rooms(sel_building_id):
                self.comboBox_3.addItem(r.get("name", ""))
        if hasattr(self, "comboBox") and hasattr(self.comboBox, "currentIndexChanged"):
            self.comboBox.currentIndexChanged.connect(lambda _: refresh_rooms())
        refresh_rooms()
        if hasattr(self, "comboBox_2"):
            self.comboBox_2.clear()
            for org in load_organizers():
                self.comboBox_2.addItem(org.get("name", ""), org.get("id"))

    def _save_and_open_event_timeline(self):
        try:
            from services.event_proposal_service import add_proposal
        except Exception:
            add_proposal = None
        if add_proposal:
            payload = {
                "eventName": getattr(self.lineEdit, "text", lambda: "")(),
                "building": getattr(self.comboBox, "currentText", lambda: "")(),
                "description": getattr(self.lineEdit_2, "text", lambda: "")(),
                "date": getattr(self.dateEdit, "date", lambda: None)().toString("yyyy-MM-dd") if hasattr(self, "dateEdit") else "",
                "time": getattr(self.timeEdit, "time", lambda: None)().toString("HH:mm") if hasattr(self, "timeEdit") else "",
                "roomName": getattr(self.comboBox_3, "currentText", lambda: "")(),
                "organizer": getattr(self.comboBox_2, "currentText", lambda: "")(),
                "budget": getattr(self.doubleSpinBox, "value", lambda: 0.0)(),
            }
            add_proposal(payload)
        dialog = EventTimelineDialog(self)
        dialog.exec()

    def _save_only(self):
        try:
            from services.event_proposal_service import add_proposal
        except Exception:
            add_proposal = None
        if not add_proposal:
            return
        payload = {
            "eventName": getattr(self.lineEdit, "text", lambda: "")(),
            "building": getattr(self.comboBox, "currentText", lambda: "")(),
            "description": getattr(self.lineEdit_2, "text", lambda: "")(),
            "date": getattr(self.dateEdit, "date", lambda: None)().toString("yyyy-MM-dd") if hasattr(self, "dateEdit") else "",
            "time": getattr(self.timeEdit, "time", lambda: None)().toString("HH:mm") if hasattr(self, "timeEdit") else "",
            "roomName": getattr(self.comboBox_3, "currentText", lambda: "")(),
            "organizer": getattr(self.comboBox_2, "currentText", lambda: "")(),
            "budget": getattr(self.doubleSpinBox, "value", lambda: 0.0)(),
        }
        add_proposal(payload)

    def _delete_current(self):
        try:
            from services.event_proposal_service import delete_proposal_by_name
        except Exception:
            delete_proposal_by_name = None
        if not delete_proposal_by_name:
            return
        name = getattr(self.lineEdit, "text", lambda: "")()
        if name:
            delete_proposal_by_name(name)

class RequestRescheduleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(ui_path("Request Event Reschedule.ui"), self)
        if hasattr(self, "ViewEventTimeline"):
            self.ViewEventTimeline.clicked.connect(self.open_event_timeline)
        self._populate_dropdowns()

    def open_event_timeline(self):
        dialog = EventTimelineDialog(self)
        dialog.exec()

    def _populate_dropdowns(self):
        try:
            from services.events_metadata_service import load_buildings, load_rooms, load_organizers
            from services.event_proposal_service import list_proposals, get_proposal_by_name
        except Exception:
            return
        if hasattr(self, "comboBox_4"):
            self.comboBox_4.clear()
            for p in list_proposals():
                name = p.get("eventName", "")
                if name:
                    self.comboBox_4.addItem(name)
            if hasattr(self.comboBox_4, "currentIndexChanged"):
                self.comboBox_4.currentIndexChanged.connect(lambda _: self._apply_selected_event(get_proposal_by_name))
        if hasattr(self, "comboBox"):
            self.comboBox.clear()
            for b in load_buildings():
                self.comboBox.addItem(b.get("name", ""), b.get("id"))
        def refresh_rooms():
            if not hasattr(self, "comboBox_3"):
                return
            self.comboBox_3.clear()
            sel_building_id = None
            if hasattr(self, "comboBox") and hasattr(self.comboBox, "currentData"):
                sel_building_id = self.comboBox.currentData()
            for r in load_rooms(sel_building_id):
                self.comboBox_3.addItem(r.get("name", ""))
        if hasattr(self, "comboBox") and hasattr(self.comboBox, "currentIndexChanged"):
            self.comboBox.currentIndexChanged.connect(lambda _: refresh_rooms())
        refresh_rooms()
        if hasattr(self, "comboBox_2"):
            self.comboBox_2.clear()
            for org in load_organizers():
                self.comboBox_2.addItem(org.get("name", ""), org.get("id"))

    def _apply_selected_event(self, get_proposal_by_name):
        if not hasattr(self, "comboBox_4"):
            return
        name = self.comboBox_4.currentText()
        if not name:
            return
        proposal = get_proposal_by_name(name) or {}
        if hasattr(self, "comboBox"):
            idx = self.comboBox.findText(proposal.get("building", ""))
            if idx >= 0:
                self.comboBox.setCurrentIndex(idx)
        if hasattr(self, "comboBox_3"):
            room_name = proposal.get("roomName", "")
            idx = self.comboBox_3.findText(room_name)
            if idx >= 0:
                self.comboBox_3.setCurrentIndex(idx)
        if hasattr(self, "comboBox_2"):
            idx = self.comboBox_2.findText(proposal.get("organizer", ""))
            if idx >= 0:
                self.comboBox_2.setCurrentIndex(idx)
        # Description
        if hasattr(self, "lineEdit_2") and hasattr(self.lineEdit_2, "setText"):
            try:
                self.lineEdit_2.setText(proposal.get("description", ""))
            except Exception:
                pass
        # Budget
        if hasattr(self, "doubleSpinBox") and hasattr(self.doubleSpinBox, "setValue"):
            try:
                val = float(proposal.get("budget", 0.0) or 0.0)
                self.doubleSpinBox.setValue(val)
            except Exception:
                pass
        try:
            if hasattr(self, "dateEdit") and proposal.get("date"):
                from PyQt6.QtCore import QDate
                y, m, d = [int(x) for x in proposal["date"].split("-")]
                self.dateEdit.setDate(QDate(y, m, d))
            if hasattr(self, "timeEdit") and proposal.get("time"):
                from PyQt6.QtCore import QTime
                hh, mm = [int(x) for x in proposal["time"].split(":")]
                self.timeEdit.setTime(QTime(hh, mm))
        except Exception:
            pass

class AttendanceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(ui_path("Attendance.ui"), self)
        if hasattr(self, "tableWidget"):
            self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            self.tableWidget.resizeRowsToContents()
        if hasattr(self, "pushButton_4"):
            self.pushButton_4.clicked.connect(self.close)

class OrgOfficerWindow(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), "EventManager-OrgOfficer.ui"), self)

        # Attendance will be lazy-loaded by the controller when needed

        # Wire common table sizing and signals via controller
        try:
            from controller.module6.event_manager_controller import wire_org_officer_signals
            wire_org_officer_signals(self, ui_path)
        except Exception as e:
            print(f"Error wiring Module 6 org officer signals: {e}")
            # Fallback: load Attendance UI and populate from JSON
            if hasattr(self, "ViewAttendanceButton"):
                from PyQt6 import uic as _fallback_uic
                from controller.module6.event_manager_controller import _populate_attendance_table as _fallback_pop
                def _fallback_open():
                    attendance_widget = QWidget()
                    _fallback_uic.loadUi(ui_path("Attendance.ui"), attendance_widget)
                    table = attendance_widget.findChild(QTableWidget, "tableWidget")
                    if table:
                        _fallback_pop(table)
                    if hasattr(self, "stackedWidget"):
                        if self.stackedWidget.count() > 1:
                            self.stackedWidget.removeWidget(self.stackedWidget.widget(1))
                            self.stackedWidget.insertWidget(1, attendance_widget)
                        else:
                            self.stackedWidget.insertWidget(1, attendance_widget)
                    self.stackedWidget.setCurrentIndex(1)
                self.ViewAttendanceButton.clicked.connect(_fallback_open)

        # Make all table columns fit the table width and rows fit contents
        for table_name in [
            "PendingTable", "Events_table_3", "Events_table_4",
            "Events_table_6", "Events_table_7", "tableWidget"
        ]:
            table = getattr(self, table_name, None)
            if table:
                table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                table.resizeRowsToContents()

        # Connect new dialog buttons
        if hasattr(self, "RequestRescheduleButton"):
            self.RequestRescheduleButton.clicked.connect(self.open_request_reschedule)
        if hasattr(self, "RequestEventProposalButton"):
            self.RequestEventProposalButton.clicked.connect(self.open_request_proposal)

    def show_attendance_page(self):
        self.stackedWidget.setCurrentIndex(1)  # Show attendance page

    def show_main_page(self):
        self.stackedWidget.setCurrentIndex(0)  # Show main page

    def open_event_timeline(self):
        dialog = EventTimelineDialog(self)
        dialog.exec()

    def open_request_proposal(self):
        dialog = RequestProposalDialog(self)
        dialog.exec()

    def open_request_reschedule(self):
        dialog = RequestRescheduleDialog(self)
        dialog.exec()

    def open_attendance_dialog(self):
        dialog = AttendanceDialog(self)
        dialog.exec()

if __name__ == "__main__":
    app = QApplication([])
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    style_qss = os.path.join(project_root, "styles", "style.qss")
    if os.path.exists(style_qss):
        with open(style_qss, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    window = OrgOfficerWindow()
    window.show()
    app.exec()