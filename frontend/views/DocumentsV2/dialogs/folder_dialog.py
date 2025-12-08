"""
Folder Dialog - Create New Folder

Simple dialog for creating a new folder with:
- Folder name input
- Category selection
- Description (optional)

Usage:
    dialog = FolderDialog(categories, document_service, current_folder_id)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        print("Folder created successfully")
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QTextEdit, QPushButton, QHBoxLayout, QLabel, QMessageBox
)
from PyQt6.QtCore import pyqtSignal


class FolderDialog(QDialog):
    """
    Dialog for creating a new folder.
    
    Signals:
        folder_created: Emitted when folder is created successfully
    """
    
    folder_created = pyqtSignal(dict)  # Emits created folder data
    
    def __init__(self, categories: list, document_service, 
                 current_folder_id: int = None, parent=None):
        """
        Initialize folder creation dialog.
        
        Args:
            categories (list): List of category dicts from API
            document_service: DocumentService instance
            current_folder_id (int): Current folder ID (will be parent)
            parent: Parent widget
        """
        super().__init__(parent)
        self.categories = categories
        self.document_service = document_service
        self.current_folder_id = current_folder_id
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI."""
        self.setWindowTitle("Create New Folder")
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Create New Folder")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title_label)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Folder name (required)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter folder name")
        form_layout.addRow("Folder Name *:", self.name_input)
        
        # Category dropdown (required)
        self.category_combo = QComboBox()
        self.category_combo.addItem("-- Select Category --", None)
        for cat in self.categories:
            name = cat.get('name', 'Unknown')
            self.category_combo.addItem(name, cat['id'])
        form_layout.addRow("Category *:", self.category_combo)
        
        # Description (optional)
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Optional description...")
        self.description_input.setMaximumHeight(80)
        form_layout.addRow("Description:", self.description_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)
        
        self.btn_create = QPushButton("Create Folder")
        self.btn_create.clicked.connect(self._create_folder)
        self.btn_create.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        button_layout.addWidget(self.btn_create)
        
        layout.addLayout(button_layout)
    
    def _create_folder(self):
        """Validate inputs and create folder."""
        # Validate folder name
        folder_name = self.name_input.text().strip()
        if not folder_name:
            QMessageBox.warning(
                self,
                "Missing Folder Name",
                "Please enter a folder name."
            )
            return
        
        # Validate category
        category_id = self.category_combo.currentData()
        if category_id is None:
            QMessageBox.warning(
                self,
                "Missing Category",
                "Please select a category."
            )
            return
        
        # Get optional fields
        description = self.description_input.toPlainText().strip()
        
        # Show loading state
        self.btn_create.setText("Creating...")
        self.btn_create.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.name_input.setEnabled(False)
        self.category_combo.setEnabled(False)
        self.description_input.setEnabled(False)
        
        # Create folder via API
        result = self.document_service.create_folder(
            name=folder_name,
            category_id=category_id,
            parent_id=self.current_folder_id,
            description=description
        )
        
        # Reset button states
        self.btn_create.setText("Create Folder")
        self.btn_create.setEnabled(True)
        self.btn_cancel.setEnabled(True)
        self.name_input.setEnabled(True)
        self.category_combo.setEnabled(True)
        self.description_input.setEnabled(True)
        
        if result['success']:
            QMessageBox.information(
                self,
                "Success",
                f"Folder '{folder_name}' created successfully!"
            )
            self.folder_created.emit(result['data'])
            self.accept()
        else:
            error_msg = result.get('error', 'Unknown error')
            QMessageBox.critical(
                self,
                "Error Creating Folder",
                f"Failed to create folder:\n{error_msg}"
            )
