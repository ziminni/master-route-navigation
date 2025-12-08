"""
Collection/Folder Model

Data model for collections and folders in the document management system.
Note: Frontend uses "Collections" while backend uses "Folders" (hierarchical).
This model supports both concepts.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class CollectionModel:
    """
    Data model for a collection/folder.
    
    Can represent both:
    - Frontend "Collections" (flat groupings)
    - Backend "Folders" (hierarchical tree structure)
    """
    id: int
    name: str
    
    # Optional fields
    icon: str = 'folder.png'
    description: str = ''
    slug: Optional[str] = None
    
    # Files in this collection
    files: List[dict] = field(default_factory=list)
    
    # Hierarchy fields (for folder structure)
    parent_id: Optional[int] = None
    parent: Optional['CollectionModel'] = None
    subfolders: List['CollectionModel'] = field(default_factory=list)
    
    # Category association
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    
    # Ownership and permissions
    created_by: Optional[str] = None
    created_by_id: Optional[int] = None
    is_public: bool = True
    
    # Timestamps
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    # Soft delete
    deleted_at: Optional[str] = None
    deleted_by: Optional[str] = None
    
    @property
    def file_count(self) -> int:
        """Get number of files in this collection"""
        return len(self.files)
    
    @property
    def is_empty(self) -> bool:
        """Check if collection has no files"""
        return self.file_count == 0
    
    @property
    def is_root(self) -> bool:
        """Check if this is a root folder (no parent)"""
        return self.parent_id is None
    
    @property
    def has_subfolders(self) -> bool:
        """Check if this folder has subfolders"""
        return len(self.subfolders) > 0
    
    @property
    def full_path(self) -> str:
        """
        Get full path of folder (e.g., /Academic/CS101/Lectures).
        For flat collections, just returns the name.
        """
        if self.parent:
            return f"{self.parent.full_path}/{self.name}"
        return f"/{self.name}"
    
    def get_ancestors(self) -> List['CollectionModel']:
        """Get all parent folders up to root"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors
    
    def add_file(self, file_data: dict) -> None:
        """Add a file to this collection"""
        self.files.append(file_data)
    
    def remove_file(self, file_id: int) -> bool:
        """
        Remove a file from this collection by file_id.
        
        Returns:
            True if file was found and removed, False otherwise
        """
        for i, file_data in enumerate(self.files):
            if file_data.get('file_id') == file_id:
                self.files.pop(i)
                return True
        return False
    
    def get_file(self, file_id: int) -> Optional[dict]:
        """Get a file from this collection by file_id"""
        for file_data in self.files:
            if file_data.get('file_id') == file_id:
                return file_data
        return None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CollectionModel':
        """
        Create CollectionModel from dictionary (e.g., from JSON or API response).
        
        Args:
            data: Dictionary containing collection data
            
        Returns:
            CollectionModel instance
        """
        return cls(
            id=data.get('id', 0),
            name=data.get('name', ''),
            icon=data.get('icon', 'folder.png'),
            description=data.get('description', ''),
            slug=data.get('slug'),
            files=data.get('files', []),
            parent_id=data.get('parent_id'),
            parent=None,  # Set separately if needed
            subfolders=[],  # Set separately if needed
            category_id=data.get('category_id'),
            category_name=data.get('category_name'),
            created_by=data.get('created_by'),
            created_by_id=data.get('created_by_id'),
            is_public=data.get('is_public', True),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            deleted_at=data.get('deleted_at'),
            deleted_by=data.get('deleted_by')
        )
    
    def to_dict(self) -> dict:
        """
        Convert CollectionModel to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of the collection
        """
        return {
            'id': self.id,
            'name': self.name,
            'icon': self.icon,
            'description': self.description,
            'slug': self.slug,
            'files': self.files,
            'parent_id': self.parent_id,
            'category_id': self.category_id,
            'category_name': self.category_name,
            'created_by': self.created_by,
            'created_by_id': self.created_by_id,
            'is_public': self.is_public,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'deleted_at': self.deleted_at,
            'deleted_by': self.deleted_by
        }
    
    def __str__(self) -> str:
        return f"Collection({self.id}: {self.name}, {self.file_count} files)"
    
    def __repr__(self) -> str:
        return f"CollectionModel(id={self.id}, name='{self.name}', file_count={self.file_count})"
