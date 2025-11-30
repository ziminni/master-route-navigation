from PyQt6 import QtWidgets, QtCore
from typing import Dict
from .user import User
from widgets.orgs_custom_widgets.dialogs import OfficerDialog
from widgets.orgs_custom_widgets.tables import ViewMembers
from ui.Organization.org_main_ui import Ui_Widget
from typing import Optional

class OrganizationViewBase(User):
    """
    Base class for organization views (Student, Faculty, Admin).
    Handles common UI setup, signal connections, and default (non-manager)
    page navigation and data loading.
    """
    def __init__(self, name: str):
        super().__init__(name=name)
        self.ui = Ui_Widget()
        self.ui.setupUi(self)
        self._apply_table_style()
        
        self.joined_org_count: int = 0
        self.edit_btn: Optional[QtWidgets.QPushButton] = None
        
        self.table = self.findChild(QtWidgets.QTableView, "list_view")
        self._setup_no_member_label()
        self.ui.verticalLayout_17.addWidget(self.no_member_label)
        self._setup_connections()

        # Pagination setup
        self.items_per_page = 50
        self.current_members_page = 0
        self.total_members_pages = 1
        self.filtered_members = []

        self.pagination_layout = QtWidgets.QHBoxLayout()
        self.prev_btn = QtWidgets.QPushButton("Previous")
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn = QtWidgets.QPushButton("Next")
        self.next_btn.clicked.connect(self.next_page)
        self.page_label = QtWidgets.QLabel("Page 1 of 1")

        self.pagination_layout.addStretch()
        self.pagination_layout.addWidget(self.prev_btn)
        self.pagination_layout.addWidget(self.page_label)
        self.pagination_layout.addWidget(self.next_btn)
        self.pagination_layout.addStretch()

        self.ui.verticalLayout_17.addLayout(self.pagination_layout)

    def _setup_connections(self) -> None:
        """Set up signal-slot connections.
        
        This method connects signals to the methods defined in this class
        (or overridden by subclasses). Polymorphism ensures the correct
        method (e.g., Student._to_members_page vs ManagerBase._to_members_page)
        is called based on the object's inheritance.
        """
        self.ui.view_members_btn.clicked.connect(self._to_members_page)
        self.ui.back_btn_member.clicked.connect(self._return_to_prev_page)
        self.ui.back_btn.clicked.connect(self._return_to_prev_page)
        self.ui.search_line.textChanged.connect(self._perform_search)
        self.ui.search_line_3.textChanged.connect(self._perform_member_search)
        self.ui.officer_history_dp.currentIndexChanged.connect(self._on_officer_history_changed)

    def _setup_no_member_label(self) -> None:
        """Initialize the 'No Record(s) Found' label for members."""
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
        """Handle organization/branch search based on combo box selection."""
        search_text = self.ui.search_line.text().strip().lower()
        self.load_orgs(search_text)

    def _perform_member_search(self) -> None:
        """Handle member search (non-manager version)."""
        search_text = self.ui.search_line_3.text().strip().lower()
        self.load_members(search_text)

    def load_members(self, search_text: str = "") -> None: # MODIFIED
            """Load and filter members into the table view (non-manager version)."""
            from widgets.orgs_custom_widgets.tables import ViewMembers 

            if not self.current_org:
                return

            members_data = self.current_org.get("members", [])
            self.filtered_members = [
                member for member in members_data
                if any(search_text in str(field).lower() for field in member)
            ] if search_text else members_data.copy()

            total_items = len(self.filtered_members)
            self.total_members_pages = max(1, (total_items + self.items_per_page - 1) // self.items_per_page)
            self.current_members_page = max(0, min(self.current_members_page, self.total_members_pages - 1))

            start = self.current_members_page * self.items_per_page
            end = start + self.items_per_page
            paged_data = self.filtered_members[start:end]

            model = self.ui.list_view.model()
            
            if model and isinstance(model, ViewMembers):
                model.update_data(paged_data)
            else:
                self.ui.list_view.setModel(None)
                self.ui.list_view.clearSpans()
                self.ui.list_view.verticalHeader().reset()
                model = ViewMembers(paged_data, is_managing=False)
                self.ui.list_view.setModel(model)
                self._apply_table_style()
                
            self._update_pagination_buttons()

            if total_items:
                self.ui.list_view.show()
                self.no_member_label.hide()
            else:
                self.ui.list_view.hide()
                self.no_member_label.show()

    def _on_combobox_changed(self, index: int) -> None:
        """Handle combo box change - now always shows organizations."""
        # ComboBox is now hidden, always show all organizations
        self.ui.college_label.setText("College Organization(s)")
        self.load_orgs()
        self.ui.college_org_scrollable.verticalScrollBar().setValue(0)

    def _add_college_org(self, org_data: Dict) -> None:
        """Add a college organization card to the grid."""
        from widgets.orgs_custom_widgets.cards import CollegeOrgCard
        
        card = CollegeOrgCard(
            self._get_logo_path(org_data["logo_path"]),
            org_data.get("description", "No description available"), 
            org_data, self
        )
        col = self.college_org_count % 5
        row = self.college_org_count // 5
        self.ui.college_org_grid.addWidget(
            card, row, col, alignment=QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignHCenter
        )
        self.college_org_count += 1
        self.ui.college_org_grid.setRowMinimumHeight(row, 300)

    def show_officer_dialog(self, officer_data: Dict) -> None:
        """Display officer details in a dialog."""
        OfficerDialog(officer_data, self).exec()

    def _on_officer_history_changed(self, index: int) -> None:
        """Handle officer history combobox change to display officers for selected semester."""
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
        """Navigate to the members page (non-manager version)."""
        if self.current_org:
            self.ui.header_label_3.setText("Organization")
        self.load_members(self.ui.search_line_3.text().strip().lower())
        self.ui.stacked_widget.setCurrentIndex(2)

    def _return_to_prev_page(self) -> None:
        """Navigate back to the previous page (non-manager version)."""
        if self.ui.stacked_widget.currentIndex() == 2:
            self.ui.stacked_widget.setCurrentIndex(1)
        else:
            self.load_orgs()
            self.ui.stacked_widget.setCurrentIndex(0)

    def prev_page(self) -> None:
        if self.current_members_page > 0:
            self.current_members_page -= 1
            self.load_members(self.ui.search_line_3.text().strip().lower())

    def next_page(self) -> None:
        if self.current_members_page < self.total_members_pages - 1:
            self.current_members_page += 1
            self.load_members(self.ui.search_line_3.text().strip().lower())

    def _update_pagination_buttons(self) -> None:
        self.page_label.setText(f"Page {self.current_members_page + 1} of {self.total_members_pages}")
        self.prev_btn.setEnabled(self.current_members_page > 0)
        self.next_btn.setEnabled(self.current_members_page < self.total_members_pages - 1)
            
    def load_orgs(self, search_text: str = "") -> None:
        """Load and display organizations."""
        raise NotImplementedError("Subclass must implement load_orgs")

    def load_branches(self, search_text: str = "") -> None:
        """Load and display branches - now just redirects to load_orgs."""
        # Branches are now just organizations with main_org set
        self.load_orgs(search_text)