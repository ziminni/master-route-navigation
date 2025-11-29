from PyQt6 import QtWidgets, QtCore
from ..Base.faculty_admin_base import FacultyAdminBase
from ..Base.manager_base import ManagerBase
from widgets.orgs_custom_widgets.adviser_assign_dialog import AdviserAssignDialog


class Dean(ManagerBase, FacultyAdminBase):
    """
    Dean view – identical UI to Faculty/Admin but with extra powers:
    1. Assign a faculty adviser to any org/branch
    2. Approve/Reject pending officer changes
    3. See current adviser and pending officer requests clearly
    """

    def __init__(self, dean_name: str):
        FacultyAdminBase.__init__(self, name=dean_name)
        ManagerBase.__init__(self)
        self.load_orgs()

    def show_org_details(self, org_data: dict) -> None:
        super().show_org_details(org_data)
        self.current_org = org_data
        self.ui.view_members_btn.setText("Manage Members")

        # === 1. Remove old dynamic widgets to prevent duplicates ===
        for attr in ["adviser_label", "assign_adviser_btn", "pending_container"]:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                widget = getattr(self, attr)
                self.ui.verticalLayout_10.removeWidget(widget)
                widget.deleteLater()
                setattr(self, attr, None)

        # === 2. Show current Faculty Adviser ===
        adviser = org_data.get("adviser") or "Not Assigned"
        self.adviser_label = QtWidgets.QLabel(f"Faculty Adviser: <b>{adviser}</b>")
        self.adviser_label.setStyleSheet("""
            QLabel {
                color: #084924;
                font-size: 16px;
                font-weight: bold;
                background-color: #e8f5e8;
                padding: 12px;
                border-radius: 12px;
                margin: 10px 0;
                border: 2px solid #084924;
            }
        """)
        self.adviser_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.ui.verticalLayout_10.insertWidget(2, self.adviser_label)  # Right after org name

        # === 3. Assign Adviser Button (Dean only) ===
        self.assign_adviser_btn = QtWidgets.QPushButton("Assign / Change Faculty Adviser")
        self.assign_adviser_btn.setStyleSheet("""
            QPushButton {
                background-color: #084924;
                color: white;
                border-radius: 12px;
                padding: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #098f42; }
        """)
        self.assign_adviser_btn.clicked.connect(self._open_assign_adviser_dialog)

        # Insert after Edit button
        edit_idx = self.ui.verticalLayout_10.indexOf(self.edit_btn)
        spacer1 = QtWidgets.QSpacerItem(20, 15, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        self.ui.verticalLayout_10.insertItem(edit_idx + 1, spacer1)
        self.ui.verticalLayout_10.insertWidget(edit_idx + 2, self.assign_adviser_btn)

        # === 4. Show Pending Officer Changes ===
        self._refresh_pending_officers_display()

    # ===================================================================
    # Assign Faculty Adviser
    # ===================================================================
    def _open_assign_adviser_dialog(self):
        if not self.current_org:
            return
        dialog = AdviserAssignDialog(self.current_org, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            selected_faculty = dialog.get_selected_faculty()
            if selected_faculty:
                old_adviser = self.current_org.get("adviser")
                self.current_org["adviser"] = selected_faculty
                self.save_data()
                self._log_action(
                    "ASSIGN_ADVISER",
                    self.current_org["name"],
                    subject_name=selected_faculty,
                    changes=f"Adviser changed from '{old_adviser or 'None'}' to '{selected_faculty}'"
                )
                QtWidgets.QMessageBox.information(
                    self, "Success", f"Faculty adviser updated to: <b>{selected_faculty}</b>"
                )
                # Refresh the label
                self.show_org_details(self.current_org)

    # ===================================================================
    # Pending Officer Changes System
    # ===================================================================
    def update_officer_in_org(self, updated_officer: dict, bypass_cooldown: bool = False):
        if not self.current_org:
            return

        # Dean bypasses pending system → apply immediately
        if bypass_cooldown:
            super(Dean, self).update_officer_in_org(updated_officer, bypass_cooldown=True)
            self._clear_pending_for_officer(updated_officer["name"])
            self._refresh_pending_officers_display()
            self._log_action("APPROVE_OFFICER_CHANGE", self.current_org["name"],
                             subject_name=updated_officer["name"],
                             changes=f"Position → {updated_officer.get('position')}")
            return

        # Normal path: officer or adviser → goes to pending
        pending = self.current_org.setdefault("pending_officers", [])
        pending = [p for p in pending if p.get("name") != updated_officer.get("name")]
        pending.append(updated_officer)
        self.current_org["pending_officers"] = pending
        self.save_data()

        QtWidgets.QMessageBox.information(
            self,
            "Pending Approval",
            f"<b>{updated_officer['name']}</b> → <b>{updated_officer.get('position')}</b><br><br>"
            "This officer change is now <b>pending Dean approval</b>."
        )
        self._refresh_pending_officers_display()

    def _refresh_pending_officers_display(self):
        # Remove old pending container
        if hasattr(self, "pending_container") and self.pending_container:
            self.ui.verticalLayout_10.removeWidget(self.pending_container)
            self.pending_container.deleteLater()
            self.pending_container = None

        pending = self.current_org.get("pending_officers", [])
        if not pending:
            return

        self.pending_container = QtWidgets.QGroupBox("Pending Officer Changes")
        self.pending_container.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
                color: #084924;
                border: 2px solid #084924;
                border-radius: 12px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        layout = QtWidgets.QVBoxLayout(self.pending_container)

        for officer in pending:
            frame = QtWidgets.QFrame()
            frame.setStyleSheet("background-color: #f8fff8; border-radius: 8px; margin: 5px; padding: 10px;")
            hbox = QtWidgets.QHBoxLayout(frame)

            name_pos = f"<b>{officer.get('name')}</b> → <b>{officer.get('position')}</b>"
            hbox.addWidget(QtWidgets.QLabel(name_pos))

            approve_btn = QtWidgets.QPushButton("Approve")
            approve_btn.setStyleSheet("background:#084924; color:white; border-radius:8px; padding:6px 12px;")
            approve_btn.clicked.connect(lambda _, o=officer.copy(): self._approve_pending(o))

            reject_btn = QtWidgets.QPushButton("Reject")
            reject_btn.setStyleSheet("background:#EB5757; color:white; border-radius:8px; padding:6px 12px;")
            reject_btn.clicked.connect(lambda _, o=officer.copy(): self._reject_pending(o))

            hbox.addStretch()
            hbox.addWidget(approve_btn)
            hbox.addWidget(reject_btn)

            layout.addWidget(frame)

        # Insert below adviser info
        edit_idx = self.ui.verticalLayout_10.indexOf(self.edit_btn) if self.edit_btn else -1
        insert_pos = edit_idx + 3 if edit_idx != -1 else -1
        self.ui.verticalLayout_10.insertWidget(insert_pos, self.pending_container)

    def _approve_pending(self, officer_data: dict):
        self.update_officer_in_org(officer_data, bypass_cooldown=True)
        QtWidgets.QMessageBox.information(
            self, "Approved", f"<b>{officer_data['name']}</b> is now <b>{officer_data.get('position')}</b>"
        )

    def _reject_pending(self, officer_data: dict):
        name = officer_data.get("name", "Unknown")
        self._clear_pending_for_officer(name)
        self.save_data()
        QtWidgets.QMessageBox.warning(
            self, "Rejected", f"Officer change for <b>{name}</b> has been rejected."
        )
        self._refresh_pending_officers_display()

    def _clear_pending_for_officer(self, name: str):
        pending = self.current_org.get("pending_officers", [])
        self.current_org["pending_officers"] = [p for p in pending if p.get("name") != name]