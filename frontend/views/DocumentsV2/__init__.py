"""
DocumentsV2 - CISC Virtual Hub Document Management System

A Google Drive-like document management interface built with PyQt6.
Provides file browsing, upload, organization, and approval workflow features.

Main Components:
- MainWindow: Main application window with sidebar, toolbar, and content area
- Sidebar: Navigation panel (My Drive, Recent, Starred, Trash, Categories)
- Toolbar: Action buttons and breadcrumb navigation
- FileListView: Table view for displaying documents
- UploadDialog: Dialog for uploading files with metadata
- DocumentService: Backend API communication

Role-Based Views:
- AdminDocumentView: Full CRUD + Approvals + System Management
- FacultyDocumentView: Upload and manage own documents
- StaffDocumentView: Upload with approval required
- StudentDocumentView: View and download only

Author: CISC Development Team
Version: 2.0
"""

from .DocumentsV2 import DocumentsV2View
from .utils.role_router import DocumentRoleRouter

# Factory function for role-based routing
def create_document_view(username: str, roles: list, primary_role: str, token: str):
    """
    Factory function to create appropriate document view based on user role.
    
    This is the recommended entry point for creating DocumentsV2 views.
    It automatically routes users to the appropriate view (Admin, Faculty, Staff, or Student).
    
    Args:
        username (str): Logged-in username
        roles (list): List of user roles
        primary_role (str): Primary role (admin, faculty, staff, student)
        token (str): JWT authentication token
    
    Returns:
        QWidget: The appropriate role-based document view
    
    Example:
        view = create_document_view(
            username="john.doe",
            roles=["admin"],
            primary_role="admin",
            token="jwt_token_here"
        )
    """
    return DocumentRoleRouter.route_to_view(username, roles, primary_role, token)

__all__ = [
    'DocumentsV2View',
    'DocumentRoleRouter', 
    'create_document_view'
]
__version__ = '2.0.0'
