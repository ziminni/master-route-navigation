"""
Admin Document Management View

Provides full CRUD operations plus:
- Approval workflow management
- Permanent delete
- User document management
- System analytics
- Bulk operations
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QLabel, QMessageBox, QPushButton, QStackedWidget
)
from PyQt6.QtCore import Qt

from ..DocumentsV2 import DocumentsV2View
from ..widgets import Sidebar, AnalyticsWidget, UserActivityWidget, BulkOperationsWidget
from ..services import DocumentService


class AdminDocumentView(DocumentsV2View):
    """
    Admin view with additional administrative tools.
    
    Extends the base DocumentsV2View with:
    - Admin Tools section in sidebar
    - Approval management tab
    - System-wide document operations
    - Analytics and reporting
    """
    
    def __init__(self, username: str, roles: list, primary_role: str, token: str, parent=None):
        """Initialize admin document view."""
        # Initialize parent first
        super().__init__(username, roles, primary_role, token, parent)
        
        # Override window title
        self.setWindowTitle(f"CISC Documents - Admin Panel - {self.username}")
        
        # Extend cache for admin-specific views
        self.cache['approvals'] = {'data': None, 'timestamp': None}
        self.cache['all_documents'] = {'data': None, 'timestamp': None}
        self.cache['analytics'] = {'data': None, 'timestamp': None}
        
        # Create admin widgets
        self.analytics_widget = None
        self.activity_widget = None
        self.bulk_ops_widget = None
        
        # Add admin-specific features
        self._add_admin_tools()
        self._setup_admin_context_menu()
        self._init_admin_widgets()
    
    def _add_admin_tools(self):
        """Add admin tools section to sidebar."""
        # Add separator in sidebar
        admin_label = QLabel("ADMIN TOOLS")
        admin_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #F44336;
                padding: 10px 10px 5px 10px;
                background-color: #FFF3E0;
                border-bottom: 2px solid #F44336;
            }
        """)
        
        # Insert admin section after navigation list, before categories
        sidebar_layout = self.sidebar.layout()
        # Insert at index 2 (after nav_list at index 1, before CATEGORIES label)
        sidebar_layout.insertWidget(2, admin_label)
        
        # Add admin navigation buttons
        admin_buttons = QWidget()
        admin_layout = QVBoxLayout(admin_buttons)
        admin_layout.setContentsMargins(5, 5, 5, 5)
        admin_layout.setSpacing(2)
        
        # Pending Approvals button
        btn_approvals = QPushButton("Pending Approvals")
        btn_approvals.setStyleSheet(self._get_admin_button_style())
        btn_approvals.clicked.connect(lambda: self._handle_navigation_change('approvals', None))
        admin_layout.addWidget(btn_approvals)
        
        # All Documents button (admin can see everything)
        btn_all_docs = QPushButton("All Files")
        btn_all_docs.setStyleSheet(self._get_admin_button_style())
        btn_all_docs.clicked.connect(lambda: self._handle_navigation_change('all_documents', None))
        admin_layout.addWidget(btn_all_docs)
        
        # User Management button
        btn_users = QPushButton("User Files")
        btn_users.setStyleSheet(self._get_admin_button_style())
        btn_users.clicked.connect(lambda: self._handle_navigation_change('user_management', None))
        admin_layout.addWidget(btn_users)
        
        # System Analytics button
        btn_analytics = QPushButton("Analytics")
        btn_analytics.setStyleSheet(self._get_admin_button_style())
        btn_analytics.clicked.connect(lambda: self._handle_navigation_change('analytics', None))
        admin_layout.addWidget(btn_analytics)
        
        # User Activity button
        btn_activity = QPushButton("User Activity")
        btn_activity.setStyleSheet(self._get_admin_button_style())
        btn_activity.clicked.connect(lambda: self._handle_navigation_change('activity', None))
        admin_layout.addWidget(btn_activity)
        
        # Bulk Operations button
        btn_bulk = QPushButton("Bulk Operations")
        btn_bulk.setStyleSheet(self._get_admin_button_style())
        btn_bulk.clicked.connect(lambda: self._handle_navigation_change('bulk_ops', None))
        admin_layout.addWidget(btn_bulk)
        
        # Add separator
        admin_layout.addSpacing(10)
        
        # Add Category button
        btn_add_category = QPushButton("Add Category")
        btn_add_category.setStyleSheet(self._get_admin_button_style())
        btn_add_category.clicked.connect(self._open_add_category_dialog)
        admin_layout.addWidget(btn_add_category)
        
        sidebar_layout.insertWidget(3, admin_buttons)
    
    def _setup_admin_context_menu(self):
        """Setup admin-specific context menu items."""
        admin_menu_items = [
            # (Label, Action Name, Condition Callback)
            ("Approve", "approve", lambda doc: doc.get('approval_status') == 'pending'),
            ("Reject", "reject", lambda doc: doc.get('approval_status') == 'pending'),
            # Note: "Delete Permanently" is now built into base file_list for admins on trash items
            ("Transfer Ownership", "transfer_ownership", lambda doc: doc.get('folder') is not True),
        ]
        self.file_list.set_custom_menu_items(admin_menu_items)
    
    def _get_admin_button_style(self) -> str:
        """Get stylesheet for admin buttons."""
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
                background-color: #FFEBEE;
            }
            QPushButton:pressed {
                background-color: #FFCDD2;
            }
        """
    
    def _handle_navigation_change(self, nav_type: str, item_id: int):
        """
        Override navigation handler to support admin views.
        
        Args:
            nav_type (str): Navigation type
            item_id (int): Item ID (for categories)
        """
        # Handle admin-specific navigation
        if nav_type == 'approvals':
            self._show_approvals_view()
            return
        elif nav_type == 'all_documents':
            self._show_all_documents()
            return
        elif nav_type == 'user_management':
            self._show_user_management()
            return
        elif nav_type == 'analytics':
            self._show_analytics()
            return
        elif nav_type == 'activity':
            self._show_user_activity()
            return
        elif nav_type == 'bulk_ops':
            self._show_bulk_operations()
            return
        
        # Fall back to parent navigation
        super()._handle_navigation_change(nav_type, item_id)
    
    def _init_admin_widgets(self):
        """Initialize admin-specific widgets."""
        if self.analytics_widget is None:
            # Analytics widget
            self.analytics_widget = AnalyticsWidget()
            self.analytics_widget.refresh_requested.connect(self._show_analytics)
            self.content_stack.addWidget(self.analytics_widget)
            
            # User activity widget
            self.activity_widget = UserActivityWidget()
            self.activity_widget.refresh_requested.connect(self._show_user_activity)
            self.activity_widget.filter_changed.connect(self._on_activity_filter_changed)
            self.content_stack.addWidget(self.activity_widget)
            
            # Bulk operations widget
            self.bulk_ops_widget = BulkOperationsWidget()
            self.bulk_ops_widget.bulk_operation_requested.connect(self._handle_bulk_operation)
            self.content_stack.addWidget(self.bulk_ops_widget)
            
            # Connect file list selection to bulk ops
            self.file_list.selection_changed.connect(self.bulk_ops_widget.update_selection_count)
    
    def _show_user_activity(self):
        """Show user activity monitoring."""
        if not self.activity_widget:
            self._init_admin_widgets()
        
        self.content_stack.setCurrentWidget(self.activity_widget)
        self.activity_widget.show_loading()
        
        # Load activity data
        result = self.document_service.get_user_activity()
        if result['success']:
            self.activity_widget.update_activity(result['data'])
        else:
            self.activity_widget.show_error(result['error'])
    
    def _on_activity_filter_changed(self, action_filter: str):
        """Handle activity filter change."""
        result = self.document_service.get_user_activity(action_filter=action_filter)
        if result['success']:
            self.activity_widget.update_activity(result['data'])
        else:
            self.activity_widget.show_error(result['error'])
    
    def _show_bulk_operations(self):
        """Show bulk operations panel."""
        if not self.bulk_ops_widget:
            self._init_admin_widgets()
        
        self.content_stack.setCurrentWidget(self.bulk_ops_widget)
    
    def _handle_bulk_operation(self, operation_type: str, params: dict):
        """Handle bulk operation request from bulk ops widget."""
        selected_ids = self.file_list.get_selected_ids()
        
        if not selected_ids:
            QMessageBox.warning(self, "No Selection", "No documents selected")
            return
        
        self._execute_bulk_operation(operation_type, selected_ids, params)
    
    def _show_approvals_view(self):
        """Show pending approvals for admin review."""
        self.current_view = 'approvals'
        self.current_folder_id = None
        self.current_category_id = None
        
        self.breadcrumb.reset()
        self.breadcrumb.set_path([{'id': None, 'name': 'Pending Approvals'}])
        
        # Try cache first
        cached_data, is_valid = self._get_from_cache('approvals', 'approvals')
        if is_valid:
            approvals = cached_data
            
            # Convert approvals to document format for display
            self.documents = []
            for approval in approvals:
                doc = approval.get('document', {})
                doc['approval_status'] = approval.get('status')
                doc['submitted_at'] = approval.get('submitted_at')
                doc['approval_id'] = approval.get('id')
                self.documents.append(doc)
            
            self._display_documents_immediately()
            self.set_status(f"{len(approvals)} pending approval(s) - Sorted by oldest first (cached)")
            return
        
        from ..workers import APIWorker
        
        self._show_loading(True)
        self.set_status("Loading pending approvals...")
        
        # Load async
        worker = APIWorker(self.document_service.get_pending_approvals)
        worker.finished.connect(self._on_approvals_loaded)
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        worker.error.connect(lambda err: self._on_load_error("approvals", err))
        worker.error.connect(lambda: self._cleanup_worker(worker))
        self.active_workers.append(worker)
        worker.start()
    
    def _on_approvals_loaded(self, result: dict):
        """Handle approvals load completion."""
        if result['success']:
            # Approvals are sorted by oldest first (submitted_at ascending)
            approvals = result['data']
            
            # Save to cache
            self._save_to_cache('approvals', approvals, 'approvals')
            
            # Convert approvals to document format for display
            self.documents = []
            for approval in approvals:
                doc = approval.get('document', {})
                doc['approval_status'] = approval.get('status')
                doc['submitted_at'] = approval.get('submitted_at')
                doc['approval_id'] = approval.get('id')
                self.documents.append(doc)
            
            if not self.documents:
                self._show_empty_state('approvals')
            else:
                self._display_documents_immediately()
                self.content_stack.setCurrentIndex(0)
            self._show_loading(False)
            self.set_status(f"{len(approvals)} pending approval(s) - Sorted by oldest first")
        else:
            self._on_load_error("approvals", result.get('error', 'Unknown error'))
    
    def _show_all_documents(self):
        """Show all documents in the system (admin privilege)."""
        self.current_view = 'all_documents'
        self.current_folder_id = None
        self.current_category_id = None
        
        self.breadcrumb.reset()
        self.breadcrumb.set_path([{'id': None, 'name': 'All Documents'}])
        
        # Try cache first
        cached_data, is_valid = self._get_from_cache('all_documents', 'all_documents')
        if is_valid:
            self.documents = cached_data
            self._display_documents_immediately()
            self.set_status(f"Loaded {len(self.documents)} document(s) from cache")
            return
        
        # Force refresh from API
        from ..workers import APIWorker
        
        self._show_loading(True)
        self.set_status("Loading all documents...")
        
        # Load async
        worker = APIWorker(self.document_service.get_all_documents)
        worker.finished.connect(self._on_all_documents_loaded)
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        worker.error.connect(lambda err: self._on_load_error("all documents", err))
        worker.error.connect(lambda: self._cleanup_worker(worker))
        self.active_workers.append(worker)
        worker.start()
    
    def _on_all_documents_loaded(self, result: dict):
        """Handle all documents load completion."""
        if result['success']:
            self.documents = result['data']
            
            # Save to cache
            self._save_to_cache('all_documents', self.documents, 'all_documents')
            
            if not self.documents:
                self._show_empty_state('mydrive')
            else:
                self._display_documents_immediately()
                self.content_stack.setCurrentIndex(0)
            self._show_loading(False)
            self.set_status(f"Loaded {len(self.documents)} document(s)")
        else:
            self._on_load_error("all documents", result.get('error', 'Unknown error'))
    
    def _on_load_error(self, context: str, error_msg: str):
        """Handle load error for admin views."""
        self._show_loading(False)
        self.show_error(f"Failed to load {context}", error_msg)
        self._show_empty_state('error')
    
    def _show_user_management(self):
        """Show user document management interface."""
        QMessageBox.information(
            self,
            "User Management",
            "User document management interface will be implemented.\n\n"
            "Features:\n"
            "- View documents by user\n"
            "- Transfer ownership\n"
            "- Bulk operations\n"
            "- User storage quotas"
        )
    
    def _show_analytics(self):
        """Show system analytics dashboard."""
        if not self.analytics_widget:
            self._init_admin_widgets()
        
        # Switch to analytics widget
        self.content_stack.setCurrentWidget(self.analytics_widget)
        self.analytics_widget.show_loading()
        
        # Load analytics data
        result = self.document_service.get_analytics()
        if result['success']:
            self.analytics_widget.update_analytics(result['data'])
        else:
            self.analytics_widget.show_error(result['error'])
    
    def _handle_context_menu_action(self, action: str, item_id: int):
        """
        Override context menu handler to support bulk operations and admin actions.
        
        Args:
            action (str): Action name
            item_id (int): Document or folder ID
        """
        # Check if multiple items are selected for bulk operations
        selected_ids = self.file_list.get_selected_ids()
        
        # Bulk operations for multi-selection
        if len(selected_ids) > 1 and action in ['delete', 'restore', 'move', 'delete_permanent']:
            if action == 'delete':
                self._execute_bulk_operation('delete', selected_ids)
            elif action == 'restore':
                self._execute_bulk_operation('restore', selected_ids)
            elif action == 'move':
                self._bulk_move_documents(selected_ids)
            elif action == 'delete_permanent':
                self._execute_bulk_operation('permanent_delete', selected_ids)
            return
        
        # Admin-specific single-item actions
        if action == 'approve':
            self._approve_document(item_id)
            return
        elif action == 'reject':
            self._reject_document(item_id)
            return
        elif action == 'delete_permanent':
            self._permanent_delete_document(item_id)
            return
        elif action == 'transfer_ownership':
            self._transfer_ownership(item_id)
            return
        
        # Fall back to parent actions
        super()._handle_context_menu_action(action, item_id)
    
    def _approve_document(self, doc_id: int):
        """Approve a pending document."""
        # Find the document data
        doc_data = next((doc for doc in self.documents if doc.get('id') == doc_id), None)
        if not doc_data:
            QMessageBox.warning(self, "Error", "Document not found")
            return
        
        # Get approval ID
        approval_id = doc_data.get('approval_id')
        if not approval_id:
            QMessageBox.warning(self, "Error", "No pending approval found for this document")
            return
        
        from ..dialogs import ApprovalDialog
        
        dialog = ApprovalDialog(
            doc_data, 
            approval_id, 
            'approve',
            self.document_service,
            self
        )
        dialog.action_completed.connect(self._on_approval_action_completed)
        dialog.exec()
    
    def _on_approval_action_completed(self, result_data: dict):
        """Handle approval/rejection completion."""
        # Invalidate caches
        self.invalidate_cache('approvals')
        self.invalidate_cache('documents')
        self.invalidate_cache('all_documents')
        
        # Refresh current view
        if self.current_view == 'approvals':
            self._show_approvals_view()
        else:
            self.load_documents(force_refresh=True)
    
    def _reject_document(self, doc_id: int):
        """Reject a pending document."""
        # Find the document data
        doc_data = next((doc for doc in self.documents if doc.get('id') == doc_id), None)
        if not doc_data:
            QMessageBox.warning(self, "Error", "Document not found")
            return
        
        # Get approval ID
        approval_id = doc_data.get('approval_id')
        if not approval_id:
            QMessageBox.warning(self, "Error", "No pending approval found for this document")
            return
        
        from ..dialogs import ApprovalDialog
        
        dialog = ApprovalDialog(
            doc_data, 
            approval_id, 
            'reject',
            self.document_service,
            self
        )
        dialog.action_completed.connect(self._on_approval_action_completed)
        dialog.exec()
    
    def _permanent_delete_document(self, doc_id: int):
        """Permanently delete a document (admin only)."""
        reply = QMessageBox.warning(
            self,
            "Permanent Delete",
            "This will PERMANENTLY delete the document.\n\n"
            "This action CANNOT be undone!\n\n"
            "Are you sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            result = self.document_service.permanent_delete_document(doc_id)
            
            if result['success']:
                QMessageBox.information(self, "Success", "Document permanently deleted")
                # Invalidate all relevant caches
                self.invalidate_cache('documents')
                self.invalidate_cache('all_documents')
                self.invalidate_cache('trash')
                self.load_documents(force_refresh=True)
            else:
                self.show_error("Permanent Delete Failed", result['error'])
    
    def _transfer_ownership(self, doc_id: int):
        """Transfer document ownership to another user."""
        # TODO: Implement user selection dialog
        QMessageBox.information(
            self,
            "Transfer Ownership",
            "Ownership transfer dialog will be implemented.\n\n"
            "Features:\n"
            "- Select new owner\n"
            "- Add transfer notes\n"
            "- Notify both parties"
        )
    
    def _open_add_category_dialog(self):
        """Open dialog to add a new category."""
        from ..dialogs.category_dialog import CategoryDialog
        
        dialog = CategoryDialog(self.document_service, self)
        dialog.category_created.connect(self._on_category_created)
        dialog.exec()
    
    def _on_category_created(self, category_data: dict):
        """Handle successful category creation."""
        # Invalidate categories cache
        self.invalidate_cache('categories')
        
        # Reload categories in sidebar
        self.load_categories()
        
        # Show success message
        category_name = category_data.get('name', 'New category')
        self.set_status(f"Category '{category_name}' created successfully")
    
    def _execute_bulk_operation(self, operation_type: str, doc_ids: list, params: dict = None):
        """
        Execute bulk operation on multiple documents.
        
        Args:
            operation_type (str): Operation type ('delete', 'restore', 'move', 'permanent_delete')
            doc_ids (list): List of document IDs
            params (dict): Additional parameters for the operation
        """
        if not doc_ids:
            return
        
        params = params or {}
        count = len(doc_ids)
        
        # Confirm dangerous operations
        if operation_type == 'delete':
            reply = QMessageBox.question(
                self,
                "Confirm Bulk Delete",
                f"Move {count} document(s) to trash?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            self.set_status(f"Deleting {count} document(s)...")
            result = self.document_service.bulk_delete(doc_ids)
            
        elif operation_type == 'restore':
            self.set_status(f"Restoring {count} document(s)...")
            result = self.document_service.bulk_restore(doc_ids)
            
        elif operation_type == 'move':
            folder_id = params.get('folder_id')
            folder_name = params.get('folder_name', 'selected folder')
            
            reply = QMessageBox.question(
                self,
                "Confirm Bulk Move",
                f"Move {count} document(s) to '{folder_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            self.set_status(f"Moving {count} document(s)...")
            result = self.document_service.bulk_move(doc_ids, folder_id)
            
        elif operation_type == 'permanent_delete':
            reply = QMessageBox.warning(
                self,
                "Confirm Permanent Delete",
                f"PERMANENTLY delete {count} document(s)?\n\n"
                "This action CANNOT be undone!",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            self.set_status(f"Permanently deleting {count} document(s)...")
            result = self.document_service.bulk_permanent_delete(doc_ids)
            
        else:
            QMessageBox.warning(self, "Unknown Operation", f"Unknown operation: {operation_type}")
            return
        
        # Handle result
        if result['success']:
            data = result['data']
            if operation_type == 'delete':
                QMessageBox.information(
                    self, "Success", 
                    f"Successfully deleted {data['deleted']} document(s)"
                )
            elif operation_type == 'restore':
                QMessageBox.information(
                    self, "Success",
                    f"Successfully restored {data['restored']} document(s)"
                )
            elif operation_type == 'move':
                QMessageBox.information(
                    self, "Success",
                    f"Successfully moved {data['moved']} document(s)"
                )
            elif operation_type == 'permanent_delete':
                QMessageBox.information(
                    self, "Success",
                    f"Successfully permanently deleted {data['deleted']} document(s)"
                )
            
            # Clear selection
            self.file_list.clear_selection()
            
            # Invalidate caches and refresh
            self.invalidate_cache('documents')
            self.invalidate_cache('all_documents')
            self.invalidate_cache('trash')
            self.load_documents(force_refresh=True)
            
        else:
            data = result.get('data', {})
            failed = data.get('failed', [])
            error_msg = result.get('error', 'Unknown error')
            
            if failed:
                failed_ids = [str(f['id']) for f in failed[:5]]
                error_details = ', '.join(failed_ids)
                if len(failed) > 5:
                    error_details += f', ... ({len(failed) - 5} more)'
                
                QMessageBox.warning(
                    self, "Partial Failure",
                    f"{error_msg}\n\nFailed IDs: {error_details}"
                )
            else:
                self.show_error("Bulk Operation Failed", error_msg)
    
    def _bulk_move_documents(self, doc_ids: list):
        """Show folder selection dialog and move multiple documents."""
        from ..dialogs import MoveFolderDialog
        
        dialog = MoveFolderDialog(
            self.folders,
            self.categories,
            self.document_service,
            self
        )
        
        if dialog.exec():
            folder_id = dialog.get_selected_folder()
            folder_name = dialog.get_selected_folder_name()
            
            self._execute_bulk_operation('move', doc_ids, {
                'folder_id': folder_id,
                'folder_name': folder_name or 'Root'
            })
