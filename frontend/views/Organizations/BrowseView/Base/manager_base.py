"""
Base class for organization managers (Officers and Faculty).
Contains shared functionality for managing members and applicants.
"""
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QMessageBox
from typing import Dict, List, Optional, Tuple
import datetime
from widgets.orgs_custom_widgets.tables import ActionDelegate


class ManagerBase:
    """Mixin class providing member and applicant management functionality."""
    
    STYLE_GREEN_BTN = "background-color: #084924; color: white; border-radius: 5px;"
    STYLE_RED_BTN = "background-color: #EB5757; color: white; border-radius: 5px;"
    STYLE_PRIMARY_BTN = "background-color: #084924; color: white; border-radius: 5px;"
    
    def __init__(self):
        self.is_managing: bool = True
        self.is_viewing_applicants: bool = False
        self.manage_applicants_btn: Optional[QtWidgets.QPushButton] = None
        self.current_members_page: int = 0
        self.current_applicants_page: int = 0
        self.total_members_pages: int = 1
        self.total_applicants_pages: int = 1
        self.filtered_members: List = []
        self.filtered_applicants: List = []
    
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
            self.manage_applicants_btn.setText("View Members")
            self.manage_applicants_btn.disconnect()
            self.manage_applicants_btn.clicked.connect(
                lambda: self.load_members(self._get_search_text())
            )
            self.manage_applicants_btn.show()
        else:
            self.ui.label_2.setText("Member List")
            self.manage_applicants_btn.setText("Manage Applicants")
            self.manage_applicants_btn.disconnect()
            self.manage_applicants_btn.clicked.connect(
                lambda: self.load_applicants(self._get_search_text())
            )
            self.manage_applicants_btn.show()
            
    def load_members(self, search_text: str = "") -> None: # MODIFIED
        """Load and filter members into the table view with management controls."""
        from widgets.orgs_custom_widgets.tables import ViewMembers
        
        if not self.current_org:
            print("DEBUG load_members: No current_org")
            return
            
        self.is_viewing_applicants = False
        
        members_data = self.current_org.get("members", [])
        print(f"DEBUG load_members: Found {len(members_data)} members in current_org")
        print(f"DEBUG load_members: Members data: {members_data}")
        
        self.filtered_members = [
            member for member in members_data
            if any(search_text in str(field).lower() for field in member)
        ] if search_text else members_data.copy()

        total_items = len(self.filtered_members)
        print(f"DEBUG load_members: Total items after filter: {total_items}")
        
        self.total_members_pages = max(1, (total_items + self.items_per_page - 1) // self.items_per_page)
        self.current_members_page = max(0, min(self.current_members_page, self.total_members_pages - 1))

        start = self.current_members_page * self.items_per_page
        end = start + self.items_per_page
        paged_data = self.filtered_members[start:end]
        
        print(f"DEBUG load_members: Paged data ({start}:{end}): {paged_data}")

        model = self.ui.list_view.model()
        
        if model and isinstance(model, ViewMembers) and model.is_managing == self.is_managing:
            model.update_data(paged_data)
        else:
            self.ui.list_view.setModel(None)
            self.ui.list_view.clearSpans()
            self.ui.list_view.verticalHeader().reset()
            model = ViewMembers(paged_data, is_managing=self.is_managing)
            self.ui.list_view.setModel(model)
            self._apply_table_style()
            self._setup_action_delegate()

        if total_items:
            print("DEBUG load_members: Showing table, hiding no_member_label")
            self.ui.list_view.show()
            self.no_member_label.hide()
        else:
            print("DEBUG load_members: Hiding table, showing no_member_label")
            self.ui.list_view.hide()
            self.no_member_label.setText("No Member(s) Found")
            self.no_member_label.show()

        self._setup_list_header()
        self._update_pagination_buttons_members()

    def load_applicants(self, search_text: str = "") -> None: # MODIFIED
        from widgets.orgs_custom_widgets.tables import ViewApplicants

        if not self.current_org:
            return

        self.is_viewing_applicants = True

        applicants_data = self.current_org.get("applicants", [])
        self.filtered_applicants = [
            applicant for applicant in applicants_data
            if any(search_text in str(field).lower() for field in applicant.values())
        ] if search_text else applicants_data.copy()

        total_items = len(self.filtered_applicants)
        self.total_applicants_pages = max(1, (total_items + self.items_per_page - 1) // self.items_per_page)
        self.current_applicants_page = max(0, min(self.current_applicants_page, self.total_applicants_pages - 1))

        start = self.current_applicants_page * self.items_per_page
        end = start + self.items_per_page
        paged_data = self.filtered_applicants[start:end]

        model = self.ui.list_view.model()
        
        if model and isinstance(model, ViewApplicants):
             model.update_data(paged_data)
        else:
            self.ui.list_view.setModel(None)
            self.ui.list_view.clearSpans()
            self.ui.list_view.verticalHeader().reset()
            model = ViewApplicants(paged_data)
            self.ui.list_view.setModel(model)
            self._apply_table_style()

        if total_items:
            self.ui.list_view.show()
            self.no_member_label.hide()
        else:
            self.ui.list_view.hide()
            self.no_member_label.setText("No Applicant(s) Found")
            self.no_member_label.show()

        self._setup_list_header()
        self._setup_applicant_action_delegate()
        self._update_pagination_buttons_applicants()

    def _update_pagination_buttons_members(self) -> None:
        self.page_label.setText(f"Page {self.current_members_page + 1} of {self.total_members_pages}")
        self.prev_btn.setEnabled(self.current_members_page > 0)
        self.next_btn.setEnabled(self.current_members_page < self.total_members_pages - 1)

    def _update_pagination_buttons_applicants(self) -> None:
        self.page_label.setText(f"Page {self.current_applicants_page + 1} of {self.total_applicants_pages}")
        self.prev_btn.setEnabled(self.current_applicants_page > 0)
        self.next_btn.setEnabled(self.current_applicants_page < self.total_applicants_pages - 1)

    def prev_page(self) -> None:
        if self.is_viewing_applicants:
            if self.current_applicants_page > 0:
                self.current_applicants_page -= 1
        else:
            if self.current_members_page > 0:
                self.current_members_page -= 1
        self._reload_current_view()

    def next_page(self) -> None:
        if self.is_viewing_applicants:
            if self.current_applicants_page < self.total_applicants_pages - 1:
                self.current_applicants_page += 1
        else:
            if self.current_members_page < self.total_members_pages - 1:
                self.current_members_page += 1
        self._reload_current_view()

    def _reload_current_view(self) -> None:
        search_text = self._get_search_text()
        if self.is_viewing_applicants:
            self.load_applicants(search_text)
        else:
            self.load_members(search_text)
    
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
        """Open dialog to edit member's position via API"""
        from widgets.orgs_custom_widgets.dialogs import EditMemberDialog
        from services.organization_api_service import OrganizationAPIService
        
        if not self.current_org:
            return
        
        search_text = self._get_search_text()
        members = self.current_org.get("members", [])
        
        original_index, member = self._filter_and_find_original_index(
            members, row, search_text
        )
        
        if original_index is None:
            return
        
        # Get member_id from members_dict (set by admin view's _fetch_members)
        member_name = member[0]
        member_id = None
        
        # Try to find member_id from members_dict if it exists
        if hasattr(self, 'members_dict'):
            for mid, mdata in self.members_dict.items():
                if mdata.get('name') == member_name:
                    member_id = mid
                    break
        
        if member_id is None:
            QMessageBox.critical(
                self,
                "Error",
                "Could not identify member. Please refresh and try again."
            )
            return
        
        dialog = EditMemberDialog(member, member_id, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            new_position = dialog.updated_position
            position_id = dialog.updated_position_id
            start_term = getattr(dialog, 'start_term', None)
            end_term = getattr(dialog, 'end_term', None)
            old_position = member[1]
            
            print(f"DEBUG manager_base: Extracted from dialog - start_term={start_term}, end_term={end_term}")
            
            # Get current user ID for audit trail
            updated_by_id = None
            
            # Try API call first
            if hasattr(self, 'name') and self.name:
                print(f"DEBUG: self.name = '{self.name}', calling API...")
                try:
                    api_response = OrganizationAPIService.get_current_user_by_username(self.name)
                    print(f"DEBUG: API response = {api_response}")
                    if api_response.get('success') and api_response.get('data'):
                        updated_by_id = api_response['data'].get('profile_id')
                        print(f"DEBUG: Got updated_by_id from API: {updated_by_id}")
                    else:
                        print(f"DEBUG: API call failed or no data: {api_response}")
                except Exception as e:
                    print(f"DEBUG: Exception calling API: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"DEBUG: self.name not available (hasattr={hasattr(self, 'name')}, value={getattr(self, 'name', None)})")
            
            # Fallback to other sources
            if not updated_by_id:
                if hasattr(self, 'admin_profile') and self.admin_profile:
                    updated_by_id = self.admin_profile.get('id')
                elif hasattr(self, 'current_user') and self.current_user:
                    updated_by_id = self.current_user.get('id')
                elif hasattr(self, 'user_id'):
                    updated_by_id = self.user_id
                elif hasattr(self, 'profile_id'):
                    updated_by_id = self.profile_id
            
            # Try QSettings as last resort
            if not updated_by_id:
                try:
                    from PyQt6.QtCore import QSettings
                    settings = QSettings("CISC", "MasterRoute")
                    updated_by_id = settings.value("user_profile_id", type=int)
                    if updated_by_id:
                        print(f"DEBUG: Got updated_by_id from QSettings: {updated_by_id}")
                except Exception as e:
                    print(f"DEBUG: Could not get user_profile_id from QSettings: {e}")
            
            print(f"DEBUG: Updating member {member_id} with updated_by_id={updated_by_id}")
            print(f"DEBUG manager_base: position_id={position_id}, position_name={new_position}")
            print(f"DEBUG manager_base: start_term={start_term}, end_term={end_term}")
            
            if not updated_by_id:
                print("WARNING: Could not determine updated_by_id - audit trail will be incomplete")
            
            # Update position via API
            try:
                api_response = OrganizationAPIService.update_member_position(
                    member_id=member_id,
                    position_id=position_id,
                    position_name=new_position,
                    start_term=start_term,
                    end_term=end_term,
                    updated_by_id=updated_by_id
                )
                
                if not api_response:
                    raise Exception("No response from API")
                
                if api_response.get('success'):
                    QMessageBox.information(
                        self,
                        "Success",
                        f"{member_name}'s position updated to {new_position}."
                    )
                    
                    # Get updated member data from API response
                    updated_member_data = api_response.get('data', {})
                    print(f"DEBUG: Received updated member data: {updated_member_data}")
                    
                    # Update the member in memory without full refresh
                    if updated_member_data and hasattr(self, '_update_member_in_list'):
                        try:
                            self._update_member_in_list(member_id, updated_member_data)
                            self.load_members(search_text)
                        except Exception as e:
                            print(f"WARNING: Failed to update member in list: {e}")
                            # Fallback to full refresh
                            if self.current_org and hasattr(self, '_fetch_members'):
                                self._fetch_members(self.current_org["id"])
                                self.load_members(search_text)
                    elif self.current_org and hasattr(self, '_fetch_members'):
                        # Fallback: full refresh if _update_member_in_list not available
                        self._fetch_members(self.current_org["id"])
                        self.load_members(search_text)
                    else:
                        # Last resort: update locally
                        self.current_org["members"][original_index][1] = new_position
                        self.load_members(search_text)
                    
                    org_name = self.current_org.get('name', 'Unknown Org')
                    details = f"Position changed from '{old_position}' to '{new_position}'."
                    self._log_action("EDIT_MEMBER", org_name, subject_name=member_name, changes=details)
                else:
                    error_msg = api_response.get('message', 'Failed to update position')
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Failed to update member position:\n{error_msg}"
                    )
                    
            except Exception as e:
                print(f"ERROR: Exception during member position update: {str(e)}")
                import traceback
                traceback.print_exc()
                QMessageBox.critical(
                    self,
                    "Error",
                    f"An unexpected error occurred:\n{str(e)}"
                )
    
    def kick_member(self, row: int, bypass_cooldown: bool = False) -> None:
        """
        Remove a member from the organization via API
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
        
        # Get member_id from members_dict
        member_id = None
        if hasattr(self, 'members_dict'):
            for mid, mdata in self.members_dict.items():
                if mdata.get('name') == member_name:
                    member_id = mid
                    break
        
        if member_id is None:
            QMessageBox.critical(
                self,
                "Error",
                "Could not identify member. Please refresh and try again."
            )
            return
        
        # Check if member is an officer
        position = member[1] if len(member) > 1 else "Member"
        is_officer = position and position.lower() != "member"
        
        # Confirm kick action
        if is_officer:
            message = f"Caution: {member_name} is an officer ({position}).\n\nAre you sure you want to kick them?"
            confirm = QMessageBox.warning(
                self, "Confirm Kick Officer", message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
        else:
            confirm = QMessageBox.question(
                self, "Confirm Kick",
                f"Are you sure you want to kick {member_name}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
        
        if confirm != QMessageBox.StandardButton.Yes:
            return
        
        # Get admin username
        username = getattr(self, 'name', None)
        if not username:
            QMessageBox.critical(
                self,
                "Error",
                "Could not identify admin user. Please log in again."
            )
            return
        
        # Call API to kick member
        from services.organization_api_service import OrganizationAPIService
        api_response = OrganizationAPIService.kick_member(member_id, username)
        
        if api_response.get('success'):
            QMessageBox.information(
                self,
                "Success",
                f"{member_name} has been removed from the organization."
            )
            # Refresh members list
            if hasattr(self, '_fetch_members'):
                self._fetch_members(self.current_org["id"])
                self.load_members(self._get_search_text())
        else:
            error_msg = api_response.get('message', 'Failed to kick member')
            QMessageBox.critical(self, "Error", error_msg)
    
    def update_officer_in_org(self, updated_officer: Dict, bypass_cooldown: bool = False) -> None:
            """Update the officer data in the current organization and save.
            
            [UPDATE] Implements granular updates to preserve photo/CV paths 
            and clears pending officer request for the live update.
            """
            if not self.current_org:
                return

            member_name = updated_officer.get("name", "Unknown")
            new_position = updated_officer.get("position", "Unknown")
            org_name = self.current_org.get("name", "Unknown Org")
            officer_positions = ["Chairperson", "Vice - Internal Chairperson", "Vice - External Chairperson", "Secretary", "Treasurer"]

            old_position = "Member"
            is_new_officer = False
            officers = self.current_org.get("officers", [])
            
            # Find existing officer to get old position and current photo paths
            existing_officer_index = -1
            for i, off in enumerate(officers):
                if off["name"] == member_name:
                    existing_officer_index = i
                    old_position = off.get("position", "Member")
                    break
                
            if existing_officer_index == -1 and new_position in officer_positions:
                is_new_officer = True
                old_position = "Member" # Will be set below when appending

            is_position_change = (new_position != old_position)
            is_officer_change = is_position_change and (new_position in officer_positions or old_position in officer_positions)
            
            # --- Cooldown Check (unchanged) ---
            if is_officer_change and not bypass_cooldown:
                is_on_cooldown, end_time = self.check_manager_action_cooldown(self.current_org['id'], "OFFICER_CHANGE")
                if is_on_cooldown:
                    QMessageBox.warning(
                        self, 
                        "Action Cooldown", 
                        f"Officer position changes are on cooldown for this organization.\n\nPlease try again after {end_time.strftime('%I:%M:%S %p')}."
                    )
                    return
            # --- End Cooldown Check ---

            details = f"Officer details updated."
            if is_position_change:
                details += f" Position changed from '{old_position}' to '{new_position}'."

            self._log_action("UPDATE_OFFICER", org_name, subject_name=member_name, changes=details)
            
            # --- FIX START: Granular Update of Officer Data (Photo Preservation) ---
            new_officers = []
            found = False
            for off in self.current_org.get("officers", []):
                if off["name"] == member_name:
                    if new_position in officer_positions:
                        # Update fields only if they are present in updated_officer (from dialog)
                        off["position"] = updated_officer.get("position", off["position"])
                        if "photo_path" in updated_officer: off["photo_path"] = updated_officer["photo_path"]
                        if "card_image_path" in updated_officer: off["card_image_path"] = updated_officer["card_image_path"]
                        if "cv_path" in updated_officer: off["cv_path"] = updated_officer["cv_path"]
                        new_officers.append(off)
                        found = True
                else:
                    new_officers.append(off)
            
            if not found and new_position in officer_positions:
                # New officer being promoted - append the full updated_officer dict
                new_officers.append(updated_officer)
                    
            self.current_org["officers"] = new_officers
            # --- FIX END ---
            
            # --- FIX: Clear pending request for the edited officer (Sync Pending List) ---
            self.current_org["pending_officers"] = [
                p for p in self.current_org.get("pending_officers", []) 
                if p.get("name") != member_name
            ]
            # --- END FIX ---

            # --- Update Officer History ---
            if "officer_history" in self.current_org:
                for semester, offs in self.current_org["officer_history"].items():
                    new_offs = []
                    found_in_history = False
                    for off in offs:
                        if off["name"] == member_name:
                            if new_position in officer_positions:
                                # Apply same granular update logic for history
                                off["position"] = updated_officer.get("position", off["position"])
                                if "photo_path" in updated_officer: off["photo_path"] = updated_officer["photo_path"]
                                if "card_image_path" in updated_officer: off["card_image_path"] = updated_officer["card_image_path"]
                                if "cv_path" in updated_officer: off["cv_path"] = updated_officer["cv_path"]
                                new_offs.append(off)
                                found_in_history = True
                        else:
                            new_offs.append(off)
                    if not found_in_history and new_position in officer_positions:
                        new_offs.append(updated_officer)
                    self.current_org["officer_history"][semester] = new_offs
            
            # --- Update Members List ---
            members = self.current_org.get("members", [])
            member_found = False
            for i, mem in enumerate(members):
                if mem[0] == member_name:
                    if is_position_change:
                        members[i][1] = new_position
                    member_found = True
                    break
                    
            if not member_found and new_position in officer_positions:
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
            self.load_orgs()
            self.ui.stacked_widget.setCurrentIndex(0)
            
        else:
            self.load_orgs()
            self.ui.stacked_widget.setCurrentIndex(0)
    
    def _setup_action_delegate(self):
        """Setup permanent Edit/Kick buttons – called after setting model"""
        model = self.ui.list_view.model()
        if not model or not getattr(self, 'is_managing', False):
            return

        delegate = ActionDelegate(self.ui.list_view)  # Pass the view!
        delegate.edit_clicked.connect(self._handle_delegate_edit_click) # MODIFIED
        delegate.kick_clicked.connect(self._handle_delegate_kick_click) # MODIFIED

        last_column = model.columnCount() - 1
        self.ui.list_view.setItemDelegateForColumn(last_column, delegate)

    def _handle_delegate_edit_click(self, row: int):
        """Edit button clicked - now correctly calls edit_member core logic"""
        self.edit_member(row)

    def _handle_delegate_kick_click(self, row: int):
        """Kick button clicked - now correctly calls kick_member core logic"""
        self.kick_member(row)

    def _setup_applicant_action_delegate(self):
        """Setup permanent Accept/Reject buttons for applicants view"""
        from widgets.orgs_custom_widgets.tables import ApplicantActionDelegate
        
        model = self.ui.list_view.model()
        if not model:
            return

        delegate = ApplicantActionDelegate(self.ui.list_view)
        delegate.accept_clicked.connect(self._handle_accept_applicant)
        delegate.reject_clicked.connect(self._handle_reject_applicant)

        last_column = model.columnCount() - 1
        self.ui.list_view.setItemDelegateForColumn(last_column, delegate)

    def _handle_accept_applicant(self, row: int):
        """Accept button clicked - process acceptance"""
        if row < 0 or row >= len(self.filtered_applicants):
            return
        
        applicant = self.filtered_applicants[row]
        application_id = applicant.get("id")
        applicant_name = applicant.get("student_name", "this student")
        
        # Confirm acceptance
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, 
            "Confirm Acceptance",
            f"Accept {applicant_name}'s application?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._process_application_action(application_id, "accept", applicant_name)

    def _handle_reject_applicant(self, row: int):
        """Reject button clicked - process rejection"""
        if row < 0 or row >= len(self.filtered_applicants):
            return
        
        applicant = self.filtered_applicants[row]
        application_id = applicant.get("id")
        applicant_name = applicant.get("student_name", "this student")
        
        # Confirm rejection
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, 
            "Confirm Rejection",
            f"Reject {applicant_name}'s application?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._process_application_action(application_id, "reject", applicant_name)

    def _process_application_action(self, application_id: int, action: str, applicant_name: str):
        """Process accept or reject action via API with auto-remove"""
        from services.organization_api_service import OrganizationAPIService
        from PyQt6.QtWidgets import QMessageBox
        
        api_response = OrganizationAPIService.process_application(application_id, action)
        
        if api_response.get("success"):
            action_text = "accepted" if action == "accept" else "rejected"
            QMessageBox.information(
                self,
                "Success",
                f"{applicant_name}'s application has been {action_text}."
            )
            
            # Auto-remove: Remove from filtered_applicants and all_applicants immediately
            if hasattr(self, 'filtered_applicants'):
                self.filtered_applicants = [
                    app for app in self.filtered_applicants 
                    if app.get("id") != application_id
                ]
            
            if hasattr(self, 'all_applicants'):
                self.all_applicants = [
                    app for app in self.all_applicants 
                    if app.get("id") != application_id
                ]
            
            # Refresh the applicants view without API call (already removed from lists)
            self.load_applicants(self._get_search_text())
        else:
            error_msg = api_response.get("error", f"Failed to {action} application")
            QMessageBox.critical(self, "Error", error_msg)

    def _fetch_applicants(self, org_id: int):
        """Override in subclass to fetch applicants from API"""
        pass