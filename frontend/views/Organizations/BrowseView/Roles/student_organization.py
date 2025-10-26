from PyQt6 import QtWidgets, QtCore
from typing import Dict
from ..Base.organization_view_base import OrganizationViewBase
from widgets.orgs_custom_widgets.cards import JoinedOrgCard, CollegeOrgCard

class Student(OrganizationViewBase):
    def __init__(self, student_name: str):
        super().__init__(name=student_name)
        self.load_orgs()

    def load_orgs(self, search_text: str = "") -> None:
        """Load and display organizations, filtered by search text."""
        organizations = self._load_data()
        self._clear_grid(self.ui.joined_org_grid)
        self._clear_grid(self.ui.college_org_grid)
        self.joined_org_count = 0
        self.college_org_count = 0

        student_name = self.name
        filtered_joined = [
            org for org in organizations
            if not org["is_branch"] and (search_text in org["name"].lower() or not search_text) and
            any(member[0] == student_name for member in org.get("members", []))
        ]
        
        joined_org_ids = {org['id'] for org in filtered_joined}
        
        filtered_college = [
            org for org in organizations
            if not org["is_branch"] and (search_text in org["name"].lower() or not search_text) and
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
        """Load and display branches, filtered by search text."""
        organizations = self._load_data()
        self._clear_grid(self.ui.joined_org_grid)
        self._clear_grid(self.ui.college_org_grid)
        self.joined_org_count = 0
        self.college_org_count = 0

        student_name = self.name

        temp_joined_branches = []
        for org in organizations:
            for branch in org.get("branches", []):
                if search_text in branch["name"].lower() or not search_text:
                    is_member = any(member[0] == student_name for member in branch.get("members", []))
                    if is_member:
                        temp_joined_branches.append(branch)
        
        joined_branch_ids = {branch['id'] for branch in temp_joined_branches}

        filtered_joined_branches = []
        filtered_college_branches = []
        
        for org in organizations:
            for branch in org.get("branches", []):
                if search_text in branch["name"].lower() or not search_text:
                    if branch['id'] in joined_branch_ids:
                        if branch not in filtered_joined_branches:
                            filtered_joined_branches.append(branch)
                    else:
                        if branch not in filtered_college_branches:
                            filtered_college_branches.append(branch)
        
        for branch in filtered_joined_branches:
            self._add_joined_org(branch)
        for branch in filtered_college_branches:
            self._add_college_org(branch)

        if self.joined_org_count == 0:
            self._add_no_record_label(self.ui.joined_org_grid)
        if self.college_org_count == 0:
            self._add_no_record_label(self.ui.college_org_grid)

        self._update_scroll_areas()

    def _on_combobox_changed(self, index: int) -> None:
        """Handle combo box change (Student override)."""
        self.ui.joined_label.setText("Joined Organization(s)" if index == 0 else "Joined Branch(es)")
        self.ui.college_label.setText("College Organization(s)" if index == 0 else "College Branch(es)")
        self.load_orgs() if index == 0 else self.load_branches()
        self.ui.joined_org_scrollable.verticalScrollBar().setValue(0)
        self.ui.college_org_scrollable.verticalScrollBar().setValue(0)

    def _add_joined_org(self, org_data: Dict) -> None:
        """Add a joined organization card to the grid."""
        card = JoinedOrgCard(self._get_logo_path(org_data["logo_path"]), org_data, self)
        col = self.joined_org_count % 5
        row = self.joined_org_count // 5
        self.ui.joined_org_grid.addWidget(
            card, row, col, alignment=QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignHCenter
        )
        self.joined_org_count += 1
        self.ui.joined_org_grid.setRowMinimumHeight(row, 300)