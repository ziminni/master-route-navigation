"""
Role-based Document Management Views

Provides specialized document management interfaces for each user role.
"""

from .admin_view import AdminDocumentView
from .faculty_view import FacultyDocumentView
from .staff_view import StaffDocumentView
from .student_view import StudentDocumentView

__all__ = [
    'AdminDocumentView',
    'FacultyDocumentView',
    'StaffDocumentView',
    'StudentDocumentView'
]
