import os
from PyQt6.QtWidgets import QWidget, QMainWindow, QDialog
from PyQt6 import uic


class Events(QMainWindow):
    def __init__(self, username: str = "", roles=None, primary_role: str = "", token: str = ""):
        super().__init__()
        # Choose UI based on role: Faculty vs Student/Org Officer
        # Normalize roles to a set of strings for robust checks
        normalized_roles = set(roles or [])
        is_faculty = "faculty" in normalized_roles
        is_org_officer = "org_officer" in normalized_roles
        base_dir = os.path.dirname(__file__)
        users_root = os.path.join(base_dir, "Events", "Users")

        # Ensure project root is on sys.path for controller/service imports
        try:
            import sys as _sys
            frontend_root = os.path.abspath(os.path.join(base_dir, "..", ".."))
            if frontend_root not in _sys.path:
                _sys.path.insert(0, frontend_root)
        except Exception:
            pass

        # Prefer using the Python view classes under Module-6 rather than loading .ui directly
        loaded = None
        try:
            if is_faculty:
                spec_path = os.path.join(users_root, "Faculty", "module6_faculty_event_manager.py")
                from importlib.util import spec_from_file_location, module_from_spec
                spec = spec_from_file_location("module6_faculty", spec_path)
                mod = module_from_spec(spec)
                spec.loader.exec_module(mod)
                loaded = getattr(mod, "FacultyWindow")()
            elif is_org_officer:
                spec_path = os.path.join(users_root, "Student", "module6_orgofficer_event_manager.py")
                from importlib.util import spec_from_file_location, module_from_spec
                spec = spec_from_file_location("module6_orgofficer", spec_path)
                mod = module_from_spec(spec)
                spec.loader.exec_module(mod)
                loaded = getattr(mod, "OrgOfficerWindow")()
            else:
                spec_path = os.path.join(users_root, "Student", "module6_student_event_manager.py")
                from importlib.util import spec_from_file_location, module_from_spec
                spec = spec_from_file_location("module6_student", spec_path)
                mod = module_from_spec(spec)
                spec.loader.exec_module(mod)
                loaded = getattr(mod, "EventManagerStudent")()
        except Exception:
            # Fallback: load the appropriate .ui directly if the view classes cannot be imported
            if is_faculty:
                ui_file = os.path.join(users_root, "Faculty", "EventManager-Faculty.ui")
            elif is_org_officer:
                ui_file = os.path.join(users_root, "Student", "EventManager-OrgOfficer.ui")
            else:
                ui_file = os.path.join(users_root, "Student", "EventManager-Student.ui")
            if not os.path.exists(ui_file):
                raise FileNotFoundError(f"Events UI file not found at '{ui_file}'. Verify the .ui files under 'Module-6_Event_Manager/Users'.")
            uic.loadUi(ui_file, self)
            loaded = None

        # If a view class was loaded, set it as the central widget
        if loaded:
            self.setCentralWidget(loaded)

        # Ensure frontend root is importable
        try:
            import sys as _sys
            frontend_root = os.path.abspath(os.path.join(base_dir, "..", ".."))
            if frontend_root not in _sys.path:
                _sys.path.insert(0, frontend_root)
        except Exception:
            pass

        # Local helper to resolve shared Event Manager UIs

        def _ui_path(filename: str) -> str:
            return os.path.abspath(os.path.join(base_dir, "..", "..", "ui", "Event Manager", filename))

        # Refactored: Open Event Timeline dialog, Add button uses proposal data directly
        def _open_event_timeline_dialog() -> None:
            # Prefer delegating to the loaded view if it implements an open_event_timeline method
            try:
                if loaded and hasattr(loaded, "open_event_timeline"):
                    try:
                        loaded.open_event_timeline()
                        return
                    except Exception:
                        pass
                # Fallback: open shared dialog UI directly
                from services.event_timeline_service import load_timeline
                from PyQt6.QtWidgets import QTableWidgetItem
                dialog = QDialog(self)
                uic.loadUi(_ui_path("Event Timeline.ui"), dialog)
                table = getattr(dialog, "WeekTable_2", None)
                if table:
                    # Set up headers (same as Student Mod 6)
                    days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
                    times = [
                        "7:00 AM", "8:00 AM", "9:00 AM", "10:00 AM", "11:00 AM",
                        "12:00 PM", "1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM",
                        "5:00 PM", "6:00 PM", "7:00 PM",
                    ]
                    table.setRowCount(len(times))
                    table.setColumnCount(len(days))
                    for r, label in enumerate(times):
                        table.setVerticalHeaderItem(r, QTableWidgetItem(label))
                        for c in range(len(days)):
                            table.setItem(r, c, QTableWidgetItem(""))
                    for c, d in enumerate(days):
                        table.setHorizontalHeaderItem(c, QTableWidgetItem(d))
                    # Load and place activities
                    data = load_timeline() if callable(load_timeline) else {"timeline": []}
                    items = data.get("timeline", []) if isinstance(data, dict) else []
                    for it in items:
                        day = it.get("day")
                        time = it.get("time")
                        activity = it.get("activity", "")
                        event_name = it.get("eventName", "")
                        cell_text = f"{event_name}: {activity}" if event_name else activity
                        # Convert time to display header
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
                dialog.exec()
            except Exception as e:
                print(f"Events: failed to open Event Timeline dialog: {e}")

        def _open_request_proposal_dialog() -> None:
            try:
                dialog = QDialog(self)
                uic.loadUi(_ui_path("Request Event Proposal.ui"), dialog)
                # Optional: forward to timeline from within proposal dialog
                try:
                    btn = getattr(dialog, "ViewEventTimeline", None)
                    if btn and hasattr(btn, "clicked"):
                        btn.clicked.connect(_open_event_timeline_dialog)
                except Exception:
                    pass
                dialog.exec()
            except Exception as e:
                print(f"Events: failed to open Request Proposal dialog: {e}")

        def _open_request_reschedule_dialog() -> None:
            try:
                dialog = QDialog(self)
                uic.loadUi(_ui_path("Request Event Reschedule.ui"), dialog)
                try:
                    btn = getattr(dialog, "ViewEventTimeline", None)
                    if btn and hasattr(btn, "clicked"):
                        btn.clicked.connect(_open_event_timeline_dialog)
                except Exception:
                    pass
                dialog.exec()
            except Exception as e:
                print(f"Events: failed to open Request Reschedule dialog: {e}")

        # Wire signals via Module 6 controller
        try:
            from controller.module6.event_manager_controller import wire_faculty_signals, wire_org_officer_signals
            if is_faculty:
                # Provide open_* methods if present
                open_timeline = _open_event_timeline_dialog
                open_resched = _open_request_reschedule_dialog
                open_prop = _open_request_proposal_dialog
                wire_faculty_signals(self, open_timeline, open_resched, open_prop)
            else:
                wire_org_officer_signals(self, _ui_path)
                # Also connect request buttons directly if they exist on this UI
                try:
                    if hasattr(self, "RequestEventProposalButton") and hasattr(self.RequestEventProposalButton, "clicked"):
                        self.RequestEventProposalButton.clicked.connect(_open_request_proposal_dialog)
                    if hasattr(self, "RequestRescheduleButton") and hasattr(self.RequestRescheduleButton, "clicked"):
                        self.RequestRescheduleButton.clicked.connect(_open_request_reschedule_dialog)
                except Exception:
                    pass
        except Exception as e:
            print(f"Events: warning wiring controller signals failed: {e}")


