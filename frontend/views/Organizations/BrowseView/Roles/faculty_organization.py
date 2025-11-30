from ..Base.faculty_admin_base import FacultyAdminBase
from ..Base.manager_base import ManagerBase
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QMessageBox
from services.organization_api_service import OrganizationAPIService
import datetime
from typing import Dict

class Faculty(ManagerBase, FacultyAdminBase):
    """
    Faculty view — position changes go to pending with FULL photo preservation.
    Cooldowns are bypassed to allow 'spamming' changes.
    """

    def __init__(self, faculty_name: str):
        FacultyAdminBase.__init__(self, name=faculty_name)
        ManagerBase.__init__(self)
        self.load_orgs()

    def edit_member(self, row: int, bypass_cooldown: bool = True) -> None:
        """
        Override: Edit member via list triggers a PENDING REQUEST.
        Does not apply changes immediately. Bypasses cooldown.
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
            
            # --- Check 1: Stop redundant requests from List Edit ---
            if new_position == old_position:
                return

            # --- Construct officer data for pending request ---
            existing_officer = next((o for o in self.current_org.get("officers", []) if o["name"] == member_name), None)
            
            # Use .get() with default to "No Photo" to prevent None/Null in JSON
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
            
            self.update_officer_in_org(officer_data, bypass_cooldown=True)

    def update_officer_in_org(self, updated_officer: Dict, bypass_cooldown: bool = True):
        """Faculty submits officer position change → goes to pending with FULL photo preservation"""
        if not self.current_org:
            return

        officers = self.current_org.get("officers", [])
        current_officer_data = None
        for off in officers:
            if off.get("name") == updated_officer.get("name"):
                current_officer_data = off
                break

        # --- FIX: Stop redundant requests from Officer Card Edit ---
        # If the officer exists and the position is the same, do nothing.
        if current_officer_data and current_officer_data.get("position") == updated_officer.get("position"):
            return
        # -----------------------------------------------------------

        # Safety check: Ensure we don't accidentally write None to photo paths
        safe_photo = updated_officer.get("photo_path")
        if not safe_photo or safe_photo == "None": safe_photo = "No Photo"
        
        safe_card = updated_officer.get("card_image_path")
        if not safe_card or safe_card == "None": safe_card = "No Photo"

        final_officer_data = {
            "name": updated_officer["name"],
            "position": updated_officer["position"],
            "old_position": current_officer_data.get("position", "Member") if current_officer_data else "Member",
            # Prioritize existing data to avoid overwriting valid paths with defaults
            "photo_path": current_officer_data.get("photo_path") if current_officer_data else safe_photo,
            "card_image_path": current_officer_data.get("card_image_path") if current_officer_data else safe_card,
            "cv_path": current_officer_data.get("cv_path") if current_officer_data else updated_officer.get("cv_path"),
            "start_date": current_officer_data.get("start_date") if current_officer_data else updated_officer.get("start_date"),
        }
        
        # If the dialog passed a NEW photo (different from existing), use that instead
        if updated_officer.get("photo_path") and updated_officer["photo_path"] != "No Photo" and updated_officer["photo_path"] != final_officer_data["photo_path"]:
             final_officer_data["photo_path"] = updated_officer["photo_path"]
             final_officer_data["card_image_path"] = updated_officer.get("card_image_path", final_officer_data["photo_path"])

        if updated_officer.get("cv_path") and updated_officer["cv_path"] != final_officer_data["cv_path"]:
             final_officer_data["cv_path"] = updated_officer["cv_path"]

        # Final Null Check before saving
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

        QMessageBox.information(
            self,
            "Request Submitted",
            f"Officer position change for <b>{final_officer_data['name']}</b><br>"
            f"to <b>{final_officer_data['position']}</b><br><br>"
            "Awaiting <b>Dean approval</b>.",
            QMessageBox.StandardButton.Ok
        )

        self.show_org_details(self.current_org)

    def load_orgs(self, search_text: str = "") -> None:
        # Fetch organizations from API with optional search query
        api_response = OrganizationAPIService.fetch_organizations(search_query=search_text if search_text else None)
        
        if api_response.get('success'):
            organizations_data = api_response.get('data', [])
            
            # Convert API data to the format expected by the UI
            organizations = []
            for org in organizations_data:
                org_dict = {
                    "id": org.get('id'),
                    "name": org.get('name'),
                    "description": org.get('description', ''),
                    "objectives": org.get('objectives', ''),
                    "status": org.get('status', 'active'),
                    "logo_path": org.get('logo_path', 'No Photo'),
                    "org_level": org.get('org_level', 'col'),
                    "created_at": org.get('created_at'),
                    "is_branch": False,  # TODO: Add is_branch field to backend model
                    "is_archived": False,  # TODO: Check status field
                    "brief": "College Level" if org.get('org_level') == 'col' else "Program Level",
                    "branches": [],
                    "events": [],
                    "officers": [],
                    "members": [],
                    "applicants": [],
                    "adviser": org.get('adviser', ''),
                    "officer_history": {}
                }
                organizations.append(org_dict)
        else:
            # Fallback to JSON data if API fails
            print(f"API Error: {api_response.get('message')}")
            organizations = self._load_data()
        
        self._clear_grid(self.ui.college_org_grid)
        self.college_org_count = 0

        # Filter by adviser (search is done on backend)
        filtered = [
            org for org in organizations
            if not org.get("is_archived", False)
            and not org.get("is_branch", False)
            and org.get("adviser") == self.name
        ]

        for org in filtered:
            self._add_college_org(org)

        if self.college_org_count == 0:
            self._add_no_record_label(self.ui.college_org_grid)

        self._update_scroll_areas()
        self.hide_apply_buttons()

    def load_branches(self, search_text: str = "") -> None:
        """Load branches - now just redirects to load_orgs since branches are organizations with main_org."""
        self.load_orgs(search_text)