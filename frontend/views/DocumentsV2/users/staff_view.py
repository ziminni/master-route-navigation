"""
Staff Document Management View

Provides document management for staff/org officers:
- Upload documents (requires approval)
- View own pending documents
- View all approved documents
"""

from PyQt6.QtWidgets import QLabel, QWidget, QVBoxLayout, QPushButton
from ..DocumentsV2 import DocumentsV2View


class StaffDocumentView(DocumentsV2View):
    """
    Staff view with limited upload permissions.
    
    Staff can:
    - Upload documents (pending approval)
    - View own documents
    - View all approved documents
    - See approval status
    """
    
    def __init__(self, username: str, roles: list, primary_role: str, token: str, parent=None):
        """Initialize staff document view."""
        super().__init__(username, roles, primary_role, token, parent)
        self.setWindowTitle(f"CISC Documents - Staff - {self.username}")
        
        # Extend cache for staff-specific views
        self.cache['my_uploads'] = {'data': None, 'timestamp': None}
        self.cache['pending_approval'] = {'data': None, 'timestamp': None}
        
        # Add staff-specific features
        self._add_staff_tools()
    
    def _add_staff_tools(self):
        """Add staff tools section to sidebar."""
        # Add separator in sidebar
        staff_label = QLabel("STAFF TOOLS")
        staff_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #FF9800;
                padding: 10px 10px 5px 10px;
                background-color: #FFF3E0;
                border-bottom: 2px solid #FF9800;
            }
        """)
        
        # Insert staff section after navigation items
        sidebar_layout = self.sidebar.layout()
        sidebar_layout.insertWidget(3, staff_label)
        
        # Add staff navigation buttons
        staff_buttons = QWidget()
        staff_layout = QVBoxLayout(staff_buttons)
        staff_layout.setContentsMargins(5, 5, 5, 5)
        staff_layout.setSpacing(2)
        
        # My Uploads button
        btn_my_uploads = QPushButton("My Uploads")
        btn_my_uploads.setStyleSheet(self._get_staff_button_style())
        btn_my_uploads.clicked.connect(lambda: self._handle_navigation_change('my_uploads', None))
        staff_layout.addWidget(btn_my_uploads)
        
        # Pending Approval button
        btn_pending = QPushButton("Pending Approval")
        btn_pending.setStyleSheet(self._get_staff_button_style())
        btn_pending.clicked.connect(lambda: self._handle_navigation_change('pending_approval', None))
        staff_layout.addWidget(btn_pending)
        
        sidebar_layout.insertWidget(4, staff_buttons)
    
    def _get_staff_button_style(self) -> str:
        """Get stylesheet for staff buttons."""
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
                background-color: #FFF3E0;
            }
            QPushButton:pressed {
                background-color: #FFE0B2;
            }
        """
    
    def _handle_navigation_change(self, nav_type: str, item_id: int):
        """
        Override navigation handler to support staff views.
        
        Args:
            nav_type (str): Navigation type
            item_id (int): Item ID (for categories)
        """
        # Handle staff-specific navigation
        if nav_type == 'my_uploads':
            self._show_my_uploads()
            return
        elif nav_type == 'pending_approval':
            self._show_pending_approval()
            return
        
        # Fall back to parent navigation
        super()._handle_navigation_change(nav_type, item_id)
    
    def _show_my_uploads(self):
        """Show documents uploaded by this staff member."""
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
    
    def _show_pending_approval(self):
        """Show documents pending approval."""
        self.current_view = 'pending_approval'
        self.current_folder_id = None
        self.current_category_id = None
        
        self.breadcrumb.reset()
        self.breadcrumb.set_path([{'id': None, 'name': 'Pending Approval'}])
        
        # Try cache first
        cached_data, is_valid = self._get_from_cache('pending_approval', 'pending_approval')
        if is_valid:
            self.documents = cached_data
            self._display_documents_immediately()
            self.set_status(f"Loaded {len(self.documents)} document(s) from cache")
            return
        
        from ..workers import APIWorker
        
        self._show_loading(True)
        self.set_status("Loading pending documents...")
        
        # Load async - filter own documents with pending status
        def get_pending():
            result = self.document_service.get_my_documents()
            if result['success']:
                # Filter only pending documents
                pending = [doc for doc in result['data'] 
                          if doc.get('approval_status') == 'pending']
                return {'success': True, 'data': pending}
            return result
        
        worker = APIWorker(get_pending)
        worker.finished.connect(self._on_pending_approval_loaded)
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        worker.error.connect(lambda err: self._on_load_error("pending documents", err))
        worker.error.connect(lambda: self._cleanup_worker(worker))
        self.active_workers.append(worker)
        worker.start()
    
    def _on_pending_approval_loaded(self, result: dict):
        """Handle pending approval load completion."""
        if result['success']:
            self.documents = result['data']
            
            # Save to cache
            self._save_to_cache('pending_approval', self.documents, 'pending_approval')
            
            if not self.documents:
                self._show_empty_state('pending_approval')
            else:
                self._display_documents_immediately()
                self.content_stack.setCurrentIndex(0)
            self._show_loading(False)
            self.set_status(f"Loaded {len(self.documents)} document(s) pending approval")
        else:
            self._on_load_error("pending documents", result.get('error', 'Unknown error'))
    
    def _on_load_error(self, context: str, error_msg: str):
        """Handle load error for staff views."""
        self._show_loading(False)
        self.show_error(f"Failed to load {context}", error_msg)
        self._show_empty_state('error')
