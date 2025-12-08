"""
Role-based Router for DocumentsV2

Routes users to appropriate document management views based on their role.
Admin users get additional tools for approvals, permanent delete, and system management.
"""

from typing import Optional
from PyQt6.QtWidgets import QWidget


class DocumentRoleRouter:
    """
    Router for DocumentsV2 role-based views.
    
    Routes users to appropriate document management interfaces:
    - Admin: Full CRUD + Approvals + System Management
    - Faculty: Upload, Manage own documents, View approvals
    - Staff: Upload with approval, View documents
    - Student: View and download only
    """
    
    # Role hierarchy
    ROLE_HIERARCHY = {
        'admin': ['admin', 'super_admin', 'administrator'],
        'faculty': ['faculty', 'dean', 'professor', 'instructor', 'teacher'],
        'staff': ['staff', 'registrar', 'hr', 'clerk', 'secretary', 'org_officer', 'officer'],
        'student': ['student', 'learner']
    }
    
    @staticmethod
    def is_admin(primary_role: str = None, roles: list = None) -> bool:
        """Check if user has admin privileges."""
        if primary_role and primary_role.lower() in DocumentRoleRouter.ROLE_HIERARCHY['admin']:
            return True
        if roles:
            return any(role.lower() in DocumentRoleRouter.ROLE_HIERARCHY['admin'] for role in roles)
        return False
    
    @staticmethod
    def is_faculty(primary_role: str = None, roles: list = None) -> bool:
        """Check if user has faculty privileges."""
        if primary_role and primary_role.lower() in DocumentRoleRouter.ROLE_HIERARCHY['faculty']:
            return True
        if roles:
            return any(role.lower() in DocumentRoleRouter.ROLE_HIERARCHY['faculty'] for role in roles)
        return False
    
    @staticmethod
    def is_staff(primary_role: str = None, roles: list = None) -> bool:
        """Check if user has staff privileges."""
        if primary_role and primary_role.lower() in DocumentRoleRouter.ROLE_HIERARCHY['staff']:
            return True
        if roles:
            return any(role.lower() in DocumentRoleRouter.ROLE_HIERARCHY['staff'] for role in roles)
        return False
    
    @staticmethod
    def is_student(primary_role: str = None, roles: list = None) -> bool:
        """Check if user has student role."""
        if primary_role and primary_role.lower() in DocumentRoleRouter.ROLE_HIERARCHY['student']:
            return True
        if roles:
            return any(role.lower() in DocumentRoleRouter.ROLE_HIERARCHY['student'] for role in roles)
        return False
    
    @staticmethod
    def get_primary_role(primary_role: str = None, roles: list = None) -> str:
        """
        Get the primary role category.
        
        Returns:
            str: 'admin', 'faculty', 'staff', 'student', or 'guest'
        """
        if primary_role:
            role_lower = primary_role.lower()
            for primary, sub_roles in DocumentRoleRouter.ROLE_HIERARCHY.items():
                if role_lower in [r.lower() for r in sub_roles]:
                    return primary
        
        if roles:
            for role in roles:
                role_lower = role.lower()
                for primary, sub_roles in DocumentRoleRouter.ROLE_HIERARCHY.items():
                    if role_lower in [r.lower() for r in sub_roles]:
                        return primary
        
        return 'guest'
    
    @staticmethod
    def route_to_view(username: str, roles: list, primary_role: str, token: str) -> Optional[QWidget]:
        """
        Route user to appropriate DocumentsV2 view based on role.
        
        Args:
            username (str): User's username
            roles (list): List of user roles
            primary_role (str): User's primary role
            token (str): JWT authentication token
            
        Returns:
            QWidget: The appropriate document management view
            
        Example:
            view = DocumentRoleRouter.route_to_view(
                username="john.doe",
                roles=["admin"],
                primary_role="admin",
                token="jwt_token_here"
            )
        """
        from ..users import AdminDocumentView, FacultyDocumentView, StaffDocumentView, StudentDocumentView
        
        role_type = DocumentRoleRouter.get_primary_role(primary_role, roles)
        
        view_map = {
            'admin': AdminDocumentView,
            'faculty': FacultyDocumentView,
            'staff': StaffDocumentView,
            'student': StudentDocumentView,
        }
        
        view_class = view_map.get(role_type, StudentDocumentView)  # Default to student view
        return view_class(username, roles, primary_role, token)


# Convenience functions
def is_admin(primary_role: str = None, roles: list = None) -> bool:
    """Quick check if user is admin."""
    return DocumentRoleRouter.is_admin(primary_role, roles)


def is_faculty(primary_role: str = None, roles: list = None) -> bool:
    """Quick check if user is faculty."""
    return DocumentRoleRouter.is_faculty(primary_role, roles)


def is_staff(primary_role: str = None, roles: list = None) -> bool:
    """Quick check if user is staff."""
    return DocumentRoleRouter.is_staff(primary_role, roles)


def is_student(primary_role: str = None, roles: list = None) -> bool:
    """Quick check if user is student."""
    return DocumentRoleRouter.is_student(primary_role, roles)
