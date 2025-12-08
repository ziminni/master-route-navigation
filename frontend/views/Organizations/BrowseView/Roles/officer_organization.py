from PyQt6 import QtWidgets
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QMessageBox, QFileDialog
import datetime
from typing import Dict
from .student_organization import Student
from ..Base.manager_base import ManagerBase
from widgets.orgs_custom_widgets.dialogs import OfficerDialog
from ..Utils.image_utils import copy_image_to_data


class Officer(ManagerBase, Student):
    """Officer view — same pending flow as Faculty, full photo preservation"""

    def __init__(self, officer_name: str, user_id: int = None):
        Student.__init__(self, student_name=officer_name, user_id=user_id)
        ManagerBase.__init__(self)
        self._setup_officer_connections()

    def _setup_officer_connections(self) -> None:
        self.ui.view_members_btn.clicked.disconnect()
        self.ui.view_members_btn.clicked.connect(self._to_members_page)
        self.ui.back_btn_member.clicked.disconnect()
        self.ui.back_btn_member.clicked.connect(self._return_to_prev_page)
        # Search only on button click or Enter key press
        self.ui.search_btn_3.clicked.connect(self._perform_member_search)
        self.ui.search_line_3.returnPressed.connect(self._perform_member_search)

    def edit_member(self, row: int, bypass_cooldown: bool = False) -> None:
        """
        Override: Edit member via list triggers a PENDING REQUEST.
        Does not apply changes immediately. Respects cooldown.
        """
        from widgets.orgs_custom_widgets.dialogs import EditMemberDialog
        
        if not self.current_org:
            return
        
        search_text = self._get_search_text()
        members = self.current_org.get("members", [])
        
        original_index, member = self._filter_and_find_original_index(
            members, row, search_text
        )
        
        if original_index is None:
            return
        
        member_name = member[0]
        
        dialog = EditMemberDialog(member, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            new_position = dialog.updated_position
            old_position = member[1]

            # --- Check 1: Stop redundant requests ---
            if new_position == old_position:
                return
            
            # --- Construct officer data for pending request ---
            existing_officer = next((o for o in self.current_org.get("officers", []) if o["name"] == member_name), None)
            
            # Safe getters for paths
            photo_path = existing_officer.get("photo_path") if existing_officer else "No Photo"
            if not photo_path: photo_path = "No Photo"

            card_path = existing_officer.get("card_image_path") if existing_officer else "No Photo"
            if not card_path: card_path = "No Photo"

            officer_data = {
                "name": member_name,
                "position": new_position,
                "photo_path": photo_path,
                "card_image_path": card_path,
                "cv_path": existing_officer.get("cv_path") if existing_officer else None,
                "start_date": existing_officer.get("start_date") if existing_officer else datetime.datetime.now().strftime("%m/%d/%Y")
            }
            
            # Student officers respect cooldowns (bypass_cooldown=False)
            self.update_officer_in_org(officer_data, bypass_cooldown=False)

    def show_officer_dialog(self, officer_data: Dict) -> None:
        OfficerDialog(officer_data, self).exec()

    def show_org_details(self, org_data: Dict) -> None:
        super().show_org_details(org_data)
        self.current_org = org_data

        if self.edit_btn:
            self.ui.verticalLayout_10.removeWidget(self.edit_btn)
            self.edit_btn.deleteLater()
            self.edit_btn = None

        officers = org_data.get("officers", [])
        officer_names = [off.get("name", "") for off in officers]
        self.is_managing = self.name in officer_names

        if self.is_managing:
            self.ui.view_members_btn.setText("Manage Members")
            self.edit_btn = QtWidgets.QPushButton("Edit")
            self.edit_btn.setObjectName("edit_btn")
            self.edit_btn.clicked.connect(self.open_edit_dialog)
            self.edit_btn.setStyleSheet("border-radius: 10px; background-color: transparent; color: #084924; border: 2px solid #084924")
            self.ui.verticalLayout_10.addWidget(self.edit_btn)

    def update_officer_in_org(self, updated_officer: Dict, bypass_cooldown: bool = False):
        """Officer submits position change → pending with FULL photo preservation"""
        if not self.current_org:
            return
        
        if not bypass_cooldown:
             is_on_cooldown, end_time = self.check_manager_action_cooldown(self.current_org['id'], "OFFICER_CHANGE")
             if is_on_cooldown:
                QMessageBox.warning(self, "Cooldown", f"Action on cooldown until {end_time.strftime('%I:%M:%S %p')}")
                return

        officers = self.current_org.get("officers", [])
        current_officer_data = None
        for off in officers:
            if off.get("name") == updated_officer.get("name"):
                current_officer_data = off
                break

        # --- FIX: Stop redundant requests from Officer Card Edit ---
        if current_officer_data and current_officer_data.get("position") == updated_officer.get("position"):
            return
        # -----------------------------------------------------------

        safe_photo = updated_officer.get("photo_path")
        if not safe_photo or safe_photo == "None": safe_photo = "No Photo"
        
        safe_card = updated_officer.get("card_image_path")
        if not safe_card or safe_card == "None": safe_card = "No Photo"

        final_officer_data = {
            "name": updated_officer["name"],
            "position": updated_officer["position"],
            "old_position": current_officer_data.get("position", "Member") if current_officer_data else "Member",
            "photo_path": current_officer_data.get("photo_path") if current_officer_data else safe_photo,
            "card_image_path": current_officer_data.get("card_image_path") if current_officer_data else safe_card,
            "cv_path": current_officer_data.get("cv_path") if current_officer_data else updated_officer.get("cv_path"),
            "start_date": current_officer_data.get("start_date") if current_officer_data else updated_officer.get("start_date"),
        }

        if updated_officer.get("photo_path") and updated_officer["photo_path"] != "No Photo" and updated_officer["photo_path"] != final_officer_data["photo_path"]:
             final_officer_data["photo_path"] = updated_officer["photo_path"]
             final_officer_data["card_image_path"] = updated_officer.get("card_image_path", final_officer_data["photo_path"])

        if updated_officer.get("cv_path") and updated_officer["cv_path"] != final_officer_data["cv_path"]:
             final_officer_data["cv_path"] = updated_officer["cv_path"]

        # Final Null Check
        if not final_officer_data["photo_path"]: final_officer_data["photo_path"] = "No Photo"
        if not final_officer_data["card_image_path"]: final_officer_data["card_image_path"] = "No Photo"

        pending = self.current_org.setdefault("pending_officers", [])
        pending = [p for p in pending if p.get("name") != final_officer_data["name"]]

        pending.append({
            "name": final_officer_data["name"],
            "position": final_officer_data["position"],
            "old_position": final_officer_data["old_position"],
            "proposed_by": self.name,
            "proposed_at": datetime.datetime.now().isoformat(),
            "photo_path": final_officer_data.get("photo_path"),
            "card_image_path": final_officer_data.get("card_image_path"),
            "cv_path": final_officer_data.get("cv_path"),
            "start_date": final_officer_data.get("start_date"),
        })

        self.current_org["pending_officers"] = pending
        self.save_data()
        
        if not bypass_cooldown:
            self.set_manager_action_cooldown(self.current_org['id'], "OFFICER_CHANGE", minutes=5)

        QMessageBox.information(
            self,
            "Request Submitted",
            f"Position change to <b>{final_officer_data['position']}</b><br><br>"
            "Awaiting <b>Dean approval</b>.",
            QMessageBox.StandardButton.Ok
        )

        self.show_org_details(self.current_org)
    
    # ... (rest of methods unchanged)
    def _prompt_for_cv(self) -> None:
        confirm = QMessageBox.question(
            self, 
            "Upload CV", 
            "As a new officer, you are required to upload your Curriculum Vitae (CV). Would you like to upload it now?", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "Select CV", 
                "", 
                "Files (*.png *.jpg *.jpeg *.pdf)"
            )
            
            if file_path:
                org_name = self.current_org.get("name", "Unknown")
                new_cv_filename = copy_image_to_data(file_path, org_name)
                
                if new_cv_filename:
                    for officer in self.current_org.get("officers", []):
                        if officer.get("name") == self.name:
                            officer["cv_path"] = new_cv_filename
                            self.save_data()
                            QMessageBox.information(self, "Success", "CV uploaded successfully.")
                            break
                else:
                    QMessageBox.warning(self, "CV Error", "Failed to save the selected CV. Please try again.")
        else:
            QMessageBox.information(
                self, 
                "CV Upload", 
                "You can upload your CV later by clicking 'Officer Details' on your card and selecting 'Edit'."
            )
    
    def _to_members_page(self) -> None:
        if self.current_org:
            self.ui.header_label_3.setText(
                "Organization" if not self.current_org["is_branch"] else "Branch"
            )
        self.is_viewing_applicants = False
        self.load_members(self._get_search_text())
        self.ui.stacked_widget.setCurrentIndex(2)
    
    def _return_to_prev_page(self) -> None:
        if self.ui.stacked_widget.currentIndex() == 2:
            if self.is_viewing_applicants:
                self.is_viewing_applicants = False
                self.load_members(self._get_search_text())
            else:
                self.ui.stacked_widget.setCurrentIndex(1)
        else:
            self.load_orgs()
            self.ui.stacked_widget.setCurrentIndex(0)