from PyQt6 import QtWidgets
from typing import Dict
from .organization_view_base import OrganizationViewBase
from services.organization_api_service import OrganizationAPIService

class FacultyAdminBase(OrganizationViewBase):
    """
    Base class for Faculty and Admin views.
    Implements common logic for non-student managers, such as
    hiding the 'Joined Orgs' container and loading all orgs
    into a single grid.
    """
    
    def __init__(self, name: str):
        super().__init__(name=name)
        self.ui.joined_container.setVisible(False)

    def load_orgs(self, search_text: str = "") -> None:
        # Fetch organizations from API
        api_response = OrganizationAPIService.fetch_organizations()
        
        if api_response.get('success'):
            organizations_data = api_response.get('data', {}).get('data', [])
            
            # Convert API data to the format expected by the UI
            organizations = []
            for org in organizations_data:
                org_dict = {
                    "id": org.get('id'),
                    "name": org.get('name'),
                    "description": org.get('description', ''),
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
                    "officer_history": {}
                }
                organizations.append(org_dict)
        else:
            # Fallback to JSON data if API fails
            print(f"API Error: {api_response.get('message')}")
            organizations = self._load_data()
        
        self._clear_grid(self.ui.college_org_grid)
        self.college_org_count = 0
        
        filtered_college = [
            org for org in organizations 
            if not org.get("is_archived", False) and not org["is_branch"] and (search_text in org["name"].lower() or not search_text)
        ]
        
        for org in filtered_college:
            self._add_college_org(org)
        
        if self.college_org_count == 0:
            self._add_no_record_label(self.ui.college_org_grid)
        
        self._update_scroll_areas()
        self.hide_apply_buttons()
    
    def load_branches(self, search_text: str = "") -> None:
        """Load branches - now just redirects to load_orgs since branches are organizations with main_org."""
        self.load_orgs(search_text)
    
    def hide_apply_buttons(self) -> None:
        """Hide all 'Apply' buttons in the organization cards."""
        for child in self.ui.other_container.findChildren(QtWidgets.QPushButton):
            if child.text() == "Apply":
                child.setVisible(False)
    
    def show_org_details(self, org_data: Dict) -> None:
        """Display organization details with faculty/admin-specific features."""
        super().show_org_details(org_data)
        self.current_org = org_data
        self.ui.view_members_btn.setText("Manage Members")
        
        if self.edit_btn is None:
            self.edit_btn = QtWidgets.QPushButton("Edit")
            self.edit_btn.setObjectName("edit_btn")
            self.edit_btn.clicked.connect(self.open_edit_dialog)
            self.edit_btn.setStyleSheet("border-radius: 10px; background-color: transparent; color: #084924; border: 2px solid #084924")
            
            branch_list_index = self.ui.verticalLayout_10.indexOf(self.ui.obj_label_2)
            if branch_list_index != -1:
                spacer = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
                self.ui.verticalLayout_10.insertItem(branch_list_index + 1, spacer)
                self.ui.verticalLayout_10.insertWidget(branch_list_index + 2, self.edit_btn)
            else:
                spacer = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
                self.ui.verticalLayout_10.addItem(spacer)
                self.ui.verticalLayout_10.addWidget(self.edit_btn)
    
    def open_edit_dialog(self):
        """Open the edit dialog for current organization."""
        from widgets.orgs_custom_widgets.dialogs import EditOrgDialog
        
        if self.current_org:
            # Fetch fresh organization data from API
            org_id = self.current_org.get("id")
            if org_id:
                api_response = OrganizationAPIService.fetch_organization_details(org_id)
                
                if api_response.get('success'):
                    org_data = api_response.get('data', {}).get('data', {})
                    
                    # Open edit dialog with fresh data
                    dialog = EditOrgDialog(org_data, self)
                    
                    if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
                        # Refresh the details view with updated data
                        updated_response = OrganizationAPIService.fetch_organization_details(org_id)
                        if updated_response.get('success'):
                            updated_org = updated_response.get('data', {}).get('data', {})
                            self.show_org_details(updated_org)
                else:
                    QtWidgets.QMessageBox.critical(
                        self,
                        "Error",
                        f"Failed to load organization details: {api_response.get('message')}",
                        QtWidgets.QMessageBox.StandardButton.Ok
                    )
            else:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Error",
                    "Organization ID not found.",
                    QtWidgets.QMessageBox.StandardButton.Ok
                )