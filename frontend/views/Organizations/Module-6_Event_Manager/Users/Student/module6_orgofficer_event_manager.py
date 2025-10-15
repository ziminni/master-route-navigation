import os
import sys
from PyQt6 import uic
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHeaderView, QDialog, QWidget, QPushButton, QInputDialog, QTableWidgetItem, QTableWidget, QHBoxLayout
)

def ui_path(filename):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "ui", "Event Manager", filename))

# Ensure project root is importable for 'controller.*' modules when running directly
try:
    from services.json_paths import get_project_root
    _project_root = get_project_root()
except Exception:
    _project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))) )
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

class EventTimelineDialog(QDialog):
    def __init__(self, parent=None, hide_add=False, hide_edit_delete=False, reschedule_dialog=None):
        super().__init__(parent)
        uic.loadUi(ui_path("Event Timeline.ui"), self)
        if hasattr(self, "WeekTable_2"):
            self.WeekTable_2.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # Hide Add button if requested (for reschedule context)
        if hide_add and hasattr(self, "Event_Add"):
            self.Event_Add.setVisible(False)
        # Hide Edit and Delete buttons if requested (for proposal context)
        if hide_edit_delete:
            if hasattr(self, "Event_Edit"):
                self.Event_Edit.setVisible(False)
            if hasattr(self, "Event_Delete"):
                self.Event_Delete.setVisible(False)
        try:
            from services.event_timeline_service import add_timeline_item, load_timeline, update_timeline_item, delete_timeline_item
            from services.event_proposal_service import list_proposals
        except Exception:
            add_timeline_item = None
            load_timeline = None
            update_timeline_item = None
            delete_timeline_item = None
            list_proposals = None
        self._requested_event = None
        if list_proposals:
            proposals = list_proposals() or []
            if proposals:
                self._requested_event = proposals[0].get("eventName")
        # Only wire Add if not hidden
        if not hide_add and hasattr(self, "Event_Add") and add_timeline_item:
            self.Event_Add.clicked.connect(lambda: self._add_activity_and_close(add_timeline_item))
        # If in reschedule mode, wire Edit to parent's _save_reschedule
        if hide_add and hasattr(self, "Event_Edit") and reschedule_dialog and hasattr(reschedule_dialog, "_save_reschedule"):
            self.Event_Edit.clicked.connect(lambda: self._edit_and_close(reschedule_dialog._save_reschedule))
        elif hasattr(self, "Event_Edit") and update_timeline_item:
            self.Event_Edit.clicked.connect(lambda: self._edit_and_close(lambda: self._edit_timeline(update_timeline_item)))
        if hasattr(self, "Event_Delete"):
            if hide_add and reschedule_dialog and hasattr(reschedule_dialog, "_delete_selected_proposal"):
                # Delete proposal and close both the reschedule dialog and this timeline dialog
                self.Event_Delete.clicked.connect(lambda: (reschedule_dialog._delete_selected_proposal(), reschedule_dialog.accept(), self.accept()))
            elif delete_timeline_item:
                self.Event_Delete.clicked.connect(lambda: self._delete_and_close(delete_timeline_item))
        if load_timeline and hasattr(self, "WeekTable_2"):
            data = load_timeline()
            self._render_timeline_table(data)

    def _add_activity_and_close(self, add_func):
        self._add_activity_direct(add_func)
        self.accept()

    def _edit_and_close(self, edit_func):
        edit_func()
        self.accept()

    def _delete_and_close(self, delete_func):
        self._delete_timeline(delete_func)
        self.accept()


    def _add_activity_direct(self, add_func):
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
        # Use proposal data directly (or default values)
        time_hhmm = self._to_24h(time_label)
        activity = "Activity"  # Or fetch from proposal if needed
        building = ""  # Set if proposal/building info is available
        room = ""      # Set if proposal/room info is available
        if day_label and time_hhmm and activity:
            add_func(day_label, time_hhmm, activity, self._requested_event, building=building, room=room)
            self._place_activity_at(table, day_label, time_hhmm, activity)

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
            event_name = item.get("eventName", "")
            cell_text = f"{event_name}: {activity}" if event_name else activity
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
                table.setItem(row, col, QTableWidgetItem(cell_text))
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
    def __init__(self, parent=None, hide_edit_delete=True):
        super().__init__(parent)
        uic.loadUi(ui_path("Request Event Proposal.ui"), self)
        if hasattr(self, "ViewEventTimeline"):
            self.ViewEventTimeline.clicked.connect(self._save_and_open_event_timeline)
        self._populate_dropdowns()
        # Hide Edit and Delete buttons if requested, just like hide_add for reschedule
        if hide_edit_delete:
            if hasattr(self, "EditProposalButton"):
                self.EditProposalButton.setVisible(False)
            if hasattr(self, "DeleteProposalButton"):
                self.DeleteProposalButton.setVisible(False)
            # Always show Add button
            if hasattr(self, "SaveProposalButton"):
                self.SaveProposalButton.setVisible(True)

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
        # After saving, open the EventTimelineDialog (not RequestProposalDialog)
        dialog = EventTimelineDialog(self, hide_add=False, hide_edit_delete=True)
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
    def _delete_selected_proposal(self):
        try:
            from services.event_proposal_service import delete_proposal_by_name
        except Exception:
            delete_proposal_by_name = None
        if not delete_proposal_by_name:
            return
        if hasattr(self, "comboBox_4"):
            name = self.comboBox_4.currentText()
            if name:
                delete_proposal_by_name(name)
    def _save_reschedule(self):
        try:
            from services.event_proposal_service import list_proposals, get_proposal_by_name, save_proposal
        except Exception:
            return
        if not hasattr(self, "comboBox_4"):
            return
        event_name = self.comboBox_4.currentText()
        if not event_name:
            return
        proposals = list_proposals() or []
        # Find and update the selected proposal
        for proposal in proposals:
            if (proposal.get("eventName") or "").strip().lower() == event_name.strip().lower():
                proposal["building"] = getattr(self.comboBox, "currentText", lambda: "")()
                proposal["description"] = getattr(self.lineEdit_2, "text", lambda: "")()
                proposal["date"] = getattr(self.dateEdit, "date", lambda: None)().toString("yyyy-MM-dd") if hasattr(self, "dateEdit") else ""
                proposal["time"] = getattr(self.timeEdit, "time", lambda: None)().toString("HH:mm") if hasattr(self, "timeEdit") else ""
                proposal["roomName"] = getattr(self.comboBox_3, "currentText", lambda: "")()
                proposal["organizer"] = getattr(self.comboBox_2, "currentText", lambda: "")()
                proposal["budget"] = getattr(self.doubleSpinBox, "value", lambda: 0.0)()
                break
        # Save the updated proposals list
        save_proposal({"proposals": proposals})

    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(ui_path("Request Event Reschedule.ui"), self)
        if hasattr(self, "ViewEventTimeline"):
            self.ViewEventTimeline.clicked.connect(self.open_event_timeline)
        self._populate_dropdowns()

    def open_event_timeline(self):
        dialog = EventTimelineDialog(self, hide_add=True, hide_edit_delete=False, reschedule_dialog=self)
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

        # Apply QSS to this widget only
        qss_path = os.path.join(_project_root, "assets", "qss", "module6_styles.qss")
        if os.path.exists(qss_path):
            with open(qss_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())

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
    try:
        from services.json_paths import get_project_root
        project_root = get_project_root()
    except Exception:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    style_qss = os.path.join(project_root, "assets", "qss", "module6_styles.qss")
    if os.path.exists(style_qss):
        with open(style_qss, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    window = OrgOfficerWindow()
    window.show()
    app.exec()