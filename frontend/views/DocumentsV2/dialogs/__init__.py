"""
Dialogs package for DocumentsV2

Contains dialog windows for various operations.
"""

from .upload_dialog import UploadDialog
from .folder_dialog import FolderDialog
from .category_dialog import CategoryDialog
from .approval_dialog import ApprovalDialog
from .download_dialog import DownloadDialog
from .move_dialog import MoveDialog

__all__ = ['UploadDialog', 'FolderDialog', 'CategoryDialog', 'ApprovalDialog', 'DownloadDialog', 'MoveDialog']
