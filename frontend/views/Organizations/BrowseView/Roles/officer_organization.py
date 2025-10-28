from PyQt6 import QtWidgets
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QMessageBox, QFileDialog

from typing import Dict
from .student_organization import Student
from ..Base.manager_base import ManagerBase
from widgets.orgs_custom_widgets.dialogs import OfficerDialog
from ..Utils.image_utils import copy_image_to_data

class Officer(ManagerBase, Student):
    """Officer view with member and applicant management capabilities."""
    
    def __init__(self, officer_name: str):
        Student.__init__(self, student_name=officer_name)
        ManagerBase.__init__(self)
        self._setup_officer_connections()
    
    def _setup_officer_connections(self) -> None:
        """Set up additional signal-slot connections for officer-specific functionality."""
        self.ui.view_members_btn.clicked.disconnect()
        self.ui.view_members_btn.clicked.connect(self._to_members_page)
        self.ui.back_btn_member.clicked.disconnect()
        self.ui.back_btn_member.clicked.connect(self._return_to_prev_page)
        self.ui.search_line_3.textChanged.connect(self._perform_member_search)
    
    def show_officer_dialog(self, officer_data: Dict) -> None:
        """Display officer details in a dialog."""
        OfficerDialog(officer_data, self).exec()
    
    def show_org_details(self, org_data: Dict) -> None:
        """Display organization details with officer-specific features."""
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
            
            branch_list_index = self.ui.verticalLayout_10.indexOf(self.ui.obj_label_2)
            if branch_list_index != -1:
                spacer = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
                self.ui.verticalLayout_10.insertItem(branch_list_index + 1, spacer)
                
                self.ui.verticalLayout_10.insertWidget(branch_list_index + 2, self.edit_btn)
            else:
                spacer = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
                self.ui.verticalLayout_10.addItem(spacer)
                self.ui.verticalLayout_10.addWidget(self.edit_btn)
            
            my_officer_data = next((off for off in officers if off.get("name") == self.name), None)
            if my_officer_data and not my_officer_data.get("cv_path"):
                QTimer.singleShot(100, self._prompt_for_cv)
            
        else:
            self.ui.view_members_btn.setText("View Members")
    
    def _prompt_for_cv(self) -> None:
        """Prompt the new officer to upload their CV."""
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
                    # Update self.current_org and save
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
        """Navigate to the members page with officer-specific view."""
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