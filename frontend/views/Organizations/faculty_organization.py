from PyQt6 import QtWidgets
import sys
import os

from typing import Dict
from .user import User
from .manager_base import ManagerBase
from widgets.orgs_custom_widgets.dialogs import OfficerDialog
from ui.Organization.org_main_ui import Ui_Widget

class Faculty(ManagerBase, User):
    """Faculty view with full member and applicant management capabilities."""
    
    def __init__(self, faculty_name: str = "Faculty Name"):
        User.__init__(self, name=faculty_name)
        ManagerBase.__init__(self)
        
        self.ui = Ui_Widget()
        self.ui.setupUi(self)
        self._apply_table_style()
        self.ui.joined_container.setVisible(False)
        
        self.table = self.findChild(QtWidgets.QTableView, "list_view")
        self._setup_no_member_label()
        self.ui.verticalLayout_17.addWidget(self.no_member_label)
        self._setup_connections()
        self.load_orgs()
    
    def show_officer_dialog(self, officer_data: Dict) -> None:
        """Display officer details in a dialog."""
        OfficerDialog(officer_data, self).exec()
    
    def _setup_connections(self) -> None:
        """Set up signal-slot connections."""
        self.ui.comboBox.currentIndexChanged.connect(self._on_combobox_changed)
        self.ui.view_members_btn.clicked.connect(self._to_members_page)
        self.ui.back_btn_member.clicked.connect(self._return_to_prev_page)
        self.ui.back_btn.clicked.connect(self._return_to_prev_page)
        self.ui.search_line.textChanged.connect(self._perform_search)
        self.ui.search_line_3.textChanged.connect(self._perform_member_search)
        self.ui.officer_history_dp.currentIndexChanged.connect(self._on_officer_history_changed)
    
    def _setup_no_member_label(self) -> None:
        """Initialize the 'No Record(s) Found' label for members or applicants."""
        from PyQt6 import QtCore
        
        self.no_member_label = QtWidgets.QLabel("No Record(s) Found", self.ui.list_container)
        self.no_member_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.no_member_label.setStyleSheet("font-size: 20px;")
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred, 
            QtWidgets.QSizePolicy.Policy.Expanding
        )
        self.no_member_label.setSizePolicy(sizePolicy)
        self.no_member_label.hide()
    
    def _perform_search(self) -> None:
        """Handle organization/branch search."""
        search_text = self.ui.search_line.text().strip().lower()
        if self.ui.comboBox.currentIndex() == 0:
            self.load_orgs(search_text)
        else:
            self.load_branches(search_text)
    
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
        """Display organization details with faculty-specific features."""
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

    def _add_college_org(self, org_data: Dict) -> None:
        """Add a college organization card to the grid."""
        from PyQt6 import QtCore
        from widgets.orgs_custom_widgets.cards import CollegeOrgCard
        
        card = CollegeOrgCard(
            self._get_logo_path(org_data["logo_path"]), 
            org_data["name"],
            org_data, 
            self
        )
        col = self.college_org_count % 5
        row = self.college_org_count // 5
        self.ui.college_org_grid.addWidget(
            card, row, col, 
            alignment=QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignHCenter
        )
        self.college_org_count += 1
        self.ui.college_org_grid.setRowMinimumHeight(row, 300)
    
    def _on_combobox_changed(self, index: int) -> None:
        """Handle combo box change to switch between organizations and branches."""
        self.ui.college_label.setText(
            "College Organization(s)" if index == 0 else "College Branch(es)"
        )
        if self.ui.comboBox.currentIndex() == 0:
            self.load_orgs()
        else:
            self.load_branches()
        self.ui.college_org_scrollable.verticalScrollBar().setValue(0)
    
    def _on_officer_history_changed(self, index: int) -> None:
        """Handle officer history combobox change."""
        if not self.current_org:
            return
        
        selected_semester = self.ui.officer_history_dp.itemText(index)
        officers = (
            self.current_org.get("officer_history", {}).get(selected_semester, [])
            if selected_semester != "Current Officers"
            else self.current_org.get("officers", [])
        )
        self.load_officers(officers)
    
    def _to_members_page(self) -> None:
        """Navigate to the members page."""
        if self.current_org:
            self.ui.header_label_3.setText(
                "Organization" if not self.current_org["is_branch"] else "Branch"
            )
        self.is_viewing_applicants = False
        self.load_members(self._get_search_text())
        self.ui.stacked_widget.setCurrentIndex(2)
    
    def _return_to_prev_page(self) -> None:
        """Navigate back to the previous page, handling applicants view."""
        if self.ui.stacked_widget.currentIndex() == 2:
            if self.is_viewing_applicants:
                self.is_viewing_applicants = False
                self.load_members(self._get_search_text())
            else:
                self.ui.stacked_widget.setCurrentIndex(1)
        else:
            if self.ui.comboBox.currentIndex() == 0:
                self.load_orgs()
            else:
                self.load_branches()
            self.ui.stacked_widget.setCurrentIndex(0)