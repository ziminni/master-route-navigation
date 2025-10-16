from PyQt6 import QtWidgets, QtCore, QtGui

from typing import Dict
from .user import User
from widgets.orgs_custom_widgets.cards import JoinedOrgCard, CollegeOrgCard
from widgets.orgs_custom_widgets.dialogs import OfficerDialog
from widgets.orgs_custom_widgets.tables import ViewMembers
from ui.Organization.org_main_ui import Ui_Widget


class Student(User):
    def __init__(self, student_name: str = "Student"):
        super().__init__(name=student_name)
        self.ui = Ui_Widget()
        self.ui.setupUi(self)
        self._apply_table_style()
        self.joined_org_count: int = 0
        self.table = self.findChild(QtWidgets.QTableView, "list_view")
        self._setup_no_member_label()
        self.ui.verticalLayout_17.addWidget(self.no_member_label)
        self._setup_connections()
        self.load_orgs()

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
        self.load_orgs(search_text) if self.ui.comboBox.currentIndex() == 0 else self.load_branches(search_text)

    def _perform_member_search(self) -> None:
        """Handle member search based on input text."""
        search_text = self.ui.search_line_3.text().strip().lower()
        self.load_members(search_text)

    def load_orgs(self, search_text: str = "") -> None:
        """Load and display organizations, filtered by search text."""
        organizations = self._load_data()
        self._clear_grid(self.ui.joined_org_grid)
        self._clear_grid(self.ui.college_org_grid)
        self.joined_org_count = 0
        self.college_org_count = 0

        filtered_joined = [
            org for org in organizations
            if org["is_joined"] and not org["is_branch"] and (search_text in org["name"].lower() or not search_text)
        ]
        filtered_college = [
            org for org in organizations
            if not org["is_branch"] and (search_text in org["name"].lower() or not search_text)
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

        filtered_joined_branches = []
        filtered_college_branches = []

        for org in organizations:
            for branch in org.get("branches", []):
                if search_text in branch["name"].lower() or not search_text:
                    if branch["is_joined"]:
                        filtered_joined_branches.append(branch)
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

    def load_members(self, search_text: str = "") -> None:
        """Load and filter members into the table view."""
        if not self.current_org:
            return

        members_data = self.current_org.get("members", [])
        filtered_members = [
            member for member in members_data
            if any(search_text in str(field).lower() for field in member)
        ] if search_text else members_data

        self.ui.list_view.setModel(None)
        self.ui.list_view.clearSpans()
        self.ui.list_view.verticalHeader().reset()

        model = ViewMembers(filtered_members, is_managing=False)
        self.ui.list_view.setModel(model)

        self._apply_table_style()

        if filtered_members:
            self.ui.list_view.show()
            self.no_member_label.hide()
        else:
            self.ui.list_view.hide()
            self.no_member_label.show()

    def _on_combobox_changed(self, index: int) -> None:
        """Handle combo box change to switch between organizations and branches."""
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

    def _add_college_org(self, org_data: Dict) -> None:
        """Add a college organization card to the grid."""
        card = CollegeOrgCard(
            self._get_logo_path(org_data["logo_path"]),
            org_data["name"], org_data, self
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
        """Navigate to the members page."""
        if self.current_org:
            self.ui.header_label_3.setText("Organization" if not self.current_org["is_branch"] else "Branch")
        self.load_members()
        self.ui.stacked_widget.setCurrentIndex(2)

    def _return_to_prev_page(self) -> None:
        """Navigate back to the previous page."""
        if self.ui.stacked_widget.currentIndex() == 2:
            self.ui.stacked_widget.setCurrentIndex(1)
        else:
            self.load_orgs() if self.ui.comboBox.currentIndex() == 0 else self.load_branches()
            self.ui.stacked_widget.setCurrentIndex(0)