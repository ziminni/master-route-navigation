from PyQt6 import QtWidgets
from typing import Dict
from .organization_view_base import OrganizationViewBase

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
        """Load and display organizations, filtered by search text."""
        organizations = self._load_data()
        self._clear_grid(self.ui.college_org_grid)
        self.college_org_count = 0
        
        filtered_college = [
            org for org in organizations 
            if not org["is_branch"] and (search_text in org["name"].lower() or not search_text)
        ]
        
        for org in filtered_college:
            self._add_college_org(org)
        
        if self.college_org_count == 0:
            self._add_no_record_label(self.ui.college_org_grid)
        
        self._update_scroll_areas()
        self.hide_apply_buttons()
    
    def load_branches(self, search_text: str = "") -> None:
        """Load and display branches, filtered by search text."""
        organizations = self._load_data()
        self._clear_grid(self.ui.college_org_grid)
        self.college_org_count = 0
        
        filtered_college_branches = []
        for org in organizations:
            for branch in org.get("branches", []):
                if search_text in branch["name"].lower() or not search_text:
                    filtered_college_branches.append(branch)
        
        for branch in filtered_college_branches:
            self._add_college_org(branch)
        
        if self.college_org_count == 0:
            self._add_no_record_label(self.ui.college_org_grid)
        
        self._update_scroll_areas()
        self.hide_apply_buttons()
    
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