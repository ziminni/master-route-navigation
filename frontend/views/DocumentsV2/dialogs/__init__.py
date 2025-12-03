"""
Dialogs package for DocumentsV2

Contains dialog windows for various operations.
"""

from .upload_dialog import UploadDialog
from .folder_dialog import FolderDialog
from .category_dialog import CategoryDialog
from .approval_dialog import ApprovalDialog

__all__ = ['UploadDialog', 'FolderDialog', 'CategoryDialog', 'ApprovalDialog']
