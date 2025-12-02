from PyQt6 import QtCore
from PyQt6.QtWidgets import QMessageBox, QFileDialog
from PyQt6.QtCore import QTimer
from typing import Dict
from ..Base.organization_view_base import OrganizationViewBase
from widgets.orgs_custom_widgets.cards import JoinedOrgCard, CollegeOrgCard
from services.organization_api_service import OrganizationAPIService
from ..Utils.image_utils import get_image_path, copy_image_to_data

class Student(OrganizationViewBase):
    def __init__(self, student_name: str, user_id: int = None):
        # Write to log file for debugging
        import os
        log_path = os.path.join(os.path.dirname(__file__), "student_debug.log")
        with open(log_path, "a") as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"STUDENT __INIT__ CALLED\n")
            f.write(f"  student_name={student_name}\n")
            f.write(f"  user_id parameter={user_id} (type={type(user_id)})\n")
        
        print(f"="*80)
        print(f"STUDENT __INIT__ CALLED")
        print(f"  student_name={student_name}")
        print(f"  user_id parameter={user_id} (type={type(user_id)})")
        print(f"="*80)
        
        super().__init__(name=student_name)
        
        # user_id is the StudentProfile ID passed from Browse
        self.user_id = user_id
        
        print(f"  FINAL self.user_id={self.user_id} (type={type(self.user_id)})")
        print(f"="*80)
        
        with open(log_path, "a") as f:
            f.write(f"  FINAL self.user_id={self.user_id} (type={type(self.user_id)})\n")
            f.write(f"{'='*80}\n")
        self.load_orgs()
        self._check_for_notifications()

    def show_org_details(self, org_data: Dict) -> None:
        """Display organization details and fetch members/officers from database."""
        # First call the parent to set up the organization details UI
        super().show_org_details(org_data)
        
        # Then fetch members and officers from database and update current_org
        if org_data.get('id'):
            self._fetch_members(org_data['id'])
            
            # Reload officers into the UI after fetching from database
            if self.current_org:
                officers = self.current_org.get("officers", [])
                self.load_officers(officers)
        
        # Check if the current user is an officer without CV
        officers = self.current_org.get("officers", []) if self.current_org else []
        my_officer_data = next((off for off in officers if off.get("name") == self.name), None)
        
        if my_officer_data and not my_officer_data.get("cv_path"):
            QTimer.singleShot(100, self._prompt_for_cv_on_promotion)
    
    def _fetch_members(self, org_id: int) -> None:
        """Fetch members and officers from database API"""
        response = OrganizationAPIService.get_organization_members(org_id)
        
        if response.get('success'):
            members_data = response.get('data', [])
            
            # Store in members_dict for access by other methods
            self.members_dict = {
                member['id']: member for member in members_data
            }
            
            # Update current_org with members and officers
            if self.current_org:
                # Filter officers (members with positions other than 'Member')
                officers = [
                    {
                        'id': member.get('id'),
                        'name': member.get('name', 'Unknown'),
                        'position': member.get('position', 'Member'),
                        'position_id': member.get('position_id'),
                        'email': member.get('email', ''),
                        'program': member.get('program', 'N/A'),
                        'year_level': member.get('year_level', ''),
                        'photo_path': member.get('photo_url', 'No Photo'),
                        'card_image_path': member.get('photo_url', 'No Photo'),
                        'start_term': member.get('start_term'),
                        'end_term': member.get('end_term')
                    }
                    for member in members_data
                    if member.get('position') and member.get('position') != 'Member'
                ]
                
                # All members (including officers) - format: [name, position, status, join_date]
                members = [
                    [member.get('name', 'Unknown'), 
                     member.get('position', 'Member'),
                     'Active' if member.get('status') == 'active' else 'Inactive',  # Format status
                     member.get('joined_at', 'N/A')]  # Join date from database
                    for member in members_data
                ]
                
                self.current_org['officers'] = officers
                self.current_org['members'] = members
                
                print(f"DEBUG: Fetched {len(members)} members and {len(officers)} officers for org {org_id}")
        else:
            print(f"ERROR: Failed to fetch members: {response.get('message')}")

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
        """Load organizations - fetching joined orgs from database and others from API"""
        print(f"DEBUG: load_orgs called with user_id={self.user_id}")
        
        # Fetch ALL organizations from API with optional search query
        all_orgs_response = OrganizationAPIService.fetch_organizations(search_query=search_text if search_text else None)
        
        # Fetch joined organizations specifically for this student
        joined_orgs_response = None
        if self.user_id:
            print(f"DEBUG load_orgs: About to call API with user_id={self.user_id} (type={type(self.user_id)})")
            joined_orgs_response = OrganizationAPIService.get_student_joined_organizations(self.user_id)
            print(f"DEBUG load_orgs: Joined orgs API response: {joined_orgs_response}")
            if joined_orgs_response.get('success'):
                print(f"DEBUG load_orgs: API SUCCESS - returned {len(joined_orgs_response.get('data', []))} organizations")
            else:
                print(f"DEBUG load_orgs: API FAILED - {joined_orgs_response.get('message', 'Unknown error')}")
        else:
            print("WARNING load_orgs: No user_id available, cannot fetch joined organizations")
        
        # Fetch student's application statuses
        app_statuses_response = OrganizationAPIService.get_student_application_statuses(self.user_id) if self.user_id else {'success': False}
        application_statuses = app_statuses_response.get('data', {}) if app_statuses_response.get('success') else {}
        
        if all_orgs_response.get('success'):
            all_organizations_data = all_orgs_response.get('data', [])
            joined_orgs_data = joined_orgs_response.get('data', []) if joined_orgs_response and joined_orgs_response.get('success') else []
            
            print(f"DEBUG: Total orgs: {len(all_organizations_data)}, Joined orgs: {len(joined_orgs_data)}")
            print(f"DEBUG: Joined orgs data details: {joined_orgs_data}")
            
            # Get joined org IDs for filtering
            joined_org_ids = {org.get('id') for org in joined_orgs_data}
            print(f"DEBUG: Joined org IDs: {joined_org_ids}")
            
            # Convert API data to the format expected by the UI
            joined_organizations = []
            college_organizations = []
            
            for org in all_organizations_data:
                org_id = org.get('id')
                print(f"DEBUG: Processing org_id={org_id}, name={org.get('name')}, is_joined={org_id in joined_org_ids}")
                
                # Check if student has applied to this org
                applicants = []
                if str(org_id) in application_statuses:
                    app_status = application_statuses[str(org_id)]['status']
                    if app_status == 'pen':  # Pending
                        applicants.append([self.name, "Member", ""])
                
                org_dict = {
                    "id": org_id,
                    "name": org.get('name'),
                    "description": org.get('description', ''),
                    "objectives": org.get('objectives', ''),
                    "status": org.get('status', 'active'),
                    "logo_path": org.get('logo_path', 'No Photo'),
                    "org_level": org.get('org_level', 'col'),
                    "created_at": org.get('created_at'),
                    "is_branch": False,
                    "is_archived": False,
                    "brief": "College Level" if org.get('org_level') == 'col' else "Program Level",
                    "branches": [],
                    "events": [],
                    "officers": [],  # Will be fetched when viewing details
                    "members": [],   # Will be fetched when viewing details
                    "applicants": applicants,
                    "officer_history": {}
                }
                
                # Separate joined vs not joined
                if org_id in joined_org_ids:
                    joined_organizations.append(org_dict)
                    print(f"DEBUG: Added '{org.get('name')}' to joined orgs")
                else:
                    college_organizations.append(org_dict)
        else:
            # Fallback to JSON data if API fails
            print(f"API Error: {all_orgs_response.get('message')}")
            organizations = self._load_data()
            
            student_name = self.name
            joined_organizations = [
                org for org in organizations
                if not org.get("is_archived", False) and not org.get("is_branch", False) and
                any(member[0] == student_name for member in org.get("members", []))
            ]
            
            joined_org_ids = {org['id'] for org in joined_organizations}
            
            college_organizations = [
                org for org in organizations
                if not org.get("is_archived", False) and not org.get("is_branch", False) and
                org['id'] not in joined_org_ids
            ]
        
        print(f"DEBUG: Final counts - Joined: {len(joined_organizations)}, College: {len(college_organizations)}")
        
        # Clear and populate grids
        self._clear_grid(self.ui.joined_org_grid)
        self._clear_grid(self.ui.college_org_grid)
        self.joined_org_count = 0
        self.college_org_count = 0

        for org in joined_organizations:
            self._add_joined_org(org)
        for org in college_organizations:
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