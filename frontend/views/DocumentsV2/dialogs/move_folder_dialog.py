"""
Move Folder Dialog - For Bulk Move Operations

Shows all available folders for selecting a destination to move multiple documents.

Features:
- Hierarchical folder tree view
- Category filtering
- Search folders
- Move to root option
- Visual folder paths

Usage:
    dialog = MoveFolderDialog(categories, document_service, parent)
    if dialog.exec():
        folder_id = dialog.get_selected_folder()
        folder_name = dialog.get_selected_folder_name()
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTreeWidget, QTreeWidgetItem,
    QComboBox, QLineEdit, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal


class MoveFolderDialog(QDialog):
    """
    Dialog for selecting a folder destination for bulk move operations.
    
    Provides a tree view of all available folders organized by category.
    Users can select a destination folder or move to root.
    """
    
    folder_created = pyqtSignal()  # Emitted when new folder is created
    
    def __init__(self, categories: list, document_service, parent=None):
        """
        Initialize move folder dialog.
        
        Args:
            categories (list): List of available categories
            document_service: Service for API calls
            parent: Parent widget
        """
        super().__init__(parent)
        self.categories = categories
        self.document_service = document_service
        
        self.folders = []  # All folders from API
        self.selected_folder_id = None
        self.selected_folder_name = None
        
        self.init_ui()
        self.load_folders()
    
    def init_ui(self):
        """Initialize the dialog UI."""
        self.setWindowTitle("Select Destination Folder")
        self.setModal(True)
        self.setMinimumSize(600, 650)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Select destination folder for documents")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # Instructions
        instruction_label = QLabel("Choose a folder to move the selected documents to:")
        instruction_label.setStyleSheet("color: #666;")
        layout.addWidget(instruction_label)
        
        # Category filter
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Filter by category:")
        filter_layout.addWidget(filter_label)
        
        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories", None)
        for category in self.categories:
            icon = category.get('icon', '')
            name = category.get('name', 'Unknown')
            self.category_filter.addItem(f"{icon} {name}", category.get('id'))
        self.category_filter.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.category_filter, 1)
        layout.addLayout(filter_layout)
        
        # Search box
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to search folders...")
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_input, 1)
        layout.addLayout(search_layout)
        
        # Folder tree
        self.folder_tree = QTreeWidget()
        self.folder_tree.setHeaderLabels(["Folder", "Path"])
        self.folder_tree.setColumnWidth(0, 250)
        self.folder_tree.setAlternatingRowColors(True)
        self.folder_tree.itemClicked.connect(self._on_item_clicked)
        self.folder_tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.folder_tree)
        
        # Current selection info
        self.selection_label = QLabel("No folder selected (will move to root)")
        self.selection_label.setStyleSheet("""
            padding: 10px;
            background-color: #e3f2fd;
            border-radius: 5px;
            color: #1976d2;
            font-weight: bold;
        """)
        layout.addWidget(self.selection_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # New folder button
        self.new_folder_btn = QPushButton("Create New Folder")
        self.new_folder_btn.clicked.connect(self._create_new_folder)
        self.new_folder_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                border: 1px solid #2196F3;
                border-radius: 4px;
                background-color: white;
                color: #2196F3;
            }
            QPushButton:hover {
                background-color: #e3f2fd;
            }
        """)
        button_layout.addWidget(self.new_folder_btn)
        
        button_layout.addStretch()
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
            }
        """)
        button_layout.addWidget(cancel_btn)
        
        # Select button
        self.select_btn = QPushButton("Select Folder")
        self.select_btn.clicked.connect(self.accept)
        self.select_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        button_layout.addWidget(self.select_btn)
        
        layout.addLayout(button_layout)
    
    def load_folders(self):
        """Load all folders from API."""
        print("[MoveFolderDialog] Loading folders...")
        result = self.document_service.get_folders()
        
        if result['success']:
            self.folders = result['data']
            print(f"[MoveFolderDialog] Loaded {len(self.folders)} folders")
            self._populate_tree()
        else:
            QMessageBox.warning(
                self,
                "Load Error",
                f"Failed to load folders: {result['error']}"
            )
    
    def _populate_tree(self):
        """Populate the folder tree with folders."""
        self.folder_tree.clear()
        
        # Get filter settings
        selected_category = self.category_filter.currentData()
        search_text = self.search_input.text().lower()
        
        # Filter folders
        filtered_folders = []
        for folder in self.folders:
            # Apply category filter
            if selected_category and folder.get('category') != selected_category:
                continue
            
            # Apply search filter
            if search_text and search_text not in folder.get('name', '').lower():
                continue
            
            filtered_folders.append(folder)
        
        # Build tree structure
        # First, add root folders (no parent)
        root_items = {}
        for folder in filtered_folders:
            if not folder.get('parent'):
                item = self._create_tree_item(folder)
                self.folder_tree.addTopLevelItem(item)
                root_items[folder['id']] = item
        
        # Then, add child folders recursively
        self._add_child_folders(filtered_folders, root_items)
        
        # Expand all items
        self.folder_tree.expandAll()
        
        print(f"[MoveFolderDialog] Displayed {len(filtered_folders)} folders in tree")
    
    def _add_child_folders(self, folders: list, parent_items: dict):
        """
        Recursively add child folders to the tree.
        
        Args:
            folders (list): All folders to process
            parent_items (dict): Dictionary mapping folder IDs to tree items
        """
        added_new = True
        while added_new:
            added_new = False
            for folder in folders:
                folder_id = folder.get('id')
                parent_id = folder.get('parent')
                
                # Skip if already added or has no parent
                if folder_id in parent_items or not parent_id:
                    continue
                
                # Add if parent exists in tree
                if parent_id in parent_items:
                    item = self._create_tree_item(folder)
                    parent_items[parent_id].addChild(item)
                    parent_items[folder_id] = item
                    added_new = True
    
    def _create_tree_item(self, folder: dict) -> QTreeWidgetItem:
        """
        Create a tree item for a folder.
        
        Args:
            folder (dict): Folder data
            
        Returns:
            QTreeWidgetItem: Tree item
        """
        folder_name = folder.get('name', 'Unnamed')
        folder_path = self._get_folder_path(folder)
        
        item = QTreeWidgetItem([folder_name, folder_path])
        item.setData(0, Qt.ItemDataRole.UserRole, folder['id'])
        item.setData(0, Qt.ItemDataRole.UserRole + 1, folder)
        
        # Add folder icon
        item.setText(0, f"📁 {folder_name}")
        
        return item
    
    def _get_folder_path(self, folder: dict) -> str:
        """
        Get full path of folder.
        
        Args:
            folder (dict): Folder data
            
        Returns:
            str: Full path like /Category/Parent/Folder
        """
        path_parts = [folder.get('name', 'Unnamed')]
        parent_id = folder.get('parent')
        
        # Traverse up to build path
        max_depth = 10  # Prevent infinite loops
        depth = 0
        while parent_id and depth < max_depth:
            parent = next((f for f in self.folders if f.get('id') == parent_id), None)
            if parent:
                path_parts.insert(0, parent.get('name', 'Unnamed'))
                parent_id = parent.get('parent')
            else:
                break
            depth += 1
        
        # Add category at the beginning
        category_id = folder.get('category')
        category = next((c for c in self.categories if c.get('id') == category_id), None)
        if category:
            path_parts.insert(0, category.get('name', 'Unknown'))
        
        return '/' + '/'.join(path_parts)
    
    def _on_filter_changed(self, index: int):
        """Handle category filter change."""
        print(f"[MoveFolderDialog] Filter changed to: {self.category_filter.currentText()}")
        self._populate_tree()
    
    def _on_search_changed(self, text: str):
        """Handle search text change."""
        print(f"[MoveFolderDialog] Search: {text}")
        self._populate_tree()
    
    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle tree item click."""
        folder_id = item.data(0, Qt.ItemDataRole.UserRole)
        folder_data = item.data(0, Qt.ItemDataRole.UserRole + 1)
        
        self.selected_folder_id = folder_id
        self.selected_folder_name = folder_data.get('name', 'Unnamed')
        folder_path = self._get_folder_path(folder_data)
        
        self.selection_label.setText(f"Selected: {folder_path}")
        print(f"[MoveFolderDialog] Selected folder: {self.selected_folder_name} (ID: {folder_id})")
    
    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle tree item double-click (select immediately)."""
        self._on_item_clicked(item, column)
        self.accept()
    
    def _create_new_folder(self):
        """Open dialog to create a new folder in selected location."""
        from .folder_dialog import FolderDialog
        
        # Determine parent folder for new folder
        parent_id = self.selected_folder_id
        
        dialog = FolderDialog(
            self.categories,
            self.document_service,
            parent_id,
            self
        )
        
        if dialog.exec():
            # Reload folders after creation
            self.load_folders()
            self.folder_created.emit()
            
            QMessageBox.information(
                self,
                "Folder Created",
                "New folder created successfully. You can now select it."
            )
    
    def get_selected_folder(self) -> int:
        """
        Get the selected folder ID.
        
        Returns:
            int: Selected folder ID (None for root)
        """
        return self.selected_folder_id
    
    def get_selected_folder_name(self) -> str:
        """
        Get the selected folder name.
        
        Returns:
            str: Selected folder name (None if moving to root)
        """
        return self.selected_folder_name
