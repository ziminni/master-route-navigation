# views/House/HouseDetails.py
import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QMessageBox, QFrame, QHeaderView,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
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
        main_layout.setContentsMargins(32, 24, 32, 24)
        main_layout.setSpacing(20)

        # === TOP ROW: BACK BUTTON + TITLE ===
        top_row = QHBoxLayout()
        
        back_btn = QPushButton("← Back")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #084924;
                border: 2px solid #084924;
                border-radius: 8px;
                padding: 10px 20px;
                font-family: 'Inter', sans-serif;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #084924;
                color: white;
            }
        """)
        back_btn.clicked.connect(self.go_back)
        top_row.addWidget(back_btn)
        
        top_row.addStretch()
        
        title = QLabel(self.house_name)
        title.setStyleSheet("""
            font-family: 'Poppins', sans-serif;
            font-size: 32px;
            font-weight: 800;
            color: #084924;
            letter-spacing: -0.5px;
        """)
        top_row.addWidget(title)
        
        top_row.addStretch()
        
        # Spacer to balance the back button
        spacer = QWidget()
        spacer.setFixedWidth(100)
        top_row.addWidget(spacer)

        main_layout.addLayout(top_row)

        # === POINTS CARDS ===
        points_layout = QHBoxLayout()
        points_layout.setSpacing(20)
        
        # Behavioral Points Card
        beh_card = self._create_points_card(
            "Behavioral Points",
            str(house_data.get('behavioral_points', 0)),
            "#4CAF50"
        )
        points_layout.addWidget(beh_card)
        
        # Competitive Points Card
        comp_card = self._create_points_card(
            "Competitive Points",
            str(house_data.get('competitive_points', 0)),
            "#084924"
        )
        points_layout.addWidget(comp_card)

        main_layout.addLayout(points_layout)

        # === MEMBERS TABLE SECTION ===
        table_section = QFrame()
        table_section.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        # Add shadow to section
        section_shadow = QGraphicsDropShadowEffect()
        section_shadow.setBlurRadius(15)
        section_shadow.setXOffset(0)
        section_shadow.setYOffset(4)
        section_shadow.setColor(QColor(0, 0, 0, 25))
        table_section.setGraphicsEffect(section_shadow)
        
        table_layout = QVBoxLayout(table_section)
        table_layout.setContentsMargins(24, 20, 24, 20)
        table_layout.setSpacing(16)
        
        # Table header row
        table_header_row = QHBoxLayout()
        table_title = QLabel("House Members")
        table_title.setStyleSheet("""
            font-family: 'Inter', sans-serif;
            font-size: 20px;
            font-weight: 700;
            color: #084924;
        """)
        table_header_row.addWidget(table_title)
        table_header_row.addStretch()
        
        add_member_btn = QPushButton("+ Add Member")
        add_member_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_member_btn.setStyleSheet("""
            QPushButton {
                background-color: #084924;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-family: 'Inter', sans-serif;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #0a5c2e;
            }
        """)
        add_member_btn.clicked.connect(self.open_add_member_dialog)
        table_header_row.addWidget(add_member_btn)
        
        remove_member_btn = QPushButton("− Remove")
        remove_member_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_member_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-family: 'Inter', sans-serif;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        remove_member_btn.clicked.connect(self.remove_selected_member)
        table_header_row.addWidget(remove_member_btn)
        
        table_layout.addLayout(table_header_row)

        # Table widget
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Member Name", "Role", "Points"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        
        # Make columns stretch
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #e8e8e8;
                border-radius: 8px;
                font-family: 'Inter', sans-serif;
                font-size: 14px;
            }
            QTableWidget::item {
                padding: 12px 16px;
                border-bottom: 1px solid #f0f0f0;
                color: #333333;
            }
            QTableWidget::item:selected {
                background-color: #e8f5e9;
                color: #084924;
            }
            QTableWidget::item:alternate {
                background-color: #fafafa;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                color: #666666;
                padding: 12px 16px;
                border: none;
                border-bottom: 2px solid #084924;
                font-family: 'Inter', sans-serif;
                font-weight: 600;
                font-size: 12px;
                text-transform: uppercase;
            }
            QScrollBar:vertical {
                background-color: #f5f5f5;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #cccccc;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #084924;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        table_layout.addWidget(self.table)
        main_layout.addWidget(table_section)
        
        # Load members from API
        self.load_members()

    def _create_points_card(self, title, value, accent_color):
        """Create a styled points card"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }}
        """)
        
        # Add shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setXOffset(0)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 20))
        card.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(8)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-family: 'Inter', sans-serif;
            font-size: 14px;
            color: #888888;
            font-weight: 500;
        """)
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            font-family: 'Poppins', sans-serif;
            font-size: 36px;
            font-weight: 800;
            color: {accent_color};
        """)
        layout.addWidget(value_label)
        
        return card

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
            
            # Center align role and points
            role_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            points_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Store the membership ID in the first column for deletion
            name_item.setData(Qt.ItemDataRole.UserRole, member.get("id"))
            
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, role_item)
            self.table.setItem(row, 2, points_item)
        
        # Set row height for better spacing
        for row in range(self.table.rowCount()):
            self.table.setRowHeight(row, 48)

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
