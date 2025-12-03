# views/House/HouseDetails.py
import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt
from .AddMemberDialog import AddMemberDialog


class HouseDetailsPage(QWidget):
    def __init__(self, house_name="Gryffindor", house_data=None, token=None, api_base=None, parent_manager=None):
        super().__init__()
        
        self.parent_manager = parent_manager
        self.token = token
        self.api_base = api_base or "http://127.0.0.1:8000"

        # === MOCK DATA (if none provided) ===
        if house_data is None:
            house_data = {
                "name": house_name,
                "behavioral_points": 2847,
                "competitive_points": 512,
                "students": [
                    {"Name": "Harry Potter", "Year": "Year 7"},
                    {"Name": "Hermione Granger", "Year": "Year 7"},
                    {"Name": "Ron Weasley", "Year": "Year 7"},
                ]
            }

        self.house_name = house_data.get("name", house_name)
        self.house_data = house_data
        
        # Members will be loaded from API
        self.members = []

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # === BACK BUTTON + TITLE ===
        top_row = QHBoxLayout()
        
        back_btn = QPushButton("← Back")
        back_btn.clicked.connect(self.go_back)
        top_row.addWidget(back_btn)
        
        top_row.addStretch()
        
        title = QLabel(f"{self.house_name}")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        top_row.addWidget(title)
        
        top_row.addStretch()

        main_layout.addLayout(top_row)

        # === POINTS SUMMARY ===
        points_layout = QHBoxLayout()
        
        beh_label = QLabel(f"Behavioral Points: {house_data.get('behavioral_points', 0)}")
        beh_label.setStyleSheet("font-size: 16px;")
        points_layout.addWidget(beh_label)
        
        points_layout.addStretch()
        
        comp_label = QLabel(f"Competitive Points: {house_data.get('competitive_points', 0)}")
        comp_label.setStyleSheet("font-size: 16px;")
        points_layout.addWidget(comp_label)

        main_layout.addLayout(points_layout)

        # === STUDENTS TABLE ===
        table_header_row = QHBoxLayout()
        table_title = QLabel("House Members")
        table_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px;")
        table_header_row.addWidget(table_title)
        table_header_row.addStretch()
        
        add_member_btn = QPushButton("+ Add Member")
        add_member_btn.setStyleSheet("background-color: #084924; color: white; padding: 8px 16px;")
        add_member_btn.clicked.connect(self.open_add_member_dialog)
        table_header_row.addWidget(add_member_btn)
        
        remove_member_btn = QPushButton("- Remove Member")
        remove_member_btn.setStyleSheet("background-color: #dc3545; color: white; padding: 8px 16px;")
        remove_member_btn.clicked.connect(self.remove_selected_member)
        table_header_row.addWidget(remove_member_btn)
        
        main_layout.addLayout(table_header_row)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Member Name", "Role", "Points"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        main_layout.addWidget(self.table)
        
        # Load members from API
        self.load_members()

    def load_members(self):
        """Load house members from the API"""
        house_id = self.house_data.get("id")
        if not house_id:
            return
        
        try:
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            
            # Fetch memberships for this house
            url = f"{self.api_base}/api/house/memberships/?house={house_id}"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    self.members = data.get("results", [])
                else:
                    self.members = data
                
                self.populate_members_table()
            else:
                print(f"Failed to load members: HTTP {response.status_code}")
                self.members = []
                self.populate_members_table()
        except Exception as e:
            print(f"Error loading members: {e}")
            self.members = []
            self.populate_members_table()
    
    def populate_members_table(self):
        """Populate the table with member data"""
        self.table.setRowCount(len(self.members))
        
        for row, member in enumerate(self.members):
            # Get member display info
            name = member.get("user_display", f"User {member.get('user', 'Unknown')}")
            role = member.get("role", "member").replace("_", " ").title()
            points = str(member.get("points", 0))
            
            name_item = QTableWidgetItem(name)
            role_item = QTableWidgetItem(role)
            points_item = QTableWidgetItem(points)
            
            # Store the membership ID in the first column for deletion
            name_item.setData(Qt.ItemDataRole.UserRole, member.get("id"))
            
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, role_item)
            self.table.setItem(row, 2, points_item)
        
        self.table.resizeColumnsToContents()

    def remove_selected_member(self):
        """Remove the selected member from the house"""
        selected_rows = self.table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a member to remove.")
            return
        
        row = selected_rows[0].row()
        name_item = self.table.item(row, 0)
        membership_id = name_item.data(Qt.ItemDataRole.UserRole)
        member_name = name_item.text()
        
        if not membership_id:
            QMessageBox.warning(self, "Error", "Could not retrieve membership ID.")
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Remove Member",
            f"Are you sure you want to remove {member_name} from {self.house_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Call API to delete the membership
        try:
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            
            url = f"{self.api_base}/api/house/memberships/{membership_id}/"
            response = requests.delete(url, headers=headers, timeout=10)
            
            if response.status_code in (200, 204):
                QMessageBox.information(self, "Success", f"{member_name} has been removed from {self.house_name}.")
                self.load_members()  # Refresh the list
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("detail") or error_data.get("error") or str(error_data)
                except:
                    error_msg = f"HTTP {response.status_code}"
                QMessageBox.critical(self, "Error", f"Failed to remove member: {error_msg}")
        except requests.RequestException as e:
            QMessageBox.critical(self, "Error", f"Cannot reach backend: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error removing member: {e}")

    def open_add_member_dialog(self):
        """Open dialog to add a member to the house"""
        house_id = self.house_data.get("id")
        if not house_id:
            QMessageBox.warning(self, "Error", "House ID not available.")
            return
        
        dialog = AddMemberDialog(
            house_id=house_id,
            house_name=self.house_name,
            token=self.token,
            api_base=self.api_base,
            parent=self
        )
        
        if dialog.exec():
            # Refresh the member list after adding
            self.load_members()
    
    def refresh_members(self):
        """Reload the members from API"""
        self.load_members()
    
    def go_back(self):
        """Navigate back to the house manager page"""
        if self.parent_manager and hasattr(self.parent_manager, 'stacked_widget'):
            # Remove this details page from the stack
            self.parent_manager.stacked_widget.removeWidget(self)
            # Go back to the house manager page
            self.parent_manager.stacked_widget.setCurrentWidget(self.parent_manager)
            self.deleteLater()