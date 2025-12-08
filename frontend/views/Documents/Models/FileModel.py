"""
File Model

Data model for documents/files in the document management system.
Matches backend Document model structure.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class FileModel:
    """
    Data model for a file/document.
    
    Matches backend Document model with fields relevant for UI display.
    """
    file_id: int
    filename: str
    extension: str
    file_path: str
    category: str
    uploader: str
    role: str
    uploaded_date: str
    timestamp: str
    
    # Optional fields
    title: Optional[str] = None
    description: Optional[str] = None
    time: Optional[str] = None  # Display time (e.g., "02:30 pm")
    file_size: Optional[int] = None  # Size in bytes
    mime_type: Optional[str] = None
    
    # Foreign keys (IDs)
    category_id: Optional[int] = None
    folder_id: Optional[int] = None
    document_type_id: Optional[int] = None
    uploaded_by_id: Optional[int] = None
    
    # Status fields
    is_deleted: bool = False
    is_active: bool = True
    is_featured: bool = False
    view_count: int = 0
    
    # Approval workflow fields
    approval_status: str = 'approved'  # pending, approved, rejected, resubmitted
    requires_approval: bool = False
    
    # Soft delete fields
    deleted_at: Optional[str] = None
    deleted_by: Optional[str] = None
    recycle_bin_path: Optional[str] = None
    
    # Collection tracking
    collection: Optional[str] = None
    collection_id: Optional[int] = None
    _original_collections: List[int] = field(default_factory=list)  # For restore
    
    @property
    def display_name(self) -> str:
        """Get display name with extension"""
        if self.title:
            return self.title
        return f"{self.filename}.{self.extension}" if self.extension else self.filename
    
    @property
    def file_size_mb(self) -> float:
        """Get file size in megabytes"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0.0
    
    @property
    def needs_approval(self) -> bool:
        """Check if file is pending approval"""
        return self.approval_status == 'pending'
    
    @property
    def is_approved(self) -> bool:
        """Check if file is approved"""
        return self.approval_status == 'approved'
    
    @property
    def is_rejected(self) -> bool:
        """Check if file is rejected"""
        return self.approval_status == 'rejected'
    
    @property
    def can_be_downloaded(self) -> bool:
        """Check if file can be downloaded"""
        if not self.is_active:
            return False
        if self.requires_approval:
            return self.is_approved
        return True
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FileModel':
        """
        Create FileModel from dictionary (e.g., from JSON or API response).
        
        Args:
            data: Dictionary containing file data
            
        Returns:
            FileModel instance
        """
        return cls(
            file_id=data.get('file_id', 0),
            filename=data.get('filename', ''),
            extension=data.get('extension', ''),
            file_path=data.get('file_path', ''),
            category=data.get('category', 'None'),
            uploader=data.get('uploader', ''),
            role=data.get('role', ''),
            uploaded_date=data.get('uploaded_date', ''),
            timestamp=data.get('timestamp', ''),
            title=data.get('title'),
            description=data.get('description'),
            time=data.get('time'),
            file_size=data.get('file_size'),
            mime_type=data.get('mime_type'),
            category_id=data.get('category_id'),
            folder_id=data.get('folder_id'),
            document_type_id=data.get('document_type_id'),
            uploaded_by_id=data.get('uploaded_by_id'),
            is_deleted=data.get('is_deleted', False),
            is_active=data.get('is_active', True),
            is_featured=data.get('is_featured', False),
            view_count=data.get('view_count', 0),
            approval_status=data.get('approval_status', 'approved'),
            requires_approval=data.get('requires_approval', False),
            deleted_at=data.get('deleted_at'),
            deleted_by=data.get('deleted_by'),
            recycle_bin_path=data.get('recycle_bin_path'),
            collection=data.get('collection'),
            collection_id=data.get('collection_id'),
            _original_collections=data.get('_original_collections', [])
        )
    
    def to_dict(self) -> dict:
        """
        Convert FileModel to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of the file
        """
        return {
            'file_id': self.file_id,
            'filename': self.filename,
            'extension': self.extension,
            'file_path': self.file_path,
            'category': self.category,
            'uploader': self.uploader,
            'role': self.role,
            'uploaded_date': self.uploaded_date,
            'timestamp': self.timestamp,
            'title': self.title,
            'description': self.description,
            'time': self.time,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'category_id': self.category_id,
            'folder_id': self.folder_id,
            'document_type_id': self.document_type_id,
            'uploaded_by_id': self.uploaded_by_id,
            'is_deleted': self.is_deleted,
            'is_active': self.is_active,
            'is_featured': self.is_featured,
            'view_count': self.view_count,
            'approval_status': self.approval_status,
            'requires_approval': self.requires_approval,
            'deleted_at': self.deleted_at,
            'deleted_by': self.deleted_by,
            'recycle_bin_path': self.recycle_bin_path,
            'collection': self.collection,
            'collection_id': self.collection_id,
            '_original_collections': self._original_collections
        }
    
    def __str__(self) -> str:
        return f"File({self.file_id}: {self.display_name})"
    
    def __repr__(self) -> str:
        return f"FileModel(file_id={self.file_id}, filename='{self.filename}', uploader='{self.uploader}')"
