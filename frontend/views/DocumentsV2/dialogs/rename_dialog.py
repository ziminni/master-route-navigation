"""
Rename Dialog

Simple dialog for renaming documents and folders.

Features:
- Pre-filled current name
- Input validation
- Character limit
- Real-time validation feedback

Usage:
    dialog = RenameDialog(item_id, current_name, item_type, service, parent)
    if dialog.exec():
        new_name = dialog.get_new_name()
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QMessageBox
)
from PyQt6.QtCore import Qt


class RenameDialog(QDialog):
    """
    Dialog for renaming documents and folders.
    
    Provides a simple input field with validation.
    """
    
    def __init__(self, item_id: int, current_name: str, item_type: str, 
                 document_service, parent=None):
        """
        Initialize rename dialog.
        
        Args:
            item_id (int): ID of item to rename
            current_name (str): Current name
            item_type (str): Type of item ('document' or 'folder')
            document_service: Service for API calls
            parent: Parent widget
        """
        super().__init__(parent)
        self.item_id = item_id
        self.current_name = current_name
        self.item_type = item_type
        self.document_service = document_service
        
        self.new_name = current_name
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI."""
        item_label = "Document" if self.item_type == 'document' else "Folder"
        self.setWindowTitle(f"Rename {item_label}")
        self.setModal(True)
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel(f"Rename {item_label}")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Current name display
        current_layout = QHBoxLayout()
        current_layout.addWidget(QLabel("Current name:"))
        current_name_label = QLabel(self.current_name)
        current_name_label.setStyleSheet("color: #666; font-style: italic;")
        current_layout.addWidget(current_name_label, 1)
        layout.addLayout(current_layout)
        
        # New name input
        name_layout = QVBoxLayout()
        name_label = QLabel("New name:")
        name_layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setText(self.current_name)
        self.name_input.setPlaceholderText(f"Enter new {item_label.lower()} name...")
        self.name_input.setMaxLength(255)
        self.name_input.textChanged.connect(self._validate_input)
        self.name_input.selectAll()  # Select all text for easy replacement
        self.name_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
        """)
        name_layout.addWidget(self.name_input)
        
        # Validation feedback
        self.validation_label = QLabel("")
        self.validation_label.setStyleSheet("color: #f44336; font-size: 12px;")
        self.validation_label.setWordWrap(True)
        name_layout.addWidget(self.validation_label)
        
        layout.addLayout(name_layout)
        
        # Character count
        self.char_count_label = QLabel(f"{len(self.current_name)}/255 characters")
        self.char_count_label.setStyleSheet("color: #999; font-size: 11px;")
        self.char_count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.char_count_label)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
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
        
        # Rename button
        self.rename_btn = QPushButton("Rename")
        self.rename_btn.clicked.connect(self._on_rename_clicked)
        self.rename_btn.setDefault(True)
        self.rename_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        button_layout.addWidget(self.rename_btn)
        
        layout.addLayout(button_layout)
        
        # Initial validation
        self._validate_input()
    
    def _validate_input(self):
        """Validate the input and update UI feedback."""
        new_name = self.name_input.text().strip()
        char_count = len(new_name)
        
        # Update character count
        self.char_count_label.setText(f"{char_count}/255 characters")
        
        # Validation checks
        if not new_name:
            self.validation_label.setText("Name cannot be empty")
            self.rename_btn.setEnabled(False)
            return
        
        if new_name == self.current_name:
            self.validation_label.setText("Name is unchanged")
            self.rename_btn.setEnabled(False)
            return
        
        # Check for invalid characters (basic validation)
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            if char in new_name:
                self.validation_label.setText(f"Name cannot contain: {' '.join(invalid_chars)}")
                self.rename_btn.setEnabled(False)
                return
        
        # All valid
        self.validation_label.setText("")
        self.rename_btn.setEnabled(True)
        self.new_name = new_name
    
    def _on_rename_clicked(self):
        """Handle rename button click."""
        new_name = self.name_input.text().strip()
        
        if not new_name or new_name == self.current_name:
            return
        
        # Confirm rename
        item_label = "document" if self.item_type == 'document' else "folder"
        reply = QMessageBox.question(
            self,
            "Confirm Rename",
            f"Rename {item_label} from '{self.current_name}' to '{new_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.accept()
    
    def get_new_name(self) -> str:
        """
        Get the new name entered by user.
        
        Returns:
            str: New name
        """
        return self.new_name
