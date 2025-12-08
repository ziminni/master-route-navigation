from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import QMessageBox
from typing import Dict
from ..Base.faculty_admin_base import FacultyAdminBase
from ..Base.manager_base import ManagerBase
from widgets.orgs_custom_widgets.adviser_assign_dialog import AdviserAssignDialog
from widgets.orgs_custom_widgets.pending_officer_dialog import PendingOfficerDialog
import datetime

class Dean(ManagerBase, FacultyAdminBase):
    """
    Dean view – with full control:
    - Assign advisers
    - Approve/Reject officer position changes
    - See pending changes clearly via top button
    """

    def __init__(self, dean_name: str):
        FacultyAdminBase.__init__(self, name=dean_name)
        ManagerBase.__init__(self)
        self.pending_btn = None
        self._per_org_pending_btn = None
        self.load_orgs()

    def load_orgs(self, search_text: str = "") -> None:
        super().load_orgs(search_text)
        self._update_pending_button()

    def load_branches(self, search_text: str = "") -> None:
        super().load_branches(search_text)
        self._update_pending_button()
            
    def _update_pending_button(self):
            """Show global pending changes button on landing page"""
            if self.pending_btn and self.pending_btn.parent():
                self.ui.horizontalLayout_2.removeWidget(self.pending_btn)
                self.pending_btn.deleteLater()
                self.pending_btn = None

            try:
                organizations = self._load_data()
            except:
                return

            total_pending = 0
            first_pending_org = None

            for org in organizations:
                pending_count = len(org.get("pending_officers", []))
                total_pending += pending_count
                if pending_count > 0 and not first_pending_org:
                    first_pending_org = org

                for branch in org.get("branches", []):
                    branch_pending = len(branch.get("pending_officers", []))
                    total_pending += branch_pending
                    if branch_pending > 0 and not first_pending_org:
                        first_pending_org = branch

            if total_pending == 0:
                return

            self.pending_btn = QtWidgets.QPushButton(f"Pending Changes ({total_pending})")
            self.pending_btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
            self.pending_btn.setStyleSheet("""
                QPushButton {
                    background: #F2C94C;
                    color: black;
                    font-weight: bold;
                    border-radius: 20px;
                    padding: 10px 20px;
                    border: 2px solid #F2C94C;
                    font-size: 14px;
                }
                QPushButton:hover { background: #e0b843; }
            """)

            self._first_pending_org = first_pending_org
            self.pending_btn.clicked.connect(self._open_first_pending_dialog)

            back_idx = self.ui.horizontalLayout_2.indexOf(self.ui.back_btn)
            if back_idx != -1:
                self.ui.horizontalLayout_2.insertWidget(back_idx, self.pending_btn)
            else:
                self.ui.horizontalLayout_2.addWidget(self.pending_btn)

    def _open_first_pending_dialog(self):
        if not hasattr(self, "_first_pending_org") or not self._first_pending_org:
            QMessageBox.information(self, "No Changes", "No pending officer changes found.")
            return

        self.current_org = self._first_pending_org
        dialog = PendingOfficerDialog(self.current_org, self, self)
        dialog.exec()
        self._update_pending_button()

        if self.ui.stacked_widget.currentIndex() == 1:
            self.show_org_details(self.current_org)

    def show_org_details(self, org_data: Dict) -> None:
            super().show_org_details(org_data)
            self.current_org = org_data
            self.ui.view_members_btn.setText("Manage Members")

            self._remove_per_org_pending_btn()
            
            pending_count = len(org_data.get("pending_officers", []))
            if pending_count > 0:
                btn = QtWidgets.QPushButton(f"Pending ({pending_count})")
                btn.setStyleSheet("background:#F2C94C;color:black;font-weight:bold;border-radius:20px;padding:8px 16px;")
                btn.clicked.connect(lambda: PendingOfficerDialog(org_data, self, self).exec())
                
                self._per_org_pending_btn = btn
                idx = self.ui.horizontalLayout_2.indexOf(self.ui.back_btn)
                self.ui.horizontalLayout_2.insertWidget(idx, self._per_org_pending_btn)

            self._update_pending_button()
    
    def _remove_per_org_pending_btn(self):
        if self._per_org_pending_btn and self._per_org_pending_btn.parent():
            self.ui.horizontalLayout_2.removeWidget(self._per_org_pending_btn)
            self._per_org_pending_btn.deleteLater()
            self._per_org_pending_btn = None

    def _return_to_prev_page(self) -> None:
        self._remove_per_org_pending_btn()
        super()._return_to_prev_page()

    def _show_current_adviser(self):
        if hasattr(self, "adviser_label") and self.adviser_label:
            self.ui.verticalLayout_10.removeWidget(self.adviser_label)
            self.adviser_label.deleteLater()

        adviser = self.current_org.get("adviser") or "Not Assigned"
        self.adviser_label = QtWidgets.QLabel(f"Faculty Adviser: <b>{adviser}</b>")
        self.adviser_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.adviser_label.setStyleSheet("""
            QLabel {
                color: #084924;
                font-size: 13px;
                background: #e8f5e8;
                padding: 12px;
                border-radius: 12px;
                border: 2px solid #084924;
                margin: 10px 0;
            }
        """)

        brief_idx = self.ui.verticalLayout_10.indexOf(self.ui.brief_btn)
        if brief_idx != -1:
            self.ui.verticalLayout_10.insertWidget(brief_idx, self.adviser_label)
        else:
            self.ui.verticalLayout_10.insertWidget(2, self.adviser_label)

    def _open_assign_adviser_dialog(self):
        if not self.current_org:
            return
        dialog = AdviserAssignDialog(self.current_org, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            selected_faculty = dialog.get_selected_faculty()
            if selected_faculty:
                old_adviser = self.current_org.get("adviser")
                self.current_org["adviser"] = selected_faculty
                self.save_data()
                self._log_action(
                    "ASSIGN_ADVISER",
                    self.current_org["name"],
                    subject_name=selected_faculty,
                    changes=f"from {old_adviser or 'None'} → {selected_faculty}"
                )
                self.show_org_details(self.current_org)

    def update_officer_in_org(self, updated_officer: Dict, bypass_cooldown: bool = False):
            """Dean applies officer change — CHECKS IF ALREADY APPLIED & PRESERVES VISUALS"""
            if not self.current_org:
                return

            officers = self.current_org.get("officers", [])
            target_officer = None

            for off in officers:
                if off.get("name") == updated_officer.get("name"):
                    target_officer = off
                    break
            
            # --- FIX: Check if the change is already in effect ---
            # If the officer already has this position, we do nothing.
            # The calling function _approve_pending_officer will proceed to clear the 
            # pending request, effectively treating it as 'resolved'.
            if target_officer and target_officer.get("position") == updated_officer.get("position"):
                return
            # -----------------------------------------------------

            is_new_officer = target_officer is None

            officer_positions = ["Chairperson", "Vice - Internal Chairperson", "Vice - External Chairperson", "Secretary", "Treasurer"]
            
            if is_new_officer and updated_officer["position"] in officer_positions:
                target_officer = {
                    "name": updated_officer["name"],
                    "position": updated_officer["position"],
                    "photo_path": updated_officer.get("photo_path", "No Photo"),
                    "card_image_path": updated_officer.get("card_image_path", "No Photo"),
                    "cv_path": updated_officer.get("cv_path"),
                    "start_date": updated_officer.get("start_date", datetime.datetime.now().strftime("%m/%d/%Y")),
                }
                officers.append(target_officer)
            elif not is_new_officer:
                target_officer["position"] = updated_officer["position"]

                if updated_officer.get("photo_path") and updated_officer["photo_path"] != "No Photo":
                    target_officer["photo_path"] = updated_officer["photo_path"]
                
                if updated_officer.get("card_image_path") and updated_officer["card_image_path"] != "No Photo":
                    target_officer["card_image_path"] = updated_officer["card_image_path"]
                
                if "cv_path" in updated_officer:
                    target_officer["cv_path"] = updated_officer["cv_path"]
                
                if "start_date" in updated_officer:
                    target_officer["start_date"] = updated_officer["start_date"]

            if updated_officer["position"] not in officer_positions:
                self.current_org["officers"] = [
                    o for o in self.current_org.get("officers", []) 
                    if o["name"] != updated_officer["name"]
                ]
            else:
                self.current_org["officers"] = officers

            action = "APPROVE_OFFICER_CHANGE" if bypass_cooldown else "UPDATE_OFFICER"
            self._log_action(
                action,
                self.current_org["name"],
                subject_name=updated_officer["name"],
                changes=f"Position → {updated_officer.get('position')}"
            )

            self.save_data()
            self.load_officers(self.current_org["officers"])

    def _approve_pending_officer(self, officer_data: dict, dialog=None):
        if not officer_data:
            return 
        # This will now return early if the change is already done
        self.update_officer_in_org(officer_data, bypass_cooldown=True)
        # This cleans up the request regardless
        self._clear_pending_officer(officer_data["name"])
        
        QMessageBox.information(self, "Approved", f"{officer_data['name']} is now {officer_data.get('position')}.")
        if self.current_org:
            self.show_org_details(self.current_org)
        if dialog and hasattr(dialog, 'load_data'):
            dialog.load_data()
        self._update_pending_button()

    def _reject_pending_officer(self, officer_data: dict, dialog=None):
        if not self.current_org:
            return
        name = officer_data.get("name", "Unknown")
        self._clear_pending_officer(name)
        QMessageBox.warning(self, "Rejected", f"Officer change for <b>{name}</b> has been rejected.")
        self.show_org_details(self.current_org)
        if dialog and hasattr(dialog, 'load_data'):
            dialog.load_data()

    def _clear_pending_officer(self, name: str):
        if not self.current_org:
            return
        self.current_org["pending_officers"] = [
            p for p in self.current_org.get("pending_officers", []) if p.get("name") != name
        ]
        self.save_data()