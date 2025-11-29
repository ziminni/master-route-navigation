from ..Base.faculty_admin_base import FacultyAdminBase
from ..Base.manager_base import ManagerBase

class Faculty(ManagerBase, FacultyAdminBase):
    """
    Faculty view. Inherits from ManagerBase (for management methods) and
    FacultyAdminBase (for the non-student UI layout and org loading).
    
    MRO: Faculty -> ManagerBase -> FacultyAdminBase -> OrganizationViewBase -> User
    This ensures manager methods (e.g., _to_members_page) are used.
    """
    
    def __init__(self, faculty_name: str):
        FacultyAdminBase.__init__(self, name=faculty_name)
        ManagerBase.__init__(self)
                
        self.load_orgs()

    def load_orgs(self, search_text: str = "") -> None:
        organizations = self._load_data()
        self._clear_grid(self.ui.college_org_grid)
        self.college_org_count = 0

        filtered = [
            org for org in organizations
            if not org.get("is_archived", False)
            and not org.get("is_branch", False)
            and (search_text.lower() in org["name"].lower() or not search_text)
            and org.get("adviser") == self.name
        ]

        for org in filtered:
            self._add_college_org(org)

        if self.college_org_count == 0:
            self._add_no_record_label(self.ui.college_org_grid)

        self._update_scroll_areas()
        self.hide_apply_buttons()

    def load_branches(self, search_text: str = "") -> None:
        organizations = self._load_data()
        self._clear_grid(self.ui.college_org_grid)
        self.college_org_count = 0

        filtered_branches = []
        for org in organizations:
            if org.get("adviser") != self.name:
                continue
            for branch in org.get("branches", []):
                if branch.get("is_archived", False):
                    continue
                if search_text.lower() in branch["name"].lower() or not search_text:
                    filtered_branches.append(branch)

        for branch in filtered_branches:
            self._add_college_org(branch)

        if self.college_org_count == 0:
            self._add_no_record_label(self.ui.college_org_grid)

        self._update_scroll_areas()
        self.hide_apply_buttons()