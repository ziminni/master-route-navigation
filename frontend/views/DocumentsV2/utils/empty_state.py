"""
Empty State Widget

Displays friendly empty state messages when there are no documents to show.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class EmptyStateWidget(QWidget):
    """
    Widget to display empty state with icon, message, and optional action button.
    
    Signals:
        action_clicked: Emitted when action button is clicked
    """
    
    action_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize empty state widget."""
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)
        
        # Icon label
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_font = QFont()
        icon_font.setPointSize(48)
        self.icon_label.setFont(icon_font)
        self.icon_label.setStyleSheet("color: #bbb;")
        layout.addWidget(self.icon_label)
        
        # Title label
        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #666;")
        layout.addWidget(self.title_label)
        
        # Description label
        self.desc_label = QLabel()
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("color: #999; font-size: 13px;")
        layout.addWidget(self.desc_label)
        
        # Action button (optional)
        self.action_button = QPushButton()
        self.action_button.setVisible(False)
        self.action_button.clicked.connect(self.action_clicked.emit)
        self.action_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 10px 24px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        layout.addWidget(self.action_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch()
    
    def set_state(self, icon: str, title: str, description: str, 
                  action_text: str = None):
        """
        Set the empty state content.
        
        Args:
            icon (str): Icon text/emoji to display
            title (str): Main title text
            description (str): Description text
            action_text (str): Optional action button text
        """
        self.icon_label.setText(icon)
        self.title_label.setText(title)
        self.desc_label.setText(description)
        
        if action_text:
            self.action_button.setText(action_text)
            self.action_button.setVisible(True)
        else:
            self.action_button.setVisible(False)


class EmptyStateFactory:
    """Factory for creating pre-configured empty states."""
    
    @staticmethod
    def no_documents(parent=None) -> EmptyStateWidget:
        """Empty state for when there are no documents in current view."""
        widget = EmptyStateWidget(parent)
        widget.set_state(
            icon="📄",
            title="No documents yet",
            description="This folder is empty. Upload your first document to get started.",
            action_text="Upload Document"
        )
        return widget
    
    @staticmethod
    def no_results(parent=None) -> EmptyStateWidget:
        """Empty state for when search returns no results."""
        widget = EmptyStateWidget(parent)
        widget.set_state(
            icon="🔍",
            title="No results found",
            description="Try adjusting your search terms or filters."
        )
        return widget
    
    @staticmethod
    def no_recent(parent=None) -> EmptyStateWidget:
        """Empty state for recent documents view."""
        widget = EmptyStateWidget(parent)
        widget.set_state(
            icon="🕐",
            title="No recent documents",
            description="Documents you access will appear here for quick reference."
        )
        return widget
    
    @staticmethod
    def no_starred(parent=None) -> EmptyStateWidget:
        """Empty state for starred documents view."""
        widget = EmptyStateWidget(parent)
        widget.set_state(
            icon="⭐",
            title="No starred documents",
            description="Star important documents to find them easily later."
        )
        return widget
    
    @staticmethod
    def trash_empty(parent=None) -> EmptyStateWidget:
        """Empty state for trash view."""
        widget = EmptyStateWidget(parent)
        widget.set_state(
            icon="🗑️",
            title="Trash is empty",
            description="Deleted documents will appear here and can be restored within 30 days."
        )
        return widget
    
    @staticmethod
    def no_approvals(parent=None) -> EmptyStateWidget:
        """Empty state for pending approvals view (admin)."""
        widget = EmptyStateWidget(parent)
        widget.set_state(
            icon="✅",
            title="No pending approvals",
            description="All documents have been reviewed. New submissions will appear here."
        )
        return widget
    
    @staticmethod
    def no_uploads(parent=None) -> EmptyStateWidget:
        """Empty state for my uploads view."""
        widget = EmptyStateWidget(parent)
        widget.set_state(
            icon="📤",
            title="No uploads yet",
            description="Documents you upload will appear here.",
            action_text="Upload Document"
        )
        return widget
    
    @staticmethod
    def no_category_documents(category_name: str, parent=None) -> EmptyStateWidget:
        """Empty state for category with no documents."""
        widget = EmptyStateWidget(parent)
        widget.set_state(
            icon="📂",
            title=f"No documents in {category_name}",
            description="This category is empty. Upload documents to this category to see them here.",
            action_text="Upload Document"
        )
        return widget
    
    @staticmethod
    def permission_denied(parent=None) -> EmptyStateWidget:
        """Empty state for when user doesn't have permission."""
        widget = EmptyStateWidget(parent)
        widget.set_state(
            icon="🔒",
            title="Access Denied",
            description="You don't have permission to view documents in this location."
        )
        return widget
    
    @staticmethod
    def error_loading(parent=None) -> EmptyStateWidget:
        """Empty state for when loading fails."""
        widget = EmptyStateWidget(parent)
        widget.set_state(
            icon="⚠️",
            title="Unable to load documents",
            description="An error occurred while loading documents. Please try again.",
            action_text="Retry"
        )
        return widget
