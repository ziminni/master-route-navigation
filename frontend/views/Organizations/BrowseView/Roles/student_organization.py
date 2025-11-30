from PyQt6 import QtCore
from PyQt6.QtWidgets import QMessageBox, QFileDialog
from PyQt6.QtCore import QTimer
from typing import Dict
from ..Base.organization_view_base import OrganizationViewBase
from widgets.orgs_custom_widgets.cards import JoinedOrgCard, CollegeOrgCard
from services.organization_api_service import OrganizationAPIService
from ..Utils.image_utils import get_image_path, copy_image_to_data

class Student(OrganizationViewBase):
    def __init__(self, student_name: str):
        super().__init__(name=student_name)
        self.load_orgs()
        self._check_for_notifications()

    def show_org_details(self, org_data: Dict) -> None:
        """Display organization details and check for officer promotion."""
        super().show_org_details(org_data) 
        
        officers = org_data.get("officers", [])
        my_officer_data = next((off for off in officers if off.get("name") == self.name), None)
        
        if my_officer_data and not my_officer_data.get("cv_path"):
            QTimer.singleShot(100, self._prompt_for_cv_on_promotion)

    def _prompt_for_cv_on_promotion(self) -> None:
        """Prompt the newly promoted student to upload their CV."""
        confirm = QMessageBox.question(
            self, 
            "Congratulations on your Promotion!", 
            "It looks like you've been promoted to an officer position! As an officer, you are required to upload your Curriculum Vitae (CV).\n\n"
            "Would you like to upload it now?", 
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
                if not self.current_org:
                    return
                org_name = self.current_org.get("name", "Unknown")
                
                new_cv_filename = copy_image_to_data(file_path, org_name)
                
                if new_cv_filename:
                    for officer in self.current_org.get("officers", []):
                        if officer.get("name") == self.name:
                            officer["cv_path"] = new_cv_filename
                            self.save_data()
                            QMessageBox.information(
                                self, 
                                "Success", 
                                "CV uploaded successfully!\n\n"
                                "Please log out and log back in to access your new officer privileges."
                            )
                            break
                else:
                    QMessageBox.warning(self, "CV Error", "Failed to save the selected CV. Please try again.")
        else:
            QMessageBox.information(
                self, 
                "CV Upload", 
                "You can upload your CV later by clicking 'Officer Details' on your card and selecting 'Edit'."
            )

    def update_own_officer_data(self, officer_data: Dict) -> None:
        if not self.current_org:
            return
            
        org_officers = self.current_org.get("officers", [])
        officer_found = False
        
        for officer in org_officers:
            if officer.get("name") == self.name:
                if "photo_path" in officer_data:
                    officer["photo_path"] = officer_data["photo_path"]
                if "card_image_path" in officer_data:
                    officer["card_image_path"] = officer_data["card_image_path"]
                if "cv_path" in officer_data:
                    officer["cv_path"] = officer_data["cv_path"]
                
                officer_found = True
                break
        
        if officer_found:
            self.save_data()
            QMessageBox.information(
                self,
                "Details Updated",
                "Your details have been successfully updated.\n\n"
                "Please log out and log back in to access your officer privileges."
            )
        else:
            QMessageBox.warning(
                self,
                "Error",
                "Could not find your officer data to update. Please try logging in again."
            )

    def load_orgs(self, search_text: str = "") -> None:
        # Fetch organizations from API with optional search query
        api_response = OrganizationAPIService.fetch_organizations(search_query=search_text if search_text else None)
        
        # Fetch student's application statuses
        user_id = getattr(self, 'user_id', 1)  # TODO: Use actual user_id from session
        app_statuses_response = OrganizationAPIService.get_student_application_statuses(user_id)
        application_statuses = app_statuses_response.get('data', {}) if app_statuses_response.get('success') else {}
        
        if api_response.get('success'):
            organizations_data = api_response.get('data', [])
            
            # Convert API data to the format expected by the UI
            organizations = []
            for org in organizations_data:
                org_id = org.get('id')
                
                # Check if student has applied to this org
                applicants = []
                if str(org_id) in application_statuses:
                    app_status = application_statuses[str(org_id)]['status']
                    if app_status == 'pen':  # Pending
                        applicants.append([self.name, "Member", ""])  # Add to applicants list
                
                org_dict = {
                    "id": org_id,
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
                    "applicants": applicants,
                    "officer_history": {}
                }
                organizations.append(org_dict)
        else:
            # Fallback to JSON data if API fails
            print(f"API Error: {api_response.get('message')}")
            organizations = self._load_data()
        
        self._clear_grid(self.ui.joined_org_grid)
        self._clear_grid(self.ui.college_org_grid)
        self.joined_org_count = 0
        self.college_org_count = 0

        student_name = self.name
        # Since search is now done on backend, no need to filter by name again
        filtered_joined = [
            org for org in organizations
            if not org.get("is_archived", False) and not org.get("is_branch", False) and
            any(member[0] == student_name for member in org.get("members", []))
        ]
        
        joined_org_ids = {org['id'] for org in filtered_joined}
        
        filtered_college = [
            org for org in organizations
            if not org.get("is_archived", False) and not org.get("is_branch", False) and
            org['id'] not in joined_org_ids
        ]

        for org in filtered_joined:
            self._add_joined_org(org)
        for org in filtered_college:
            self._add_college_org(org)

        if self.joined_org_count == 0:
            self._add_no_record_label(self.ui.joined_org_grid)
        if self.college_org_count == 0:
            self._add_no_record_label(self.ui.college_org_grid)

        self._update_scroll_areas()

    def load_branches(self, search_text: str = "") -> None:
        """Load branches - now just redirects to load_orgs since branches are organizations with main_org."""
    def load_branches(self, search_text: str = "") -> None:
        """Load branches - now just redirects to load_orgs since branches are organizations with main_org."""
        self.load_orgs(search_text)

    def _on_combobox_changed(self, index: int) -> None:
        """Handle combo box change - now always shows organizations."""
        self.ui.joined_label.setText("Joined Organization(s)")
        self.ui.college_label.setText("College Organization(s)")
        self.load_orgs()
        self.ui.joined_org_scrollable.verticalScrollBar().setValue(0)
        self.ui.college_org_scrollable.verticalScrollBar().setValue(0)

    def _add_joined_org(self, org_data: Dict) -> None:
        card = JoinedOrgCard(self._get_logo_path(org_data["logo_path"]), org_data, self)
        col = self.joined_org_count % 5
        row = self.joined_org_count // 5
        self.ui.joined_org_grid.addWidget(
            card, row, col, alignment=QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignHCenter
        )
        self.joined_org_count += 1
        self.ui.joined_org_grid.setRowMinimumHeight(row, 300)

    def _check_for_notifications(self) -> None:
        notifications = self.get_notifications_for_student(self.name)
        if not notifications:
            return

        accepted_orgs = []
        notification_ids_to_clear = []
        
        for notif in notifications:
            if notif.get("type") == "ACCEPTANCE":
                accepted_orgs.append(notif.get("org_name", "an organization"))
                notification_ids_to_clear.append(notif.get("id"))
        
        if accepted_orgs:
            org_list_str = "\n - ".join(accepted_orgs)
            title = "Congratulations!"
            message = f"You have been accepted into the following organizations/branches:\n\n - {org_list_str}"
            
            QMessageBox.information(self, title, message)
            
            self.clear_notifications_for_student(self.name, notification_ids_to_clear)