"""
Utilities for DocumentsV2 Application

Provides role-based routing and helper functions.
"""

from .role_router import DocumentRoleRouter, is_admin, is_faculty, is_staff, is_student
from .empty_state import EmptyStateWidget, EmptyStateFactory

__all__ = [
    'DocumentRoleRouter',
    'is_admin',
    'is_faculty',
    'is_staff',
    'is_student',
    'EmptyStateWidget',
    'EmptyStateFactory'
]
