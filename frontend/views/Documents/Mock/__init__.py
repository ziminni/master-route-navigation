"""
Mock Data Package
"""

from .data_loader import (
    get_uploaded_files,
    get_deleted_files,
    get_collections,
    get_collection_by_name,
    get_storage_data,
    get_all_mock_data
)
from .initializer import (
    initialize_documents_data,
    ensure_data_integrity
)

__all__ = [
    'get_uploaded_files',
    'get_deleted_files',
    'get_collections',
    'get_collection_by_name',
    'get_storage_data',
    'get_all_mock_data',
    'initialize_documents_data',
    'ensure_data_integrity'
]
