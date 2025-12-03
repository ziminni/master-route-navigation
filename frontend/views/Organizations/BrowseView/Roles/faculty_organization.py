from ..Base.faculty_admin_base import FacultyAdminBase
from ..Base.manager_base import ManagerBase
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QSettings
from services.organization_api_service import OrganizationAPIService
import datetime
from typing import Dict

class Faculty(ManagerBase, FacultyAdminBase):
    """
    Faculty Adviser view — has admin-like powers for organizations they advise.
    Faculty can:
    - Only see organizations they are an adviser to (via OrgAdviserTerm)
    - Accept/reject membership applications
    - Edit member positions directly (no Dean approval needed)
    - Kick members from organizations
    - Full management capabilities like Admin role
    """

    def __init__(self, faculty_name: str):
        FacultyAdminBase.__init__(self, name=faculty_name)
        ManagerBase.__init__(self)
        self.members_dict = {}  # Store full member data for Edit operations
        self.user_role = "faculty"  # Set role for API calls
        self.load_orgs()

    # --- Cooldown Bypass Overrides (same as Admin) ---
    
    def edit_member(self, row: int) -> None:
        """Faculty override to bypass manager cooldown."""
        super().edit_member(row, bypass_cooldown=True)

    def kick_member(self, row: int) -> None:
        """Faculty override to bypass manager cooldown."""
        super().kick_member(row, bypass_cooldown=True)

    def update_officer_in_org(self, updated_officer: Dict) -> None:
        """Faculty override to bypass manager cooldown."""
        super().update_officer_in_org(updated_officer, bypass_cooldown=True)

    # --- End Cooldown Bypass ---

    def load_orgs(self, search_text: str = "") -> None:
        """Load only organizations where this faculty is an adviser via OrgAdviserTerm."""
        # Use new API endpoint that filters by adviser relationship
        api_response = OrganizationAPIService.get_faculty_advised_organizations(
            username=self.name,
            search_query=search_text if search_text else None
        )
        
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
                    "is_branch": False,
                    "is_archived": org.get('is_archived', False),
                    "is_active": org.get('is_active', True),
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
            # Fallback - show empty list if API fails
            organizations = []
        
        self._clear_grid(self.ui.college_org_grid)
        self.college_org_count = 0

        # All orgs from the API are already filtered to those the faculty advises
        filtered = [
            org for org in organizations
            if not org.get("is_archived", False) and not org.get("is_branch", False)
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

    def show_org_details(self, org_data: Dict) -> None:
        """Display organization details with full management features like admin."""
        super().show_org_details(org_data)
        self.current_org = org_data
        self.ui.view_members_btn.setText("Manage Members")
        
        # Fetch pending applicants and active members for this organization
        if org_data.get("id"):
            self._fetch_applicants(org_data["id"])
            self._fetch_members(org_data["id"])
            
            # Load officers from fetched members data
            self._on_officer_history_changed(0)  # Load "Current Officers"
            
            # Load members view by default (this triggers the UI update)
            self.load_members()

    def _fetch_applicants(self, org_id: int) -> None:
        """Fetch pending applicants for the organization from the API."""
        api_response = OrganizationAPIService.get_organization_applicants(org_id)
        if api_response.get("success"):
            applicants = api_response.get("data", [])
            # Store applicants in current_org for load_applicants to use
            if self.current_org:
                self.current_org["applicants"] = applicants
        else:
            if self.current_org:
                self.current_org["applicants"] = []

    def _fetch_members(self, org_id: int) -> None:
        """Fetch active members for the organization from the API."""
        api_response = OrganizationAPIService.get_organization_members(org_id)
        if api_response.get("success"):
            members_data = api_response.get("data", [])
            
            # Transform member data to match ViewMembers table format: [Name, Position, Status, Join Date]
            # But also store the full member dict for Edit functionality
            transformed_members = []
            self.members_dict = {}  # Store full member data by member_id
            
            for member in members_data:
                member_id = member.get('id')  # This is OrganizationMembers.id
                transformed = [
                    member.get('name', 'Unknown'),                                      # Name
                    member.get('position', 'Member'),                                   # Position (from backend)
                    'Active' if member.get('status') == 'active' else 'Inactive',      # Status
                    member.get('joined_at', '')[:10] if member.get('joined_at') else '' # Join Date (YYYY-MM-DD)
                ]
                transformed_members.append(transformed)
                # Store full member data keyed by member_id for Edit operations
                self.members_dict[member_id] = member
            
            # Store transformed members in current_org for load_members to use
            if self.current_org:
                self.current_org["members"] = transformed_members
        else:
            if self.current_org:
                self.current_org["members"] = []
                self.members_dict = {}

    def _update_member_in_list(self, member_id: int, updated_data: dict) -> None:
        """Update a single member in the members list without full refresh"""
        if not hasattr(self, 'members_dict') or not self.current_org:
            return
        
        try:
            # Update members_dict with new data
            self.members_dict[member_id] = updated_data
            
            # Find and update the member in current_org["members"]
            members = self.current_org.get("members", [])
            member_name = updated_data.get('name', 'Unknown')
            
            for idx, member in enumerate(members):
                if member[0] == member_name:  # Match by name
                    # Update the position (index 1)
                    new_position = updated_data.get('position', 'Member')
                    members[idx][1] = new_position
                    break
                
        except Exception:
            raise

    def _process_application_action(self, application_id: int, action: str, applicant_name: str):
        """Process accept or reject action via API - override to refresh members on accept"""
        # Get the current user's profile_id for logging
        admin_user_id = None
        try:
            settings = QSettings("CISC", "MasterRoute")
            admin_user_id = settings.value("user_profile_id")
            if admin_user_id:
                admin_user_id = int(admin_user_id)
        except Exception:
            pass
        
        api_response = OrganizationAPIService.process_application(application_id, action, admin_user_id)
        
        if api_response.get("success"):
            action_text = "accepted" if action == "accept" else "rejected"
            QMessageBox.information(
                self,
                "Success",
                f"{applicant_name}'s application has been {action_text}."
            )
            # Refresh the applicants list and members list
            if self.current_org:
                self._fetch_applicants(self.current_org["id"])
                if action == "accept":
                    # Refresh members when accepting to show new member
                    self._fetch_members(self.current_org["id"])
                self.load_applicants(self._get_search_text())
        else:
            error_msg = api_response.get("error", f"Failed to {action} application")
            QMessageBox.critical(self, "Error", error_msg)