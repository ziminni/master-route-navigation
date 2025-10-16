from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                             QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QHeaderView, QLineEdit, QStackedWidget, QMessageBox)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal
from ...controller.document_controller import DocumentController
from ...utils.icon_utils import create_back_button, create_search_button, create_floating_add_button
from ...utils.bulk_operations import execute_bulk_operation
from ...widgets.empty_state import EmptyStateWidget

class UploadedFilesView(QWidget):
    """
    Uploaded Files View - displays all uploaded files in a table
    Similar to DeletedFilesView but for active/uploaded files
    """
    file_deleted = pyqtSignal(dict)  # Signal to notify parent of file deletion
    file_uploaded = pyqtSignal(dict)  # Signal to notify parent of file upload
    
    def __init__(self, username, roles, primary_role, token, stack=None):
        super().__init__()

        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        
        # Initialize controller
        self.controller = DocumentController(username, roles, primary_role, token)

        self.stack: QStackedWidget = stack
        self.setWindowTitle("Uploaded Files")
        
        # Track file data for efficient operations
        self.file_data_cache = {}  # {'filename': {'file_id': ..., 'timestamp': ..., 'row_index': ...}}
        
        main_layout = QVBoxLayout()

        # Header with back button
        header_layout = QHBoxLayout()
        back_btn = create_back_button(callback=self.go_back)

        header = QLabel("Uploaded Files")
        header.setFont(QFont("Arial", 16))
        
        search_bar = QLineEdit()
        search_button = create_search_button(callback=lambda: print("Search button clicked"))
        search_bar.setPlaceholderText("Search Uploaded Files...")
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

        # Table for uploaded files with checkboxes
        self.table = QTableWidget()
        self.table.setColumnCount(4)  # Added checkbox column
        self.table.setHorizontalHeaderLabels(["", "Filename", "Time", "Actions"])
        
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

        # Load uploaded files data using controller
        self.load_uploaded_files()
        
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
        """Create action buttons for each file row"""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        download_btn = QPushButton("Download")
        delete_btn = QPushButton("Delete")
        
        download_btn.clicked.connect(lambda: self.handle_download(filename))
        delete_btn.clicked.connect(lambda: self.handle_delete(filename))
        
        layout.addWidget(download_btn)
        layout.addWidget(delete_btn)
        widget.setLayout(layout)
        return widget

    def go_back(self):
        """Navigate back to dashboard"""
        print("Back button clicked")
        if self.stack:
            self.stack.setCurrentIndex(0)  # Assuming dashboard is at index 0

    def add_file_to_table(self, name, time, ext):
        """Add a file row to the table with checkbox"""
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
        
        # Add actions widget
        actions_widget = self.create_actions_widget(name)
        self.table.setCellWidget(row, 3, actions_widget)

    def handle_item_clicked(self, item):
        """Handle table item click (not action buttons or checkbox)"""
        # Skip checkbox column (0) and actions column (3)
        if item.column() != 0 and item.column() != 3:
            filename = self.table.item(item.row(), 1).text()
            print(f"Uploaded file row clicked: {filename}")
    
    def handle_item_double_clicked(self, item):
        """Handle table item double-click - show file details dialog"""
        # Skip checkbox column (0) and actions column (3)
        if item.column() != 0 and item.column() != 3:
            filename = self.table.item(item.row(), 1).text()
            self.show_file_details(filename)
    
    def load_uploaded_files(self):
        """Load and populate uploaded files table"""
        # Clear existing rows and cache
        self.table.setRowCount(0)
        self.file_data_cache.clear()
        
        # Get uploaded files from controller
        files_data = self.controller.get_files()
        
        # Handle empty state
        if len(files_data) == 0:
            self.table.setVisible(False)
            if not hasattr(self, 'empty_state'):
                self.empty_state = EmptyStateWidget(
                    icon_name="document.png",
                    title="No Uploaded Files",
                    message="Upload files to see them listed here.",
                    action_text="Upload File"
                )
                self.empty_state.action_clicked.connect(self.handle_add_file)
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
            self.add_file_to_table(
                file_data['filename'], 
                file_data.get('time', 'N/A'), 
                file_data['extension']
            )
            
            # Cache file data with file_id and timestamp for bulk operations
            self.file_data_cache[file_data['filename']] = {
                'file_id': file_data.get('file_id'),
                'timestamp': file_data.get('timestamp'),
                'extension': file_data.get('extension'),
                'time': file_data.get('time', 'N/A'),
                'row_index': idx
            }
    
    def handle_add_file(self):
        """Open the file upload dialog"""
        print("Add file clicked - Opening dialog")
        from ..Dialogs.file_upload_dialog import FileUploadDialog
        dialog = FileUploadDialog(self, username=self.username, role=self.primary_role)
        dialog.file_uploaded.connect(self.on_file_uploaded)
        dialog.exec()
    
    def handle_bulk_delete(self):
        """Handle bulk deletion of selected files"""
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
            confirmation_message=f"Are you sure you want to delete {len(selected_files)} file(s)?\n\n"
                               "The files will be moved to the Recycle Bin and can be restored later."
        )
        
        # Refresh the view after bulk deletion
        if successful > 0:
            self.load_uploaded_files()
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
        """Handle file uploaded event - refresh the table and notify parent"""
        print(f"File uploaded: {file_data}")
        
        # CRITICAL FIX: Handle empty state transition
        # If table is hidden (empty state showing), we need to show it before adding
        if not self.table.isVisible():
            print("Transitioning from empty state to populated table")
            if hasattr(self, 'empty_state') and self.empty_state:
                self.empty_state.setVisible(False)
            self.table.setVisible(True)
        
        # Emit signal to notify parent (AdminDash)
        self.file_uploaded.emit(file_data)
        # Refresh the table
        self.load_uploaded_files()
    
    def handle_download(self, filename):
        """Handle file download"""
        print(f"Download file: {filename}")
        # TODO: Implement download functionality with controller
        QMessageBox.information(self, "Download", f"Downloading '{filename}'...\n\n(Download functionality to be implemented)")
    
    def handle_delete(self, filename):
        """Delete a file (move to trash/deleted files)"""
        # Confirmation dialog
        reply = QMessageBox.question(
            self, 
            'Confirm Delete',
            f"Are you sure you want to delete '{filename}'?\n\nYou can restore it later from Deleted Files.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Get full file data before deletion (need file_id)
            files_data = self.controller.get_files()
            file_data = None
            for f in files_data:
                if f['filename'] == filename:
                    file_data = f
                    break
            
            if not file_data or not file_data.get('file_id'):
                QMessageBox.warning(self, "Error", "Cannot delete file: Missing file ID")
                return
            
            success, message = self.controller.delete_file(file_data['file_id'])
            
            if success:
                QMessageBox.information(self, "Success", message)
                # Emit signal to notify parent with full file data
                self.file_deleted.emit(file_data)
                # Refresh the table
                self.load_uploaded_files()
            else:
                QMessageBox.warning(self, "Error", message)
    
    def show_file_details(self, filename):
        """Show file details dialog using custom widget"""
        # Get file details from uploaded files
        files_data = self.controller.get_files()
        file_data = None
        
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
            dialog.file_updated.connect(self.on_file_updated)
            dialog.file_deleted.connect(self.on_file_deleted_from_dialog)
            dialog.exec()
        else:
            QMessageBox.warning(self, "Error", f"Could not find details for '{filename}'")
    
    def on_file_updated(self, file_data):
        """Handle file updated signal from details dialog"""
        print(f"File updated: {file_data}")
        # Refresh the table to show updated data
        self.load_uploaded_files()
    
    def on_file_deleted_from_dialog(self, file_data):
        """Handle file deleted signal from details dialog"""
        print(f"File deleted from dialog: {file_data}")
        # Emit signal to notify parent
        self.file_deleted.emit(file_data)
        # Refresh the table
        self.load_uploaded_files()
