from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                             QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QHeaderView, QLineEdit, QStackedWidget, QMessageBox)
from PyQt6.QtGui import QFont, QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt, pyqtSignal
from ...controller.document_controller import DocumentController
from ...utils.icon_utils import create_back_button, create_search_button
from ...utils.bulk_operations import execute_bulk_operation
from ...widgets.empty_state import EmptyStateWidget

class DeletedFileView(QWidget):
    file_restored = pyqtSignal(dict)  # Signal to notify parent of file restoration
    
    def __init__(self, username, roles, primary_role, token, stack=None):
        super().__init__()

        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        
        # Initialize controller
        self.controller = DocumentController(username, roles, primary_role, token)

        self.stack: QStackedWidget = stack
        self.setWindowTitle("Deleted Files")
        
        # Track file data for efficient incremental updates
        self.file_data_cache = {}  # {'filename': {'time': ..., 'extension': ..., 'deleted_at': ..., 'days_remaining': ..., 'row_index': ...}}
        
        main_layout = QVBoxLayout()

        # Header with back button
        header_layout = QHBoxLayout()
        back_btn = create_back_button(callback=self.go_back)

        header = QLabel("Deleted Files")
        header.setFont(QFont("Arial", 16))
        
        search_bar = QLineEdit()
        search_button = create_search_button(callback=lambda: print("Search button clicked"))
        search_bar.setPlaceholderText("Search Deleted Files...")
        search_bar.setMinimumWidth(200)
        
        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(search_bar)
        header_layout.addWidget(search_button)
        header_layout.addWidget(back_btn)
        main_layout.addLayout(header_layout)
        
        # Action buttons row (between header and table)
        actions_layout = QHBoxLayout()
        
        # Restore All button
        restore_all_btn = QPushButton("Restore All")
        restore_all_btn.setStyleSheet("""
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
        restore_all_btn.clicked.connect(self.handle_restore_all)
        
        # Bulk Restore button (for selected items)
        bulk_restore_btn = QPushButton("Restore")
        bulk_restore_btn.setStyleSheet("""
            QPushButton {
                background-color: #5cb85c;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4cae4c;
            }
        """)
        bulk_restore_btn.clicked.connect(self.handle_bulk_restore)
        
        # Erase All button
        erase_all_btn = QPushButton("Delete All")
        erase_all_btn.setStyleSheet("""
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
        erase_all_btn.clicked.connect(self.handle_erase_all)
        
        # Bulk Delete button (for selected items)
        bulk_delete_btn = QPushButton("Delete")
        bulk_delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #d9534f;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c9302c;
            }
        """)
        bulk_delete_btn.clicked.connect(self.handle_bulk_delete)
        
        actions_layout.addWidget(restore_all_btn)
        actions_layout.addWidget(bulk_restore_btn)
        actions_layout.addWidget(erase_all_btn)
        actions_layout.addWidget(bulk_delete_btn)
        actions_layout.addStretch()
        main_layout.addLayout(actions_layout)

        # Table logic with Days Remaining column and checkboxes
        self.table = QTableWidget()
        self.table.setColumnCount(6)  # Added checkbox column
        self.table.setHorizontalHeaderLabels(["", "Filename", "Time", "Extension", "Days Remaining", "Actions"])
        
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

        # Load deleted files data using controller
        self.load_deleted_files()
        
        self.table_container_layout.addWidget(self.table)
        main_layout.addWidget(self.table_container)

        self.setLayout(main_layout)
    
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

    def create_actions_widget(self, filename, deleted_at=None):
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        erase_btn = QPushButton("Erase")
        restore_btn = QPushButton("Restore")
        erase_btn.clicked.connect(lambda: self.handle_permanent_delete(filename, deleted_at))
        restore_btn.clicked.connect(lambda: self.handle_restore(filename, deleted_at))
        layout.addWidget(erase_btn)
        layout.addWidget(restore_btn)
        widget.setLayout(layout)
        return widget
    
    def create_days_remaining_item(self, days_remaining):
        """Create a colored item based on days remaining"""
        if days_remaining is None:
            item = QTableWidgetItem("N/A")
        else:
            item = QTableWidgetItem(f"{days_remaining} days")
            # Color code based on urgency
            if days_remaining <= 3:
                item.setForeground(Qt.GlobalColor.red)
            elif days_remaining <= 7:
                item.setForeground(Qt.GlobalColor.darkYellow)
        return item

    def go_back(self):
        print("Back button clicked")
        if self.stack:
            self.stack.setCurrentIndex(0)  # Assuming dashboard is at index 0

    def add_file_to_table(self, name, time, ext, deleted_at=None, days_remaining=None):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Add checkbox in first column
        checkbox_item = QTableWidgetItem()
        checkbox_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        checkbox_item.setCheckState(Qt.CheckState.Unchecked)
        self.table.setItem(row, 0, checkbox_item)
        
        # Add file data (shifted by 1 column)
        self.table.setItem(row, 1, QTableWidgetItem(name))
        self.table.setItem(row, 2, QTableWidgetItem(time))
        self.table.setItem(row, 3, QTableWidgetItem(ext))
        self.table.setItem(row, 4, self.create_days_remaining_item(days_remaining))
        
        # Add actions widget
        actions_widget = self.create_actions_widget(name, deleted_at)
        self.table.setCellWidget(row, 5, actions_widget)

    def handle_item_clicked(self, item):
        # Skip checkbox column (0) and actions column (5)
        if item.column() != 0 and item.column() != 5:
            filename = self.table.item(item.row(), 1).text()
            print(f"Deleted file row clicked: {filename}")
    
    def handle_item_double_clicked(self, item):
        """Handle table item double-click - show file details dialog"""
        # Skip checkbox column (0) and actions column (5)
        if item.column() != 0 and item.column() != 5:
            filename = self.table.item(item.row(), 1).text()
            # Need to find the deleted_at timestamp for this file
            files_data = self.controller.get_deleted_files()
            deleted_at = None
            for f in files_data:
                if f['filename'] == filename:
                    deleted_at = f.get('deleted_at')
                    break
            self.show_file_details(filename, deleted_at)
    
    def load_deleted_files(self):
        """Load and populate deleted files table with days remaining (initial load)"""
        # Clear existing rows and cache
        self.table.setRowCount(0)
        self.file_data_cache.clear()
        
        # Get deleted files from controller
        files_data = self.controller.get_deleted_files()
        
        # Handle empty state
        if len(files_data) == 0:
            self.table.setVisible(False)
            if not hasattr(self, 'empty_state'):
                self.empty_state = EmptyStateWidget(
                    icon_name="folder-open.png",
                    title="No Deleted Files",
                    message="Files you delete will appear here and be automatically removed after 15 days.",
                    action_text=None  # No action button for empty deleted files
                )
                self.table_container_layout.addWidget(self.empty_state)
            else:
                self.empty_state.setVisible(True)
            return
        else:
            # Hide empty state and show table
            if hasattr(self, 'empty_state'):
                self.empty_state.setVisible(False)
            self.table.setVisible(True)
        
        for idx, file_data in enumerate(files_data):
            # Get file info with age calculation
            file_info = self.controller.get_recycle_bin_file_info(
                file_data['filename'], 
                file_data.get('deleted_at')
            )
            
            days_remaining = None
            if file_info:
                days_remaining = file_info.get('days_remaining')
            
            self.add_file_to_table(
                file_data['filename'], 
                file_data.get('time', 'N/A'), 
                file_data['extension'],
                file_data.get('deleted_at'),
                days_remaining
            )
            
            # Track file data in cache with file_id for bulk operations
            cache_key = self._get_cache_key(file_data['filename'], file_data.get('deleted_at'))
            self.file_data_cache[cache_key] = {
                'filename': file_data['filename'],
                'time': file_data.get('time', 'N/A'),
                'extension': file_data['extension'],
                'deleted_at': file_data.get('deleted_at'),
                'days_remaining': days_remaining,
                'file_id': file_data.get('file_id'),  # Store file_id for bulk operations
                'row_index': idx
            }
    
    def handle_restore(self, filename, deleted_at=None):
        """Restore a deleted file"""
        # Confirmation dialog
        reply = QMessageBox.question(
            self, 
            'Confirm Restore',
            f"Are you sure you want to restore '{filename}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Get full file data before restoring (to capture _original_collections)
            deleted_files = self.controller.get_deleted_files()
            file_data = None
            for f in deleted_files:
                if f['filename'] == filename and (deleted_at is None or f.get('deleted_at') == deleted_at):
                    file_data = f.copy()  # Make a copy to preserve original data
                    break
            
            if not file_data or not file_data.get('file_id'):
                QMessageBox.warning(self, "Error", "Cannot restore file: Missing file ID")
                return
            
            success, message = self.controller.restore_file(file_data['file_id'])
            
            if success:
                QMessageBox.information(self, "Success", message)
                # Emit signal to notify parent with full file data (includes _original_collections)
                self.file_restored.emit(file_data)
                # Remove file incrementally instead of full reload
                self._remove_file_from_table(filename, deleted_at)
            else:
                QMessageBox.warning(self, "Error", message)
    
    def handle_permanent_delete(self, filename, deleted_at=None):
        """Permanently delete a file"""
        # Confirmation dialog with warning
        reply = QMessageBox.warning(
            self, 
            'Confirm Permanent Delete',
            f"Are you sure you want to PERMANENTLY delete '{filename}'?\n\nThis action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Get file_id from deleted files
            deleted_files = self.controller.get_deleted_files()
            file_id = None
            for f in deleted_files:
                if f['filename'] == filename and (deleted_at is None or f.get('deleted_at') == deleted_at):
                    file_id = f.get('file_id')
                    break
            
            if not file_id:
                QMessageBox.warning(self, "Error", "Cannot delete file: Missing file ID")
                return
            
            success, message = self.controller.permanent_delete_file(file_id)
            
            if success:
                QMessageBox.information(self, "Success", message)
                # Remove file incrementally instead of full reload
                self._remove_file_from_table(filename, deleted_at)
            else:
                QMessageBox.warning(self, "Error", message)
    
    def handle_restore_all(self):
        """Restore all deleted files"""
        # Get all deleted files
        files_data = self.controller.get_deleted_files()
        
        if not files_data:
            QMessageBox.information(self, "No Files", "There are no deleted files to restore.")
            return
        
        # Confirmation dialog
        reply = QMessageBox.question(
            self, 
            'Confirm Restore All',
            f"Are you sure you want to restore all {len(files_data)} deleted file(s)?\n\nAll files will be moved back to uploaded files.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success_count = 0
            failed_count = 0
            error_messages = []
            
            # Restore each file
            for file_data in files_data:
                file_id = file_data.get('file_id')
                filename = file_data['filename']
                
                if not file_id:
                    failed_count += 1
                    error_messages.append(f"'{filename}': Missing file ID")
                    continue
                
                success, message = self.controller.restore_file(file_id)
                
                if success:
                    success_count += 1
                    # Emit signal to notify parent with full file data (includes _original_collections)
                    self.file_restored.emit(file_data)
                else:
                    failed_count += 1
                    error_messages.append(f"- {filename}: {message}")
            
            # Show results
            if failed_count == 0:
                QMessageBox.information(
                    self, 
                    "Success", 
                    f"Successfully restored all {success_count} file(s)!"
                )
            else:
                result_msg = f"Restored: {success_count} file(s)\nFailed: {failed_count} file(s)\n\nErrors:\n"
                result_msg += "\n".join(error_messages[:5])  # Show first 5 errors
                if len(error_messages) > 5:
                    result_msg += f"\n... and {len(error_messages) - 5} more"
                QMessageBox.warning(self, "Partial Success", result_msg)
            
            # Refresh the table
            self.load_deleted_files()
    
    def handle_erase_all(self):
        """Permanently delete all files"""
        # Get all deleted files
        files_data = self.controller.get_deleted_files()
        
        if not files_data:
            QMessageBox.information(self, "No Files", "There are no deleted files to erase.")
            return
        
        # Confirmation dialog with strong warning
        reply = QMessageBox.warning(
            self, 
            'Confirm Erase All',
            f"⚠️ WARNING ⚠️\n\nAre you sure you want to PERMANENTLY delete all {len(files_data)} file(s)?\n\n"
            f"This action CANNOT be undone!\n\nAll files will be removed from the Recycle Bin forever.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Double confirmation for destructive action
            reply2 = QMessageBox.warning(
                self,
                'Final Confirmation',
                f"This is your LAST CHANCE!\n\n{len(files_data)} file(s) will be permanently deleted.\n\nAre you absolutely sure?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply2 == QMessageBox.StandardButton.Yes:
                success_count = 0
                failed_count = 0
                error_messages = []
                
                # Delete each file
                for file_data in files_data:
                    file_id = file_data.get('file_id')
                    filename = file_data['filename']
                    
                    if not file_id:
                        failed_count += 1
                        error_messages.append(f"'{filename}': Missing file ID")
                        continue
                    
                    success, message = self.controller.permanent_delete_file(file_id)
                    
                    if success:
                        success_count += 1
                    else:
                        failed_count += 1
                        error_messages.append(f"- {filename}: {message}")
                
                # Show results
                if failed_count == 0:
                    QMessageBox.information(
                        self, 
                        "Success", 
                        f"Successfully erased all {success_count} file(s) permanently."
                    )
                else:
                    result_msg = f"Erased: {success_count} file(s)\nFailed: {failed_count} file(s)\n\nErrors:\n"
                    result_msg += "\n".join(error_messages[:5])  # Show first 5 errors
                    if len(error_messages) > 5:
                        result_msg += f"\n... and {len(error_messages) - 5} more"
                    QMessageBox.warning(self, "Partial Success", result_msg)
                
                # Refresh with incremental update
                self.refresh_deleted_files()
    
    def show_file_details(self, filename, deleted_at=None):
        """Show file details dialog using custom widget"""
        # Get file details from deleted files
        files_data = self.controller.get_deleted_files()
        file_data = None
        
        for f in files_data:
            if f['filename'] == filename:
                if deleted_at is None or f.get('deleted_at') == deleted_at:
                    file_data = f
                    break
        
        if file_data:
            # Get extended info with days remaining
            file_info = self.controller.get_recycle_bin_file_info(filename, deleted_at)
            
            if file_info:
                file_data['days_remaining'] = file_info.get('days_remaining')
                file_data['age_days'] = file_info.get('age_days')
            
            from ..Dialogs.file_details_dialog import FileDetailsDialog
            dialog = FileDetailsDialog(
                self, 
                file_data=file_data, 
                controller=self.controller,
                is_deleted=True  # Important: this is a deleted file
            )
            dialog.file_deleted.connect(self.on_file_action_from_dialog)
            dialog.file_restored.connect(self.on_file_restored_from_dialog)
            dialog.exec()
        else:
            QMessageBox.warning(self, "Error", f"Could not find details for '{filename}'")
    
    def on_file_action_from_dialog(self, file_data):
        """Handle file deleted signal from details dialog"""
        print(f"File action from dialog: {file_data}")
        # Refresh deleted files table
        self.refresh_deleted_files()
    
    def on_file_restored_from_dialog(self, file_data):
        """Handle file restored signal from details dialog"""
        print(f"File restored from dialog: {file_data}")
        # Forward the signal to parent (AdminDash)
        self.file_restored.emit(file_data)
        # Refresh deleted files table
        self.refresh_deleted_files()
    
    def _get_cache_key(self, filename, deleted_at):
        """Generate unique cache key from filename and deleted_at timestamp"""
        return f"{filename}|{deleted_at}"
    
    def _remove_file_from_table(self, filename, deleted_at=None):
        """Remove a single file from table incrementally"""
        cache_key = self._get_cache_key(filename, deleted_at)
        
        if cache_key in self.file_data_cache:
            row_idx = self.file_data_cache[cache_key]['row_index']
            self.table.removeRow(row_idx)
            del self.file_data_cache[cache_key]
            
            # Rebuild indices after removal
            self._rebuild_file_indices()
            print(f"Removed deleted file from UI: {filename}")
        else:
            # Fallback to full refresh if not found in cache
            print(f"File '{filename}' not found in cache, doing full refresh")
            self.refresh_deleted_files()
    
    def refresh_deleted_files(self):
        """Efficiently refresh deleted files with incremental updates"""
        # Get fresh data from controller
        files_data = self.controller.get_deleted_files()
        
        # Build fresh data dict with cache keys
        fresh_files = {}
        for file_data in files_data:
            # Get file info with age calculation
            file_info = self.controller.get_recycle_bin_file_info(
                file_data['filename'], 
                file_data.get('deleted_at')
            )
            
            days_remaining = None
            if file_info:
                days_remaining = file_info.get('days_remaining')
            
            cache_key = self._get_cache_key(file_data['filename'], file_data.get('deleted_at'))
            fresh_files[cache_key] = {
                'filename': file_data['filename'],
                'time': file_data.get('time', 'N/A'),
                'extension': file_data['extension'],
                'deleted_at': file_data.get('deleted_at'),
                'days_remaining': days_remaining
            }
        
        current_keys = set(self.file_data_cache.keys())
        fresh_keys = set(fresh_files.keys())
        
        # Identify changes
        removed_files = current_keys - fresh_keys
        new_files = fresh_keys - current_keys
        existing_files = current_keys & fresh_keys
        
        # Check for modified files (days remaining may change)
        modified_files = set()
        for cache_key in existing_files:
            cached = self.file_data_cache[cache_key]
            fresh = fresh_files[cache_key]
            if (cached['time'] != fresh['time'] or 
                cached['extension'] != fresh['extension'] or
                cached['days_remaining'] != fresh['days_remaining']):
                modified_files.add(cache_key)
        
        # Remove deleted files (sort by row index descending)
        for cache_key in sorted(removed_files, 
                               key=lambda k: self.file_data_cache[k]['row_index'], 
                               reverse=True):
            row_idx = self.file_data_cache[cache_key]['row_index']
            self.table.removeRow(row_idx)
            del self.file_data_cache[cache_key]
            print(f"Removed deleted file: {cache_key}")
        
        # Update modified files
        for cache_key in modified_files:
            row_idx = self.file_data_cache[cache_key]['row_index']
            fresh = fresh_files[cache_key]
            
            self.table.item(row_idx, 0).setText(fresh['filename'])
            self.table.item(row_idx, 1).setText(fresh['time'])
            self.table.item(row_idx, 2).setText(fresh['extension'])
            self.table.setItem(row_idx, 3, self.create_days_remaining_item(fresh['days_remaining']))
            
            # Update cache
            self.file_data_cache[cache_key]['time'] = fresh['time']
            self.file_data_cache[cache_key]['extension'] = fresh['extension']
            self.file_data_cache[cache_key]['days_remaining'] = fresh['days_remaining']
            print(f"Updated deleted file: {cache_key}")
        
        # Add new files
        for cache_key in new_files:
            fresh = fresh_files[cache_key]
            self.add_file_to_table(
                fresh['filename'], 
                fresh['time'], 
                fresh['extension'],
                fresh['deleted_at'],
                fresh['days_remaining']
            )
            
            # Add to cache
            self.file_data_cache[cache_key] = {
                'time': fresh['time'],
                'extension': fresh['extension'],
                'deleted_at': fresh['deleted_at'],
                'days_remaining': fresh['days_remaining'],
                'row_index': self.table.rowCount() - 1
            }
            print(f"Added deleted file: {cache_key}")
        
        # Rebuild row indices after removals
        if removed_files:
            self._rebuild_file_indices()
        
        print(f"Refreshed deleted files with incremental updates")
    
    def _rebuild_file_indices(self):
        """Rebuild row indices in file_data_cache after removals"""
        for row_idx in range(self.table.rowCount()):
            # Column 1 now contains filename (column 0 is checkbox)
            filename_item = self.table.item(row_idx, 1)
            if filename_item:
                filename = filename_item.text()
                # Need to find the cache key for this row
                for cache_key, cached_data in self.file_data_cache.items():
                    if cache_key.startswith(filename + "|"):
                        cached_data['row_index'] = row_idx
                        break
    
    def handle_bulk_delete(self):
        """Handle bulk permanent deletion of selected files"""
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
            """Permanently delete a single file using the controller"""
            filename = file_data.get('filename')
            file_id = file_data.get('file_id')
            
            if not file_id:
                return False, f"Missing file ID for '{filename}'"
            
            try:
                # Use controller to permanently delete file by file_id
                success, message = self.controller.permanent_delete_file(file_id)
                print(f"Permanently deleting file by file_id: {file_id} ({filename})")
                return success, message
            
            except Exception as e:
                print(f"Error permanently deleting file: {e}")
                return False, str(e)
        
        # Execute bulk operation with confirmation dialog
        successful, failed, failed_items = execute_bulk_operation(
            items=selected_files,
            operation_func=delete_file_operation,
            operation_name="Permanently Delete",
            parent=self,
            item_display_func=lambda item: f"{item['filename']} ({item['extension']})",
            confirmation_message=f"⚠️ WARNING ⚠️\n\nAre you sure you want to PERMANENTLY delete {len(selected_files)} file(s)?\n\n"
                               "This action CANNOT be undone!\n\nThe files will be removed from the Recycle Bin forever."
        )
        
        # Refresh the view after bulk deletion
        if successful > 0:
            self.load_deleted_files()
            print(f"Bulk permanent delete completed: {successful} succeeded, {failed} failed")
    
    def handle_bulk_restore(self):
        """Handle bulk restoration of selected files"""
        # Get checked files from table
        selected_files = self._get_checked_files()
        
        if not selected_files:
            QMessageBox.warning(
                self,
                "No Files Selected",
                "Please check at least one file to restore.\n\n"
                "Tip: Use the checkboxes in the first column to select files."
            )
            return
        
        # Define the restore operation for a single file
        def restore_file_operation(file_data):
            """Restore a single file using the controller"""
            filename = file_data.get('filename')
            file_id = file_data.get('file_id')
            
            if not file_id:
                return False, f"Missing file ID for '{filename}'"
            
            try:
                # Use controller to restore file by file_id
                success, message = self.controller.restore_file(file_id)
                print(f"Restoring file by file_id: {file_id} ({filename})")
                
                if success:
                    # Emit signal for each restored file
                    self.file_restored.emit(file_data)
                
                return success, message
            
            except Exception as e:
                print(f"Error restoring file: {e}")
                return False, str(e)
        
        # Execute bulk operation with confirmation dialog
        successful, failed, failed_items = execute_bulk_operation(
            items=selected_files,
            operation_func=restore_file_operation,
            operation_name="Restore",
            parent=self,
            item_display_func=lambda item: f"{item['filename']} ({item['extension']})",
            confirmation_message=f"Are you sure you want to restore {len(selected_files)} file(s)?\n\n"
                               "The files will be moved back to the uploaded files list."
        )
        
        # Refresh the view after bulk restoration
        if successful > 0:
            self.load_deleted_files()
            print(f"Bulk restore completed: {successful} succeeded, {failed} failed")
    
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
                    # Need to find the cache key
                    for cache_key, cached_data in self.file_data_cache.items():
                        if cached_data.get('filename') == filename:
                            file_data = cached_data.copy()
                            checked_files.append(file_data)
                            print(f"Checked file: {filename} (file_id: {file_data.get('file_id')})")
                            break
        
        return checked_files
