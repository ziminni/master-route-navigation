import os
from PyQt6 import uic
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHeaderView, QDialog, QInputDialog, QTableWidgetItem, QPushButton, QHBoxLayout
)
#TODO
def ui_path(filename):
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
            
        # Store reschedule_dialog reference for later use
        self.reschedule_dialog = reschedule_dialog
        
        if not hide_add and hasattr(self, "Event_Add") and add_timeline_item:
            self.Event_Add.clicked.connect(lambda: self._add_timeline(add_timeline_item))
            
        # FIXED: Edit button now closes dialog after successful edit
        if hasattr(self, "Event_Edit") and update_timeline_item:
            if hide_add and reschedule_dialog and hasattr(reschedule_dialog, "_save_reschedule"):
                # In reschedule mode: save reschedule AND close both dialogs
                self.Event_Edit.clicked.connect(self._edit_and_close_reschedule)
            else:
                # Normal mode: edit timeline and close this dialog
                self.Event_Edit.clicked.connect(lambda: self._edit_timeline_and_close(update_timeline_item))
                
        # FIXED: Delete button logic consolidated
        if hasattr(self, "Event_Delete"):
            if hide_add and reschedule_dialog and hasattr(reschedule_dialog, "_delete_selected_proposal"):
                # In reschedule mode: delete proposal and close both dialogs
                self.Event_Delete.clicked.connect(self._delete_and_close_reschedule)
            elif delete_timeline_item:
                # Normal mode: delete timeline and close this dialog
                self.Event_Delete.clicked.connect(lambda: self._delete_timeline_and_close(delete_timeline_item))
                
        if load_timeline and hasattr(self, "WeekTable_2"):
            data = load_timeline()
            self._render_timeline_table(data)

    def _edit_and_close_reschedule(self):
        """Edit in reschedule mode: save reschedule and close both dialogs"""
        if self.reschedule_dialog and hasattr(self.reschedule_dialog, "_save_reschedule"):
            self.reschedule_dialog._save_reschedule()
            self.reschedule_dialog.accept()  # Close reschedule dialog
            self.accept()  # Close timeline dialog

    def _delete_and_close_reschedule(self):
        """Delete in reschedule mode: delete proposal and close both dialogs"""
        if self.reschedule_dialog and hasattr(self.reschedule_dialog, "_delete_selected_proposal"):
            self.reschedule_dialog._delete_selected_proposal()
            self.reschedule_dialog.accept()  # Close reschedule dialog
            self.accept()  # Close timeline dialog

    def _edit_timeline_and_close(self, update_func):
        """Edit timeline and close dialog after successful update"""
        if self._edit_timeline(update_func):
            self.accept()  # Close dialog after successful edit

    def _delete_timeline_and_close(self, delete_func):
        """Delete timeline and close dialog after successful deletion"""
        if self._delete_timeline(delete_func):
            self.accept()  # Close dialog after successful deletion

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

    def _edit_timeline(self, update_func):
        """Edit timeline item - returns True if successful"""
        table = getattr(self, "WeekTable_2", None)
        if table is None:
            return False
        row = table.currentRow()
        col = table.currentColumn()
        if row < 0 or col < 0:
            return False
        v_item = table.verticalHeaderItem(row)
        h_item = table.horizontalHeaderItem(col)
        time_label = v_item.text() if v_item else ""
        day_label = h_item.text() if h_item else ""
        if not time_label or not day_label:
            return False
        current_item = table.item(row, col)
        current_text = current_item.text() if current_item else ""
        text, ok = QInputDialog.getText(self, "Edit Timeline Item", f"Edit activity for {day_label} @ {time_label}:", text=current_text)
        if not ok or not text:
            return False
        hhmm = self._to_24h(time_label)
        event_name = None
        try:
            from services.event_proposal_service import load_proposal
            prop = load_proposal() or {}
            event_name = prop.get("eventName")
        except Exception:
            pass
        success = update_func(day_label, hhmm, text, event_name)
        if success:
            table.setItem(row, col, QTableWidgetItem(text))
        return success

    def _delete_timeline(self, delete_func):
        """Delete timeline item - returns True if successful"""
        table = getattr(self, "WeekTable_2", None)
        if table is None:
            return False
        row = table.currentRow()
        col = table.currentColumn()
        if row < 0 or col < 0:
            return False
        v_item = table.verticalHeaderItem(row)
        h_item = table.horizontalHeaderItem(col)
        time_label = v_item.text() if v_item else ""
        day_label = h_item.text() if h_item else ""
        if not time_label or not day_label:
            return False
        hhmm = self._to_24h(time_label)
        event_name = None
        try:
            from services.event_proposal_service import load_proposal
            prop = load_proposal() or {}
            event_name = prop.get("eventName")
        except Exception:
            pass
        success = delete_func(day_label, hhmm, event_name)
        if success:
            table.setItem(row, col, QTableWidgetItem(""))
        return success

    def _add_timeline(self, add_func):
        """Add timeline item - stays open for multiple additions"""
        # Keep this as-is since users might want to add multiple items
        day, ok1 = QInputDialog.getText(self, "Add Timeline Item", "Enter day (e.g., Monday):")
        if not ok1 or not day:
            return
        time, ok2 = QInputDialog.getText(self, "Add Timeline Item", "Enter time (e.g., 14:30):")
        if not ok2 or not time:
            return
        activity, ok3 = QInputDialog.getText(self, "Add Timeline Item", "Enter activity:")
        if not ok3 or not activity:
            return
        
        event_name = None
        try:
            from services.event_proposal_service import load_proposal
            prop = load_proposal() or {}
            event_name = prop.get("eventName")
        except Exception:
            pass
        
        if add_func(day, time, activity, event_name):
            # Reload and refresh the table
            try:
                from services.event_timeline_service import load_timeline
                data = load_timeline()
                self._render_timeline_table(data)
            except Exception:
                pass

# ... rest of your classes (RequestProposalDialog, RequestRescheduleDialog, etc.) remain the same ...