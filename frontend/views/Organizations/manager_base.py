"""
Base class for organization managers (Officers and Faculty).
Contains shared functionality for managing members and applicants.
"""
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QMessageBox
from typing import Dict, List, Optional, Tuple

class ManagerBase:
    """Mixin class providing member and applicant management functionality."""
    
    STYLE_GREEN_BTN = "background-color: #084924; color: white; border-radius: 5px;"
    STYLE_RED_BTN = "background-color: #EB5757; color: white; border-radius: 5px;"
    STYLE_PRIMARY_BTN = "background-color: #084924; color: white; border-radius: 5px;"
    
    def __init__(self):
        self.is_managing: bool = True
        self.is_viewing_applicants: bool = False
        self.edit_btn: Optional[QtWidgets.QPushButton] = None
        self.manage_applicants_btn: Optional[QtWidgets.QPushButton] = None
    
    def _get_search_text(self) -> str:
        """Get current search text from the search field."""
        return self.ui.search_line_3.text().strip().lower()
    
    def _filter_and_find_original_index(
        self, 
        items: List, 
        row: int, 
        search_text: str = ""
    ) -> Tuple[Optional[int], Optional[List]]:
        """
        Filter items by search text and find the original index of the selected row.
        
        Returns:
            Tuple of (original_index, original_item) or (None, None) if not found
        """
        filtered_items = [
            item for item in items
            if any(search_text in str(field).lower() for field in item)
        ] if search_text else items
        
        if row >= len(filtered_items):
            return None, None
        
        filtered_item = filtered_items[row]
        original_index = next(
            (i for i, item in enumerate(items) if item[0] == filtered_item[0]), 
            None
        )
        
        if original_index is None:
            return None, None
            
        return original_index, items[original_index]
    
    def _create_action_widget(
        self, 
        btn1_text: str, 
        btn1_callback, 
        btn2_text: str, 
        btn2_callback
    ) -> QtWidgets.QWidget:
        """Create a widget with two action buttons."""
        action_widget = QtWidgets.QWidget()
        hlayout = QtWidgets.QHBoxLayout(action_widget)
        hlayout.setContentsMargins(5, 5, 5, 5)
        hlayout.setSpacing(5)
        
        btn1 = QtWidgets.QPushButton(btn1_text)
        btn1.setStyleSheet(self.STYLE_GREEN_BTN)
        btn1.clicked.connect(btn1_callback)
        
        btn2 = QtWidgets.QPushButton(btn2_text)
        btn2.setStyleSheet(self.STYLE_RED_BTN)
        btn2.clicked.connect(btn2_callback)
        
        hlayout.addWidget(btn1)
        hlayout.addWidget(btn2)
        
        return action_widget
    
    def _setup_member_header_with_applicants_btn(self):
        """Set up the member list header with 'Manage Applicants' button."""
        self.ui.verticalLayout_16.removeWidget(self.ui.label_2)
        self.ui.verticalLayout_16.removeWidget(self.ui.line_5)
        
        header_hlayout = QtWidgets.QHBoxLayout()
        self.ui.label_2.setText("Member List")
        header_hlayout.addWidget(self.ui.label_2)
        header_hlayout.addStretch()
        
        self.manage_applicants_btn = QtWidgets.QPushButton("Manage Applicants")
        self.manage_applicants_btn.setStyleSheet("background-color: transparent; border: none; text-decoration: underline;")
        self.manage_applicants_btn.clicked.connect(
            lambda: self.load_applicants(self._get_search_text())
        )
        header_hlayout.addWidget(self.manage_applicants_btn)
        
        self.ui.verticalLayout_16.insertLayout(0, header_hlayout)
        self.ui.verticalLayout_16.addWidget(self.ui.line_5)
    
    def _setup_applicant_header(self):
        """Set up the applicant list header."""
        if self.ui.verticalLayout_16.itemAt(0):
            item = self.ui.verticalLayout_16.itemAt(0)
            if isinstance(item, QtWidgets.QHBoxLayout):
                self.ui.verticalLayout_16.removeItem(item)
        
        self.ui.verticalLayout_16.removeWidget(self.ui.label_2)
        self.ui.verticalLayout_16.removeWidget(self.ui.line_5)
        
        header_hlayout = QtWidgets.QHBoxLayout()
        self.ui.label_2.setText("Applicant List")
        header_hlayout.addWidget(self.ui.label_2)
        header_hlayout.addStretch()
        
        self.ui.verticalLayout_16.insertLayout(0, header_hlayout)
        self.ui.verticalLayout_16.addWidget(self.ui.line_5)
    
    def _cleanup_manage_applicants_btn(self):
        """Remove the 'Manage Applicants' button if it exists."""
        if self.manage_applicants_btn:
            self.ui.verticalLayout_16.removeWidget(self.manage_applicants_btn)
            self.manage_applicants_btn.deleteLater()
            self.manage_applicants_btn = None
            self.ui.verticalLayout_16.removeItem(self.ui.verticalLayout_16.itemAt(0))
            self.ui.verticalLayout_16.insertWidget(0, self.ui.label_2)
            self.ui.verticalLayout_16.addWidget(self.ui.line_5)
    
    def load_members(self, search_text: str = "") -> None:
        """Load and filter members into the table view with management controls."""
        from widgets.orgs_custom_widgets.tables import ViewMembers
        
        if not self.current_org:
            return
        
        members_data = self.current_org.get("members", [])
        officers_data = self.current_org.get("officers", [])
        
        # Add officers to members list if not already present
        officer_names = {officer["name"] for officer in officers_data}
        existing_member_names = {member[0] for member in members_data}
        
        # Create a combined list with officers included
        combined_members = list(members_data)
        for officer in officers_data:
            if officer["name"] not in existing_member_names:
                # Add officer as member with their position
                combined_members.append([
                    officer["name"],
                    officer["position"],
                    "Active",
                    officer.get("start_date", QtCore.QDate.currentDate().toString("yyyy-MM-dd"))
                ])
        
        # Update members in current_org to include officers
        self.current_org["members"] = combined_members
        
        filtered_members = [
            member for member in combined_members
            if any(search_text in str(field).lower() for field in member)
        ] if search_text else combined_members
        
        # Reset table
        self.ui.list_view.setModel(None)
        self.ui.list_view.clearSpans()
        self.ui.list_view.verticalHeader().reset()
        
        # Set up model
        model = ViewMembers(filtered_members, is_managing=self.is_managing)
        self.ui.list_view.setModel(model)
        self.ui.list_view.horizontalHeader().setStretchLastSection(True)
        self.ui.list_view.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        
        # Show/hide based on data
        if filtered_members:
            self.ui.list_view.show()
            self.no_member_label.hide()
        else:
            self.ui.list_view.hide()
            self.no_member_label.show()
        
        self._cleanup_manage_applicants_btn()
        
        # Add action buttons if managing
        if self.is_managing:
            for row in range(len(filtered_members)):
                action_widget = self._create_action_widget(
                    "Edit", lambda checked, r=row: self.edit_member(r),
                    "Kick", lambda checked, r=row: self.kick_member(r)
                )
                self.ui.list_view.setIndexWidget(
                    model.index(row, model.columnCount() - 1), 
                    action_widget
                )
            
            if self.is_managing:
                self._setup_member_header_with_applicants_btn()
        
        self._apply_table_style()

    def load_applicants(self, search_text: str = ""):
        """Load and filter applicants into the table view with action controls."""
        from widgets.orgs_custom_widgets.tables import ViewApplicants
        
        if not self.current_org:
            return
        
        applicants_data = self.current_org.get("applicants", [])
        filtered_applicants = [
            applicant for applicant in applicants_data
            if any(search_text in str(field).lower() for field in applicant)
        ] if search_text else applicants_data
        
        # Reset table
        self.ui.list_view.setModel(None)
        self.ui.list_view.clearSpans()
        self.ui.list_view.verticalHeader().reset()
        
        # Set up model
        model = ViewApplicants(filtered_applicants)
        self.ui.list_view.setModel(model)
        self.ui.list_view.horizontalHeader().setStretchLastSection(True)
        self.ui.list_view.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        
        # Show/hide based on data
        if filtered_applicants:
            self.ui.list_view.show()
            self.no_member_label.hide()
        else:
            self.ui.list_view.hide()
            self.no_member_label.show()
        
        self._cleanup_manage_applicants_btn()
        
        # Add action buttons
        for row in range(len(filtered_applicants)):
            action_widget = self._create_action_widget(
                "Accept", lambda checked, r=row: self.accept_applicant(r),
                "Decline", lambda checked, r=row: self.decline_applicant(r)
            )
            self.ui.list_view.setIndexWidget(
                model.index(row, model.columnCount() - 1), 
                action_widget
            )
        
        self._setup_applicant_header()
        self.is_viewing_applicants = True
        self._apply_table_style()
    
    def accept_applicant(self, row: int):
        """Confirm and move applicant to members."""
        search_text = self._get_search_text()
        applicants = self.current_org.get("applicants", [])
        
        original_index, applicant = self._filter_and_find_original_index(
            applicants, row, search_text
        )
        
        if original_index is None:
            return
        
        confirm = QMessageBox.question(
            self,
            "Confirm Accept",
            f"Are you sure you want to accept {applicant[0]} as a member?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            self.current_org["applicants"].pop(original_index)
            self.current_org["members"].append([
                applicant[0], applicant[1], "Active",
                QtCore.QDate.currentDate().toString("yyyy-MM-dd")
            ])
            self.save_data()
            self.load_applicants(search_text)
    
    def decline_applicant(self, row: int):
        """Confirm and remove applicant from list."""
        search_text = self._get_search_text()
        applicants = self.current_org.get("applicants", [])
        
        original_index, applicant = self._filter_and_find_original_index(
            applicants, row, search_text
        )
        
        if original_index is None:
            return
        
        confirm = QMessageBox.question(
            self,
            "Confirm Decline",
            f"Are you sure you want to decline {applicant[0]}'s application?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            self.current_org["applicants"].pop(original_index)
            self.save_data()
            self.load_applicants(search_text)
    
    def edit_member(self, row: int) -> None:
        """Open dialog to edit member's position."""
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
        
        dialog = EditMemberDialog(member, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            new_position = dialog.updated_position
            old_position = member[1]
            member_name = member[0]
            
            # Update member position
            self.current_org["members"][original_index][1] = new_position
            
            officer_positions = ["Chairperson", "Vice - Internal Chairperson", "Vice - External Chairperson", "Secretary", "Treasurer"]
            
            if new_position in officer_positions:
                # Check if member is already in officers list
                officers = self.current_org.get("officers", [])
                is_already_officer = any(officer["name"] == member_name for officer in officers)
                
                if not is_already_officer:
                    # Promote member to officer
                    new_officer = {
                        "name": member_name,
                        "position": new_position,
                        "card_image_path": "No Photo",
                        "photo_path": "No Photo",
                        "start_date": QtCore.QDate.currentDate().toString("MM/dd/yyyy")
                    }
                    self.current_org["officers"].append(new_officer)
                else:
                    # Update existing officer position
                    for officer in officers:
                        if officer["name"] == member_name:
                            officer["position"] = new_position
                            break
            elif old_position in officer_positions and new_position == "Member":
                officers = self.current_org.get("officers", [])
                self.current_org["officers"] = [
                    officer for officer in officers if officer["name"] != member_name
                ]
            
            self.save_data()
            self.load_members(search_text)
            
            if new_position in officer_positions or old_position in officer_positions:
                current_index = self.ui.officer_history_dp.currentIndex()
                selected_semester = self.ui.officer_history_dp.itemText(current_index)
                officers = (
                    self.current_org.get("officer_history", {}).get(selected_semester, [])
                    if selected_semester != "Current Officers"
                    else self.current_org.get("officers", [])
                )
                self.load_officers(officers)
    
    def kick_member(self, row: int) -> None:
        """Remove a member from the organization."""
        if not self.current_org:
            return
        
        search_text = self._get_search_text()
        members = self.current_org.get("members", [])
        
        original_index, member = self._filter_and_find_original_index(
            members, row, search_text
        )
        
        if original_index is None:
            return
        
        confirm = QMessageBox.question(
            self, "Confirm Kick",
            f"Are you sure you want to kick {member[0]}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            del self.current_org["members"][original_index]
            self.save_data()
            self.load_members(search_text)
    
    def update_officer_in_org(self, updated_officer: Dict) -> None:
        """Update the officer data in the current organization and save."""
        if not self.current_org:
            return
        
        officer_positions = ["Chairperson", "Vice - Internal Chairperson", "Vice - External Chairperson", "Secretary", "Treasurer"]
        member_name = updated_officer["name"]
        new_position = updated_officer["position"]
        
        if "officers" in self.current_org:
            new_officers = []
            for off in self.current_org["officers"]:
                if off["name"] == member_name:
                    if new_position in officer_positions:
                        new_officers.append(updated_officer)
                else:
                    new_officers.append(off)
            self.current_org["officers"] = new_officers
        
        if "officer_history" in self.current_org:
            for semester, offs in self.current_org["officer_history"].items():
                new_offs = []
                for off in offs:
                    if off["name"] == member_name:
                        if new_position in officer_positions:
                            new_offs.append(updated_officer)
                    else:
                        new_offs.append(off)
                self.current_org["officer_history"][semester] = new_offs
        
        if new_position not in officer_positions:
            members = self.current_org.get("members", [])
            member_found = False
            for i, mem in enumerate(members):
                if mem[0] == member_name:
                    members[i][1] = new_position 
                    member_found = True
                    break
            if not member_found:
                new_member = [
                    member_name,
                    new_position,
                    "Active",
                    updated_officer.get("start_date", QtCore.QDate.currentDate().toString("MM/dd/yyyy"))
                ]
                members.append(new_member)
            self.current_org["members"] = members
        
        self.save_data()
        
        current_index = self.ui.officer_history_dp.currentIndex()
        selected_semester = self.ui.officer_history_dp.itemText(current_index)
        officers = (
            self.current_org.get("officer_history", {}).get(selected_semester, [])
            if selected_semester != "Current Officers"
            else self.current_org.get("officers", [])
        )
        self.load_officers(officers)
    
    def open_edit_dialog(self):
        """Open the edit dialog for current org."""
        from widgets.orgs_custom_widgets.dialogs import EditOrgDialog
        
        if self.current_org:
            dialog = EditOrgDialog(self.current_org, self)
            dialog.exec()
    
    def _perform_member_search(self) -> None:
        """Handle member or applicant search based on current view."""
        search_text = self._get_search_text()
        if self.is_viewing_applicants:
            self.load_applicants(search_text)
        else:
            self.load_members(search_text)
