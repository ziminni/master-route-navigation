"""
Document Service - API Communication Layer

Handles all HTTP requests to the Django backend for document operations.
Provides methods for CRUD operations, file uploads, and approval workflows.

API Base URL: http://localhost:8000/api/documents/

Endpoints Used:
- /documents/ - List, create, update, delete documents
- /documents/my-recent/ - Get user's recent documents
- /documents/trash/ - Get deleted documents
- /documents/{id}/restore/ - Restore deleted document
- /documents/{id}/move/ - Move document to folder
- /documents/{id}/download/ - Download document
- /folders/ - Folder operations
- /categories/ - Category operations
- /approvals/ - Approval workflow operations
"""

import requests
from typing import Dict, List, Optional, Any
from PyQt6.QtCore import QObject, pyqtSignal


class DocumentService(QObject):
    """
    Service class for document-related API operations.
    
    Emits signals for async operations and error handling.
    All methods return dictionaries with 'success', 'data', and 'error' keys.
    
    Signals:
        upload_progress(int): Emitted during file upload with percentage
        operation_completed(str): Emitted when operation completes with message
        operation_failed(str): Emitted when operation fails with error message
    """
    
    # Signals for async feedback
    upload_progress = pyqtSignal(int)  # percentage
    operation_completed = pyqtSignal(str)  # success message
    operation_failed = pyqtSignal(str)  # error message
    
    def __init__(self, base_url: str = "http://localhost:8000", token: str = None):
        """
        Initialize the document service.
        
        Args:
            base_url (str): Backend API base URL
            token (str): JWT authentication token
        """
        super().__init__()
        self.base_url = base_url
        self.api_url = f"{base_url}/api/documents"
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}' if token else '',
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None, 
                     files: Dict = None, params: Dict = None) -> Dict[str, Any]:
        """
        Internal method to make HTTP requests with error handling.
        
        Args:
            method (str): HTTP method (GET, POST, PATCH, DELETE)
            endpoint (str): API endpoint (e.g., '/documents/')
            data (dict): JSON data for request body
            files (dict): Files for multipart upload
            params (dict): Query parameters
            
        Returns:
            dict: {'success': bool, 'data': any, 'error': str}
        """
        url = f"{self.api_url}{endpoint}"
        headers = self.headers.copy()
        
        # Remove Content-Type for file uploads (requests will set it)
        if files:
            headers.pop('Content-Type', None)
        
        try:
            response = requests.request(
                method=method,
                url=url,
                json=data if not files else None,
                files=files,
                data=data if files else None,
                params=params,
                headers=headers,
                timeout=30
            )
            
            print(f"[DocumentService] {method} {url} - Status: {response.status_code}")
            print(f"[DocumentService] Response content length: {len(response.content) if response.content else 0}")
            
            if response.status_code in [200, 201, 204]:
                # 204 No Content returns empty response (e.g., DELETE operations)
                if response.status_code == 204 or not response.content:
                    print(f"[DocumentService] No content response, returning None")
                    data = None
                else:
                    try:
                        data = response.json()
                        print(f"[DocumentService] Successfully parsed JSON response")
                    except Exception as json_error:
                        print(f"[DocumentService] JSON parse error: {json_error}")
                        print(f"[DocumentService] Response text: {response.text[:200]}")
                        raise
                    
                return {
                    'success': True,
                    'data': data,
                    'error': None
                }
            else:
                print(f"[DocumentService] Error response: {response.status_code}")
                try:
                    error_msg = response.json().get('error', response.text) if response.content else 'Unknown error'
                except:
                    error_msg = response.text if response.text else 'Unknown error'
                print(f"[DocumentService] Error message: {error_msg}")
                return {
                    'success': False,
                    'data': None,
                    'error': f"HTTP {response.status_code}: {error_msg}"
                }
                
        except requests.exceptions.ConnectionError as e:
            print(f"[DocumentService] Connection error: {e}")
            return {
                'success': False,
                'data': None,
                'error': "Cannot connect to server. Is the backend running?"
            }
        except requests.exceptions.Timeout as e:
            print(f"[DocumentService] Timeout error: {e}")
            return {
                'success': False,
                'data': None,
                'error': "Request timed out"
            }
        except Exception as e:
            print(f"[DocumentService] Unexpected error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'data': None,
                'error': str(e)
            }
    
    # ==================== Document Operations ====================
    
    def get_documents(self, filters: Dict = None) -> Dict[str, Any]:
        """
        Get list of documents with optional filters.
        
        Args:
            filters (dict): Optional filters
                - category (int): Filter by category ID
                - folder (int): Filter by folder ID
                - search (str): Search in title/description
                - is_featured (bool): Get featured documents only
                - ordering (str): Sort field (e.g., '-uploaded_at', 'title')
                
        Returns:
            dict: {'success': bool, 'data': list of documents, 'error': str}
        """
        return self._make_request('GET', '/documents/', params=filters)
    
    def get_my_recent(self) -> Dict[str, Any]:
        """
        Get current user's recently accessed documents.
        Uses activity log to determine recent access.
        
        Returns:
            dict: {'success': bool, 'data': list of documents, 'error': str}
        """
        return self._make_request('GET', '/documents/my-recent/')
    
    def get_my_documents(self) -> Dict[str, Any]:
        """
        Get documents uploaded by the current user.
        Uses the /documents/my-uploads/ endpoint.
        
        Returns:
            dict: {'success': bool, 'data': list of documents, 'error': str}
        """
        return self._make_request('GET', '/documents/my-uploads/')
    
    def get_starred_documents(self) -> Dict[str, Any]:
        """
        Get starred/featured documents.
        Uses the is_featured filter.
        
        Returns:
            dict: {'success': bool, 'data': list of starred documents, 'error': str}
        """
        return self.get_documents(filters={'is_featured': True})
    
    def get_trash(self) -> Dict[str, Any]:
        """
        Get soft-deleted documents (trash bin).
        Users see only their own deleted docs unless admin.
        
        Returns:
            dict: {'success': bool, 'data': list of deleted documents, 'error': str}
        """
        return self._make_request('GET', '/documents/trash/')
    
    def get_document(self, doc_id: int) -> Dict[str, Any]:
        """
        Get detailed information about a specific document.
        
        Args:
            doc_id (int): Document ID
            
        Returns:
            dict: {'success': bool, 'data': document details, 'error': str}
        """
        return self._make_request('GET', f'/documents/{doc_id}/')
    
    def upload_document(self, file_path: str, title: str, category_id: int,
                       folder_id: int = None, document_type_id: int = None,
                       description: str = "") -> Dict[str, Any]:
        """
        Upload a new document.
        
        Args:
            file_path (str): Path to file on local system
            title (str): Document title
            category_id (int): Category ID (required)
            folder_id (int): Folder ID (optional)
            document_type_id (int): Document type ID (optional)
            description (str): Document description (optional)
            
        Returns:
            dict: {'success': bool, 'data': created document, 'error': str}
        """
        try:
            with open(file_path, 'rb') as f:
                files = {'file_path': f}
                data = {
                    'title': title,
                    'category': category_id,
                    'description': description
                }
                
                if folder_id:
                    data['folder'] = folder_id
                if document_type_id:
                    data['document_type'] = document_type_id
                
                return self._make_request('POST', '/documents/', data=data, files=files)
                
        except FileNotFoundError:
            return {
                'success': False,
                'data': None,
                'error': f"File not found: {file_path}"
            }
    
    def move_document(self, doc_id: int, folder_id: int = None) -> Dict[str, Any]:
        """
        Move document to a different folder.
        
        Args:
            doc_id (int): Document ID
            folder_id (int): Destination folder ID (None for root)
            
        Returns:
            dict: {'success': bool, 'data': updated document, 'error': str}
        """
        data = {'folder_id': folder_id}
        return self._make_request('POST', f'/documents/{doc_id}/move/', data=data)
    
    def restore_document(self, doc_id: int, folder_id: int = None) -> Dict[str, Any]:
        """
        Restore a deleted document from trash.
        
        Args:
            doc_id (int): Document ID
            folder_id (int): Optional destination folder for restore
            
        Returns:
            dict: {'success': bool, 'data': restored document, 'error': str}
        """
        data = {}
        if folder_id:
            data['restore_to_folder_id'] = folder_id
        return self._make_request('POST', f'/documents/{doc_id}/restore/', data=data)
    
    def delete_document(self, doc_id: int) -> Dict[str, Any]:
        """
        Soft delete a document (move to trash).
        
        Args:
            doc_id (int): Document ID
            
        Returns:
            dict: {'success': bool, 'data': None, 'error': str}
        """
        return self._make_request('DELETE', f'/documents/{doc_id}/')
    
    def download_document(self, doc_id: int) -> Dict[str, Any]:
        """
        Get download URL for a document.
        
        Args:
            doc_id (int): Document ID
            
        Returns:
            dict: {'success': bool, 'data': {'url': str, 'filename': str}, 'error': str}
        """
        return self._make_request('GET', f'/documents/{doc_id}/download/')
    
    def rename_document(self, doc_id: int, new_title: str) -> Dict[str, Any]:
        """
        Rename a document.
        
        Args:
            doc_id (int): Document ID
            new_title (str): New title/name
            
        Returns:
            dict: {'success': bool, 'data': updated document, 'error': str}
        """
        data = {'title': new_title}
        return self._make_request('PATCH', f'/documents/{doc_id}/', data=data)
    
    def permanent_delete_document(self, doc_id: int) -> Dict[str, Any]:
        """
        Permanently delete a document (cannot be undone).
        Admin only operation.
        
        Args:
            doc_id (int): Document ID
            
        Returns:
            dict: {'success': bool, 'data': None, 'error': str}
        """
        # Use a special query parameter to signal permanent deletion
        return self._make_request('DELETE', f'/documents/{doc_id}/', params={'permanent': 'true'})
    
    # ==================== Folder Operations ====================
    
    def get_folders(self, parent_id: int = None, category_id: int = None) -> Dict[str, Any]:
        """
        Get list of folders with optional filters.
        
        Args:
            parent_id (int): Filter by parent folder (None for root level)
            category_id (int): Filter by category
            
        Returns:
            dict: {'success': bool, 'data': list of folders, 'error': str}
        """
        params = {}
        # Always include parent parameter to ensure proper hierarchy
        # Use empty string for root level, or the specific parent ID
        if parent_id is not None:
            params['parent'] = parent_id
        else:
            params['parent'] = ''
        if category_id:
            params['category'] = category_id
        return self._make_request('GET', '/folders/', params=params)
    
    def create_folder(self, name: str, category_id: int, parent_id: int = None,
                     description: str = "") -> Dict[str, Any]:
        """
        Create a new folder.
        
        Args:
            name (str): Folder name
            category_id (int): Category ID
            parent_id (int): Parent folder ID (None for root)
            description (str): Folder description
            
        Returns:
            dict: {'success': bool, 'data': created folder, 'error': str}
        """
        data = {
            'name': name,
            'category': category_id,
            'description': description
        }
        if parent_id:
            data['parent'] = parent_id
        return self._make_request('POST', '/folders/', data=data)
    
    def get_folder_breadcrumbs(self, folder_id: int) -> Dict[str, Any]:
        """
        Get breadcrumb trail for a folder.
        
        Args:
            folder_id (int): Folder ID
            
        Returns:
            dict: {'success': bool, 'data': list of breadcrumb items, 'error': str}
                  Each item: {'id': int, 'name': str, 'slug': str}
        """
        return self._make_request('GET', f'/folders/{folder_id}/breadcrumbs/')
    
    def rename_folder(self, folder_id: int, new_name: str) -> Dict[str, Any]:
        """
        Rename a folder.
        
        Args:
            folder_id (int): Folder ID
            new_name (str): New folder name
            
        Returns:
            dict: {'success': bool, 'data': updated folder, 'error': str}
        """
        data = {'name': new_name}
        return self._make_request('PATCH', f'/folders/{folder_id}/', data=data)
    
    def delete_folder(self, folder_id: int) -> Dict[str, Any]:
        """
        Delete a folder (soft delete).
        
        Args:
            folder_id (int): Folder ID
            
        Returns:
            dict: {'success': bool, 'data': None, 'error': str}
        """
        return self._make_request('DELETE', f'/folders/{folder_id}/')
    
    # ==================== Category Operations ====================
    
    def get_categories(self) -> Dict[str, Any]:
        """
        Get all document categories.
        
        Returns:
            dict: {'success': bool, 'data': list of categories, 'error': str}
        """
        return self._make_request('GET', '/categories/')
    
    def create_category(self, name: str, icon: str = '', description: str = '', display_order: int = 0) -> Dict[str, Any]:
        """
        Create a new document category (Admin only).
        
        Args:
            name (str): Category name (required, unique)
            icon (str): Icon emoji or character
            description (str): Category description
            display_order (int): Display order (lower numbers appear first)
            
        Returns:
            dict: {'success': bool, 'data': created category, 'error': str}
        """
        data = {
            'name': name,
            'icon': icon,
            'description': description,
            'display_order': display_order
        }
        return self._make_request('POST', '/categories/', data=data)
    
    # ==================== Approval Operations ====================
    
    def get_pending_approvals(self) -> Dict[str, Any]:
        """
        Get documents pending approval (Faculty/Admin only).
        
        Returns:
            dict: {'success': bool, 'data': list of pending approvals, 'error': str}
        """
        return self._make_request('GET', '/approvals/pending/')
    
    def approve_document(self, approval_id: int, notes: str = "") -> Dict[str, Any]:
        """
        Approve a document (Faculty/Admin only).
        
        Args:
            approval_id (int): Approval ID
            notes (str): Optional approval notes
            
        Returns:
            dict: {'success': bool, 'data': updated approval, 'error': str}
        """
        data = {'notes': notes} if notes else {}
        return self._make_request('POST', f'/approvals/{approval_id}/approve/', data=data)
    
    def reject_document(self, approval_id: int, notes: str = "") -> Dict[str, Any]:
        """
        Reject a document (Faculty/Admin only).
        
        Args:
            approval_id (int): Approval ID
            notes (str): Rejection reason (recommended)
            
        Returns:
            dict: {'success': bool, 'data': updated approval, 'error': str}
        """
        data = {'notes': notes} if notes else {}
        return self._make_request('POST', f'/approvals/{approval_id}/reject/', data=data)
    
    # ==================== Admin-Only Operations ====================
    
    def get_all_documents(self, filters: dict = None) -> Dict[str, Any]:
        """
        Get all documents in the system (Admin only).
        
        Ignores ownership and shows all documents regardless of user.
        
        Args:
            filters (dict): Optional filters (search, category, ordering, etc.)
            
        Returns:
            dict: {'success': bool, 'data': list of documents, 'error': str}
        """
        params = filters if filters else {}
        params['admin_view'] = True  # Signal backend to return all documents
        return self._make_request('GET', '/documents/', params=params)
    
    def transfer_ownership(self, doc_id: int, new_owner_id: int, notes: str = "") -> Dict[str, Any]:
        """
        Transfer document ownership to another user (Admin only).
        
        Args:
            doc_id (int): Document ID
            new_owner_id (int): New owner's user ID
            notes (str): Optional transfer notes
            
        Returns:
            dict: {'success': bool, 'data': updated document, 'error': str}
        """
        data = {
            'new_owner_id': new_owner_id,
            'notes': notes
        }
        return self._make_request('POST', f'/documents/{doc_id}/transfer_ownership/', data=data)
    
    def update_folder_permissions(self, folder_id: int, permissions: dict) -> Dict[str, Any]:
        """
        Update folder permissions (Admin only).
        
        Args:
            folder_id (int): Folder ID
            permissions (dict): Permission settings
                {
                    'role_permissions': [
                        {'role': 'student', 'can_view': True, 'can_upload': False, ...},
                        ...
                    ],
                    'user_permissions': [
                        {'user_id': 123, 'can_view': True, 'can_upload': True, ...},
                        ...
                    ]
                }
            
        Returns:
            dict: {'success': bool, 'data': updated permissions, 'error': str}
        """
        return self._make_request('POST', f'/folders/{folder_id}/update_permissions/', data=permissions)
    
    def get_system_analytics(self) -> Dict[str, Any]:
        """
        Get system-wide analytics (Admin only).
        
        Returns:
            dict: {'success': bool, 'data': analytics data, 'error': str}
            
        Analytics data includes:
        - Total documents/storage
        - Documents by category
        - Downloads by category
        - Most active users
        - Approval statistics
        """
        return self._make_request('GET', '/analytics/')
    
    def get_user_documents(self, user_id: int) -> Dict[str, Any]:
        """
        Get all documents for a specific user (Admin only).
        
        Args:
            user_id (int): User ID
            
        Returns:
            dict: {'success': bool, 'data': list of documents, 'error': str}
        """
        return self._make_request('GET', f'/documents/', params={'user_id': user_id})
    
    def force_activate_document(self, doc_id: int) -> Dict[str, Any]:
        """
        Force activate a document (Admin only).
        
        Sets is_active=True regardless of approval status.
        
        Args:
            doc_id (int): Document ID
            
        Returns:
            dict: {'success': bool, 'data': updated document, 'error': str}
        """
        return self._make_request('POST', f'/documents/{doc_id}/force_activate/')
    
    def get_orphaned_documents(self) -> Dict[str, Any]:
        """
        Get documents with deleted owners (Admin only).
        
        Returns:
            dict: {'success': bool, 'data': list of orphaned documents, 'error': str}
        """
        return self._make_request('GET', '/documents/orphaned/')
    
    # ==================== Analytics ====================
    
    def get_analytics(self) -> Dict[str, Any]:
        """
        Get document analytics and statistics (Admin only).
        
        Returns:
            dict: {'success': bool, 'data': analytics data, 'error': str}
                {
                    'total_documents': int,
                    'total_size_mb': float,
                    'total_users': int,
                    'total_downloads': int,
                    'recent_uploads': int,
                    'active_users': int,
                    'categories': [...],
                    'top_documents': [...]
                }
        """
        return self._make_request('GET', '/documents/analytics/')
    
    def get_user_activity(self, action_filter: str = 'all', limit: int = 100) -> Dict[str, Any]:
        """
        Get user activity logs (Admin only).
        
        Args:
            action_filter (str): Filter by action type ('all', 'upload', 'download', etc.)
            limit (int): Maximum number of records to return
            
        Returns:
            dict: {'success': bool, 'data': list of activity logs, 'error': str}
        """
        params = {
            'action': action_filter,
            'limit': limit
        }
        return self._make_request('GET', '/documents/user_activity/', params=params)
    
    # ==================== Bulk Operations ====================
    
    def bulk_delete(self, doc_ids: List[int]) -> Dict[str, Any]:
        """
        Bulk delete documents (move to trash).
        
        Args:
            doc_ids (list): List of document IDs
            
        Returns:
            dict: {'success': bool, 'data': {'deleted': int, 'failed': list}, 'error': str}
        """
        results = {'deleted': 0, 'failed': []}
        
        for doc_id in doc_ids:
            result = self.delete_document(doc_id)
            if result['success']:
                results['deleted'] += 1
            else:
                results['failed'].append({'id': doc_id, 'error': result['error']})
        
        return {
            'success': len(results['failed']) == 0,
            'data': results,
            'error': f"{len(results['failed'])} document(s) failed to delete" if results['failed'] else None
        }
    
    def bulk_restore(self, doc_ids: List[int]) -> Dict[str, Any]:
        """
        Bulk restore documents from trash.
        
        Args:
            doc_ids (list): List of document IDs
            
        Returns:
            dict: {'success': bool, 'data': {'restored': int, 'failed': list}, 'error': str}
        """
        results = {'restored': 0, 'failed': []}
        
        for doc_id in doc_ids:
            result = self.restore_document(doc_id)
            if result['success']:
                results['restored'] += 1
            else:
                results['failed'].append({'id': doc_id, 'error': result['error']})
        
        return {
            'success': len(results['failed']) == 0,
            'data': results,
            'error': f"{len(results['failed'])} document(s) failed to restore" if results['failed'] else None
        }
    
    def bulk_move(self, doc_ids: List[int], folder_id: int = None) -> Dict[str, Any]:
        """
        Bulk move documents to a folder.
        
        Args:
            doc_ids (list): List of document IDs
            folder_id (int): Destination folder ID (None for root)
            
        Returns:
            dict: {'success': bool, 'data': {'moved': int, 'failed': list}, 'error': str}
        """
        results = {'moved': 0, 'failed': []}
        
        for doc_id in doc_ids:
            result = self.move_document(doc_id, folder_id)
            if result['success']:
                results['moved'] += 1
            else:
                results['failed'].append({'id': doc_id, 'error': result['error']})
        
        return {
            'success': len(results['failed']) == 0,
            'data': results,
            'error': f"{len(results['failed'])} document(s) failed to move" if results['failed'] else None
        }
    
    def bulk_permanent_delete(self, doc_ids: List[int]) -> Dict[str, Any]:
        """
        Bulk permanently delete documents (Admin only).
        
        Args:
            doc_ids (list): List of document IDs
            
        Returns:
            dict: {'success': bool, 'data': {'deleted': int, 'failed': list}, 'error': str}
        """
        results = {'deleted': 0, 'failed': []}
        
        for doc_id in doc_ids:
            result = self.permanent_delete_document(doc_id)
            if result['success']:
                results['deleted'] += 1
            else:
                results['failed'].append({'id': doc_id, 'error': result['error']})
        
        return {
            'success': len(results['failed']) == 0,
            'data': results,
            'error': f"{len(results['failed'])} document(s) failed to permanently delete" if results['failed'] else None
        }
