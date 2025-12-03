"""
Sidebar Widget - Navigation Panel

Provides navigation options for document browsing:
- My Drive: All accessible documents
- Recent: Recently accessed documents
- Starred: Featured documents
- Trash: Soft-deleted documents
- Categories: Hierarchical category list
- Storage: Visual storage usage indicator

Emits signals when navigation items are clicked.

Usage:
    sidebar = Sidebar()
    sidebar.navigation_changed.connect(handle_navigation)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QProgressBar, QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont


class Sidebar(QWidget):
    """
    Left sidebar navigation widget.
    
    Signals:
        navigation_changed(str, int): Emitted when navigation item clicked
            - str: navigation type ('mydrive', 'recent', 'starred', 'trash', 'category')
            - int: ID (for categories) or None for special views
    """
    
    navigation_changed = pyqtSignal(str, object)  # (nav_type, item_id)
    
    def __init__(self, parent=None):
        """
        Initialize the sidebar widget.
        
        Args:
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self.current_selection = 'mydrive'
        self.categories = []  # Will be populated from API
        self.init_ui()
    
    def init_ui(self):
        """Initialize the sidebar UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Main Navigation Section
        nav_label = QLabel("NAVIGATION")
        nav_label.setStyleSheet("font-weight: bold; color: #666; padding: 10px;")
        layout.addWidget(nav_label)
        
        self.nav_list = QListWidget()
        self.nav_list.setFrameShape(QFrame.Shape.NoFrame)
        self.nav_list.itemClicked.connect(self._on_nav_item_clicked)
        
        # Add navigation items
        nav_items = [
            ('mydrive', 'Document Vault'),
            ('recent', 'Recent'),
            ('starred', 'Starred'),
            ('trash', 'Trash'),
        ]
        
        for nav_type, display_name in nav_items:
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, nav_type)
            self.nav_list.addItem(item)
        
        # Select "My Drive" by default
        self.nav_list.setCurrentRow(0)
        
        layout.addWidget(self.nav_list)
        
        # Categories Section
        cat_label = QLabel("CATEGORIES")
        cat_label.setStyleSheet("font-weight: bold; color: #666; padding: 10px;")
        layout.addWidget(cat_label)
        
        self.category_list = QListWidget()
        self.category_list.setFrameShape(QFrame.Shape.NoFrame)
        self.category_list.itemClicked.connect(self._on_category_clicked)
        layout.addWidget(self.category_list)
        
        # Storage Section
        layout.addStretch()
        storage_label = QLabel("STORAGE")
        storage_label.setStyleSheet("font-weight: bold; color: #666; padding: 10px;")
        layout.addWidget(storage_label)
        
        self.storage_bar = QProgressBar()
        self.storage_bar.setMaximum(100)
        self.storage_bar.setValue(0)
        self.storage_bar.setTextVisible(True)
        self.storage_bar.setFormat("0 / 100 GB (0%)")
        layout.addWidget(self.storage_bar)
        
        # Set fixed width for sidebar
        self.setMaximumWidth(250)
        self.setMinimumWidth(200)
    
    def load_categories(self, categories: list):
        """
        Load categories into the sidebar.
        
        Args:
            categories (list): List of category dictionaries from API
                Each dict should have: id, name, slug, icon (optional)
        """
        self.category_list.clear()
        self.categories = categories
        
        for category in categories:
            icon = category.get('icon', '📂')
            name = category.get('name', 'Unknown')
            display_name = f"{icon} {name}"
            
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, category.get('id'))
            item.setData(Qt.ItemDataRole.UserRole + 1, 'category')
            self.category_list.addItem(item)
    
    def update_storage(self, used_gb: float, total_gb: float):
        """
        Update storage usage display.
        
        Args:
            used_gb (float): Used storage in gigabytes
            total_gb (float): Total storage in gigabytes
        """
        percentage = int((used_gb / total_gb) * 100) if total_gb > 0 else 0
        self.storage_bar.setValue(percentage)
        self.storage_bar.setFormat(f"{used_gb:.1f} / {total_gb:.1f} GB ({percentage}%)")
        
        # Change color based on usage
        if percentage < 70:
            color = "#4CAF50"  # Green
        elif percentage < 90:
            color = "#FFC107"  # Yellow
        else:
            color = "#F44336"  # Red
        
        self.storage_bar.setStyleSheet(f"""
            QProgressBar::chunk {{
                background-color: {color};
            }}
        """)
    
    def _on_nav_item_clicked(self, item: QListWidgetItem):
        """
        Handle navigation item click.
        
        Args:
            item (QListWidgetItem): Clicked item
        """
        nav_type = item.data(Qt.ItemDataRole.UserRole)
        self.current_selection = nav_type
        
        # Clear category selection
        self.category_list.clearSelection()
        
        # Emit signal
        self.navigation_changed.emit(nav_type, None)
    
    def _on_category_clicked(self, item: QListWidgetItem):
        """
        Handle category item click.
        
        Args:
            item (QListWidgetItem): Clicked category item
        """
        category_id = item.data(Qt.ItemDataRole.UserRole)
        
        # Clear navigation selection
        self.nav_list.clearSelection()
        
        # Emit signal
        self.navigation_changed.emit('category', category_id)
    
    def set_active_navigation(self, nav_type: str, item_id: int = None):
        """
        Programmatically set active navigation item.
        
        Args:
            nav_type (str): Type of navigation ('mydrive', 'recent', 'starred', 'trash', 'category')
            item_id (int): Category ID if nav_type is 'category'
        """
        if nav_type == 'category' and item_id is not None:
            # Find and select category
            for i in range(self.category_list.count()):
                item = self.category_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == item_id:
                    self.category_list.setCurrentItem(item)
                    self.nav_list.clearSelection()
                    break
        else:
            # Find and select navigation item
            for i in range(self.nav_list.count()):
                item = self.nav_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == nav_type:
                    self.nav_list.setCurrentItem(item)
                    self.category_list.clearSelection()
                    break
