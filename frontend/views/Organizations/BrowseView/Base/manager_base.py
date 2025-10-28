"""
Base class for organization managers (Officers and Faculty).
Contains shared functionality for managing members and applicants.
"""
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QMessageBox
from typing import Dict, List, Optional, Tuple
import datetime

class ManagerBase:
    """Mixin class providing member and applicant management functionality."""
    
    STYLE_GREEN_BTN = "background-color: #084924; color: white; border-radius: 5px;"
    STYLE_RED_BTN = "background-color: #EB5757; color: white; border-radius: 5px;"
    STYLE_PRIMARY_BTN = "background-color: #084924; color: white; border-radius: 5px;"
    
    def __init__(self):
        self.is_managing: bool = True
        self.is_viewing_applicants: bool = False
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
    
    def _setup_list_header(self):
        """
        Efficiently sets up the list header based on management and view state.
        
        - If managing, creates the 'Manage Applicants' button once and
          adds it to a new layout with the title label.
        - Toggles the label text and button visibility based on whether
          members or applicants are being viewed.
        - If not managing, this method does nothing, preserving the
          simple label from the .ui file.
        """
        if not self.is_managing:
            self.ui.label_2.setText("Member List")
            return

        if not self.manage_applicants_btn:
            self.manage_applicants_btn = QtWidgets.QPushButton("Manage Applicants")
            self.manage_applicants_btn.setStyleSheet(
                "background-color: transparent; border: none; text-decoration: underline;"
            )
            self.manage_applicants_btn.clicked.connect(
                lambda: self.load_applicants(self._get_search_text())
            )
            
            self.ui.verticalLayout_16.removeWidget(self.ui.label_2)
            self.ui.verticalLayout_16.removeWidget(self.ui.line_5)
            
            header_hlayout = QtWidgets.QHBoxLayout()
            header_hlayout.addWidget(self.ui.label_2)
            header_hlayout.addStretch()
            header_hlayout.addWidget(self.manage_applicants_btn)
            
            self.ui.verticalLayout_16.insertLayout(0, header_hlayout)
            self.ui.verticalLayout_16.addWidget(self.ui.line_5)

        if self.is_viewing_applicants:
            self.ui.label_2.setText("Applicant List")
            self.manage_applicants_btn.hide()
        else:
            self.ui.label_2.setText("Member List")
            self.manage_applicants_btn.show()
            
    def load_members(self, search_text: str = "") -> None:
        """Load and filter members into the table view with management controls."""
        from widgets.orgs_custom_widgets.tables import ViewMembers
        
        if not self.current_org:
            return
            
        self.is_viewing_applicants = False # Set state
        
        members_data = self.current_org.get("members", [])
        officers_data = self.current_org.get("officers", [])
        
        officer_names = {officer["name"] for officer in officers_data}
        existing_member_names = {member[0] for member in members_data}
        
        combined_members = list(members_data)
        for officer in officers_data:
            if officer["name"] not in existing_member_names:
                combined_members.append([
                    officer["name"],
                    officer["position"],
                    "Active",
                    officer.get("start_date", QtCore.QDate.currentDate().toString("yyyy-MM-dd"))
                ])
        
        self.current_org["members"] = combined_members
        
        filtered_members = [
            member for member in combined_members
            if any(search_text in str(field).lower() for field in member)
        ] if search_text else combined_members
        
        self.ui.list_view.setModel(None)
        self.ui.list_view.clearSpans()
        self.ui.list_view.verticalHeader().reset()
        
        model = ViewMembers(filtered_members, is_managing=self.is_managing)
        self.ui.list_view.setModel(model)
        self.ui.list_view.horizontalHeader().setStretchLastSection(True)
        self.ui.list_view.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        
        if filtered_members:
            self.ui.list_view.show()
            self.no_member_label.hide()
        else:
            self.ui.list_view.hide()
            self.no_member_label.show()
        
        self._setup_list_header()
        
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
        
        self._apply_table_style()

    def load_applicants(self, search_text: str = ""):
        """Load and filter applicants into the table view with action controls."""
        from widgets.orgs_custom_widgets.tables import ViewApplicants
        
        if not self.current_org:
            return
            
        self.is_viewing_applicants = True
        
        applicants_data = self.current_org.get("applicants", [])
        filtered_applicants = [
            applicant for applicant in applicants_data
            if any(search_text in str(field).lower() for field in applicant)
        ] if search_text else applicants_data
        
        self.ui.list_view.setModel(None)
        self.ui.list_view.clearSpans()
        self.ui.list_view.verticalHeader().reset()
        
        model = ViewApplicants(filtered_applicants)
        self.ui.list_view.setModel(model)
        self.ui.list_view.horizontalHeader().setStretchLastSection(True)
        self.ui.list_view.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        
        if filtered_applicants:
            self.ui.list_view.show()
            self.no_member_label.hide()
        else:
            self.ui.list_view.hide()
            self.no_member_label.show()
        
        for row in range(len(filtered_applicants)):
            action_widget = self._create_action_widget(
                "Accept", lambda checked, r=row: self.accept_applicant(r),
                "Decline", lambda checked, r=row: self.decline_applicant(r)
            )
            self.ui.list_view.setIndexWidget(
                model.index(row, model.columnCount() - 1), 
                action_widget
            )
        
        self._setup_list_header()
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
            applicant_name = applicant[0]
            
            self.current_org["applicants"].pop(original_index)
            self.current_org["members"].append([
                applicant_name, applicant[1], "Active",
                QtCore.QDate.currentDate().toString("yyyy-MM-dd")
            ])
            
            if "kick_cooldowns" in self.current_org and applicant_name in self.current_org["kick_cooldowns"]:
                del self.current_org["kick_cooldowns"][applicant_name]
            
            org_name = self.current_org.get('name', 'Unknown Org')
            self._log_action("ACCEPT_APPLICANT", org_name, subject_name=applicant_name)
            
            # --- ADD NOTIFICATION FOR STUDENT ---
            notification = {
                "id": f"notif_{datetime.datetime.now().timestamp()}",
                "type": "ACCEPTANCE",
                "org_name": org_name,
                "timestamp": datetime.datetime.now().isoformat()
            }
            self.add_notification(applicant_name, notification)
            # --- END NOTIFICATION ---
            
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
            applicant_name = applicant[0]
            org_name = self.current_org.get('name', 'Unknown Org')
            self._log_action("DECLINE_APPLICANT", org_name, subject_name=applicant_name)
            
            self.current_org["applicants"].pop(original_index)
            self.save_data()
            self.load_applicants(search_text)
    
    def edit_member(self, row: int, bypass_cooldown: bool = False) -> None:
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
            
            officer_positions = ["Chairperson", "Vice - Internal Chairperson", "Vice - External Chairperson", "Secretary", "Treasurer"]
            is_officer_change = (new_position in officer_positions) or (old_position in officer_positions)

            # --- ADDED: Cooldown Check ---
            if is_officer_change and not bypass_cooldown:
                # --- FIX: Standardized cooldown key ---
                is_on_cooldown, end_time = self.check_manager_action_cooldown(self.current_org['id'], "OFFICER_CHANGE")
                if is_on_cooldown:
                    QMessageBox.warning(
                        self, 
                        "Action Cooldown", 
                        f"Officer changes are on cooldown for this organization.\n\nPlease try again after {end_time.strftime('%I:%M:%S %p')}."
                    )
                    return
            # --- END Cooldown Check ---

            self.current_org["members"][original_index][1] = new_position
            
            if new_position in officer_positions:
                officers = self.current_org.get("officers", [])
                is_already_officer = False
                for officer in officers:
                    if officer["name"] == member_name:
                        officer["position"] = new_position
                        is_already_officer = True
                        break
                
                if not is_already_officer:
                    new_officer = {
                        "name": member_name,
                        "position": new_position,
                        "card_image_path": "No Photo",
                        "photo_path": "No Photo",
                        "start_date": QtCore.QDate.currentDate().toString("MM/dd/yyyy")
                    }
                    self.current_org["officers"].append(new_officer)
                    
            elif old_position in officer_positions and new_position == "Member":
                officers = self.current_org.get("officers", [])
                self.current_org["officers"] = [
                    officer for officer in officers if officer["name"] != member_name
                ]
            
            org_name = self.current_org.get('name', 'Unknown Org')
            details = f"Position changed from '{old_position}' to '{new_position}'."
            self._log_action("EDIT_MEMBER", org_name, subject_name=member_name, changes=details)
            
            self.save_data()
            
            # --- ADDED: Set Cooldown ---
            if is_officer_change and not bypass_cooldown:
                # --- FIX: Standardized cooldown key ---
                self.set_manager_action_cooldown(self.current_org['id'], "OFFICER_CHANGE", minutes=5)
            # --- END Set Cooldown ---

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
    
    def kick_member(self, row: int, bypass_cooldown: bool = False) -> None:
        """
        Remove a member from the organization, with special handling for officers.
        [FIXED] Consolidated logic and corrected cooldown implementation.
        """
        if not self.current_org:
            return
        
        search_text = self._get_search_text()
        members = self.current_org.get("members", [])
        
        original_index, member = self._filter_and_find_original_index(
            members, row, search_text
        )
        
        if original_index is None:
            return
        
        member_name = member[0]
        officers = self.current_org.get("officers", [])
        is_officer = any(o["name"] == member_name for o in officers)
        
        # --- ADDED: Cooldown Check ---
        if is_officer and not bypass_cooldown:
            is_on_cooldown, end_time = self.check_manager_action_cooldown(self.current_org['id'], "KICK_OFFICER")
            if is_on_cooldown:
                QMessageBox.warning(
                    self, 
                    "Action Cooldown", 
                    f"Kicking officers is on cooldown for this organization.\n\nPlease try again after {end_time.strftime('%I:%M:%S %p')}."
                )
                return
        # --- END Cooldown Check ---

        kick_confirmed = False
        
        if is_officer:
            message = f"Caution: {member_name} is an officer of this {'organization' if not self.current_org.get('is_branch', False) else 'branch'}.\n\nAre you sure you want to kick them? This will remove them from both members and officers lists."
            confirm = QMessageBox.warning(
                self, "Confirm Kick Officer", message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if confirm == QMessageBox.StandardButton.Yes:
                confirm2 = QMessageBox.critical(
                    self, "Final Confirmation", 
                    f"Are you absolutely sure you want to remove {member_name} as an officer and member?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if confirm2 == QMessageBox.StandardButton.Yes:
                    self.current_org["officers"] = [o for o in officers if o["name"] != member_name]
                    kick_confirmed = True
            
        else:
            confirm = QMessageBox.question(
                self, "Confirm Kick",
                f"Are you sure you want to kick {member_name}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirm == QMessageBox.StandardButton.Yes:
                kick_confirmed = True
        
        if kick_confirmed:
            del self.current_org["members"][original_index]
            
            if "kick_cooldowns" not in self.current_org:
                self.current_org["kick_cooldowns"] = {}
            self.current_org["kick_cooldowns"][member_name] = datetime.datetime.now().isoformat()
            
            org_name = self.current_org.get('name', 'Unknown Org')
            details = f"User was an officer: {is_officer}"
            self._log_action("KICK_MEMBER", org_name, subject_name=member_name, changes=details)
            
            self.save_data()
            
            # --- ADDED: Set Cooldown ---
            if is_officer and not bypass_cooldown:
                self.set_manager_action_cooldown(self.current_org['id'], "KICK_OFFICER", minutes=5)
            # --- END Set Cooldown ---

            self.load_members(search_text)
            
            if is_officer:
                current_index = self.ui.officer_history_dp.currentIndex()
                selected_semester = self.ui.officer_history_dp.itemText(current_index)
                current_officers = (
                    self.current_org.get("officer_history", {}).get(selected_semester, [])
                    if selected_semester != "Current Officers"
                    else self.current_org.get("officers", [])
                )
                self.load_officers(current_officers)
    
    def update_officer_in_org(self, updated_officer: Dict, bypass_cooldown: bool = False) -> None:
        """Update the officer data in the current organization and save."""
        if not self.current_org:
            return

        member_name = updated_officer.get("name", "Unknown")
        new_position = updated_officer.get("position", "Unknown")
        org_name = self.current_org.get("name", "Unknown Org")
        officer_positions = ["Chairperson", "Vice - Internal Chairperson", "Vice - External Chairperson", "Secretary", "Treasurer"]

        old_position = "Member"
        is_new_officer = False
        officers = self.current_org.get("officers", [])
        existing_officer = next((off for off in officers if off["name"] == member_name), None)
        
        if existing_officer:
            old_position = existing_officer.get("position", "Member")
        elif new_position in officer_positions:
             is_new_officer = True
             old_position = "Member"

        is_position_change = (new_position != old_position)
        is_officer_change = is_position_change and (new_position in officer_positions or old_position in officer_positions)
        
        if is_officer_change and not bypass_cooldown:
            is_on_cooldown, end_time = self.check_manager_action_cooldown(self.current_org['id'], "OFFICER_CHANGE")
            if is_on_cooldown:
                QMessageBox.warning(
                    self, 
                    "Action Cooldown", 
                    f"Officer position changes are on cooldown for this organization.\n\nPlease try again after {end_time.strftime('%I:%M:%S %p')}."
                )
                return

        details = f"Officer details updated."
        if is_position_change:
             details += f" Position changed from '{old_position}' to '{new_position}'."

        self._log_action("UPDATE_OFFICER", org_name, subject_name=member_name, changes=details)
        
        if "officers" in self.current_org:
            new_officers = []
            found = False
            for off in self.current_org["officers"]:
                if off["name"] == member_name:
                    if new_position in officer_positions:
                         new_officers.append(updated_officer)
                    found = True
                else:
                    new_officers.append(off)
            
            if not found and new_position in officer_positions:
                new_officers.append(updated_officer)
                
            self.current_org["officers"] = new_officers
        
        if "officer_history" in self.current_org:
            for semester, offs in self.current_org["officer_history"].items():
                new_offs = []
                found_in_history = False
                for off in offs:
                    if off["name"] == member_name:
                         if new_position in officer_positions:
                              new_offs.append(updated_officer)
                         found_in_history = True
                    else:
                        new_offs.append(off)
                if not found_in_history and new_position in officer_positions:
                     new_offs.append(updated_officer)
                self.current_org["officer_history"][semester] = new_offs
        
        members = self.current_org.get("members", [])
        member_found = False
        for i, mem in enumerate(members):
            if mem[0] == member_name:
                if is_position_change:
                     members[i][1] = new_position
                member_found = True
                break
                
        if not member_found:
            new_member_start_date = QtCore.QDate.currentDate().toString("yyyy-MM-dd")
            new_member = [
                member_name,
                new_position,
                "Active",
                updated_officer.get("start_date", new_member_start_date)
            ]
            members.append(new_member)
        
        if new_position not in officer_positions:
             self.current_org["officers"] = [
                 o for o in self.current_org.get("officers", []) if o["name"] != member_name
             ]

        self.current_org["members"] = members
        self.save_data()
        
        if is_officer_change and not bypass_cooldown:
            self.set_manager_action_cooldown(self.current_org['id'], "OFFICER_CHANGE", minutes=5)

        current_index = self.ui.officer_history_dp.currentIndex()
        selected_semester = self.ui.officer_history_dp.itemText(current_index)
        officers_to_display = (
            self.current_org.get("officer_history", {}).get(selected_semester, [])
            if selected_semester != "Current Officers"
            else self.current_org.get("officers", [])
        )
        self.load_officers(officers_to_display)
    
    def open_edit_dialog(self):
        """Open the edit dialog for current org."""
        from widgets.orgs_custom_widgets.dialogs import EditOrgDialog
        
        if self.current_org:
            org_name_before = self.current_org.get("name", "Unknown")
            dialog = EditOrgDialog(self.current_org, self)
            
            if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
                org_name_after = self.current_org.get("name", "Unknown")
                details = f"Org details updated. Name changed from '{org_name_before}' to '{org_name_after}'." if org_name_before != org_name_after else "Org details updated."
                self._log_action("EDIT_ORGANIZATION", org_name_after, subject_name=org_name_after, changes=details)
    
    def _perform_member_search(self) -> None:
        """Handle member or applicant search based on current view."""
        search_text = self._get_search_text()
        if self.is_viewing_applicants:
            self.load_applicants(search_text)
        else:
            self.load_members(search_text)
                
    def _to_members_page(self) -> None:
        """Navigate to the members/management page."""
        if self.current_org:
            self.ui.header_label_3.setText(
                "Organization" if not self.current_org["is_branch"] else "Branch"
            )
        self.is_viewing_applicants = False
        self.load_members(self._get_search_text())
        self.ui.stacked_widget.setCurrentIndex(2)

    def _return_to_prev_page(self) -> None:
        """Navigate back, handling manager/applicant view state."""
        current_index = self.ui.stacked_widget.currentIndex()
        
        if current_index == 2:
            if self.is_viewing_applicants:
                self.is_viewing_applicants = False
                self.load_members(self._get_search_text())
            else:
                self.ui.stacked_widget.setCurrentIndex(1)
        
        elif current_index == 1:
            if self.ui.comboBox.currentIndex() == 0:
                self.load_orgs()
            else:
                self.load_branches()
            self.ui.stacked_widget.setCurrentIndex(0)
            
        else:
            if self.ui.comboBox.currentIndex() == 0:
                self.load_orgs()
            else:
                self.load_branches()
            self.ui.stacked_widget.setCurrentIndex(0)