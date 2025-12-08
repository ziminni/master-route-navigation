"""
Models Package

Data models for the document management system.
These models match the backend Django models structure.
"""

from .FileModel import FileModel
from .CollectionModel import CollectionModel
from .CategoryModel import CategoryModel
from .PermissionModel import (
    DocumentPermissionModel,
    FolderPermissionModel,
    FolderRolePermissionModel,
    DocumentApprovalModel,
    UserRole,
    ApprovalStatus
)

__all__ = [
    'FileModel',
    'CollectionModel',
    'CategoryModel',
    'DocumentPermissionModel',
    'FolderPermissionModel',
    'FolderRolePermissionModel',
    'DocumentApprovalModel',
    'UserRole',
    'ApprovalStatus'
]
