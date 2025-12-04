"""
Main Window - DocumentsV2 Application

The main application window that integrates all components:
- Sidebar for navigation
- Toolbar for actions
- Breadcrumb bar for folder navigation
- File list view for displaying documents
- Handles all user interactions and API calls

This is the entry point widget for the Documents module.

Usage:
    window = DocumentsV2MainWindow(username, roles, primary_role, token)
    window.show()
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QMessageBox,
    QSplitter, QLabel, QStackedWidget, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer
from datetime import datetime, timedelta

from .widgets import Sidebar, Toolbar, FileListView, BreadcrumbBar
from .dialogs import UploadDialog, FolderDialog, DownloadDialog, MoveDialog, RenameDialog
from .services import DocumentService
from .workers import APIWorker, DownloadWorker
from .utils import EmptyStateWidget, EmptyStateFactory


class DocumentsV2View(QWidget):
    """
    Main window for the Documents V2 application.
    
    Provides a complete document management interface with Google Drive-like features.
    Handles user authentication, API communication, and UI coordination.
    """
    
    def __init__(self, username: str, roles: list, primary_role: str, token: str, parent=None):
        """
        Initialize the main window.
        
        Args:
            username (str): Logged-in username
            roles (list): List of user roles
            primary_role (str): Primary role (admin, faculty, staff, student)
            token (str): JWT authentication token
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        
        # Store user session data
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        
        # Initialize service
        self.document_service = DocumentService(token=token)
        
        # State management
        self.current_view = 'mydrive'  # Current navigation view
        self.current_folder_id = None  # Current folder ID
        self.current_category_id = None  # Current category filter
        self.current_sort = '-uploaded_at'  # Current sort field
        self.current_search = ''  # Current search query
        
        # Data caches
        self.categories = []
        self.folders = []
        self.documents = []
        
        # Cache system with TTL (Time To Live)
        self.cache = {
            'documents': {},  # Key: view_type+filters hash, Value: {data, timestamp}
            'folders': {},    # Key: parent_id, Value: {data, timestamp}
            'categories': {'data': None, 'timestamp': None},
            'recent': {'data': None, 'timestamp': None},
            'trash': {'data': None, 'timestamp': None},
            'starred': {'data': None, 'timestamp': None},
        }
        self.cache_ttl = timedelta(minutes=5)  # Cache valid for 5 minutes
        
        # Loading state
        self.is_loading = False
        self._loading_lock = False  # Prevent simultaneous loads
        
        # Worker threads for async operations
        self.current_worker = None
        self.active_workers = []  # Keep references to prevent premature deletion
        
        # Navigation queue system to prevent spam-clicking chaos
        self._pending_navigation = None  # Store the most recent navigation request
        self._navigation_timer = QTimer()
        self._navigation_timer.setSingleShot(True)
        self._navigation_timer.timeout.connect(self._process_pending_navigation)
        
        # Debounce timer for search
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)
        
        # Initialize UI
        self.init_ui()
        
        # Load initial data
        self.load_categories()
        self.load_folders()
        self.load_documents()
    
    def closeEvent(self, event):
        """Clean up workers before closing."""
        self._cleanup_workers()
        super().closeEvent(event)
    
    def _cleanup_workers(self):
        """Stop and clean up all active worker threads."""
        # Cancel current worker
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.cancel()
            self.current_worker.wait(1000)  # Wait up to 1 second
            if self.current_worker.isRunning():
                self.current_worker.terminate()
        
        # Clean up all active workers
        for worker in self.active_workers:
            if worker.isRunning():
                worker.cancel()
                worker.wait(1000)
                if worker.isRunning():
                    worker.terminate()
        
        self.active_workers.clear()
    
    def _cleanup_worker(self, worker):
        """Remove worker from active list after completion."""
        if worker in self.active_workers:
            self.active_workers.remove(worker)
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle(f"CISC Documents - {self.username}")
        self.setMinimumSize(1200, 700)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ========== Top Section: Toolbar + Breadcrumb ==========
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)
        
        # Toolbar
        self.toolbar = Toolbar()
        self.toolbar.action_triggered.connect(self._handle_toolbar_action)
        self.toolbar.sort_changed.connect(self._handle_sort_changed)
        self.toolbar.search_requested.connect(self._handle_search)
        
        # Hide upload/new folder buttons for students (students can ONLY download)
        if self.primary_role == 'student':
            self.toolbar.btn_upload.setVisible(False)
            self.toolbar.btn_new_folder.setVisible(False)
        
        top_layout.addWidget(self.toolbar)
        
        # Breadcrumb bar
        self.breadcrumb = BreadcrumbBar()
        self.breadcrumb.breadcrumb_clicked.connect(self._handle_breadcrumb_click)
        top_layout.addWidget(self.breadcrumb)
        
        main_layout.addWidget(top_widget)
        
        # ========== Middle Section: Sidebar + Content ==========
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.navigation_changed.connect(self._handle_navigation_change)
        content_splitter.addWidget(self.sidebar)
        
        # Stacked widget for content/loading/empty states
        self.content_stack = QStackedWidget()
        
        # File list (pass user role for permission-based context menus)
        self.file_list = FileListView(user_role=self.primary_role)
        self.file_list.item_double_clicked.connect(self._handle_item_double_click)
        self.file_list.context_menu_action.connect(self._handle_context_menu_action)
        self.file_list.selection_changed.connect(self._handle_selection_changed)
        self.content_stack.addWidget(self.file_list)  # Index 0
        
        # Loading view
        self.loading_widget = self._create_loading_widget()
        self.content_stack.addWidget(self.loading_widget)  # Index 1
        
        # Empty state view (will be set dynamically)
        self.empty_state_widget = EmptyStateWidget()
        self.empty_state_widget.action_clicked.connect(self._handle_empty_state_action)
        self.content_stack.addWidget(self.empty_state_widget)  # Index 2
        
        content_splitter.addWidget(self.content_stack)
        
        # Set splitter sizes (sidebar 20%, content 80%)
        content_splitter.setSizes([250, 950])
        
        main_layout.addWidget(content_splitter)
        
        # ========== Bottom Section: Status Bar ==========
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("padding: 5px 10px; border-top: 1px solid #ddd; color: #666;")
        main_layout.addWidget(self.status_label)
    
    def _create_loading_widget(self) -> QWidget:
        """Create a loading indicator widget."""
        loading_widget = QWidget()
        loading_layout = QVBoxLayout(loading_widget)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        loading_label = QLabel("Loading...")
        loading_label.setStyleSheet("""
            font-size: 24px;
            color: #666;
            font-weight: bold;
        """)
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_layout.addWidget(loading_label)
        
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 0)  # Indeterminate progress
        progress_bar.setTextVisible(False)
        progress_bar.setMaximumWidth(300)
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 5px;
                background-color: #f0f0f0;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 3px;
            }
        """)
        loading_layout.addWidget(progress_bar)
        
        return loading_widget
    
    def _show_loading(self, show: bool = True):
        """
        Show or hide loading state.
        
        Args:
            show (bool): True to show loading, False to show content
        """
        self.is_loading = show
        if show:
            self.content_stack.setCurrentIndex(1)  # Show loading
            self.toolbar.setEnabled(False)
        else:
            self.content_stack.setCurrentIndex(0)  # Show content
            self.toolbar.setEnabled(True)
    
    def _show_empty_state(self, state_type: str):
        """
        Show appropriate empty state based on view type.
        
        Args:
            state_type (str): Type of empty state to show
        """
        if self.current_search:
            # No search results
            self.empty_state_widget.set_state(
                icon="🔍",
                title="No results found",
                description=f"No documents match '{self.current_search}'.\nTry adjusting your search terms.",
            )
        elif state_type == 'mydrive':
            self.empty_state_widget.set_state(
                icon="📄",
                title="No documents yet",
                description="This folder is empty. Upload your first document to get started.",
                action_text="Upload Document"
            )
        elif state_type == 'recent':
            self.empty_state_widget.set_state(
                icon="🕐",
                title="No recent documents",
                description="Documents you access will appear here for quick reference.",
            )
        elif state_type == 'starred':
            self.empty_state_widget.set_state(
                icon="⭐",
                title="No starred documents",
                description="Star important documents to find them easily later.",
            )
        elif state_type == 'trash':
            self.empty_state_widget.set_state(
                icon="🗑️",
                title="Trash is empty",
                description="Deleted documents will appear here and can be restored within 30 days.",
            )
        elif state_type == 'category':
            category_name = "this category"
            if self.current_category_id:
                cat = next((c for c in self.categories if c.get('id') == self.current_category_id), None)
                if cat:
                    category_name = cat.get('name', 'this category')
            self.empty_state_widget.set_state(
                icon="📂",
                title=f"No documents in {category_name}",
                description="This category is empty. Upload documents to see them here.",
                action_text="Upload Document"
            )
        elif state_type == 'approvals':
            self.empty_state_widget.set_state(
                icon="✅",
                title="No pending approvals",
                description="All documents have been reviewed. New submissions will appear here.",
            )
        elif state_type == 'my_uploads':
            self.empty_state_widget.set_state(
                icon="📤",
                title="No uploads yet",
                description="Documents you upload will appear here.",
                action_text="Upload Document"
            )
        elif state_type == 'pending_approval':
            self.empty_state_widget.set_state(
                icon="⏳",
                title="No pending documents",
                description="Your documents waiting for approval will appear here.",
            )
        elif state_type == 'error':
            self.empty_state_widget.set_state(
                icon="⚠️",
                title="Unable to load documents",
                description="An error occurred while loading documents. Please try again.",
                action_text="Retry"
            )
        else:
            # Default empty state
            self.empty_state_widget.set_state(
                icon="📄",
                title="No documents",
                description="There are no documents to display.",
            )
        
        self.content_stack.setCurrentIndex(2)  # Show empty state
    
    def _handle_empty_state_action(self):
        """Handle action button click from empty state."""
        if self.empty_state_widget.action_button.text() == "Upload Document":
            self._open_upload_dialog()
        elif self.empty_state_widget.action_button.text() == "Retry":
            self.load_documents(force_refresh=True)
    
    # ==================== Cache Management ====================
    
    def _get_cache_key(self, view_type: str, filters: dict = None) -> str:
        """
        Generate cache key from view type and filters.
        
        Args:
            view_type (str): View type (mydrive, recent, etc.)
            filters (dict): Filter parameters
            
        Returns:
            str: Cache key
        """
        if filters:
            filter_str = '_'.join(f"{k}:{v}" for k, v in sorted(filters.items()) if v)
            return f"{view_type}_{filter_str}"
        return view_type
    
    def _is_cache_valid(self, cache_entry: dict) -> bool:
        """
        Check if cache entry is still valid.
        
        Args:
            cache_entry (dict): Cache entry with 'timestamp' key
            
        Returns:
            bool: True if cache is valid
        """
        if not cache_entry or cache_entry.get('timestamp') is None:
            return False
        
        age = datetime.now() - cache_entry['timestamp']
        return age < self.cache_ttl
    
    def _get_from_cache(self, cache_key: str, cache_type: str = 'documents') -> tuple:
        """
        Get data from cache if valid.
        
        Args:
            cache_key (str): Cache key
            cache_type (str): Type of cache ('documents', 'folders', etc.)
            
        Returns:
            tuple: (data, is_valid)
        """
        if cache_type in ['categories', 'recent', 'trash', 'starred']:
            entry = self.cache[cache_type]
        else:
            entry = self.cache[cache_type].get(cache_key, {})
        
        if self._is_cache_valid(entry):
            return entry['data'], True
        return None, False
    
    def _save_to_cache(self, cache_key: str, data: list, cache_type: str = 'documents'):
        """
        Save data to cache with timestamp.
        
        Args:
            cache_key (str): Cache key
            data (list): Data to cache
            cache_type (str): Type of cache
        """
        entry = {
            'data': data,
            'timestamp': datetime.now()
        }
        
        if cache_type in ['categories', 'recent', 'trash', 'starred']:
            self.cache[cache_type] = entry
        else:
            self.cache[cache_type][cache_key] = entry
    
    def invalidate_cache(self, cache_type: str = None, cache_key: str = None):
        """
        Invalidate cache entries.
        
        Args:
            cache_type (str): Specific cache type to invalidate (None for all)
            cache_key (str): Specific key to invalidate (None for all in type)
        """
        if cache_type is None:
            # Clear all caches
            self.cache['documents'].clear()
            self.cache['folders'].clear()
            self.cache['categories'] = {'data': None, 'timestamp': None}
            self.cache['recent'] = {'data': None, 'timestamp': None}
            self.cache['trash'] = {'data': None, 'timestamp': None}
            self.cache['starred'] = {'data': None, 'timestamp': None}
        elif cache_key:
            # Clear specific key
            if cache_type in self.cache and isinstance(self.cache[cache_type], dict):
                self.cache[cache_type].pop(cache_key, None)
        else:
            # Clear entire cache type
            if cache_type in ['categories', 'recent', 'trash', 'starred']:
                self.cache[cache_type] = {'data': None, 'timestamp': None}
            else:
                self.cache[cache_type].clear()
    
    # ==================== Data Loading Methods ====================
    
    def load_categories(self):
        """Load categories from API and populate sidebar asynchronously."""
        # Try cache first
        cached_data, is_valid = self._get_from_cache('categories', 'categories')
        if is_valid:
            self.categories = cached_data
            self.sidebar.load_categories(self.categories)
            return
        
        self.set_status("Loading categories...")
        
        # Load async
        worker = APIWorker(self.document_service.get_categories)
        worker.finished.connect(self._on_categories_loaded)
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        worker.error.connect(lambda err: self.show_error("Failed to load categories", err))
        worker.error.connect(lambda: self._cleanup_worker(worker))
        self.active_workers.append(worker)
        worker.start()
    
    def _on_categories_loaded(self, result: dict):
        """Handle categories load completion."""
        if result['success']:
            self.categories = result['data']
            self._save_to_cache('categories', self.categories, 'categories')
            self.sidebar.load_categories(self.categories)
            self.set_status(f"Loaded {len(self.categories)} categories")
        else:
            self.show_error("Failed to load categories", result['error'])
    
    def load_folders(self, parent_id: int = None):
        """
        Load folders from API asynchronously.
        
        Args:
            parent_id (int): Parent folder ID to filter by (None for all)
        """
        cache_key = str(parent_id) if parent_id else 'root'
        
        # Try cache first
        cached_data, is_valid = self._get_from_cache(cache_key, 'folders')
        if is_valid:
            self.folders = cached_data
            return
        
        # Load async
        worker = APIWorker(self.document_service.get_folders, parent_id=parent_id)
        worker.finished.connect(lambda result: self._on_folders_loaded(result, cache_key))
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        worker.error.connect(lambda err: self.show_error("Failed to load folders", err))
        worker.error.connect(lambda: self._cleanup_worker(worker))
        self.active_workers.append(worker)
        worker.start()
    
    def _on_folders_loaded(self, result: dict, cache_key: str):
        """Handle folders load completion."""
        if result['success']:
            self.folders = result['data']
            self._save_to_cache(cache_key, self.folders, 'folders')
        else:
            self.show_error("Failed to load folders", result['error'])
    
    def load_documents(self, force_refresh: bool = False):
        """
        Load documents based on current view/filters.
        
        Args:
            force_refresh (bool): Force refresh from API, bypassing cache
        """
        print(f"[DocumentsV2] load_documents called - is_loading: {self.is_loading}, _loading_lock: {self._loading_lock}")
        
        # If already loading, ignore this request (prevent spam-clicking chaos)
        if self._loading_lock:
            print("[DocumentsV2] Already loading, ignoring duplicate request")
            return
        
        # Cancel any existing load operation
        if self.is_loading:
            if self.current_worker and self.current_worker.isRunning():
                print("[DocumentsV2] Cancelling existing worker")
                self.current_worker.cancel()
                self.current_worker.wait(500)  # Wait max 500ms
            self.is_loading = False
        
        # Set loading lock to prevent simultaneous loads
        self._loading_lock = True
        
        # Clear documents to prevent showing stale data
        self.documents = []
        
        # Build filters based on current state
        filters = {}
        
        if self.current_search:
            filters['search'] = self.current_search
        
        if self.current_category_id:
            filters['category'] = self.current_category_id
        
        # Always include folder filter to ensure proper hierarchy
        # For root level (no folder), pass empty string to signal root level filtering
        if self.current_view in ['mydrive', 'category']:
            if self.current_folder_id:
                filters['folder'] = self.current_folder_id
            else:
                filters['folder'] = ''
        
        # Add view-specific filters BEFORE cache key generation
        if self.current_view == 'starred':
            # Backend expects 'is_featured' for starred documents
            filters['is_featured'] = True
        
        if self.current_sort:
            filters['ordering'] = self.current_sort
        
        # Generate cache key and determine cache type
        # Special views (recent, trash, starred) use simple cache keys since they have dedicated endpoints
        cache_type = self.current_view if self.current_view in ['recent', 'trash', 'starred'] else 'documents'
        if cache_type in ['recent', 'trash', 'starred']:
            # Use simple view name as cache key for special views
            cache_key = self.current_view
        else:
            # Use filters-based cache key for general document views
            cache_key = self._get_cache_key(self.current_view, filters)
        
        # Show loading state immediately
        self._show_loading(True)
        self.set_status("Preparing documents...")
        
        # Try cache first (unless force refresh)
        if not force_refresh:
            cached_data, is_valid = self._get_from_cache(cache_key, cache_type)
            if is_valid:
                print("[DocumentsV2] Using cached data")
                # Prepare data from cache
                self.documents = cached_data
                # Turn off loading before displaying (display will set correct index)
                self.is_loading = False
                self.toolbar.setEnabled(True)
                self._display_documents_immediately()
                self.set_status(f"Loaded {len(self.documents)} document(s)")
                # Release lock after cache hit
                self._loading_lock = False
                return
        
        # Fetch from API asynchronously
        self.set_status("Loading documents from server...")
        
        # Determine which API function to call based on current view
        if self.current_view == 'mydrive':
            api_function = self.document_service.get_documents
            api_args = (filters,)
        elif self.current_view == 'recent':
            api_function = self.document_service.get_my_recent
            api_args = ()
        elif self.current_view == 'starred':
            # is_featured filter already added above
            api_function = self.document_service.get_documents
            api_args = (filters,)
        elif self.current_view == 'trash':
            api_function = self.document_service.get_trash
            api_args = ()
        elif self.current_view == 'category':
            api_function = self.document_service.get_documents
            api_args = (filters,)
        else:
            api_function = self.document_service.get_documents
            api_args = (filters,)
        
        # Create and start worker
        self.current_worker = APIWorker(api_function, *api_args)
        self.current_worker.finished.connect(lambda result: self._on_documents_loaded(result, cache_key, cache_type))
        self.current_worker.finished.connect(lambda: self._release_loading_lock())
        self.current_worker.finished.connect(lambda: self._cleanup_worker(self.current_worker))
        self.current_worker.error.connect(self._on_documents_load_error)
        self.current_worker.error.connect(lambda: self._release_loading_lock())
        self.current_worker.error.connect(lambda: self._cleanup_worker(self.current_worker))
        self.active_workers.append(self.current_worker)
        self.current_worker.start()
        print("[DocumentsV2] Worker started")
    
    def _on_documents_loaded(self, result: dict, cache_key: str, cache_type: str):
        """
        Handle successful async document load.
        
        Args:
            result (dict): API result
            cache_key (str): Cache key for storing result
            cache_type (str): Cache type
        """
        if result['success']:
            self.documents = result['data']
            
            # Save to cache
            self._save_to_cache(cache_key, self.documents, cache_type)
            
            # Turn off loading before displaying (display will set correct index)
            self.is_loading = False
            self.toolbar.setEnabled(True)
            
            # Display documents (this will set the correct content_stack index)
            self._display_documents_immediately()
            
            self.set_status(f"Loaded {len(self.documents)} document(s)")
        else:
            self._on_documents_load_error(result.get('error', 'Unknown error'))
    
    def _on_documents_load_error(self, error_msg: str):
        """
        Handle async document load error.
        
        Args:
            error_msg (str): Error message
        """
        # Turn off loading state
        self.is_loading = False
        self.toolbar.setEnabled(True)
        
        self.show_error("Failed to load documents", error_msg)
        self._show_empty_state('error')
    
    def _display_documents_immediately(self):
        """Display documents in file list, including folders if applicable."""
        # Add folders to the list if we're in a browsable view
        if self.current_view in ['mydrive', 'category']:
            # Load subfolders for current folder
            folder_cache_key = str(self.current_folder_id) if self.current_folder_id else 'root'
            cached_folders, is_valid = self._get_from_cache(folder_cache_key, 'folders')
            
            if is_valid:
                # Use cached folders
                folders_as_items = []
                for folder in cached_folders:
                    folders_as_items.append({
                        'id': folder['id'],
                        'name': folder['name'],
                        'folder': True,
                        'created_by': folder.get('created_by'),
                        'updated_at': folder.get('updated_at'),
                    })
                all_items = folders_as_items + self.documents
                # Show empty state if no items
                if not all_items:
                    self._show_empty_state(self.current_view)
                else:
                    self.file_list.load_documents(all_items)
                    self.content_stack.setCurrentIndex(0)
            else:
                # Fetch folders in background
                folder_result = self.document_service.get_folders(parent_id=self.current_folder_id)
                if folder_result['success']:
                    self._save_to_cache(folder_cache_key, folder_result['data'], 'folders')
                    folders_as_items = []
                    for folder in folder_result['data']:
                        folders_as_items.append({
                            'id': folder['id'],
                            'name': folder['name'],
                            'folder': True,
                            'created_by': folder.get('created_by'),
                            'updated_at': folder.get('updated_at'),
                        })
                    all_items = folders_as_items + self.documents
                    # Show empty state if no items
                    if not all_items:
                        self._show_empty_state(self.current_view)
                    else:
                        self.file_list.load_documents(all_items)
                        self.content_stack.setCurrentIndex(0)
                else:
                    if not self.documents:
                        self._show_empty_state(self.current_view)
                    else:
                        self.file_list.load_documents(self.documents)
                        self.content_stack.setCurrentIndex(0)
        else:
            # Show empty state if no documents
            if not self.documents:
                self._show_empty_state(self.current_view)
            else:
                self.file_list.load_documents(self.documents)
                self.content_stack.setCurrentIndex(0)
    
    # ==================== Event Handlers ====================
    
    def _handle_toolbar_action(self, action: str):
        """
        Handle toolbar button clicks.
        
        Args:
            action (str): Action name ('upload', 'new_folder', 'refresh')
        """
        if action == 'upload':
            self._open_upload_dialog()
        elif action == 'new_folder':
            self._open_folder_dialog()
        elif action == 'refresh':
            # Invalidate cache and force refresh
            # If currently loading, ignore refresh
            if self._loading_lock:
                print("[DocumentsV2] Currently loading, ignoring refresh")
                return
            self.invalidate_cache()
            self.load_documents(force_refresh=True)
    
    def _handle_sort_changed(self, sort_field: str):
        """
        Handle sort option change with anti-spam protection.
        
        Args:
            sort_field (str): Sort field with optional '-' prefix for descending
        """
        # If currently loading, ignore sort changes
        if self._loading_lock:
            print("[DocumentsV2] Currently loading, ignoring sort change")
            return
        
        self.current_sort = sort_field
        self.load_documents()
    
    def _handle_search(self, query: str):
        """
        Handle search request with debouncing.
        
        Args:
            query (str): Search query string
        """
        self.current_search = query
        # Debounce search - wait 500ms before executing
        self.search_timer.stop()
        self.search_timer.start(500)
    
    def _perform_search(self):
        """Execute the search after debounce delay."""
        self.load_documents(force_refresh=True)
    
    def _handle_navigation_change(self, nav_type: str, item_id: int):
        """
        Handle sidebar navigation change with anti-spam protection.
        
        Args:
            nav_type (str): Navigation type ('mydrive', 'recent', 'starred', 'trash', 'category')
            item_id (int): Item ID (for categories)
        """
        print(f"[DocumentsV2] Navigation requested: {nav_type}, item_id: {item_id}")
        
        # If currently loading, queue this navigation request
        if self._loading_lock:
            print("[DocumentsV2] Currently loading, queueing navigation request")
            self._pending_navigation = (nav_type, item_id)
            # Start/restart timer to process after a short delay
            self._navigation_timer.stop()
            self._navigation_timer.start(100)  # 100ms delay
            return
        
        # Process navigation immediately
        self._process_navigation(nav_type, item_id)
    
    def _process_navigation(self, nav_type: str, item_id: int):
        """
        Process navigation change immediately.
        
        Args:
            nav_type (str): Navigation type
            item_id (int): Item ID
        """
        print(f"[DocumentsV2] Processing navigation: {nav_type}")
        self.current_view = nav_type
        self.current_category_id = item_id if nav_type == 'category' else None
        self.current_folder_id = None  # Reset folder navigation
        
        # Reset breadcrumb for non-browsable views
        if nav_type in ['recent', 'starred', 'trash']:
            self.breadcrumb.reset()
            self.breadcrumb.set_path([{'id': None, 'name': nav_type.capitalize()}])
        else:
            self.breadcrumb.reset()
        
        self.load_documents()
    
    def _process_pending_navigation(self):
        """Process the most recent pending navigation request."""
        if self._pending_navigation and not self._loading_lock:
            print("[DocumentsV2] Processing pending navigation")
            nav_type, item_id = self._pending_navigation
            self._pending_navigation = None
            self._process_navigation(nav_type, item_id)
        elif self._pending_navigation and self._loading_lock:
            # Still loading, try again after a bit
            print("[DocumentsV2] Still loading, retrying pending navigation")
            self._navigation_timer.start(100)
    
    def _release_loading_lock(self):
        """Release the loading lock and process any pending navigation."""
        print("[DocumentsV2] Releasing loading lock")
        self._loading_lock = False
        
        # Check if there's a pending navigation
        if self._pending_navigation:
            print("[DocumentsV2] Found pending navigation, processing after brief delay")
            self._navigation_timer.start(50)  # Small delay before processing next
    
    def _handle_breadcrumb_click(self, folder_id: int, folder_name: str):
        """
        Handle breadcrumb segment click with anti-spam protection.
        
        Args:
            folder_id (int): Folder ID (None for root)
            folder_name (str): Folder name
        """
        print(f"[DocumentsV2] Breadcrumb click: folder_id={folder_id}")
        
        # If currently loading, ignore (breadcrumb clicks should wait)
        if self._loading_lock:
            print("[DocumentsV2] Currently loading, ignoring breadcrumb click")
            return
        
        self.current_folder_id = folder_id
        self.breadcrumb.navigate_to_level(folder_id)
        self.load_documents()
    
    def _handle_item_double_click(self, item_data: dict):
        """
        Handle double-click on file list item with anti-spam protection.
        
        Args:
            item_data (dict): Document or folder data
        """
        if item_data.get('folder'):
            # It's a folder, navigate into it
            # If currently loading, ignore (prevent spam double-clicks)
            if self._loading_lock:
                print("[DocumentsV2] Currently loading, ignoring folder double-click")
                return
            
            folder_id = item_data['id']
            folder_name = item_data['name']
            print(f"[DocumentsV2] Navigating into folder: {folder_name}")
            self.current_folder_id = folder_id
            self.breadcrumb.append_folder(folder_id, folder_name)
            self.load_documents()
        else:
            # It's a document, download it (downloads don't need loading lock)
            doc_id = item_data['id']
            self._download_document(doc_id)
    
    def _handle_context_menu_action(self, action: str, item_id: int):
        """
        Handle context menu action.
        
        Args:
            action (str): Action name
            item_id (int): Document or folder ID
        """
        if action == 'open':
            # Same as double-click
            item = next((d for d in self.documents if d['id'] == item_id), None)
            if item:
                self._handle_item_double_click(item)
        
        elif action == 'download':
            self._download_document(item_id)
        
        elif action == 'move':
            self._move_document(item_id)
        
        elif action == 'rename':
            self._rename_item(item_id)
        
        elif action == 'details':
            self._show_details(item_id)
        
        elif action == 'delete':
            self._delete_document(item_id)
        
        elif action == 'restore':
            self._restore_document(item_id)
        
        elif action == 'delete_permanent':
            self._permanent_delete(item_id)
    
    def _handle_selection_changed(self, selected_ids: list):
        """
        Handle file selection change.
        
        Args:
            selected_ids (list): List of selected document IDs
        """
        if selected_ids:
            self.set_status(f"{len(selected_ids)} item(s) selected")
        else:
            self.set_status("Ready")
    
    # ==================== Action Methods ====================
    
    def _open_upload_dialog(self):
        """Open the upload dialog with current folder as upload destination."""
        # Get current folder name for display
        current_folder_name = None
        if self.current_folder_id is not None:
            current_folder = next((f for f in self.folders if f.get('id') == self.current_folder_id), None)
            if current_folder:
                current_folder_name = current_folder.get('name', 'Unknown Folder')
        
        dialog = UploadDialog(
            self.categories,
            self.folders,
            self.document_service,
            self.current_folder_id,
            current_folder_name,
            self
        )
        dialog.upload_completed.connect(lambda: (
            self.invalidate_cache('documents'),
            self.invalidate_cache('recent'),
            self.load_documents(force_refresh=True)
        ))
        dialog.exec()
    
    def _open_folder_dialog(self):
        """Open the new folder dialog."""
        dialog = FolderDialog(
            self.categories,
            self.document_service,
            self.current_folder_id,
            self
        )
        dialog.folder_created.connect(lambda: (
            self.invalidate_cache('folders'),
            self.load_documents(force_refresh=True)
        ))
        dialog.exec()
    
    def _download_document(self, doc_id: int):
        """
        Download a document to the user's Downloads directory.
        
        Args:
            doc_id (int): Document ID
        """
        print(f"[DocumentsV2] Download requested for document ID: {doc_id}")
        self.set_status("Preparing download...")
        
        # Get download URL from API
        print("[DocumentsV2] Requesting download URL from API...")
        result = self.document_service.download_document(doc_id)
        print(f"[DocumentsV2] API result - success: {result['success']}")
        
        if not result['success']:
            print(f"[DocumentsV2] Download failed: {result['error']}")
            self.show_error("Download Failed", result['error'])
            self.set_status("Ready")
            return
        
        url = result['data']['url']
        filename = result['data']['filename']
        print(f"[DocumentsV2] Download URL: {url}")
        print(f"[DocumentsV2] Filename: {filename}")
        
        # Create and show download dialog
        print("[DocumentsV2] Creating download dialog")
        download_dialog = DownloadDialog(filename, self)
        download_dialog.show()
        
        # Create download worker
        print("[DocumentsV2] Creating download worker")
        download_worker = DownloadWorker(url, filename, self.token)
        download_worker.progress.connect(download_dialog.update_progress)
        download_worker.finished.connect(lambda path: self._on_download_finished(download_dialog, path, filename))
        download_worker.error.connect(lambda err: self._on_download_error(download_dialog, err))
        download_worker.finished.connect(lambda: self._cleanup_worker(download_worker))
        download_worker.error.connect(lambda: self._cleanup_worker(download_worker))
        
        # Handle cancel
        download_dialog.rejected.connect(download_worker.cancel)
        
        # Start download
        self.active_workers.append(download_worker)
        print("[DocumentsV2] Starting download worker thread")
        download_worker.start()
        self.set_status(f"Downloading {filename}...")
    
    def _on_download_finished(self, dialog: DownloadDialog, file_path: str, filename: str):
        """
        Handle successful download completion.
        
        Args:
            dialog (DownloadDialog): Download progress dialog
            file_path (str): Path where file was saved
            filename (str): Original filename
        """
        print(f"[DocumentsV2] Download completed successfully: {file_path}")
        dialog.set_completed(file_path)
        self.set_status(f"Downloaded {filename}")
        
        # Auto-close dialog after 2 seconds
        QTimer.singleShot(2000, dialog.accept)
        
        # Show success message
        QMessageBox.information(
            self,
            "Download Complete",
            f"File downloaded successfully:\n\n{file_path}"
        )
    
    def _on_download_error(self, dialog: DownloadDialog, error_msg: str):
        """
        Handle download error.
        
        Args:
            dialog (DownloadDialog): Download progress dialog
            error_msg (str): Error message
        """
        print(f"[DocumentsV2] Download error: {error_msg}")
        dialog.set_error(error_msg)
        self.set_status("Download failed")
        self.show_error("Download Failed", error_msg)
    
    def _move_document(self, doc_id: int):
        """
        Move document to different folder.
        
        Args:
            doc_id (int): Document ID
        """
        print(f"[DocumentsV2] Move document requested: {doc_id}")
        
        # Get document info
        doc = next((d for d in self.documents if d.get('id') == doc_id), None)
        if not doc:
            self.show_error("Move Failed", "Document not found")
            return
        
        doc_title = doc.get('title', 'Untitled')
        current_folder = doc.get('folder')
        
        # Open move dialog
        dialog = MoveDialog(
            doc_id,
            doc_title,
            self.categories,
            current_folder,
            self.document_service,
            self
        )
        
        # Handle folder creation from dialog
        dialog.folder_created.connect(lambda: (
            self.invalidate_cache('folders'),
            self.load_folders()
        ))
        
        if dialog.exec():
            # Get selected folder
            new_folder_id = dialog.get_selected_folder_id()
            
            print(f"[DocumentsV2] Moving document {doc_id} to folder {new_folder_id}")
            
            # Perform move via API
            result = self.document_service.move_document(doc_id, new_folder_id)
            
            if result['success']:
                QMessageBox.information(
                    self,
                    "Success",
                    f"Document moved successfully"
                )
                
                # Invalidate cache and refresh
                self.invalidate_cache('documents')
                self.invalidate_cache('folders')
                self.load_documents(force_refresh=True)
            else:
                self.show_error("Move Failed", result['error'])
    
    def _rename_item(self, item_id: int):
        """
        Rename document or folder.
        
        Args:
            item_id (int): Item ID
        """
        print(f"[DocumentsV2] Rename item requested: {item_id}")
        
        # Determine if it's a document or folder
        doc = next((d for d in self.documents if d.get('id') == item_id), None)
        
        if doc:
            # It's a document
            is_folder = doc.get('folder') is True
            current_name = doc.get('title') if not is_folder else doc.get('name')
            item_type = 'folder' if is_folder else 'document'
        else:
            # Not found in current view
            self.show_error("Rename Failed", "Item not found")
            return
        
        # Open rename dialog
        dialog = RenameDialog(
            item_id,
            current_name,
            item_type,
            self.document_service,
            self
        )
        
        if dialog.exec():
            new_name = dialog.get_new_name()
            print(f"[DocumentsV2] Renaming {item_type} {item_id} to: {new_name}")
            
            # Perform rename via API
            if item_type == 'document':
                result = self.document_service.rename_document(item_id, new_name)
            else:
                result = self.document_service.rename_folder(item_id, new_name)
            
            if result['success']:
                QMessageBox.information(
                    self,
                    "Success",
                    f"{item_type.capitalize()} renamed successfully"
                )
                
                # Invalidate cache and refresh
                if item_type == 'folder':
                    self.invalidate_cache('folders')
                self.invalidate_cache('documents')
                self.load_documents(force_refresh=True)
            else:
                self.show_error("Rename Failed", result['error'])
    
    def _show_details(self, doc_id: int):
        """
        Show document details (placeholder).
        
        Args:
            doc_id (int): Document ID
        """
        result = self.document_service.get_document(doc_id)
        
        if result['success']:
            doc = result['data']
            details = f"""
            Title: {doc.get('title')}
            Size: {doc.get('file_size_mb')} MB
            Type: {doc.get('file_extension')}
            Uploaded: {doc.get('uploaded_at')}
            Category: {doc.get('category_name', 'N/A')}
            """
            
            QMessageBox.information(self, "Document Details", details)
        else:
            self.show_error("Failed to load details", result['error'])
    
    def _delete_document(self, doc_id: int):
        """
        Delete (soft delete) a document.
        
        Args:
            doc_id (int): Document ID
        """
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Move this document to trash?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            result = self.document_service.delete_document(doc_id)
            
            if result['success']:
                QMessageBox.information(self, "Success", "Document moved to trash")
                self.invalidate_cache('documents')
                self.invalidate_cache('trash')
                self.load_documents(force_refresh=True)
            else:
                self.show_error("Delete Failed", result['error'])
    
    def _restore_document(self, doc_id: int):
        """
        Restore document from trash.
        
        Args:
            doc_id (int): Document ID
        """
        result = self.document_service.restore_document(doc_id)
        
        if result['success']:
            QMessageBox.information(self, "Success", "Document restored")
            self.invalidate_cache('documents')
            self.invalidate_cache('trash')
            self.load_documents(force_refresh=True)
        else:
            self.show_error("Restore Failed", result['error'])
    
    def _permanent_delete(self, doc_id: int):
        """
        Permanently delete a document (irreversible).
        
        Args:
            doc_id (int): Document ID
        """
        print(f"[DocumentsV2] Permanent delete requested: {doc_id}")
        
        # Check if user is admin
        if self.primary_role != 'admin':
            QMessageBox.warning(
                self,
                "Permission Denied",
                "Only administrators can permanently delete documents."
            )
            return
        
        # Get document info
        doc = next((d for d in self.documents if d.get('id') == doc_id), None)
        if not doc:
            self.show_error("Delete Failed", "Document not found")
            return
        
        doc_title = doc.get('title', 'Untitled')
        
        # Strong confirmation for permanent deletion
        reply = QMessageBox.warning(
            self,
            "Permanent Delete - WARNING",
            f"Are you sure you want to PERMANENTLY delete:\n\n'{doc_title}'\n\n"
            f"This action CANNOT be undone!\n"
            f"The document will be deleted forever.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No  # Default to No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Second confirmation
        reply2 = QMessageBox.critical(
            self,
            "Final Confirmation",
            f"LAST CHANCE!\n\nPermanently delete '{doc_title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply2 == QMessageBox.StandardButton.Yes:
            print(f"[DocumentsV2] Performing permanent delete of document {doc_id}")
            
            try:
                # Perform permanent delete via API
                result = self.document_service.permanent_delete_document(doc_id)
                
                print(f"[DocumentsV2] Permanent delete result: {result}")
                
                if result['success']:
                    print(f"[DocumentsV2] Document {doc_id} permanently deleted successfully")
                    QMessageBox.information(
                        self,
                        "Deleted",
                        f"Document permanently deleted"
                    )
                    
                    # Invalidate cache and refresh
                    self.invalidate_cache('documents')
                    self.invalidate_cache('trash')
                    self.load_documents(force_refresh=True)
                else:
                    print(f"[DocumentsV2] Permanent delete failed: {result['error']}")
                    self.show_error("Delete Failed", result['error'])
            except Exception as e:
                print(f"[DocumentsV2] Exception during permanent delete: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                self.show_error("Delete Failed", f"Unexpected error: {str(e)}")
    
    # ==================== Utility Methods ====================
    
    def set_status(self, message: str):
        """
        Update status bar message.
        
        Args:
            message (str): Status message
        """
        self.status_label.setText(message)
    
    def show_error(self, title: str, message: str):
        """
        Show error message dialog.
        
        Args:
            title (str): Error title
            message (str): Error message
        """
        QMessageBox.critical(self, title, message)
        self.set_status("Error")
