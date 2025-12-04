"""
Widgets package for DocumentsV2

Contains reusable UI components for the document management interface.
"""

from .sidebar import Sidebar
from .toolbar import Toolbar
from .file_list import FileListView
from .breadcrumb import BreadcrumbBar
from .analytics_widget import AnalyticsWidget
from .user_activity_widget import UserActivityWidget
from .bulk_operations_widget import BulkOperationsWidget

__all__ = [
    'Sidebar', 'Toolbar', 'FileListView', 'BreadcrumbBar',
    'AnalyticsWidget', 'UserActivityWidget', 'BulkOperationsWidget'
]
