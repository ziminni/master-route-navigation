"""
Breadcrumb Bar Widget - Folder Navigation

Displays current folder path as clickable breadcrumbs.
Allows quick navigation to parent folders.

Example path: My Drive > Projects > 2024 > Final

Each segment is clickable to navigate back to that level.

Usage:
    breadcrumb = BreadcrumbBar()
    breadcrumb.set_path([
        {'id': None, 'name': 'My Drive'},
        {'id': 1, 'name': 'Projects'},
        {'id': 5, 'name': '2024'}
    ])
    breadcrumb.breadcrumb_clicked.connect(handle_navigation)
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import pyqtSignal, Qt


class BreadcrumbBar(QWidget):
    """
    Breadcrumb navigation bar for folder hierarchy.
    
    Signals:
        breadcrumb_clicked(int, str): Emitted when breadcrumb segment clicked
            - int: folder_id (None for root/My Drive)
            - str: folder name
    """
    
    breadcrumb_clicked = pyqtSignal(object, str)  # (folder_id, folder_name)
    
    def __init__(self, parent=None):
        """
        Initialize breadcrumb bar.
        
        Args:
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self.breadcrumb_path = []
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI components."""
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(0)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Start with "My Drive" by default
        self.set_path([{'id': None, 'name': 'My Drive'}])
    
    def set_path(self, path_items: list):
        """
        Set the breadcrumb path.
        
        Args:
            path_items (list): List of dictionaries with 'id' and 'name' keys
                Example: [
                    {'id': None, 'name': 'My Drive'},
                    {'id': 1, 'name': 'Projects'},
                    {'id': 5, 'name': '2024'}
                ]
        """
        # Clear existing breadcrumbs
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.breadcrumb_path = path_items
        
        # Add breadcrumb items
        for i, item in enumerate(path_items):
            # Create button for breadcrumb segment
            btn = QPushButton(item['name'])
            btn.setFlat(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    border: none;
                    padding: 5px 10px;
                    text-align: left;
                    color: #2196F3;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #E3F2FD;
                    border-radius: 3px;
                }
            """)
            
            # Connect click signal
            folder_id = item['id']
            folder_name = item['name']
            btn.clicked.connect(lambda checked, fid=folder_id, fname=folder_name: 
                              self.breadcrumb_clicked.emit(fid, fname))
            
            self.layout.addWidget(btn)
            
            # Add separator (chevron) if not last item
            if i < len(path_items) - 1:
                separator = QLabel(" > ")
                separator.setStyleSheet("color: #999; font-weight: bold;")
                self.layout.addWidget(separator)
        
        # Add stretch to push breadcrumbs to the left
        self.layout.addStretch()
    
    def append_folder(self, folder_id: int, folder_name: str):
        """
        Append a folder to the current path.
        
        Args:
            folder_id (int): Folder ID
            folder_name (str): Folder name
        """
        self.breadcrumb_path.append({'id': folder_id, 'name': folder_name})
        self.set_path(self.breadcrumb_path)
    
    def navigate_to_level(self, folder_id: int):
        """
        Navigate to a specific level in the breadcrumb.
        Truncates path to the selected level.
        
        Args:
            folder_id (int): Folder ID to navigate to
        """
        # Find the index of the folder in path
        for i, item in enumerate(self.breadcrumb_path):
            if item['id'] == folder_id:
                # Truncate path to this level
                self.breadcrumb_path = self.breadcrumb_path[:i+1]
                self.set_path(self.breadcrumb_path)
                break
    
    def reset(self):
        """Reset breadcrumb to root (My Drive)."""
        self.set_path([{'id': None, 'name': 'My Drive'}])
    
    def get_current_folder_id(self):
        """
        Get the ID of the current (last) folder in path.
        
        Returns:
            int or None: Current folder ID (None if at root)
        """
        if self.breadcrumb_path:
            return self.breadcrumb_path[-1]['id']
        return None
