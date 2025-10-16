from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QTextEdit, QFrame, QMessageBox, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import os


class FileDetailsDialog(QDialog):
    """
    File Details Dialog - Modal popup for viewing and editing file details
    
    Shows file information in a card-based layout with:
    - File icon and name
    - Edit and Delete action buttons
    - Details section (filename, date, time, type, category)
    - Description section
    
    Signals:
        file_updated: Emitted when file details are saved
        file_deleted: Emitted when file is deleted from this dialog
        file_restored: Emitted when file is restored (from deleted state)
    """
    
    file_updated = pyqtSignal(dict)
    file_deleted = pyqtSignal(dict)
    file_restored = pyqtSignal(dict)
    
    def __init__(self, parent=None, file_data=None, controller=None, is_deleted=False):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle("File Details")
        self.setFixedSize(450, 600)
        
        self.file_data = file_data or {}
        self.controller = controller
        self.is_deleted = is_deleted  # If True, show Restore instead of Edit
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI components"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        
        # ========== FILE ICON ==========
        icon_layout = QHBoxLayout()
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Use icon based on file extension
        extension = self.file_data.get('extension', '').lower()
        icon_filename = self._get_icon_for_extension(extension)
        
        from ...utils.icon_utils import IconLoader
        file_icon = IconLoader.create_icon_label(icon_filename, size=(64, 64), alignment=Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(file_icon)
        main_layout.addLayout(icon_layout)
        
        # ========== FILENAME TITLE ==========
        filename_layout = QHBoxLayout()
        filename_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        filename_label = QLabel(self.file_data.get('filename', 'Unknown File'))
        filename_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        filename_layout.addWidget(filename_label)
        main_layout.addLayout(filename_layout)
        
        # ========== ACTION BUTTONS (Edit/Delete or Restore) ==========
        action_layout = QHBoxLayout()
        action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if self.is_deleted:
            restore_btn = QPushButton("Restore File")
            restore_btn.clicked.connect(self.handle_restore)
            action_layout.addWidget(restore_btn)
        else:
            edit_btn = QPushButton("Edit File")
            edit_btn.clicked.connect(self.handle_edit_save)
            action_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("Delete File")
        delete_btn.clicked.connect(self.handle_delete)
        action_layout.addWidget(delete_btn)
        
        main_layout.addLayout(action_layout)
        
        # ========== DETAILS SECTION ==========
        details_frame = QFrame()
        details_layout = QVBoxLayout()
        
        # Details header
        details_header = QLabel("Details")
        details_header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        details_layout.addWidget(details_header)
        
        # Filename field (editable)
        filename_row = QHBoxLayout()
        filename_row.addWidget(QLabel("Filename"))
        self.filename_input = QLineEdit(self.file_data.get('filename', ''))
        self.filename_input.setReadOnly(True)  # Start as read-only
        filename_row.addWidget(self.filename_input)
        details_layout.addLayout(filename_row)
        
        # Date Uploaded
        date_row = QHBoxLayout()
        date_row.addWidget(QLabel("Date Uploaded"))
        date_label = QLabel(self.file_data.get('uploaded_date', self.file_data.get('time', 'N/A')))
        date_row.addWidget(date_label)
        date_row.addStretch()
        details_layout.addLayout(date_row)
        
        # Time Uploaded
        time_row = QHBoxLayout()
        time_row.addWidget(QLabel("Time Uploaded"))
        time_label = QLabel(self.file_data.get('uploaded_time', self._extract_time()))
        time_row.addWidget(time_label)
        time_row.addStretch()
        details_layout.addLayout(time_row)
        
        # Type (Extension)
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Type"))
        type_label = QLabel(self.file_data.get('extension', 'N/A'))
        type_row.addWidget(type_label)
        type_row.addStretch()
        details_layout.addLayout(type_row)
        
        # Category (editable)
        category_row = QHBoxLayout()
        category_row.addWidget(QLabel("Category"))
        self.category_input = QLineEdit(self.file_data.get('category', 'N/A'))
        self.category_input.setReadOnly(True)  # Start as read-only
        category_row.addWidget(self.category_input)
        details_layout.addLayout(category_row)
        
        # Collection (editable dropdown)
        collection_row = QHBoxLayout()
        collection_row.addWidget(QLabel("Collection"))
        self.collection_combo = QComboBox()
        self.collection_combo.setEnabled(False)  # Start as disabled
        self._load_collections()
        collection_row.addWidget(self.collection_combo)
        details_layout.addLayout(collection_row)
        
        # Additional info for deleted files
        if self.is_deleted:
            deleted_at_row = QHBoxLayout()
            deleted_at_row.addWidget(QLabel("Deleted at"))
            deleted_at_label = QLabel(self.file_data.get('deleted_at', 'N/A'))
            deleted_at_row.addWidget(deleted_at_label)
            deleted_at_row.addStretch()
            details_layout.addLayout(deleted_at_row)
            
            days_remaining = self.file_data.get('days_remaining')
            if days_remaining is not None:
                days_row = QHBoxLayout()
                days_row.addWidget(QLabel("Days Remaining"))
                days_label = QLabel(f"{days_remaining} days")
                days_row.addWidget(days_label)
                days_row.addStretch()
                details_layout.addLayout(days_row)
        
        details_frame.setLayout(details_layout)
        main_layout.addWidget(details_frame)
        
        # ========== DESCRIPTION SECTION ==========
        description_frame = QFrame()
        description_layout = QVBoxLayout()
        
        # Description header
        description_header = QLabel("Description")
        description_header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        description_layout.addWidget(description_header)
        
        # Description text area (editable)
        self.description_text = QTextEdit()
        self.description_text.setPlaceholderText("No description provided...")
        self.description_text.setPlainText(self.file_data.get('description', ''))
        self.description_text.setReadOnly(True)  # Start as read-only
        self.description_text.setMinimumHeight(100)
        description_layout.addWidget(self.description_text)
        
        description_frame.setLayout(description_layout)
        main_layout.addWidget(description_frame)
        
        # ========== CLOSE BUTTON ==========
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        main_layout.addWidget(close_btn)
        
        self.setLayout(main_layout)
        
        # Track edit mode
        self.is_editing = False
    
    def _load_collections(self):
        """Load collections from data and populate dropdown"""
        from ...Mock.data_loader import get_collections
        
        collections = get_collections()
        
        # Add "None" option first
        self.collection_combo.addItem("None (Standalone)", "None")
        
        # Get current collection
        current_collection = self.file_data.get('collection', 'None')
        
        # Add all collections
        selected_index = 0
        for idx, collection in enumerate(collections, start=1):
            self.collection_combo.addItem(collection["name"], collection["name"])
            # Check if this is the current collection
            if collection["name"] == current_collection:
                selected_index = idx
        
        # Set current selection
        self.collection_combo.setCurrentIndex(selected_index)
    
    def _get_icon_for_extension(self, extension):
        """Get appropriate icon filename based on file extension"""
        extension = extension.lower().replace('.', '')
        
        icon_map = {
            'pdf': 'pdf.png',
            'doc': 'document.png',
            'docx': 'document.png',
            'txt': 'document.png',
            'xls': 'document.png',
            'xlsx': 'document.png',
            'ppt': 'document.png',
            'pptx': 'document.png',
            'zip': 'folder.png',
            'rar': 'folder.png',
            'jpg': 'document.png',
            'jpeg': 'document.png',
            'png': 'document.png',
        }
        
        return icon_map.get(extension, 'document.png')
    
    def _extract_time(self):
        """Extract time from the 'time' field if it contains both date and time"""
        time_str = self.file_data.get('time', 'N/A')
        # If time_str contains both date and time, try to extract time portion
        if ' ' in time_str:
            parts = time_str.split()
            if len(parts) >= 2:
                return parts[-1]  # Return last part (likely the time)
        return time_str
    
    def handle_edit_save(self):
        """Toggle edit mode or save changes"""
        if not self.is_editing:
            # Enter edit mode
            self.is_editing = True
            self.filename_input.setReadOnly(False)
            self.category_input.setReadOnly(False)
            self.collection_combo.setEnabled(True)  # Enable collection dropdown
            self.description_text.setReadOnly(False)
            
            # Change button text
            sender = self.sender()
            if sender:
                sender.setText("Save Changes")
        else:
            # Save changes
            self.save_changes()
    
    def save_changes(self):
        """Save the edited file details"""
        if not self.controller:
            QMessageBox.warning(self, "Error", "Cannot save changes: No controller provided")
            return
        
        new_filename = self.filename_input.text().strip()
        new_category = self.category_input.text().strip()
        new_collection = self.collection_combo.currentData()  # Get collection from dropdown
        new_description = self.description_text.toPlainText().strip()
        
        # Validate filename
        if not new_filename:
            QMessageBox.warning(self, "Invalid Input", "Filename cannot be empty")
            return
        
        # Get file_id from file_data
        file_id = self.file_data.get('file_id')
        
        if not file_id:
            QMessageBox.warning(self, "Error", "Cannot update file: Missing file ID")
            return
        
        # Call controller to update file
        success, message, updated_file_data = self.controller.update_file(
            file_id=file_id,
            new_filename=new_filename,
            category=new_category,
            description=new_description
        )
        
        # If file update was successful, also update collection if it changed
        if success and updated_file_data:
            old_collection = self.file_data.get('collection', 'None')
            if new_collection != old_collection:
                # Update collection field using file_id
                collection_success, collection_message = self.controller.update_file_collection(
                    file_id=file_id,
                    collection_name=new_collection if new_collection != "None" else None
                )
                
                if collection_success:
                    # Update the file_data with new collection
                    updated_file_data['collection'] = new_collection
                    message += f"\nCollection updated to '{new_collection}'"
                else:
                    QMessageBox.warning(self, "Partial Success", 
                                      f"File updated but collection update failed:\n{collection_message}")
        
        # Continue with existing update logic
        if success and updated_file_data:
            # Update local file_data with ALL fields from controller
            self.file_data.update(updated_file_data)
            
            # Update UI elements to reflect changes
            self.filename_input.setText(updated_file_data.get('filename', new_filename))
            self.category_input.setText(updated_file_data.get('category') or 'N/A')
            self.description_text.setPlainText(updated_file_data.get('description', ''))
            
            # Update the extension display if it changed
            extension = updated_file_data.get('extension', '')
            for i in range(self.layout().count()):
                item = self.layout().itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if isinstance(widget, QFrame):
                        # Find the extension label in details section
                        for j in range(widget.layout().count()):
                            sub_item = widget.layout().itemAt(j)
                            if sub_item and isinstance(sub_item, QHBoxLayout):
                                for k in range(sub_item.count()):
                                    label = sub_item.itemAt(k).widget()
                                    if isinstance(label, QLabel) and label.text() != "Type":
                                        # Check if this is the extension value label
                                        if k > 0:  # After the "Type" label
                                            prev_label = sub_item.itemAt(k-1).widget()
                                            if isinstance(prev_label, QLabel) and prev_label.text() == "Type":
                                                label.setText(extension)
            
            # Emit signal with updated data
            self.file_updated.emit(updated_file_data)
            
            QMessageBox.information(self, "Success", message)
            
            # Exit edit mode
            self.is_editing = False
            self.filename_input.setReadOnly(True)
            self.category_input.setReadOnly(True)
            self.collection_combo.setEnabled(False)  # Disable collection dropdown
            self.description_text.setReadOnly(True)
            
            # Change button text back
            sender = self.sender()
            if sender:
                sender.setText("Edit File")
        else:
            QMessageBox.warning(self, "Error", message or "Failed to update file details")
    
    def handle_delete(self):
        """Handle delete button click"""
        filename = self.file_data.get('filename', 'this file')
        
        if self.is_deleted:
            # Permanent delete
            reply = QMessageBox.warning(
                self,
                'Confirm Permanent Delete',
                f"Are you sure you want to PERMANENTLY delete '{filename}'?\n\nThis action cannot be undone!",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if self.controller:
                    file_id = self.file_data.get('file_id')
                    if not file_id:
                        QMessageBox.warning(self, "Error", "Cannot delete file: Missing file ID")
                        return
                    
                    success, message = self.controller.permanent_delete_file(file_id)
                    
                    if success:
                        QMessageBox.information(self, "Success", message)
                        self.file_deleted.emit(self.file_data)
                        self.accept()  # Close dialog
                    else:
                        QMessageBox.warning(self, "Error", message)
        else:
            # Move to trash
            reply = QMessageBox.question(
                self,
                'Confirm Delete',
                f"Are you sure you want to delete '{filename}'?\n\nYou can restore it later from Deleted Files.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if self.controller:
                    file_id = self.file_data.get('file_id')
                    if not file_id:
                        QMessageBox.warning(self, "Error", "Cannot delete file: Missing file ID")
                        return
                    
                    success, message = self.controller.delete_file(file_id)
                    
                    if success:
                        QMessageBox.information(self, "Success", message)
                        self.file_deleted.emit(self.file_data)
                        self.accept()  # Close dialog
                    else:
                        QMessageBox.warning(self, "Error", message)
    
    def handle_restore(self):
        """Handle restore button click (for deleted files)"""
        filename = self.file_data.get('filename', 'this file')
        
        reply = QMessageBox.question(
            self,
            'Confirm Restore',
            f"Are you sure you want to restore '{filename}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.controller:
                file_id = self.file_data.get('file_id')
                if not file_id:
                    QMessageBox.warning(self, "Error", "Cannot restore file: Missing file ID")
                    return
                
                success, message = self.controller.restore_file(file_id)
                
                if success:
                    QMessageBox.information(self, "Success", message)
                    # Emit BOTH signals - file_deleted for deleted files view, file_restored for uploads view
                    self.file_deleted.emit(self.file_data)  # Remove from deleted files view
                    self.file_restored.emit(self.file_data)  # Add to uploaded files view
                    self.accept()  # Close dialog
                else:
                    QMessageBox.warning(self, "Error", message)
