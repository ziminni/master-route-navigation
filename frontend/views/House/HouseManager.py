# views/House/HouseManager.py
import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QLineEdit, QSpacerItem, QSizePolicy, QDialog
)
from PyQt6.QtCore import Qt
from .AdminCreateHousePage import AdminCreateHousePage
from .HouseDetails import HouseDetailsPage


class HouseManager(QWidget):
    def __init__(self, token=None, api_base="http://127.0.0.1:8000", parent=None):
        super().__init__(parent)
        self.token = token
        self.api_base = api_base.rstrip("/")
        self.houses = []

        self.init_ui()
        self.load_houses()

    def init_ui(self):
        self.setWindowTitle("House Management")
        self.resize(1100, 750)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Title
        title = QLabel("House Management")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #084924;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name or slug...")
        self.search_input.setStyleSheet("""
            padding: 12px 16px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 12px;
        """)
        self.search_input.textChanged.connect(self.filter_houses)
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)

        # Table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Slug", "Actions"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 260)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setStyleSheet("""
            QTableWidget { font-size: 15px; border: none; }
            QHeaderView::section {
                background-color: #084924;
                color: white;
                padding: 12px;
                font-weight: bold;
                border: none;
            }
        """)
        main_layout.addWidget(self.table)

        # Bottom spacer so table doesn't fight with FAB
        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # THE REAL FLOATING ACTION BUTTON
        self.fab = QPushButton("+", self)  # Parent = self → floats over everything
        self.fab.setFixedSize(66, 66)
        self.fab.setStyleSheet("""
            QPushButton {
                background-color: #084924;
                color: white;
                border-radius: 33px;
                font-size: 36px;
                font-weight: bold;
                border: none;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            }
            QPushButton:hover {
                background-color: #0d7a3d;
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                background-color: #06381b;
            }
        """)
        self.fab.clicked.connect(self.open_create_house_page)

        # Position it — will be updated in resizeEvent
        self.position_fab()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.position_fab()

    def position_fab(self):
        margin = 30
        self.fab.move(
            self.width() - self.fab.width() - margin,
            self.height() - self.fab.height() - margin
        )
        self.fab.raise_()  # Always on top

    # Rest of your methods unchanged (load_houses, populate_table, etc.)
    # I'm just pasting the fixed/updated parts below:

    def populate_table(self):
        self.table.setRowCount(0)
        for house in self.houses:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(str(house["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(house["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(house.get("slug", "—")))

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(6, 4, 6, 4)
            actions_layout.setSpacing(6)

            view_btn = QPushButton("View")
            view_btn.setStyleSheet("background:#5bc0de; color:white; border-radius:6px; padding:6px 12px;")
            view_btn.clicked.connect(lambda _, h=house: self.view_house(h))

            edit_btn = QPushButton("Edit")
            edit_btn.setStyleSheet("background:#f0ad4e; color:white; border-radius:6px; padding:6px 12px;")

            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet("background:#d9534f; color:white; border-radius:6px; padding:6px 12px;")
            delete_btn.clicked.connect(lambda _, hid=house["id"]: self.delete_house(hid))

            actions_layout.addWidget(view_btn)
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()

            self.table.setCellWidget(row, 3, actions_widget)

    def filter_houses(self, text):
        text = text.lower()
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 1).text().lower()
            slug = self.table.item(row, 2).text().lower()
            self.table.setRowHidden(row, text not in name and text not in slug)

    def open_create_house_page(self):
        if not hasattr(self, 'stacked_widget') or not self.stacked_widget:
            QMessageBox.warning(self, "Error", "Navigation stack not available.")
            return
        
        create_page = AdminCreateHousePage(token=self.token, api_base=self.api_base, parent_manager=self)
        self.stacked_widget.addWidget(create_page)
        self.stacked_widget.setCurrentWidget(create_page)

    def view_house(self, house):
        """Open the detailed view of a house in the stacked widget"""
        if not hasattr(self, 'stacked_widget') or not self.stacked_widget:
            QMessageBox.warning(self, "Error", "Navigation stack not available.")
            return

        # Fetch fresh/full data if your current house dict is incomplete
        # (optional but recommended — your list might not have students/points)
        detailed_house = self.fetch_house_details(house["id"])
        if not detailed_house:
            detailed_house = house  # fallback

        # Create and add the details page
        details_page = HouseDetailsPage(
            house_name=house["name"],
            house_data=detailed_house,
            token=self.token,
            api_base=self.api_base,
            parent_manager=self
        )

        # Add to stacked widget and switch
        self.stacked_widget.addWidget(details_page)
        self.stacked_widget.setCurrentWidget(details_page)

    def fetch_house_details(self, house_id):
        """Fetch full house data including students and points"""
        try:
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"

            url = f"{self.api_base}/api/house/houses/{house_id}/"
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to fetch details: {response.status_code} {response.text}")
                return None
        except Exception as e:
            print(f"Error fetching house details: {e}")
            return None

    def delete_house(self, house_id):
        reply = QMessageBox.question(self, "Delete House", f"Delete house ID {house_id}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
                url = f"{self.api_base}/api/house/houses/{house_id}/"
                r = requests.delete(url, headers=headers)
                if r.status_code in (200, 204):
                    self.load_houses()
                    QMessageBox.information(self, "Success", "House deleted.")
                else:
                    QMessageBox.critical(self, "Error", f"Failed: {r.text}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    # load_houses stays exactly the same as your original
    def load_houses(self):
        try:
            headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
            url = f"{self.api_base}/api/house/houses/"
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                self.houses = response.json()
                self.populate_table()
            else:
                QMessageBox.critical(self, "Error", f"Failed to load houses: {response.status_code}\n{response.text}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection failed:\n{str(e)}")