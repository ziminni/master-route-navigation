import os
import json
import copy
from typing import List, Dict, Optional
from PyQt6 import QtWidgets, QtCore, QtGui
from widgets.orgs_custom_widgets.tables import ActionDelegate
from .image_utils import get_image_path

class User(QtWidgets.QWidget):
    def __init__(self, name: str = "User", parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.name = name
        self.current_org: Optional[Dict] = None
        self.ui = None
        self.no_member_label = None
        self.table = None
        self.officer_count = 0
        self.college_org_count = 0
        self.data_file = os.path.join(os.path.dirname(__file__), 'organizations_data.json')

    def _apply_table_style(self) -> None:
        """Apply modern stylesheet for the members QTableView."""
        table = self.ui.list_view
        table.setAlternatingRowColors(True)

        table.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                            QtWidgets.QSizePolicy.Policy.Expanding)

        palette = table.palette()
        palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor("white"))
        palette.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor("#f6f8fa"))
        table.setPalette(palette)

        table.setStyleSheet("""
        QTableView {
            border-radius: 10px;
            background-color: white;
            gridline-color: #084924;
            font-size: 14px;
            selection-background-color: #FDC601;
            selection-color: black;
        }
        QTableView::item {
            padding: 7px;
        }
        QTableView::item:hover {
            background-color: #FDC601;
            color: black;
        }
        """)

        header = table.horizontalHeader()
        header.setStyleSheet("""
        QHeaderView::section {
            background-color: #084924;
            color: white;
            font-weight: bold;
            padding: 6px;
            border: none;
        }
        QHeaderView::section:hover {
            background-color: #098f42;
        }
        QHeaderView::section:first {
            border-top-left-radius: 10px;
        }
        QHeaderView::section:last {
            border-top-right-radius: 10px;
        }
        """)

        table.verticalHeader().setVisible(False)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)

        model = table.model()
        if model is not None and model.columnCount() > 0:
            last_header = model.headerData(model.columnCount() - 1, QtCore.Qt.Orientation.Horizontal)
            if last_header == "Actions":
                action_column_index = model.columnCount() - 1

                header.setSectionResizeMode(action_column_index, QtWidgets.QHeaderView.ResizeMode.Interactive)
                header.resizeSection(action_column_index, 200)

                table.setItemDelegateForColumn(action_column_index, ActionDelegate(table))

    def _load_data(self) -> List[Dict]:
        """Load organization and branch data from JSON file."""
        try:
            with open(self.data_file, 'r') as file:
                data = json.load(file)
                return data.get('organizations', [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading {self.data_file}: {str(e)}")
            return []

    def save_data(self) -> None:
        """Save updated organization data back to JSON file, handling both top-level and nested branches."""
        if not self.current_org:
            print("No current organization to save.")
            return

        organizations = self._load_data()
        updated = False

        for i in range(len(organizations)):
            if organizations[i]["id"] == self.current_org["id"]:
                organizations[i] = copy.deepcopy(self.current_org)
                updated = True
                break

        if not updated:
            for org in organizations:
                branches = org.get("branches", [])
                for j in range(len(branches)):
                    if branches[j]["id"] == self.current_org["id"]:
                        branches[j] = copy.deepcopy(self.current_org)
                        updated = True
                        break
                if updated:
                    break

        if not updated:
            print(f"Warning: Could not find organization/branch with ID {self.current_org['id']} to update.")

        try:
            with open(self.data_file, 'w') as file:
                json.dump({"organizations": organizations}, file, indent=4)
            print(f"Successfully saved data to {self.data_file}")
        except Exception as e:
            print(f"Error saving {self.data_file}: {str(e)}")

    @staticmethod
    def _get_logo_path(filename: str) -> str:
        """
        Resolve absolute logo path from filename.
        
        Args:
            filename: Just the filename (e.g., "CISC_logo.jpeg") or "No Photo"
            
        Returns:
            Full absolute path to the image in the Data directory
        """
        return get_image_path(filename)

    def set_circular_logo(self, logo_label: QtWidgets.QLabel, logo_path: str, size: int = 200, border_width: int = 4) -> None:
        """Set a circular logo with a border on the given label."""
        logo_label.setFixedSize(size, size)
        if logo_path == "No Photo" or QtGui.QPixmap(logo_path).isNull():
            logo_label.setText("No Logo")
            return

        pixmap = QtGui.QPixmap(logo_path).scaled(size, size, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
        centered_pixmap = QtGui.QPixmap(size, size)
        centered_pixmap.fill(QtCore.Qt.GlobalColor.transparent)
        
        with QtGui.QPainter(centered_pixmap) as painter:
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            x = (size - pixmap.width()) // 2
            y = (size - pixmap.height()) // 2
            painter.drawPixmap(x, y, pixmap)

        mask = QtGui.QPixmap(size, size)
        mask.fill(QtCore.Qt.GlobalColor.transparent)
        with QtGui.QPainter(mask) as painter:
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            path = QtGui.QPainterPath()
            path.addEllipse(0, 0, size, size)
            painter.fillPath(path, QtCore.Qt.GlobalColor.white)

        centered_pixmap.setMask(mask.createMaskFromColor(QtCore.Qt.GlobalColor.white, QtCore.Qt.MaskMode.MaskOutColor))

        final_pixmap = QtGui.QPixmap(size, size)
        final_pixmap.fill(QtCore.Qt.GlobalColor.transparent)
        with QtGui.QPainter(final_pixmap) as painter:
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            painter.setBrush(QtGui.QBrush(centered_pixmap))
            painter.setPen(QtGui.QPen(QtGui.QColor(8, 73, 36), border_width))
            painter.drawEllipse(border_width // 2, border_width // 2, size - border_width, size - border_width)

        logo_label.setPixmap(final_pixmap)

    def show_org_details(self, org_data: Dict) -> None:
        """Display organization details on the details page."""
        self.current_org = org_data
        self.ui.header_label_2.setText("Organization" if not org_data["is_branch"] else "Branch")
        self.ui.status_btn.setText("Active")
        self.ui.org_name.setText(org_data["name"])
        self.ui.org_type.setText("Branch" if org_data["is_branch"] else "Organization")
        brief_content = org_data.get("brief", "")
        self.ui.brief_label.setText(brief_content if brief_content else "No brief overview.")
        description_content = org_data.get("description", "")
        self.ui.obj_label.setText(description_content if description_content else "No objectives.")
        
        branches = org_data.get("branches")
        if branches is None or not isinstance(branches, list):
            branches_text = "No branches available"
        elif len(branches) == 0:
            branches_text = "No branches available"
        else:
            branches_text = "\n".join([branch.get("name", "Unnamed") for branch in branches])
        self.ui.obj_label_2.setText(branches_text)
        
        self.set_circular_logo(self.ui.logo, self._get_logo_path(org_data["logo_path"]))
        
        self.ui.officer_history_dp.clear()
        semesters = org_data.get("officer_history", {}).keys()
        self.ui.officer_history_dp.addItem("Current Officers")
        self.ui.officer_history_dp.addItems(sorted(semesters))
        
        self.load_officers(org_data.get("officers", []))
        self.load_events(org_data.get("events", []))
        self.ui.label.setText("A.Y. 2025-2026 - 1st Semester")
        self.ui.stacked_widget.setCurrentIndex(1)

    def load_officers(self, officers: List[Dict]) -> None:
        """Load officer cards into the officer grid."""
        from widgets.orgs_custom_widgets.cards import OfficerCard
        self._clear_grid(self.ui.officer_cards_grid)
        self.officer_count = 0
        self.ui.officers_scroll_area.verticalScrollBar().setValue(0)

        if not officers:
            self._add_no_record_label(self.ui.officer_cards_grid)
            return

        for officer in officers:
            card = OfficerCard(officer, self)
            col = self.officer_count % 3
            row = self.officer_count // 3
            self.ui.officer_cards_grid.addWidget(card, row, col, alignment=QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignHCenter)
            self.officer_count += 1
            self.ui.officer_cards_grid.setRowMinimumHeight(row, 400)

    def load_events(self, events: List[Dict]) -> None:
        """Load event cards into the events layout."""
        from widgets.orgs_custom_widgets.cards import EventCard
        while self.ui.verticalLayout_14.count():
            if item := self.ui.verticalLayout_14.takeAt(0).widget():
                item.deleteLater()

        if not events:
            no_events_label = QtWidgets.QLabel("No upcoming events.")
            no_events_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            no_events_label.setStyleSheet("font-size: 16px; color: #666;")
            self.ui.verticalLayout_14.addWidget(no_events_label)
        else:
            for event in events:
                self.ui.verticalLayout_14.addWidget(EventCard(event, self))

        self.ui.verticalLayout_14.addStretch()
        self.ui.scroll_area_events.verticalScrollBar().setValue(0)

    def _clear_grid(self, grid_layout: QtWidgets.QGridLayout) -> None:
        """Remove all widgets from the given grid layout."""
        for i in reversed(range(grid_layout.count())):
            if widget := grid_layout.itemAt(i).widget():
                widget.setParent(None)

    def _add_no_record_label(self, grid_layout: QtWidgets.QGridLayout) -> None:
        """Add 'No Record(s) Found' label to the grid layout."""
        no_record_label = QtWidgets.QLabel("No Record(s) Found")
        no_record_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        no_record_label.setStyleSheet("font-size: 20px;")
        grid_layout.addWidget(no_record_label, 0, 0, 1, 5)

    def _update_scroll_areas(self) -> None:
        """Update scroll areas and geometry."""
        if hasattr(self.ui, 'college_org_scrollable'):
            self.ui.college_org_scrollable.adjustSize()
            self.ui.college_org_scrollable.updateGeometry()
        if hasattr(self.ui, 'joined_org_scrollable'):
            self.ui.joined_org_scrollable.adjustSize()
            self.ui.joined_org_scrollable.updateGeometry()
        self.update()
