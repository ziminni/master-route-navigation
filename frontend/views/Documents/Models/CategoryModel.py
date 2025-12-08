"""
Category Model

Data model for document categories.
Matches backend Category model.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CategoryModel:
    """
    Data model for a document category.
    
    Categories are used to organize documents and folders
    (e.g., Academic, Administrative, Projects).
    """
    id: int
    name: str
    slug: str
    
    # Optional fields
    description: Optional[str] = None
    icon: str = ''
    display_order: int = 0
    
    # Timestamps
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CategoryModel':
        """
        Create CategoryModel from dictionary.
        
        Args:
            data: Dictionary containing category data
            
        Returns:
            CategoryModel instance
        """
        return cls(
            id=data.get('id', 0),
            name=data.get('name', ''),
            slug=data.get('slug', ''),
            description=data.get('description'),
            icon=data.get('icon', ''),
            display_order=data.get('display_order', 0),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'icon': self.icon,
            'display_order': self.display_order,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def __str__(self) -> str:
        return f"Category({self.id}: {self.name})"
    
    def __repr__(self) -> str:
        return f"CategoryModel(id={self.id}, name='{self.name}')"
