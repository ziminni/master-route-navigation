"""
Toolbar Widget - Main Action Bar

Provides quick access to common actions:
- Upload file
- Create new folder
- Refresh view
- Sort documents
- Filter documents
- Search

Usage:
    toolbar = Toolbar()
    toolbar.action_triggered.connect(handle_action)
    toolbar.search_requested.connect(handle_search)
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QComboBox,
    QLineEdit, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt


class Toolbar(QWidget):
    """
    Top toolbar with action buttons and controls.
    
    Signals:
        action_triggered(str): Emitted when action button clicked
            Actions: 'upload', 'new_folder', 'refresh'
        sort_changed(str): Emitted when sort option changes
            Options: 'name', 'date', 'size', 'owner'
        search_requested(str): Emitted when search is performed
    """
    
    action_triggered = pyqtSignal(str)  # action_name
    sort_changed = pyqtSignal(str)      # sort_field
    search_requested = pyqtSignal(str)  # search_query
    
    def __init__(self, parent=None):
        """
        Initialize toolbar.
        
        Args:
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the toolbar UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # ========== Left Side: Action Buttons ==========
        
        # Upload button
        self.btn_upload = QPushButton("Upload")
        self.btn_upload.setToolTip("Upload files")
        self.btn_upload.clicked.connect(lambda: self.action_triggered.emit('upload'))
        layout.addWidget(self.btn_upload)
        
        # New folder button
        self.btn_new_folder = QPushButton("New Folder")
        self.btn_new_folder.setToolTip("Create new folder")
        self.btn_new_folder.clicked.connect(lambda: self.action_triggered.emit('new_folder'))
        layout.addWidget(self.btn_new_folder)
        
        # Refresh button
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.setToolTip("Refresh view")
        self.btn_refresh.clicked.connect(lambda: self.action_triggered.emit('refresh'))
        layout.addWidget(self.btn_refresh)
        
        # Separator
        layout.addSpacing(20)
        
        # ========== Center: Spacer ==========
        layout.addStretch()
        
        # ========== Right Side: Search & Sort ==========
        
        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search documents...")
        self.search_input.setMinimumWidth(250)
        self.search_input.returnPressed.connect(self._on_search)
        layout.addWidget(self.search_input)
        
        # Search button
        self.btn_search = QPushButton("Search")
        self.btn_search.clicked.connect(self._on_search)
        layout.addWidget(self.btn_search)
        
        layout.addSpacing(10)
        
        # Sort dropdown
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Sort: Name (A-Z)",
            "Sort: Name (Z-A)",
            "Sort: Date (Newest)",
            "Sort: Date (Oldest)",
            "Sort: Size (Largest)",
            "Sort: Size (Smallest)",
        ])
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        layout.addWidget(self.sort_combo)
        
        # Apply button styling
        self._apply_button_styles()
    
    def _apply_button_styles(self):
        """Apply consistent styling to all buttons."""
        button_style = """
            QPushButton {
                padding: 8px 15px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
                border-color: #2196F3;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
            }
        """
        
        self.btn_upload.setStyleSheet(button_style)
        self.btn_new_folder.setStyleSheet(button_style)
        self.btn_refresh.setStyleSheet(button_style)
        self.btn_search.setStyleSheet(button_style)
    
    def _on_search(self):
        """Handle search action."""
        query = self.search_input.text().strip()
        self.search_requested.emit(query)
    
    def _on_sort_changed(self, index: int):
        """
        Handle sort option change.
        
        Args:
            index (int): Selected combo box index
        """
        # Map index to sort field with direction
        sort_map = {
            0: 'title',           # Name A-Z
            1: '-title',          # Name Z-A
            2: '-uploaded_at',    # Date newest
            3: 'uploaded_at',     # Date oldest
            4: '-file_size',      # Size largest
            5: 'file_size',       # Size smallest
        }
        
        sort_field = sort_map.get(index, '-uploaded_at')
        self.sort_changed.emit(sort_field)
    
    def clear_search(self):
        """Clear the search input."""
        self.search_input.clear()
    
    def set_search_text(self, text: str):
        """
        Set search input text programmatically.
        
        Args:
            text (str): Search text
        """
        self.search_input.setText(text)
    
    def enable_actions(self, enabled: bool = True):
        """
        Enable or disable action buttons.
        
        Args:
            enabled (bool): True to enable, False to disable
        """
        self.btn_upload.setEnabled(enabled)
        self.btn_new_folder.setEnabled(enabled)
        self.btn_refresh.setEnabled(enabled)
