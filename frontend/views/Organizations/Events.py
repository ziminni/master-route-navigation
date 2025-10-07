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
        users_root = os.path.join(base_dir, "Module-6_Event_Manager", "Users")

        if is_faculty:
            ui_file = os.path.join(users_root, "Faculty", "EventManager-Faculty.ui")
        elif is_org_officer:
            ui_file = os.path.join(users_root, "Student", "EventManager-OrgOfficer.ui")
        else:
            ui_file = os.path.join(users_root, "Student", "EventManager-Student.ui")

        if not os.path.exists(ui_file):
            raise FileNotFoundError(f"Events UI file not found at '{ui_file}'. Verify the .ui files under 'Module-6_Event_Manager/Users'.")

        uic.loadUi(ui_file, self)

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

        # Lightweight dialog openers (no business logic) ---------------------------------
        def _open_add_activity_dialog() -> None:
            try:
                dialog = QDialog(self)
                uic.loadUi(_ui_path("addactivity.ui"), dialog)
                dialog.exec()
            except Exception as e:
                print(f"Events: failed to open Add Activity dialog: {e}")

        def _open_event_timeline_dialog() -> None:
            try:
                dialog = QDialog(self)
                uic.loadUi(_ui_path("Event Timeline.ui"), dialog)
                # Wire Add button just to show Add Activity dialog
                try:
                    add_btn = getattr(dialog, "Event_Add", None)
                    if add_btn and hasattr(add_btn, "clicked"):
                        add_btn.clicked.connect(_open_add_activity_dialog)
                except Exception:
                    pass
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


