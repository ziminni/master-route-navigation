"""
Add Collection Dialog

Modal popup for creating new document collections.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from ...utils.icon_utils import IconLoader


class AddCollectionDialog(QDialog):
    """
    Add Collection Dialog - Modal popup for creating new collections
    
    This dialog provides a form interface for creating collections with:
    - Collection name input
    - Icon preview
    - Create action button
    
    Signals:
        collection_created: Emitted when a collection is successfully created
    
    Args:
        parent (QWidget): Parent widget (typically AdminDash)
    """
    
    # Signal emitted when collection is created
    collection_created = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)  # Block interaction with parent window
        self.setWindowTitle("Create Collection")
        self.setFixedSize(400, 550)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI components"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        
        # ========== TITLE ==========
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_label = QLabel("Create New Collection")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_layout.addWidget(title_label)
        main_layout.addLayout(title_layout)
        
        # ========== FOLDER ICON ==========
        icon_layout = QHBoxLayout()
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        folder_icon = IconLoader.create_icon_label(
            "folder1.png", 
            size=(64, 64), 
            alignment=Qt.AlignmentFlag.AlignCenter
        )
        icon_layout.addWidget(folder_icon)
        main_layout.addLayout(icon_layout)
        
        # ========== COLLECTION NAME INPUT ==========
        name_label = QLabel("Collection Name:")
        main_layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter collection name...")
        self.name_input.setMinimumHeight(35)
        main_layout.addWidget(self.name_input)
        
        # ========== DESCRIPTION (Optional) ==========
        desc_label = QLabel("Description (Optional):")
        main_layout.addWidget(desc_label)
        
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Enter description...")
        self.description_input.setMinimumHeight(35)
        main_layout.addWidget(self.description_input)
        
        main_layout.addStretch()
        
        # ========== BUTTONS ==========
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        create_btn = QPushButton("Create Collection")
        create_btn.clicked.connect(self.handle_create)
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(create_btn)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def handle_create(self):
        """Handle create button click"""
        collection_name = self.name_input.text().strip()
        description = self.description_input.text().strip()
        
        # Validate input
        if not collection_name:
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Please enter a collection name."
            )
            return
        
        # Import service here to avoid circular imports
        from ...services.document_crud_service import DocumentCRUDService

        username = getattr(self.parent(), 'username', 'admin')
        
        # Create the collection
        crud_service = DocumentCRUDService()
        # result = crud_service.create_collection(collection_name, icon="folder.png")
        result = crud_service.create_collection(
            collection_name,
            icon="folder1.png",
            created_by=username,
            description=description
        )
        
        if result.get("success"):
            # Emit signal with collection data
            collection_data = result.get("collection")
            self.collection_created.emit(collection_data)
            
            QMessageBox.information(
                self,
                "Success",
                f"Collection '{collection_name}' created successfully!"
            )
            self.accept()  # Close dialog with success status
        else:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to create collection: {result.get('error', 'Unknown error')}"
            )
    
    def get_collection_data(self):
        """
        Get the collection data entered by the user.
        
        Returns:
            dict: Collection data with name and description
        """
        return {
            "name": self.name_input.text().strip(),
            "description": self.description_input.text().strip()
        }
