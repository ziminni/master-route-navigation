# views/House/HouseManager.py
import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QLineEdit, QSpacerItem, QSizePolicy, QDialog,
    QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
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
        main_layout.setContentsMargins(32, 24, 32, 24)
        main_layout.setSpacing(20)

        # Title
        title = QLabel("House Management")
        title.setStyleSheet("""
            font-family: 'Poppins', sans-serif;
            font-size: 32px;
            font-weight: 800;
            color: #084924;
            letter-spacing: -0.5px;
        """)
        main_layout.addWidget(title)

        # Search bar container
        search_container = QFrame()
        search_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
        """)
        search_shadow = QGraphicsDropShadowEffect()
        search_shadow.setBlurRadius(10)
        search_shadow.setXOffset(0)
        search_shadow.setYOffset(2)
        search_shadow.setColor(QColor(0, 0, 0, 15))
        search_container.setGraphicsEffect(search_shadow)
        
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(16, 8, 16, 8)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Search by name or slug...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 12px 16px;
                font-family: 'Inter', sans-serif;
                font-size: 14px;
                border: none;
                background: transparent;
                color: #333333;
            }
            QLineEdit::placeholder {
                color: #999999;
            }
        """)
        self.search_input.textChanged.connect(self.filter_houses)
        search_layout.addWidget(self.search_input)
        main_layout.addWidget(search_container)

        # Table container
        table_container = QFrame()
        table_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
        """)
        table_shadow = QGraphicsDropShadowEffect()
        table_shadow.setBlurRadius(15)
        table_shadow.setXOffset(0)
        table_shadow.setYOffset(4)
        table_shadow.setColor(QColor(0, 0, 0, 25))
        table_container.setGraphicsEffect(table_shadow)
        
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)

        # Table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Slug", "Actions"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 280)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: none;
                border-radius: 12px;
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
                padding: 14px 16px;
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
        main_layout.addWidget(table_container)

        # THE REAL FLOATING ACTION BUTTON
        self.fab = QPushButton("+", self)
        self.fab.setFixedSize(60, 60)
        self.fab.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fab.setStyleSheet("""
            QPushButton {
                background-color: #084924;
                color: white;
                border-radius: 30px;
                font-size: 32px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #0a5c2e;
            }
            QPushButton:pressed {
                background-color: #06381b;
            }
        """)
        self.fab.clicked.connect(self.open_create_house_page)
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
        self.fab.raise_()

    def populate_table(self):
        self.table.setRowCount(0)
        for house in self.houses:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setRowHeight(row, 52)

            self.table.setItem(row, 0, QTableWidgetItem(str(house["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(house["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(house.get("slug", "—")))

            actions_widget = QWidget()
            actions_widget.setStyleSheet("background: transparent;")
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(8, 6, 8, 6)
            actions_layout.setSpacing(8)

            view_btn = QPushButton("View")
            view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            view_btn.setStyleSheet("""
                QPushButton {
                    background-color: #084924;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 14px 18px;
                    font-family: 'Inter', sans-serif;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #0a5c2e;
                }
            """)
            view_btn.clicked.connect(lambda _, h=house: self.view_house(h))

            edit_btn = QPushButton("Edit")
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #084924;
                    border: 2px solid #084924;
                    border-radius: 6px;
                    padding: 12px 18px;
                    font-family: 'Inter', sans-serif;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #084924;
                    color: white;
                }
            """)

            delete_btn = QPushButton("Delete")
            delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #dc3545;
                    border: 2px solid #dc3545;
                    border-radius: 6px;
                    padding: 12px 18px;
                    font-family: 'Inter', sans-serif;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #dc3545;
                    color: white;
                }
            """)
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
        """Open the create house dialog"""
        dialog = AdminCreateHousePage(
            token=self.token, 
            api_base=self.api_base, 
            parent=self,
            parent_manager=self
        )
        dialog.exec()

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