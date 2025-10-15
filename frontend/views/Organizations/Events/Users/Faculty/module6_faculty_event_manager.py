import os
from PyQt6 import uic
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHeaderView, QDialog, QInputDialog, QTableWidgetItem, QPushButton, QHBoxLayout
)

def ui_path(filename):
    # Returns the absolute path to the shared ui file under frontend/ui/Event Manager
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "ui", "Event Manager", filename))

class EventTimelineDialog(QDialog):
    def __init__(self, parent=None, hide_add=False, reschedule_dialog=None):
        super().__init__(parent)
        uic.loadUi(ui_path("Event Timeline.ui"), self)
        if hasattr(self, "WeekTable_2"):
            self.WeekTable_2.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        if hide_add and hasattr(self, "Event_Add"):
            self.Event_Add.setVisible(False)
        try:
            from services.event_timeline_service import add_timeline_item, load_timeline, update_timeline_item, delete_timeline_item
            from services.event_proposal_service import load_proposal
        except Exception:
            add_timeline_item = None
            load_timeline = None
            update_timeline_item = None
            delete_timeline_item = None
            load_proposal = None
        if not hide_add and hasattr(self, "Event_Add") and add_timeline_item:
            self.Event_Add.clicked.connect(lambda: self._add_timeline(add_timeline_item))
        # If in reschedule mode, wire Edit to parent's _save_reschedule
        if hide_add and hasattr(self, "Event_Edit") and reschedule_dialog and hasattr(reschedule_dialog, "_save_reschedule"):
            self.Event_Edit.clicked.connect(reschedule_dialog._save_reschedule)
        elif hasattr(self, "Event_Edit") and update_timeline_item:
            self.Event_Edit.clicked.connect(lambda: self._edit_timeline(update_timeline_item))
        if hasattr(self, "Event_Delete"):
            if hide_add and reschedule_dialog and hasattr(reschedule_dialog, "_delete_selected_proposal"):
                # Delete proposal and close both the reschedule dialog and this timeline dialog
                self.Event_Delete.clicked.connect(lambda: (reschedule_dialog._delete_selected_proposal(), reschedule_dialog.accept(), self.accept()))
            elif delete_timeline_item:
                self.Event_Delete.clicked.connect(lambda: self._delete_timeline(delete_timeline_item))
        if load_timeline and hasattr(self, "WeekTable_2"):
            data = load_timeline()
            self._render_timeline_table(data)


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
            # Show as 'EventName: Activity' if eventName exists
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
        event_name = None
        try:
            from services.event_proposal_service import load_proposal
            prop = load_proposal() or {}
            event_name = prop.get("eventName")
        except Exception:
            pass
        if update_func(day_label, hhmm, text, event_name):
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
        event_name = None
        try:
            from services.event_proposal_service import load_proposal
            prop = load_proposal() or {}
            event_name = prop.get("eventName")
        except Exception:
            pass
        if delete_func(day_label, hhmm, event_name):
            table.setItem(row, col, QTableWidgetItem(""))

class RequestProposalDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(ui_path("Request Event Proposal.ui"), self)
        if hasattr(self, "ViewEventTimeline"):
            self.ViewEventTimeline.clicked.connect(self._save_and_open_event_timeline)
        # Populate dropdowns
        self._populate_dropdowns()
        # Add Save and Delete buttons programmatically
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
        # Buildings -> comboBox
        if hasattr(self, "comboBox"):
            self.comboBox.clear()
            buildings = load_buildings()
            for b in buildings:
                self.comboBox.addItem(b.get("name", ""), b.get("id"))
        # Rooms -> comboBox_3 (filtered by selected building)
        def refresh_rooms():
            if not hasattr(self, "comboBox_3"):
                return
            self.comboBox_3.clear()
            sel_building_id = None
            if hasattr(self, "comboBox") and hasattr(self.comboBox, "currentData"):
                sel_building_id = self.comboBox.currentData()
            rooms = load_rooms(sel_building_id)
            for r in rooms:
                self.comboBox_3.addItem(r.get("name", ""))
        if hasattr(self, "comboBox") and hasattr(self.comboBox, "currentIndexChanged"):
            self.comboBox.currentIndexChanged.connect(lambda _: refresh_rooms())
        refresh_rooms()
        # Organizers -> comboBox_2
        if hasattr(self, "comboBox_2"):
            self.comboBox_2.clear()
            for org in load_organizers():
                self.comboBox_2.addItem(org.get("name", ""), org.get("id"))

    def _save_and_open_event_timeline(self):
        # Save/Update proposal into proposals list (append/dedupe by name)
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
        # Populate dropdowns
        self._populate_dropdowns()

    def open_event_timeline(self):
        dialog = EventTimelineDialog(self, hide_add=True, reschedule_dialog=self)
        dialog.exec()

    def _populate_dropdowns(self):
        try:
            from services.events_metadata_service import load_buildings, load_rooms, load_organizers
            from services.event_proposal_service import list_proposals, get_proposal_by_name
        except Exception:
            return
        # Event Name choices (from all saved proposals)
        if hasattr(self, "comboBox_4"):
            self.comboBox_4.clear()
            for p in list_proposals():
                name = p.get("eventName", "")
                if name:
                    self.comboBox_4.addItem(name)
            if hasattr(self.comboBox_4, "currentIndexChanged"):
                self.comboBox_4.currentIndexChanged.connect(lambda _: self._apply_selected_event(get_proposal_by_name))
        # Buildings -> comboBox
        if hasattr(self, "comboBox"):
            self.comboBox.clear()
            for b in load_buildings():
                self.comboBox.addItem(b.get("name", ""), b.get("id"))
        # Rooms -> comboBox_3 (filtered)
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
        # Organizers -> comboBox_2
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
        # Set Building
        if hasattr(self, "comboBox"):
            idx = self.comboBox.findText(proposal.get("building", ""))
            if idx >= 0:
                self.comboBox.setCurrentIndex(idx)
        # Refresh rooms to match building then set room
        if hasattr(self, "comboBox_3"):
            room_name = proposal.get("roomName", "")
            idx = self.comboBox_3.findText(room_name)
            if idx >= 0:
                self.comboBox_3.setCurrentIndex(idx)
        # Organizer
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
        # Date/Time
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

class FacultyWindow(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), "EventManager-Faculty.ui"), self)

        try:
            import sys
            from services.json_paths import get_project_root
            project_root = get_project_root()
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
        except Exception:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))
            try:
                import sys
                if project_root not in sys.path:
                    sys.path.insert(0, project_root)
            except Exception:
                pass

        # Wire signals via controller
        try:
            from controller.module6.event_manager_controller import wire_faculty_signals
            wire_faculty_signals(self, self.open_event_timeline, self.open_request_reschedule, self.open_request_proposal)
        except Exception:
            pass

        # Apply QSS to this widget only
        qss_path = os.path.join(project_root, "assets", "qss", "module6_styles.qss")
        if os.path.exists(qss_path):
            with open(qss_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())

    def open_event_timeline(self):
        dialog = EventTimelineDialog(self)
        dialog.exec()

    def open_request_proposal(self):
        dialog = RequestProposalDialog(self)
        dialog.exec()

    def open_request_reschedule(self):
        dialog = RequestRescheduleDialog(self)
        dialog.exec()


# Move the __main__ block to the end and match module 3 style
if __name__ == "__main__":
    app = QApplication([])
    try:
        from services.json_paths import get_project_root
        project_root = get_project_root()
    except Exception:
        project_root = os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(
                            os.path.dirname(__file__)
                        )
                    )
                )
            )
        )
    qss_path = os.path.join(project_root, "assets", "qss", "module6_styles.qss")
    if os.path.exists(qss_path):
        with open(qss_path, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    window = FacultyWindow()
    window.show()
    app.exec()