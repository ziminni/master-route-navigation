"""
Student Document Management View

Provides read-only document access for students:
- View approved documents
- Download documents
- Search and filter
- No upload permissions
"""

from PyQt6.QtWidgets import QMessageBox, QLabel, QWidget, QVBoxLayout, QPushButton
from ..DocumentsV2 import DocumentsV2View


class StudentDocumentView(DocumentsV2View):
    """
    Student view with read-only access.
    
    Students can:
    - View approved documents
    - Download documents
    - Search and filter
    - Browse by category/folder
    """
    
    def __init__(self, username: str, roles: list, primary_role: str, token: str, parent=None):
        """Initialize student document view."""
        super().__init__(username, roles, primary_role, token, parent)
        self.setWindowTitle(f"CISC Documents - {self.username}")
        
        # Extend cache for student-specific views
        self.cache['starred'] = {'data': None, 'timestamp': None}
        
        # Hide upload/folder buttons for students
        self._disable_student_actions()
        
        # Add student-specific features
        self._add_student_tools()
    
    def _disable_student_actions(self):
        """Disable upload and folder creation for students."""
        # Hide upload and new folder buttons
        if hasattr(self, 'toolbar') and self.toolbar:
            self.toolbar.btn_upload.setVisible(False)
            self.toolbar.btn_new_folder.setVisible(False)
    
    def _add_student_tools(self):
        """Add student tools section to sidebar."""
        # Add separator in sidebar
        student_label = QLabel("STUDENT TOOLS")
        student_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #9C27B0;
                padding: 10px 10px 5px 10px;
                background-color: #F3E5F5;
                border-bottom: 2px solid #9C27B0;
            }
        """)
        
        # Insert student section after navigation items
        sidebar_layout = self.sidebar.layout()
        sidebar_layout.insertWidget(3, student_label)
        
        # Add student navigation buttons
        student_buttons = QWidget()
        student_layout = QVBoxLayout(student_buttons)
        student_layout.setContentsMargins(5, 5, 5, 5)
        student_layout.setSpacing(2)
        
        # Starred Documents button
        btn_starred = QPushButton("Starred Documents")
        btn_starred.setStyleSheet(self._get_student_button_style())
        btn_starred.clicked.connect(lambda: self._handle_navigation_change('starred', None))
        student_layout.addWidget(btn_starred)
        
        sidebar_layout.insertWidget(4, student_buttons)
    
    def _get_student_button_style(self) -> str:
        """Get stylesheet for student buttons."""
        return """
            QPushButton {
                text-align: left;
                padding: 8px 12px;
                border: none;
                background-color: transparent;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #F3E5F5;
            }
            QPushButton:pressed {
                background-color: #E1BEE7;
            }
        """
    
    def _handle_navigation_change(self, nav_type: str, item_id: int):
        """
        Override navigation handler to support student views.
        
        Args:
            nav_type (str): Navigation type
            item_id (int): Item ID (for categories)
        """
        # Student view uses parent's starred implementation
        # No special handling needed - parent class already handles 'starred' view
        
        # Fall back to parent navigation (includes starred handling)
        super()._handle_navigation_change(nav_type, item_id)
    
    def _open_upload_dialog(self):
        """Override to prevent students from uploading."""
        QMessageBox.warning(
            self,
            "Permission Denied",
            "Students do not have permission to upload documents.\n\n"
            "Please contact faculty or administrators for assistance."
        )
    
    def _open_folder_dialog(self):
        """Override to prevent students from creating folders."""
        QMessageBox.warning(
            self,
            "Permission Denied",
            "Students do not have permission to create folders.\n\n"
            "Please contact faculty or administrators for assistance."
        )
