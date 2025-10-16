from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                             QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QHeaderView, QLineEdit, QStackedWidget, QMessageBox)
from PyQt6.QtGui import QFont, QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt, pyqtSignal
from ...controller.document_controller import DocumentController
from ...Mock.data_loader import get_collection_by_name
from ...utils.icon_utils import create_back_button, create_search_button, create_floating_add_button
from ...utils.bulk_operations import execute_bulk_operation, get_selected_files_from_table
from ...widgets.empty_state import EmptyStateWidget

class CollectionView(QWidget):
    file_accepted = pyqtSignal(str)
    file_rejected = pyqtSignal(str)
    file_uploaded = pyqtSignal(dict)
    file_deleted = pyqtSignal(dict)
    file_updated = pyqtSignal(dict)

    def __init__(self, username, roles, primary_role, token, collection_name=None, stack=None):
        super().__init__()

        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        self.collection_name = collection_name
        
        # Initialize controller
        self.controller = DocumentController(username, roles, primary_role, token)

        self.stack: QStackedWidget = stack
        self.setWindowTitle(f"Collection: {collection_name}" if collection_name else "Collection")
        
        # Track file data for efficient incremental updates
        self.file_data_cache = {}  # {'filename': {'time': ..., 'extension': ..., 'row_index': ...}}
        
        main_layout = QVBoxLayout()

        # Header with back button
        header_layout = QHBoxLayout()
        back_btn = create_back_button(callback=self.go_back)
        
        header = QLabel(f"{collection_name}" if collection_name else "Collection")
        header.setFont(QFont("Arial", 16))

        search_bar = QLineEdit()
        search_button = create_search_button(callback=lambda: print("Search button clicked"))
        search_bar.setPlaceholderText("Search files...")
        search_bar.setMinimumWidth(200)

        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(search_bar)
        header_layout.addWidget(search_button)
        header_layout.addWidget(back_btn)
        main_layout.addLayout(header_layout)
        
        # Action buttons row (between header and table)
        actions_layout = QHBoxLayout()
        
        # Add File button
        add_file_btn = QPushButton("Add File")
        add_file_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        add_file_btn.clicked.connect(self.handle_add_file)
        
        # Bulk Delete button
        bulk_delete_btn = QPushButton("Delete")
        bulk_delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        bulk_delete_btn.clicked.connect(self.handle_bulk_delete)
        
        actions_layout.addWidget(add_file_btn)
        actions_layout.addWidget(bulk_delete_btn)
        actions_layout.addStretch()
        main_layout.addLayout(actions_layout)

        # Table logic with checkboxes for bulk selection
        self.table = QTableWidget()
        self.table.setColumnCount(5)  # Added checkbox column
        self.table.setHorizontalHeaderLabels(["", "Filename", "Time", "Extension", "Actions"])
        
        # Create "Select All" checkbox in header
        self.select_all_checkbox = QTableWidgetItem()
        self.select_all_checkbox.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        self.select_all_checkbox.setCheckState(Qt.CheckState.Unchecked)
        self.select_all_checkbox.setText("☑")
        self.table.setHorizontalHeaderItem(0, self.select_all_checkbox)
        
        # Connect header click to toggle all checkboxes
        self.table.horizontalHeader().sectionClicked.connect(self.handle_header_checkbox_clicked)
        
        # Set column widths
        self.table.setColumnWidth(0, 40)  # Checkbox column
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)  # Single selection only (use checkboxes for bulk)
        self.table.itemClicked.connect(self.handle_item_clicked)
        self.table.itemDoubleClicked.connect(self.handle_item_double_clicked)

        # Create container for table and empty state
        self.table_container = QWidget()
        self.table_container_layout = QVBoxLayout(self.table_container)
        self.table_container_layout.setContentsMargins(0, 0, 0, 0)

        # Load collection data from JSON
        collection_data = get_collection_by_name(collection_name)
        if collection_data:
            files_data = collection_data.get('files', [])
            
            # Show empty state or populate table
            if len(files_data) == 0:
                # Show empty state
                self.empty_state = EmptyStateWidget(
                    icon_name="folder-open.png",
                    title="No Files in This Collection",
                    message=f"Add files to the '{collection_name}' collection to organize your documents.",
                    action_text="Add File"
                )
                self.empty_state.action_clicked.connect(self.handle_add_file)
                self.table_container_layout.addWidget(self.empty_state)
                self.table.setVisible(False)
            else:
                # Populate table
                for idx, file_data in enumerate(files_data):
                    self.add_file_to_table(file_data['filename'], file_data['time'], file_data['extension'])
                    # Track file data in cache (including file_id for deletion)
                    self.file_data_cache[file_data['filename']] = {
                        'time': file_data['time'],
                        'extension': file_data['extension'],
                        'row_index': idx,
                        'file_id': file_data.get('file_id'),  # Store file_id for bulk operations
                        'timestamp': file_data.get('timestamp')  # Store timestamp as fallback
                    }
                self.table.setVisible(True)
        else:
            # Fallback if collection not found
            print(f"Warning: Collection '{collection_name}' not found in JSON data")
            self.error_state = EmptyStateWidget(
                icon_name="folder.png",
                title="Collection Not Found",
                message=f"The collection '{collection_name}' could not be loaded.",
                action_text=None
            )
            self.table_container_layout.addWidget(self.error_state)
            self.table.setVisible(False)
        
        self.table_container_layout.addWidget(self.table)
        main_layout.addWidget(self.table_container)

        # Floating Add Button (bottom-right corner)
        self.floating_add_btn = create_floating_add_button(callback=self.handle_add_file)
        self.floating_add_btn.setParent(self)
        self.position_floating_button()

        self.setLayout(main_layout)
    
    def resizeEvent(self, event):
        """Handle resize events to reposition floating button"""
        super().resizeEvent(event)
        self.position_floating_button()
    
    def position_floating_button(self):
        """Position the floating button in the bottom-right corner"""
        margin = 20
        button_size = self.floating_add_btn.size()
        x = self.width() - button_size.width() - margin
        y = self.height() - button_size.height() - margin
        self.floating_add_btn.move(x, y)
        self.floating_add_btn.raise_()  # Ensure button is on top
    
    def handle_header_checkbox_clicked(self, logical_index):
        """Handle click on header checkbox to select/deselect all"""
        if logical_index == 0:  # Checkbox column
            # Toggle the select all state
            current_state = self.select_all_checkbox.checkState()
            new_state = Qt.CheckState.Unchecked if current_state == Qt.CheckState.Checked else Qt.CheckState.Checked
            
            # Update header checkbox
            self.select_all_checkbox.setCheckState(new_state)
            
            # Update all row checkboxes
            for row in range(self.table.rowCount()):
                checkbox_item = self.table.item(row, 0)
                if checkbox_item:
                    checkbox_item.setCheckState(new_state)
            
            print(f"Select All: {'Checked' if new_state == Qt.CheckState.Checked else 'Unchecked'}")

    def create_actions_widget(self, filename):
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        reject_btn = QPushButton("Reject")
        accept_btn = QPushButton("Accept")
        reject_btn.clicked.connect(lambda: print(f"Reject clicked for {filename}"))
        accept_btn.clicked.connect(lambda: print(f"Accept clicked for {filename}"))
        layout.addWidget(reject_btn)
        layout.addWidget(accept_btn)
        widget.setLayout(layout)
        return widget

    def go_back(self):
        print("Back button clicked")  # Added this
        if self.stack:
            self.stack.setCurrentIndex(0)  # Assuming dashboard is at index 0

    def add_file_to_table(self, name, time, ext):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Add checkbox in first column
        checkbox_item = QTableWidgetItem()
        checkbox_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        checkbox_item.setCheckState(Qt.CheckState.Unchecked)
        self.table.setItem(row, 0, checkbox_item)
        
        # Add file data
        self.table.setItem(row, 1, QTableWidgetItem(name))
        self.table.setItem(row, 2, QTableWidgetItem(time))
        self.table.setItem(row, 3, QTableWidgetItem(ext))
        
        # Add actions widget
        actions_widget = self.create_actions_widget(name)
        self.table.setCellWidget(row, 4, actions_widget)

    def handle_item_clicked(self, item):
        # Skip checkbox column (0) and actions column (4)
        if item.column() != 0 and item.column() != 4:
            filename = self.table.item(item.row(), 1).text()
            print(f"File row clicked: {filename}")
    
    def handle_item_double_clicked(self, item):
        """Handle table item double-click - show file details dialog"""
        # Skip checkbox column (0) and actions column (4)
        if item.column() != 0 and item.column() != 4:
            filename = self.table.item(item.row(), 1).text()
            self.show_file_details(filename)
    
    def show_file_details(self, filename):
        """Show file details dialog using custom widget"""
        # Get file details from collection
        collection_data = get_collection_by_name(self.collection_name)
        file_data = None
        
        if collection_data:
            files_data = collection_data.get('files', [])
            for f in files_data:
                if f['filename'] == filename:
                    file_data = f
                    break
        
        if file_data:
            from ..Dialogs.file_details_dialog import FileDetailsDialog
            dialog = FileDetailsDialog(
                self, 
                file_data=file_data, 
                controller=self.controller,
                is_deleted=False
            )
            dialog.file_updated.connect(self.on_file_updated_from_dialog)
            dialog.file_deleted.connect(self.on_file_deleted_from_dialog)
            dialog.exec()
        else:
            QMessageBox.warning(self, "Error", f"Could not find details for '{filename}'")
    
    def on_file_updated_from_dialog(self, file_data):
        """Handle file updated signal from details dialog"""
        print(f"File updated in collection: {file_data}")
        # Refresh collection files
        self.refresh_collection_files()
        # Forward signal to parent (AdminDash)
        self.file_updated.emit(file_data)
    
    def on_file_deleted_from_dialog(self, file_data):
        """Handle file deleted signal from details dialog"""
        print(f"File deleted from collection dialog: {file_data}")
        
        # Immediate UI update - remove file from table
        filename = file_data.get('filename')
        if filename and filename in self.file_data_cache:
            row_idx = self.file_data_cache[filename]['row_index']
            self.table.removeRow(row_idx)
            del self.file_data_cache[filename]
            self._rebuild_file_indices()
            print(f"Immediately removed file from collection UI: {filename}")
        
        # Then refresh to ensure consistency with data source
        self.refresh_collection_files()
        
        # Add collection name to file_data before forwarding
        file_data['collection_name'] = self.collection_name
        print(f"Added collection_name to deleted file_data: {self.collection_name}")
        
        # Forward signal to parent (AdminDash)
        self.file_deleted.emit(file_data)
    
    def handle_add_file(self):
        """Open file upload dialog for this collection"""
        print(f"Add file to collection: {self.collection_name}")
        from ...services.document_crud_service import DocumentCRUDService
        from ..Dialogs.file_upload_dialog import FileUploadDialog
        
        # Get collection ID
        crud_service = DocumentCRUDService()
        collection = crud_service.get_collection_by_name(self.collection_name)
        
        if collection:
            collection_id = collection.get("id")
            dialog = FileUploadDialog(
                self, 
                collection_id=collection_id,
                username=self.username,
                role=self.primary_role
            )
            dialog.file_uploaded.connect(self.on_file_uploaded)
            dialog.exec()
        else:
            print(f"Error: Collection '{self.collection_name}' not found")
    
    def handle_bulk_delete(self):
        """Handle bulk deletion of selected files from collection"""
        # Get checked files from table
        selected_files = self._get_checked_files()
        
        if not selected_files:
            QMessageBox.warning(
                self,
                "No Files Selected",
                "Please check at least one file to delete.\n\n"
                "Tip: Use the checkboxes in the first column to select files."
            )
            return
        
        # Define the delete operation for a single file
        def delete_file_operation(file_data):
            """Delete a single file using the controller"""
            filename = file_data.get('filename')
            file_id = file_data.get('file_id')
            timestamp = file_data.get('timestamp')
            
            try:
                # Use controller to delete file (soft delete) - prefer file_id
                if file_id:
                    success, message = self.controller.delete_file(file_id=file_id)
                    print(f"Deleting file by file_id: {file_id} ({filename})")
                else:
                    success, message = self.controller.delete_file(
                        filename=filename,
                        timestamp=timestamp
                    )
                    print(f"Deleting file by filename: {filename}")
                
                if success:
                    # Emit signal for each deleted file
                    file_data['collection_name'] = self.collection_name
                    self.file_deleted.emit(file_data)
                
                return success, message
            
            except Exception as e:
                print(f"Error deleting file: {e}")
                return False, str(e)
        
        # Execute bulk operation with confirmation dialog
        successful, failed, failed_items = execute_bulk_operation(
            items=selected_files,
            operation_func=delete_file_operation,
            operation_name="Delete",
            parent=self,
            item_display_func=lambda item: f"{item['filename']} ({item['extension']})",
            confirmation_message=f"Are you sure you want to delete {len(selected_files)} file(s) from '{self.collection_name}'?\n\n"
                               "The files will be moved to the Recycle Bin and can be restored later."
        )
        
        # Refresh the collection view after bulk deletion
        if successful > 0:
            self.refresh_collection_files()
            print(f"Bulk delete completed: {successful} succeeded, {failed} failed")
    
    def _get_checked_files(self):
        """Get list of checked files from table with full metadata"""
        checked_files = []
        
        for row in range(self.table.rowCount()):
            checkbox_item = self.table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.CheckState.Checked:
                # Get filename from column 1
                filename_item = self.table.item(row, 1)
                if filename_item:
                    filename = filename_item.text()
                    
                    # Get complete file data from cache
                    if filename in self.file_data_cache:
                        file_data = self.file_data_cache[filename].copy()
                        file_data['filename'] = filename
                        checked_files.append(file_data)
                        print(f"Checked file: {filename} (file_id: {file_data.get('file_id')})")
        
        return checked_files
    
    def on_file_uploaded(self, file_data):
        """Handle file uploaded event - incremental update"""
        print(f"File uploaded to collection: {file_data}")
        
        filename = file_data.get('filename')
        if not filename:
            # Fallback to full refresh if filename not provided
            self.refresh_collection_files()
            self.file_uploaded.emit(file_data)
            return
        
        # CRITICAL FIX: Handle empty state transition
        # If table is hidden (empty state showing), we need to show it
        if not self.table.isVisible():
            print("Transitioning from empty state to populated table")
            if hasattr(self, 'empty_state') and self.empty_state:
                self.empty_state.setVisible(False)
            self.table.setVisible(True)
        
        # Check if file already exists
        if filename in self.file_data_cache:
            # Update existing file data (accounting for checkbox column)
            row_idx = self.file_data_cache[filename]['row_index']
            self.table.item(row_idx, 1).setText(file_data.get('filename', filename))
            self.table.item(row_idx, 2).setText(file_data.get('time', ''))
            self.table.item(row_idx, 3).setText(file_data.get('extension', ''))
            
            # Update cache
            self.file_data_cache[filename]['time'] = file_data.get('time', '')
            self.file_data_cache[filename]['extension'] = file_data.get('extension', '')
            self.file_data_cache[filename]['file_id'] = file_data.get('file_id')
            self.file_data_cache[filename]['timestamp'] = file_data.get('timestamp')
            print(f"Updated existing file in collection UI: {filename}")
        else:
            # Add new file incrementally
            self.add_file_to_table(
                file_data.get('filename', ''),
                file_data.get('time', ''),
                file_data.get('extension', '')
            )
            
            # Add to cache
            self.file_data_cache[filename] = {
                'time': file_data.get('time', ''),
                'extension': file_data.get('extension', ''),
                'row_index': self.table.rowCount() - 1,
                'file_id': file_data.get('file_id'),
                'timestamp': file_data.get('timestamp')
            }
            print(f"Added new file to collection UI: {filename}")
        
        self.file_uploaded.emit(file_data)
    
    def refresh_collection_files(self):
        """Efficiently refresh collection files with incremental updates"""
        # Get fresh data from JSON
        collection_data = get_collection_by_name(self.collection_name)
        if not collection_data:
            print(f"Warning: Collection '{self.collection_name}' not found when refreshing")
            return
        
        files_data = collection_data.get('files', [])
        
        # Handle empty state
        if len(files_data) == 0:
            self.table.setVisible(False)
            if not hasattr(self, 'empty_state'):
                self.empty_state = EmptyStateWidget(
                    icon_name="folder-open.png",
                    title="No Files in This Collection",
                    message=f"Add files to the '{self.collection_name}' collection to organize your documents.",
                    action_text="Add File"
                )
                self.empty_state.action_clicked.connect(self.handle_add_file)
                self.table_container_layout.insertWidget(0, self.empty_state)
            else:
                self.empty_state.setVisible(True)
            
            # Clear cache when empty
            self.file_data_cache.clear()
            return
        else:
            # Hide empty state and show table
            if hasattr(self, 'empty_state'):
                self.empty_state.setVisible(False)
            self.table.setVisible(True)
        
        fresh_files = {f['filename']: f for f in files_data}
        
        current_filenames = set(self.file_data_cache.keys())
        fresh_filenames = set(fresh_files.keys())
        
        # Identify changes
        removed_files = current_filenames - fresh_filenames
        new_files = fresh_filenames - current_filenames
        existing_files = current_filenames & fresh_filenames
        
        # Check for modified files
        modified_files = set()
        for filename in existing_files:
            cached = self.file_data_cache[filename]
            fresh = fresh_files[filename]
            if cached['time'] != fresh['time'] or cached['extension'] != fresh['extension']:
                modified_files.add(filename)
        
        # Remove deleted files (sort by row index descending)
        for filename in sorted(removed_files, 
                              key=lambda f: self.file_data_cache[f]['row_index'], 
                              reverse=True):
            row_idx = self.file_data_cache[filename]['row_index']
            self.table.removeRow(row_idx)
            del self.file_data_cache[filename]
            print(f"Removed file from collection: {filename}")
        
        # Update modified files (accounting for checkbox column)
        for filename in modified_files:
            row_idx = self.file_data_cache[filename]['row_index']
            fresh = fresh_files[filename]
            
            self.table.item(row_idx, 1).setText(fresh['filename'])
            self.table.item(row_idx, 2).setText(fresh['time'])
            self.table.item(row_idx, 3).setText(fresh['extension'])
            
            # Update cache
            self.file_data_cache[filename]['time'] = fresh['time']
            self.file_data_cache[filename]['extension'] = fresh['extension']
            self.file_data_cache[filename]['file_id'] = fresh.get('file_id')
            self.file_data_cache[filename]['timestamp'] = fresh.get('timestamp')
            print(f"Updated file in collection: {filename}")
        
        # Add new files
        for filename in new_files:
            fresh = fresh_files[filename]
            self.add_file_to_table(fresh['filename'], fresh['time'], fresh['extension'])
            
            # Add to cache with file_id and timestamp
            self.file_data_cache[filename] = {
                'time': fresh['time'],
                'extension': fresh['extension'],
                'row_index': self.table.rowCount() - 1,
                'file_id': fresh.get('file_id'),
                'timestamp': fresh.get('timestamp')
            }
            print(f"Added file to collection: {filename}")
        
        # Rebuild row indices after removals
        if removed_files:
            self._rebuild_file_indices()
        
        print(f"Refreshed collection '{self.collection_name}' with incremental updates")
    
    def _rebuild_file_indices(self):
        """Rebuild row indices in file_data_cache after removals"""
        for row_idx in range(self.table.rowCount()):
            # Column 1 now contains filename (column 0 is checkbox)
            filename_item = self.table.item(row_idx, 1)
            if filename_item:
                filename = filename_item.text()
                if filename in self.file_data_cache:
                    self.file_data_cache[filename]['row_index'] = row_idx