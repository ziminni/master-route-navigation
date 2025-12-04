"""
Category Dialog - Add New Category

Allows admin to create new document categories with:
- Category name
- Optional description
- Display order
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QSpinBox, QFormLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal


class CategoryDialog(QDialog):
    """
    Dialog for creating new document categories.
    
    Signals:
        category_created(dict): Emitted when category is successfully created
    """
    
    category_created = pyqtSignal(dict)  # category data
    
    def __init__(self, document_service, parent=None):
        """
        Initialize category dialog.
        
        Args:
            document_service: DocumentService instance for API calls
            parent: Parent widget
        """
        super().__init__(parent)
        self.document_service = document_service
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Add New Category")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Create Document Category")
        header.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                color: #2196F3;
            }
        """)
        layout.addWidget(header)
        
        # Form fields
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Category name (required)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Academic Resources")
        self.name_input.textChanged.connect(self._validate_form)
        form_layout.addRow("Category Name *:", self.name_input)
        
        # Description (optional)
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Brief description of this category...")
        self.description_input.setMaximumHeight(80)
        form_layout.addRow("Description:", self.description_input)
        
        # Display order
        self.order_input = QSpinBox()
        self.order_input.setRange(0, 999)
        self.order_input.setValue(0)
        self.order_input.setToolTip("Lower numbers appear first in the list")
        form_layout.addRow("Display Order:", self.order_input)
        
        layout.addLayout(form_layout)
        
        # Info label
        info_label = QLabel("* Required field")
        info_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        layout.addWidget(info_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)
        
        self.btn_create = QPushButton("Create Category")
        self.btn_create.setEnabled(False)
        self.btn_create.clicked.connect(self._create_category)
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
    
    def _validate_form(self):
        """Validate form and enable/disable create button."""
        name = self.name_input.text().strip()
        self.btn_create.setEnabled(len(name) > 0)
    
    def _create_category(self):
        """Validate inputs and create category via API."""
        # Validate category name
        category_name = self.name_input.text().strip()
        if not category_name:
            QMessageBox.warning(
                self,
                "Missing Category Name",
                "Please enter a category name."
            )
            return
        
        # Get optional fields
        description = self.description_input.toPlainText().strip()
        display_order = self.order_input.value()
        
        # Show loading state
        self.btn_create.setText("Creating...")
        self.btn_create.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.name_input.setEnabled(False)
        self.description_input.setEnabled(False)
        self.order_input.setEnabled(False)
        
        # Create category via API
        result = self.document_service.create_category(
            name=category_name,
            icon='',
            description=description if description else '',
            display_order=display_order
        )
        
        # Reset button states
        self.btn_create.setText("Create Category")
        self.btn_create.setEnabled(True)
        self.btn_cancel.setEnabled(True)
        self.name_input.setEnabled(True)
        self.description_input.setEnabled(True)
        self.order_input.setEnabled(True)
        
        if result['success']:
            QMessageBox.information(
                self,
                "Success",
                f"Category '{category_name}' created successfully!"
            )
            
            # Emit signal with new category data
            self.category_created.emit(result['data'])
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Error Creating Category",
                f"Failed to create category:\n{result.get('error', 'Unknown error')}"
            )
