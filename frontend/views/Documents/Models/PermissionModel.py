"""
Permission Models

Data models for document and folder permissions.
Matches backend permission system.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    """User roles matching backend BaseUser.ROLE_CHOICES"""
    ADMIN = 'admin'
    STUDENT = 'student'
    FACULTY = 'faculty'
    STAFF = 'staff'


class ApprovalStatus(str, Enum):
    """Document approval statuses"""
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    RESUBMITTED = 'resubmitted'


@dataclass
class DocumentPermissionModel:
    """
    Data model for role-based document permissions.
    Matches backend DocumentPermission model.
    """
    id: int
    document_id: int
    role: str  # admin, student, faculty, staff
    
    # Permission flags
    can_view: bool = True
    can_download: bool = True
    can_edit: bool = False
    can_delete: bool = False
    
    # Timestamps
    created_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DocumentPermissionModel':
        """Create from dictionary"""
        return cls(
            id=data.get('id', 0),
            document_id=data.get('document_id', 0),
            role=data.get('role', 'student'),
            can_view=data.get('can_view', True),
            can_download=data.get('can_download', True),
            can_edit=data.get('can_edit', False),
            can_delete=data.get('can_delete', False),
            created_at=data.get('created_at')
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'role': self.role,
            'can_view': self.can_view,
            'can_download': self.can_download,
            'can_edit': self.can_edit,
            'can_delete': self.can_delete,
            'created_at': self.created_at
        }
    
    def __str__(self) -> str:
        return f"DocPermission(doc={self.document_id}, role={self.role})"


@dataclass
class FolderPermissionModel:
    """
    Data model for user-specific folder permissions.
    Matches backend FolderPermission model.
    """
    id: int
    folder_id: int
    user_id: int
    username: Optional[str] = None
    
    # Permission flags
    can_view: bool = True
    can_upload: bool = False
    can_edit: bool = False
    can_delete: bool = False
    
    # Timestamps
    created_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FolderPermissionModel':
        """Create from dictionary"""
        return cls(
            id=data.get('id', 0),
            folder_id=data.get('folder_id', 0),
            user_id=data.get('user_id', 0),
            username=data.get('username'),
            can_view=data.get('can_view', True),
            can_upload=data.get('can_upload', False),
            can_edit=data.get('can_edit', False),
            can_delete=data.get('can_delete', False),
            created_at=data.get('created_at')
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'folder_id': self.folder_id,
            'user_id': self.user_id,
            'username': self.username,
            'can_view': self.can_view,
            'can_upload': self.can_upload,
            'can_edit': self.can_edit,
            'can_delete': self.can_delete,
            'created_at': self.created_at
        }
    
    def __str__(self) -> str:
        return f"FolderPermission(folder={self.folder_id}, user={self.username})"


@dataclass
class FolderRolePermissionModel:
    """
    Data model for role-based folder permissions.
    Matches backend FolderRolePermission model.
    """
    id: int
    folder_id: int
    role: str  # admin, student, faculty, staff
    
    # Permission flags
    can_view: bool = True
    can_upload: bool = False
    can_edit: bool = False
    can_delete: bool = False
    
    # Timestamps
    created_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FolderRolePermissionModel':
        """Create from dictionary"""
        return cls(
            id=data.get('id', 0),
            folder_id=data.get('folder_id', 0),
            role=data.get('role', 'student'),
            can_view=data.get('can_view', True),
            can_upload=data.get('can_upload', False),
            can_edit=data.get('can_edit', False),
            can_delete=data.get('can_delete', False),
            created_at=data.get('created_at')
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'folder_id': self.folder_id,
            'role': self.role,
            'can_view': self.can_view,
            'can_upload': self.can_upload,
            'can_edit': self.can_edit,
            'can_delete': self.can_delete,
            'created_at': self.created_at
        }
    
    def __str__(self) -> str:
        return f"FolderRolePermission(folder={self.folder_id}, role={self.role})"


@dataclass
class DocumentApprovalModel:
    """
    Data model for document approval workflow.
    Matches backend DocumentApproval model.
    """
    id: int
    document_id: int
    status: str  # pending, approved, rejected, resubmitted
    
    # Optional fields
    previous_status: Optional[str] = None
    resubmission_count: int = 0
    
    # Timestamps
    submitted_at: Optional[str] = None
    reviewed_at: Optional[str] = None
    last_resubmitted_at: Optional[str] = None
    
    # Review details
    reviewed_by: Optional[str] = None
    reviewed_by_id: Optional[int] = None
    review_notes: Optional[str] = None
    resubmission_notes: Optional[str] = None
    
    @property
    def is_pending(self) -> bool:
        return self.status == ApprovalStatus.PENDING.value
    
    @property
    def is_approved(self) -> bool:
        return self.status == ApprovalStatus.APPROVED.value
    
    @property
    def is_rejected(self) -> bool:
        return self.status == ApprovalStatus.REJECTED.value
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DocumentApprovalModel':
        """Create from dictionary"""
        return cls(
            id=data.get('id', 0),
            document_id=data.get('document_id', 0),
            status=data.get('status', 'pending'),
            previous_status=data.get('previous_status'),
            resubmission_count=data.get('resubmission_count', 0),
            submitted_at=data.get('submitted_at'),
            reviewed_at=data.get('reviewed_at'),
            last_resubmitted_at=data.get('last_resubmitted_at'),
            reviewed_by=data.get('reviewed_by'),
            reviewed_by_id=data.get('reviewed_by_id'),
            review_notes=data.get('review_notes'),
            resubmission_notes=data.get('resubmission_notes')
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'status': self.status,
            'previous_status': self.previous_status,
            'resubmission_count': self.resubmission_count,
            'submitted_at': self.submitted_at,
            'reviewed_at': self.reviewed_at,
            'last_resubmitted_at': self.last_resubmitted_at,
            'reviewed_by': self.reviewed_by,
            'reviewed_by_id': self.reviewed_by_id,
            'review_notes': self.review_notes,
            'resubmission_notes': self.resubmission_notes
        }
    
    def __str__(self) -> str:
        return f"Approval(doc={self.document_id}, status={self.status})"
