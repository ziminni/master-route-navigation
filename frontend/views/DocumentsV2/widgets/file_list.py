"""
File List View Widget - Document Table Display

Displays documents in a sortable table format with:
- Checkboxes for multi-selection
- File type icons
- Name, Owner, Modified date, Size columns
- Right-click context menu
- Double-click to open folders/download files

Usage:
    file_list = FileListView()
    file_list.load_documents(documents)
    file_list.item_double_clicked.connect(handle_open)
    file_list.context_menu_requested.connect(handle_context_menu)
"""

from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QMenu, QHeaderView,
    QAbstractItemView, QCheckBox, QWidget, QHBoxLayout
)
from PyQt6.QtCore import pyqtSignal, Qt, QPoint
from PyQt6.QtGui import QAction, QFont
from datetime import datetime


class FileListView(QTableWidget):
    """
    Table widget for displaying documents in list view.
    
    Signals:
        item_double_clicked(dict): Emitted when item is double-clicked (document dict)
        selection_changed(list): Emitted when selection changes (list of document IDs)
        context_menu_action(str, int): Emitted when context menu action selected
            - str: action name
            - int: document ID
    """
    
    item_double_clicked = pyqtSignal(dict)  # document dict
    selection_changed = pyqtSignal(list)    # list of doc IDs
    context_menu_action = pyqtSignal(str, int)  # (action, doc_id)
    
    # File type to emoji mapping
    FILE_TYPE_ICONS = {
        'pdf': '📄',
        'doc': '📝',
        'docx': '📝',
        'txt': '📃',
        'xls': '📊',
        'xlsx': '📊',
        'csv': '📊',
        'ppt': '📽️',
        'pptx': '📽️',
        'jpg': '🖼️',
        'jpeg': '🖼️',
        'png': '🖼️',
        'gif': '🖼️',
        'svg': '🎨',
        'zip': '📦',
        'rar': '📦',
        '7z': '📦',
        'py': '🐍',
        'js': '📜',
        'html': '🌐',
        'css': '🎨',
        'folder': '\U0001F4C1',  # Keep as unicode for folder display
    }
    
    def __init__(self, user_role='student', parent=None):
        """
        Initialize file list view.
        
        Args:
            user_role (str): User's primary role (admin, faculty, staff, student)
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self.documents = []  # Store current document list
        self.selected_ids = []  # Track selected document IDs
        self.custom_menu_items = []  # Store custom context menu items
        self.user_role = user_role  # Store user role for permission checks
        self.init_ui()
    
    def set_custom_menu_items(self, items: list):
        """
        Set custom context menu items.
        
        Args:
            items: List of tuples (label, action_name, condition_callback)
                   condition_callback receives doc_data and returns bool
        """
        self.custom_menu_items = items
    
    def init_ui(self):
        """Initialize the table UI."""
        # Set column count and headers
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels([
            '☑', 'Name', 'Owner', 'Modified', 'Size'
        ])
        
        # Set column widths
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Checkbox
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)           # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Owner
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Modified
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Size
        
        # Set table behavior
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        
        # Enable context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # Connect double-click signal
        self.cellDoubleClicked.connect(self._on_double_click)
        
        # Connect selection changed
        self.itemSelectionChanged.connect(self._on_selection_changed)
    
    def load_documents(self, documents: list):
        """
        Load documents into the table.
        
        Args:
            documents (list): List of document dictionaries from API
                Each dict should have: id, title, uploaded_by_name, uploaded_at, 
                file_size_mb, file_extension, folder (optional)
        """
        self.documents = documents
        self.setRowCount(len(documents))
        
        for row, doc in enumerate(documents):
            # Column 0: Checkbox
            checkbox_widget = self._create_checkbox(doc['id'])
            self.setCellWidget(row, 0, checkbox_widget)
            
            # Column 1: Name with icon
            file_type = doc.get('file_extension', '').lower()
            is_folder = doc.get('folder') is True  # Check if it's actually a folder item
            icon = self.FILE_TYPE_ICONS.get(
                'folder' if is_folder else file_type,
                '📄'  # Default icon
            )
            
            name = doc.get('title') or doc.get('name', 'Untitled')
            name_item = QTableWidgetItem(f"{icon} {name}")
            name_item.setData(Qt.ItemDataRole.UserRole, doc['id'])
            name_item.setData(Qt.ItemDataRole.UserRole + 1, doc)  # Store full document data
            self.setItem(row, 1, name_item)
            
            # Column 2: Owner
            owner = doc.get('uploaded_by_name') or doc.get('created_by', 'Unknown')
            owner_item = QTableWidgetItem(owner)
            self.setItem(row, 2, owner_item)
            
            # Column 3: Modified date
            date_str = doc.get('uploaded_at') or doc.get('updated_at', '')
            if date_str:
                try:
                    # Parse ISO format date
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime('%b %d, %Y')
                except:
                    formatted_date = date_str[:10]  # Fallback to first 10 chars
            else:
                formatted_date = '-'
            
            date_item = QTableWidgetItem(formatted_date)
            self.setItem(row, 3, date_item)
            
            # Column 4: Size
            if is_folder:
                size_text = '-'
            else:
                size_mb = doc.get('file_size_mb', 0)
                if size_mb >= 1:
                    size_text = f"{size_mb:.1f} MB"
                elif size_mb > 0:
                    size_kb = size_mb * 1024
                    size_text = f"{size_kb:.0f} KB"
                else:
                    size_text = '-'
            
            size_item = QTableWidgetItem(size_text)
            self.setItem(row, 4, size_item)
    
    def _create_checkbox(self, doc_id: int) -> QWidget:
        """
        Create a centered checkbox widget for a table cell.
        
        Args:
            doc_id (int): Document ID to associate with checkbox
            
        Returns:
            QWidget: Widget containing centered checkbox
        """
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        checkbox = QCheckBox()
        checkbox.setProperty('doc_id', doc_id)
        checkbox.stateChanged.connect(lambda state, did=doc_id: self._on_checkbox_changed(did, state))
        layout.addWidget(checkbox)
        
        return widget
    
    def _on_checkbox_changed(self, doc_id: int, state: int):
        """
        Handle checkbox state change.
        
        Args:
            doc_id (int): Document ID
            state (int): Checkbox state (0=unchecked, 2=checked)
        """
        if state == Qt.CheckState.Checked.value:
            if doc_id not in self.selected_ids:
                self.selected_ids.append(doc_id)
        else:
            if doc_id in self.selected_ids:
                self.selected_ids.remove(doc_id)
        
        self.selection_changed.emit(self.selected_ids.copy())
    
    def _on_double_click(self, row: int, column: int):
        """
        Handle double-click on table item.
        
        Args:
            row (int): Row index
            column (int): Column index
        """
        name_item = self.item(row, 1)
        if name_item:
            doc_data = name_item.data(Qt.ItemDataRole.UserRole + 1)
            self.item_double_clicked.emit(doc_data)
    
    def _on_selection_changed(self):
        """Handle table row selection change."""
        # Note: This is different from checkbox selection
        # Could be used for keyboard navigation
        pass
    
    def _show_context_menu(self, position: QPoint):
        """
        Show right-click context menu.
        
        Args:
            position (QPoint): Click position
        """
        # Get clicked row
        item = self.itemAt(position)
        if not item:
            return
        
        row = item.row()
        name_item = self.item(row, 1)
        if not name_item:
            return
        
        doc_data = name_item.data(Qt.ItemDataRole.UserRole + 1)
        doc_id = doc_data.get('id')
        is_folder = doc_data.get('folder') is True
        is_deleted = doc_data.get('deleted_at') is not None
        
        # Check if multiple items are selected
        selected_count = len(self.selected_ids)
        is_multi_select = selected_count > 1
        
        # Create context menu
        menu = QMenu(self)
        
        # Add bulk operation header if multiple items selected
        if is_multi_select:
            header_action = QAction(f"{selected_count} items selected", self)
            header_action.setEnabled(False)
            font = header_action.font()
            font.setBold(True)
            header_action.setFont(font)
            menu.addAction(header_action)
            menu.addSeparator()
        
        if is_deleted:
            # Menu for trash items
            if is_multi_select:
                restore_action = QAction(f"Restore {selected_count} items", self)
            else:
                restore_action = QAction("↩️ Restore", self)
            restore_action.triggered.connect(lambda: self.context_menu_action.emit('restore', doc_id))
            menu.addAction(restore_action)
            
            # Only admins can permanently delete
            if self.user_role == 'admin':
                menu.addSeparator()
                
                if is_multi_select:
                    delete_action = QAction(f"Permanently Delete {selected_count} items", self)
                else:
                    delete_action = QAction("Delete Permanently", self)
                delete_action.triggered.connect(lambda: self.context_menu_action.emit('delete_permanent', doc_id))
                menu.addAction(delete_action)
        
        elif is_folder:
            # Menu for folders
            open_action = QAction("Open", self)
            open_action.triggered.connect(lambda: self.context_menu_action.emit('open', doc_id))
            menu.addAction(open_action)
            
            menu.addSeparator()
            
            rename_action = QAction("Rename", self)
            rename_action.triggered.connect(lambda: self.context_menu_action.emit('rename', doc_id))
            menu.addAction(rename_action)
            
            menu.addSeparator()
            
            delete_action = QAction("Delete", self)
            delete_action.triggered.connect(lambda: self.context_menu_action.emit('delete', doc_id))
            menu.addAction(delete_action)
        
        else:
            # Menu for documents
            open_action = QAction("Open", self)
            open_action.triggered.connect(lambda: self.context_menu_action.emit('open', doc_id))
            menu.addAction(open_action)
            
            download_action = QAction("Download", self)
            download_action.triggered.connect(lambda: self.context_menu_action.emit('download', doc_id))
            menu.addAction(download_action)
            
            # Students can ONLY open and download - no other actions
            if self.user_role != 'student':
                menu.addSeparator()
                
                if is_multi_select:
                    move_action = QAction(f"Move {selected_count} items to...", self)
                else:
                    move_action = QAction("Move to...", self)
                move_action.triggered.connect(lambda: self.context_menu_action.emit('move', doc_id))
                menu.addAction(move_action)
                
                # Only show rename for single selection
                if not is_multi_select:
                    rename_action = QAction("Rename", self)
                    rename_action.triggered.connect(lambda: self.context_menu_action.emit('rename', doc_id))
                    menu.addAction(rename_action)
                
                menu.addSeparator()
                
                if is_multi_select:
                    delete_action = QAction(f"Move {selected_count} items to Trash", self)
                else:
                    delete_action = QAction("Move to Trash", self)
                delete_action.triggered.connect(lambda: self.context_menu_action.emit('delete', doc_id))
                menu.addAction(delete_action)
            
            # Always show details/info (read-only)
            menu.addSeparator()
            
            info_action = QAction("Details", self)
            info_action.triggered.connect(lambda: self.context_menu_action.emit('details', doc_id))
            menu.addAction(info_action)
        
        # Add custom menu items
        if self.custom_menu_items:
            menu.addSeparator()
            for label, action_name, condition_callback in self.custom_menu_items:
                # Check if this item should be shown
                if condition_callback and not condition_callback(doc_data):
                    continue
                
                custom_action = QAction(label, self)
                custom_action.triggered.connect(
                    lambda checked=False, aid=action_name, did=doc_id: 
                    self.context_menu_action.emit(aid, did)
                )
                menu.addAction(custom_action)
        
        # Show menu at cursor position
        menu.exec(self.viewport().mapToGlobal(position))
    
    def get_selected_ids(self) -> list:
        """
        Get list of selected document IDs.
        
        Returns:
            list: List of document IDs
        """
        return self.selected_ids.copy()
    
    def clear_selection(self):
        """Clear all selections and uncheck all checkboxes."""
        self.selected_ids.clear()
        
        # Uncheck all checkboxes
        for row in range(self.rowCount()):
            checkbox_widget = self.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(False)
        
        self.selection_changed.emit([])
    
    def refresh(self):
        """Refresh the table view (reload same documents)."""
        self.load_documents(self.documents)
