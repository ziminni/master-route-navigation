"""
Bulk Operations Utility

Provides reusable bulk operation functionality for file management.
Includes bulk deletion, bulk restore, and other batch operations.
"""

from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QListWidget, QPushButton, QHBoxLayout, QProgressBar
from PyQt6.QtCore import Qt
from typing import List, Dict, Callable, Tuple


class BulkOperationDialog(QDialog):
    """
    Generic dialog for confirming and executing bulk operations.
    
    This dialog can be reused for:
    - Bulk deletion (soft delete)
    - Bulk permanent deletion
    - Bulk restore
    - Bulk move to collection
    
    Args:
        parent: Parent widget
        operation_name: Name of operation (e.g., "Delete", "Restore", "Permanently Delete")
        items: List of items to operate on (usually file data dictionaries)
        item_display_func: Function to format item for display in list
        confirmation_message: Custom confirmation message
    """
    
    def __init__(self, parent=None, operation_name="Delete", items=None, 
                 item_display_func=None, confirmation_message=None):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle(f"Confirm Bulk {operation_name}")
        self.setFixedSize(500, 400)
        
        self.operation_name = operation_name
        self.items = items or []
        self.item_display_func = item_display_func or self._default_display_func
        self.confirmation_message = confirmation_message or f"Are you sure you want to {operation_name.lower()} the following items?"
        
        self.confirmed = False
        self.init_ui()
    
    def _default_display_func(self, item):
        """Default function to display an item (expects dict with 'filename' key)"""
        if isinstance(item, dict):
            return item.get('filename', str(item))
        return str(item)
    
    def init_ui(self):
        """Initialize the dialog UI"""
        main_layout = QVBoxLayout()
        
        # Title
        title = QLabel(f"Bulk {self.operation_name}")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(title)
        
        # Confirmation message
        message = QLabel(self.confirmation_message)
        message.setWordWrap(True)
        main_layout.addWidget(message)
        
        # Item count
        count_label = QLabel(f"Selected items: {len(self.items)}")
        count_label.setStyleSheet("font-weight: bold; color: #d9534f;")
        main_layout.addWidget(count_label)
        
        # Items list
        list_label = QLabel("Items to process:")
        main_layout.addWidget(list_label)
        
        self.items_list = QListWidget()
        for item in self.items:
            display_text = self.item_display_func(item)
            self.items_list.addItem(display_text)
        main_layout.addWidget(self.items_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        confirm_btn = QPushButton(f"{self.operation_name} All")
        
        # Use green for Restore operations, red for Delete operations
        if "restore" in self.operation_name.lower():
            button_color = "#28a745"  # Green
            hover_color = "#218838"   # Darker green
        else:
            button_color = "#d9534f"  # Red
            hover_color = "#c9302c"   # Darker red
        
        confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {button_color};
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """)
        confirm_btn.clicked.connect(self.confirm)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(confirm_btn)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def confirm(self):
        """Handle confirmation"""
        self.confirmed = True
        self.accept()


class BulkProgressDialog(QDialog):
    """
    Dialog showing progress of bulk operations.
    
    Displays a progress bar and status messages as items are processed.
    """
    
    def __init__(self, parent=None, operation_name="Processing", total_items=0):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle(f"Bulk {operation_name}")
        self.setFixedSize(400, 150)
        
        self.operation_name = operation_name
        self.total_items = total_items
        self.init_ui()
    
    def init_ui(self):
        """Initialize the progress dialog UI"""
        main_layout = QVBoxLayout()
        
        # Title
        title = QLabel(f"Bulk {self.operation_name} in Progress")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        main_layout.addWidget(title)
        
        # Status label
        self.status_label = QLabel("Processing...")
        main_layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(self.total_items)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)
        
        # Close button (initially disabled)
        self.close_btn = QPushButton("Close")
        self.close_btn.setEnabled(False)
        self.close_btn.clicked.connect(self.accept)
        main_layout.addWidget(self.close_btn)
        
        self.setLayout(main_layout)
    
    def update_progress(self, current, status_text=""):
        """Update the progress bar and status text"""
        self.progress_bar.setValue(current)
        if status_text:
            self.status_label.setText(status_text)
    
    def complete(self, success_count, failed_count):
        """Mark the operation as complete"""
        if failed_count == 0:
            self.status_label.setText(f"✅ Successfully processed {success_count} item(s)")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.status_label.setText(
                f"⚠ Completed: {success_count} succeeded, {failed_count} failed"
            )
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        
        self.close_btn.setEnabled(True)


def execute_bulk_operation(
    items: List[Dict],
    operation_func: Callable[[Dict], Tuple[bool, str]],
    operation_name: str = "Operation",
    parent=None,
    item_display_func=None,
    confirmation_message=None
) -> Tuple[int, int, List[Tuple[str, str]]]:
    """
    Execute a bulk operation on a list of items with confirmation and progress.
    
    Args:
        items: List of items to operate on (usually file data dicts)
        operation_func: Function that takes an item and returns (success: bool, message: str)
        operation_name: Name of the operation (e.g., "Delete", "Restore")
        parent: Parent widget for dialogs
        item_display_func: Optional function to format items for display
        confirmation_message: Optional custom confirmation message
    
    Returns:
        Tuple of (successful_count, failed_count, failed_items_list)
        where failed_items_list is [(item_name, error_message), ...]
    """
    
    if not items:
        QMessageBox.warning(parent, "No Items Selected", "Please select at least one item.")
        return 0, 0, []
    
    # Show confirmation dialog
    confirm_dialog = BulkOperationDialog(
        parent=parent,
        operation_name=operation_name,
        items=items,
        item_display_func=item_display_func,
        confirmation_message=confirmation_message
    )
    
    if confirm_dialog.exec() != QDialog.DialogCode.Accepted or not confirm_dialog.confirmed:
        return 0, 0, []  # User cancelled
    
    # Show progress dialog
    progress_dialog = BulkProgressDialog(
        parent=parent,
        operation_name=operation_name,
        total_items=len(items)
    )
    progress_dialog.show()
    
    # Process items
    successful = 0
    failed = 0
    failed_items = []
    
    for idx, item in enumerate(items):
        item_name = item.get('filename', str(item)) if isinstance(item, dict) else str(item)
        
        try:
            success, message = operation_func(item)
            
            if success:
                successful += 1
            else:
                failed += 1
                failed_items.append((item_name, message))
        
        except Exception as e:
            failed += 1
            failed_items.append((item_name, str(e)))
        
        # Update progress
        progress_dialog.update_progress(
            idx + 1,
            f"Processing: {item_name} ({idx + 1}/{len(items)})"
        )
    
    # Mark as complete
    progress_dialog.complete(successful, failed)
    progress_dialog.exec()
    
    # Show summary if there were failures
    if failed > 0:
        error_details = "\n".join([f"• {name}: {error}" for name, error in failed_items[:10]])
        if len(failed_items) > 10:
            error_details += f"\n... and {len(failed_items) - 10} more"
        
        QMessageBox.warning(
            parent,
            f"Bulk {operation_name} Completed with Errors",
            f"Successfully processed {successful} of {len(items)} item(s).\n\n"
            f"Failed items:\n{error_details}"
        )
    
    return successful, failed, failed_items


def get_selected_files_from_table(table_widget) -> List[Dict]:
    """
    Extract selected file data from a QTableWidget.
    
    Assumes table has columns: [Filename, Time, Extension, Actions]
    
    Args:
        table_widget: QTableWidget instance
    
    Returns:
        List of dictionaries with file data from selected rows
    """
    selected_files = []
    selected_rows = set()
    
    # Get unique selected rows
    for item in table_widget.selectedItems():
        selected_rows.add(item.row())
    
    # Extract data from each selected row
    for row in sorted(selected_rows):
        filename_item = table_widget.item(row, 0)
        time_item = table_widget.item(row, 1)
        extension_item = table_widget.item(row, 2)
        
        if filename_item:
            file_data = {
                'filename': filename_item.text(),
                'time': time_item.text() if time_item else '',
                'extension': extension_item.text() if extension_item else ''
            }
            selected_files.append(file_data)
    
    return selected_files
