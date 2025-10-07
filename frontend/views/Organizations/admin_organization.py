from PyQt6 import QtWidgets, QtGui, QtCore
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(project_root)

from typing import Dict
from frontend.views.Organizations.user import User
from frontend.views.Organizations.manager_base import ManagerBase
from frontend.widgets.orgs_custom_widgets.dialogs import OfficerDialog
from frontend.ui.Organization.org_main_ui import Ui_Widget

class Admin(ManagerBase, User):
    """Admin view with full management capabilities and additional admin features."""
    
    def __init__(self, admin_name: str = "Admin Name"):
        User.__init__(self, name=admin_name)
        ManagerBase.__init__(self)
        
        self.ui = Ui_Widget()
        self.ui.setupUi(self)
        self.ui.joined_container.setVisible(False)
        
        self.table = self.findChild(QtWidgets.QTableView, "list_view")
        self._setup_no_member_label()
        self.ui.verticalLayout_17.addWidget(self.no_member_label)
        
        self._setup_admin_menu()
        self._setup_create_button()
        
        self._setup_connections()
        self.load_orgs()
    
    def _setup_admin_menu(self) -> None:
        """Set up the admin menu button with dropdown options beside the search bar."""
        self.menu_btn = QtWidgets.QPushButton(self.ui.landing_page)
        self.menu_btn.setStyleSheet("background-color: transparent;")
        self.menu_btn.setObjectName("menu_btn")
        self.menu_btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.menu_btn.setText("")
        
        icon = QtGui.QIcon()
        menu_icon_path = os.path.join(
            os.path.dirname(__file__), 
            "..", "..", 
            "assets", "organization", "icons", "menu.png"
        )
        icon.addPixmap(
            QtGui.QPixmap(menu_icon_path), 
            QtGui.QIcon.Mode.Normal, 
            QtGui.QIcon.State.Off
        )
        self.menu_btn.setIcon(icon)
        self.menu_btn.setIconSize(QtCore.QSize(30, 30))
        
        self.ui.horizontalLayout_2.addWidget(self.menu_btn)
        
        self.admin_menu = QtWidgets.QMenu(self)
        
        generate_reports_action = self.admin_menu.addAction("Generate Reports")
        generate_reports_action.triggered.connect(self._generate_reports)
        
        audit_logs_action = self.admin_menu.addAction("Audit Logs")
        audit_logs_action.triggered.connect(self._open_audit_logs)
        
        archive_action = self.admin_menu.addAction("Archive")
        archive_action.triggered.connect(self._open_archive)
        
        self.menu_btn.clicked.connect(self._show_admin_menu)
    
    def _show_admin_menu(self) -> None:
        """Display the admin dropdown menu."""
        button_pos = self.menu_btn.mapToGlobal(QtCore.QPoint(0, self.menu_btn.height()))
        self.admin_menu.exec(button_pos)
    
    def _setup_create_button(self) -> None:
        """Set up the create organization/branch button in the lower right."""
        self.create_btn = QtWidgets.QPushButton("+ Create Organization/Branch", self.ui.landing_page)
        self.create_btn.setStyleSheet("""
            QPushButton {
                background-color: #FDC601;
                color: white;
                border-radius: 10px;
                padding: 15px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #084924;
            }
        """)
        self.create_btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.create_btn.clicked.connect(self._create_organization)
        
        self._reposition_create_button()
        self.create_btn.raise_()

    def _reposition_create_button(self) -> None:
        """Helper to set the geometry of the create button based on landing_page size."""
        if hasattr(self, 'create_btn'):
            BUTTON_WIDTH = 250
            BUTTON_HEIGHT = 50
            MARGIN_RIGHT = 30
            MARGIN_BOTTOM = 70

            self.create_btn.setGeometry(
                self.ui.landing_page.width() - BUTTON_WIDTH - MARGIN_RIGHT,
                self.ui.landing_page.height() - BUTTON_HEIGHT - MARGIN_BOTTOM,
                BUTTON_WIDTH,
                BUTTON_HEIGHT
            )
            self.create_btn.raise_()

    def resizeEvent(self, event) -> None:
        """Handle resize events to reposition the create button."""
        super().resizeEvent(event)
        if self.ui.stacked_widget.currentIndex() == 0:
            self._reposition_create_button()
    
    def _generate_reports(self) -> None:
        """Handle generate reports action."""
        # Placeholder for report generation functionality
        QtWidgets.QMessageBox.information(
            self,
            "Generate Reports",
            "Report generation feature will be implemented here."
        )
    
    def _open_audit_logs(self) -> None:
        """Handle audit logs action."""
        # Placeholder for audit logs functionality
        QtWidgets.QMessageBox.information(
            self,
            "Audit Logs",
            "Audit logs viewer will be implemented here."
        )
    
    def _open_archive(self) -> None:
        """Handle archive action."""
        # Placeholder for archive functionality
        QtWidgets.QMessageBox.information(
            self,
            "Archive",
            "Archive management feature will be implemented here."
        )
    
    def _create_organization(self) -> None:
        """Handle create organization/branch action."""
        # Placeholder for create organization functionality
        from PyQt6.QtWidgets import QInputDialog
        
        items = ["Organization", "Branch"]
        item, ok = QInputDialog.getItem(
            self, 
            "Create", 
            "What would you like to create?", 
            items, 
            0, 
            False
        )
        
        if ok and item:
            QtWidgets.QMessageBox.information(
                self,
                f"Create {item}",
                f"Create {item} dialog will be implemented here."
            )
    
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
        """Display organization details with admin-specific features."""
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
        from frontend.widgets.orgs_custom_widgets.cards import CollegeOrgCard
        
        card = CollegeOrgCard(
            self._get_logo_path(org_data["logo_path"]), 
            org_data["description"],
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
    
    # --- FIX 3: Update _return_to_prev_page to call the helper when returning to page 0 ---
    def _return_to_prev_page(self) -> None:
        """Navigate back to the previous page, handling applicants view."""
        if self.ui.stacked_widget.currentIndex() == 2:
            if self.is_viewing_applicants:
                self.is_viewing_applicants = False
                self.load_members(self._get_search_text())
            else:
                self.ui.stacked_widget.setCurrentIndex(1)
        else:
            # Code runs when returning to the main landing page (index 0)
            if self.ui.comboBox.currentIndex() == 0:
                self.load_orgs()
            else:
                self.load_branches()
            self.ui.stacked_widget.setCurrentIndex(0)
            
            # Reposition the button to account for potential window resizing
            self._reposition_create_button()