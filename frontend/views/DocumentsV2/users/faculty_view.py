"""
Faculty Document Management View

Provides document management for faculty members:
- Upload documents
- Manage own documents
- View approval status
- No permanent delete
"""

from PyQt6.QtWidgets import QLabel, QWidget, QVBoxLayout, QPushButton
from ..DocumentsV2 import DocumentsV2View


class FacultyDocumentView(DocumentsV2View):
    """
    Faculty view with enhanced permissions.
    
    Faculty can:
    - Upload documents without approval
    - Edit/delete own documents
    - View all approved documents
    - See upload statistics
    """
    
    def __init__(self, username: str, roles: list, primary_role: str, token: str, parent=None):
        """Initialize faculty document view."""
        super().__init__(username, roles, primary_role, token, parent)
        self.setWindowTitle(f"CISC Documents - Faculty - {self.username}")
        
        # Extend cache for faculty-specific views
        self.cache['my_uploads'] = {'data': None, 'timestamp': None}
        
        # Add faculty-specific features
        self._add_faculty_tools()
    
    def _add_faculty_tools(self):
        """Add faculty tools section to sidebar."""
        # Add separator in sidebar
        faculty_label = QLabel("FACULTY TOOLS")
        faculty_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #2196F3;
                padding: 10px 10px 5px 10px;
                background-color: #E3F2FD;
                border-bottom: 2px solid #2196F3;
            }
        """)
        
        # Insert faculty section after navigation items
        sidebar_layout = self.sidebar.layout()
        sidebar_layout.insertWidget(3, faculty_label)
        
        # Add faculty navigation buttons
        faculty_buttons = QWidget()
        faculty_layout = QVBoxLayout(faculty_buttons)
        faculty_layout.setContentsMargins(5, 5, 5, 5)
        faculty_layout.setSpacing(2)
        
        # My Uploads button
        btn_my_uploads = QPushButton("My Uploads")
        btn_my_uploads.setStyleSheet(self._get_faculty_button_style())
        btn_my_uploads.clicked.connect(lambda: self._handle_navigation_change('my_uploads', None))
        faculty_layout.addWidget(btn_my_uploads)
        
        sidebar_layout.insertWidget(4, faculty_buttons)
    
    def _get_faculty_button_style(self) -> str:
        """Get stylesheet for faculty buttons."""
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
                background-color: #E3F2FD;
            }
            QPushButton:pressed {
                background-color: #BBDEFB;
            }
        """
    
    def _handle_navigation_change(self, nav_type: str, item_id: int):
        """
        Override navigation handler to support faculty views.
        
        Args:
            nav_type (str): Navigation type
            item_id (int): Item ID (for categories)
        """
        # Handle faculty-specific navigation
        if nav_type == 'my_uploads':
            self._show_my_uploads()
            return
        
        # Fall back to parent navigation
        super()._handle_navigation_change(nav_type, item_id)
    
    def _show_my_uploads(self):
        """Show documents uploaded by this faculty member."""
        self.current_view = 'my_uploads'
        self.current_folder_id = None
        self.current_category_id = None
        
        self.breadcrumb.reset()
        self.breadcrumb.set_path([{'id': None, 'name': 'My Uploads'}])
        
        # Try cache first
        cached_data, is_valid = self._get_from_cache('my_uploads', 'my_uploads')
        if is_valid:
            self.documents = cached_data
            self._display_documents_immediately()
            self.set_status(f"Loaded {len(self.documents)} document(s) from cache")
            return
        
        from ..workers import APIWorker
        
        self._show_loading(True)
        self.set_status("Loading my uploads...")
        
        # Load async
        worker = APIWorker(self.document_service.get_my_documents)
        worker.finished.connect(self._on_my_uploads_loaded)
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        worker.error.connect(lambda err: self._on_load_error("my uploads", err))
        worker.error.connect(lambda: self._cleanup_worker(worker))
        self.active_workers.append(worker)
        worker.start()
    
    def _on_my_uploads_loaded(self, result: dict):
        """Handle my uploads load completion."""
        if result['success']:
            self.documents = result['data']
            
            # Save to cache
            self._save_to_cache('my_uploads', self.documents, 'my_uploads')
            
            if not self.documents:
                self._show_empty_state('my_uploads')
            else:
                self._display_documents_immediately()
                self.content_stack.setCurrentIndex(0)
            self._show_loading(False)
            self.set_status(f"Loaded {len(self.documents)} document(s)")
        else:
            self._on_load_error("my uploads", result.get('error', 'Unknown error'))
    
    def _on_load_error(self, context: str, error_msg: str):
        """Handle load error for faculty views."""
        self._show_loading(False)
        self.show_error(f"Failed to load {context}", error_msg)
        self._show_empty_state('error')
