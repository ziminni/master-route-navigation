"""
Empty State Widget

Reusable empty state component for displaying when no data is available.
Provides consistent UX across all views with customizable messages and actions.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt, pyqtSignal
import os
import sys

# Import IconLoader for consistent icon management
# Handle both relative and absolute imports for flexibility
try:
    from ..utils.icon_utils import IconLoader
except ImportError:
    # Fallback for when running as script (not as package)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    utils_dir = os.path.join(current_dir, '..', 'utils')
    sys.path.insert(0, utils_dir)
    from ..utils.icon_utils import IconLoader


class EmptyStateWidget(QWidget):
    """
    Reusable empty state widget with icon, message, and optional action button.
    
    This widget provides a consistent empty state experience across all views.
    Backend-ready: Shows when API returns empty arrays or loading fails.
    
    Signals:
        action_clicked: Emitted when the action button is clicked
    
    Args:
        icon_name (str): Name of icon file from assets folder (default: 'folder-open.png')
        title (str): Main title text (default: "No Data Available")
        message (str): Descriptive message text (default: "There's nothing here yet.")
        action_text (str, optional): Text for action button (None = no button)
        parent (QWidget, optional): Parent widget
    
    Example:
        >>> empty_state = EmptyStateWidget(
        ...     icon_name="document.png",
        ...     title="No Files Yet",
        ...     message="Upload your first file to get started",
        ...     action_text="Upload File"
        ... )
        >>> empty_state.action_clicked.connect(self.handle_upload)
    """
    
    action_clicked = pyqtSignal()
    
    def __init__(self, icon_name="folder-open.png", title="No Data Available", 
                 message="There's nothing here yet.", action_text=None, parent=None):
        super().__init__(parent)
        
        self.icon_name = icon_name
        self.title = title
        self.message = message
        self.action_text = action_text
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the empty state UI"""
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setSpacing(20)
        
        # Icon
        icon_label = self._create_icon_label()
        if icon_label:
            main_layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Title
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Poppins", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #666666;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Message
        message_label = QLabel(self.message)
        message_label.setFont(QFont("Poppins", 12))
        message_label.setStyleSheet("color: #999999;")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setWordWrap(True)
        message_label.setMaximumWidth(400)
        main_layout.addWidget(message_label)
        
        # Action button (optional)
        if self.action_text:
            action_btn = QPushButton(self.action_text)
            action_btn.setFont(QFont("Poppins", 12, QFont.Weight.Bold))
            action_btn.setStyleSheet("""
                QPushButton {
                    background-color: #084924;
                    color: white;
                    padding: 12px 24px;
                    border: none;
                    border-radius: 6px;
                    min-width: 150px;
                }
                QPushButton:hover {
                    background-color: #064018;
                }
                QPushButton:pressed {
                    background-color: #053515;
                }
            """)
            action_btn.clicked.connect(self.action_clicked.emit)
            main_layout.addWidget(action_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Add stretch to push content to center
        main_layout.addStretch()
        
        self.setLayout(main_layout)
    
    def _create_icon_label(self):
        """
        Create icon label using IconLoader utility for consistent icon management.
        
        Benefits of using IconLoader:
        - Automatic caching for performance
        - Consistent error handling
        - Centralized asset path management
        - Fallback handling
        """
        try:
            # Use IconLoader for consistent icon loading with caching
            pixmap = IconLoader.load_icon(self.icon_name, size=(128, 128))
            
            if pixmap:
                # Create label with pixmap
                icon_label = QLabel()
                icon_label.setPixmap(pixmap)
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Apply gray filter for subdued look
                icon_label.setStyleSheet("opacity: 0.5;")
                
                return icon_label
            else:
                # IconLoader already handles warning messages
                return None
                
        except Exception as e:
            print(f"Error creating icon label: {e}")
            return None
    
    def update_content(self, title=None, message=None, action_text=None):
        """
        Update the empty state content dynamically.
        
        Args:
            title (str, optional): New title text
            message (str, optional): New message text
            action_text (str, optional): New action button text (None = hide button)
        """
        if title:
            self.title = title
        if message:
            self.message = message
        if action_text is not None:
            self.action_text = action_text
        
        # Rebuild UI
        # Clear existing layout
        for i in reversed(range(self.layout().count())):
            item = self.layout().itemAt(i)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # Clear nested layout
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
        
        # Reinitialize UI with new content
        self.init_ui()


class LoadingStateWidget(QWidget):
    """
    Loading state widget with spinner and message.
    
    Use this while fetching data from backend API.
    
    Args:
        message (str): Loading message (default: "Loading...")
        parent (QWidget, optional): Parent widget
    """
    
    def __init__(self, message="Loading...", parent=None):
        super().__init__(parent)
        
        self.message = message
        self.init_ui()
    
    def init_ui(self):
        """Initialize the loading state UI"""
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setSpacing(15)
        
        # Spinner using IconLoader (fallback to emoji if loading.png not found)
        spinner_label = self._create_spinner_icon()
        if spinner_label:
            main_layout.addWidget(spinner_label)
        
        # Message
        message_label = QLabel(self.message)
        message_label.setFont(QFont("Poppins", 14))
        message_label.setStyleSheet("color: #666666;")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(message_label)
        
        # Add stretch to push content to center
        main_layout.addStretch()
        
        self.setLayout(main_layout)
    
    def _create_spinner_icon(self):
        """
        Create spinner icon using IconLoader with fallback to emoji.
        
        Tries to load 'loading.png' or 'spinner.png', falls back to emoji if not found.
        """
        # Try multiple common spinner icon names
        spinner_icons = ['loading.png', 'spinner.png', 'refresh.png']
        
        for icon_name in spinner_icons:
            pixmap = IconLoader.load_icon(icon_name, size=(64, 64))
            if pixmap:
                spinner_label = QLabel()
                spinner_label.setPixmap(pixmap)
                spinner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Add subtle animation effect with CSS
                spinner_label.setStyleSheet("""
                    QLabel {
                        border-radius: 32px;
                        background-color: rgba(8, 73, 36, 0.1);
                        padding: 16px;
                    }
                """)
                return spinner_label
        
        # Fallback to emoji if no icon found
        spinner_label = QLabel("⏳")
        spinner_label.setFont(QFont("Segoe UI Emoji", 48))
        spinner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return spinner_label


class ErrorStateWidget(QWidget):
    """
    Error state widget for when data loading fails.
    
    Use this when API calls fail or errors occur.
    
    Signals:
        retry_clicked: Emitted when the retry button is clicked
    
    Args:
        title (str): Error title (default: "Something Went Wrong")
        message (str): Error message (default: "Failed to load data.")
        show_retry (bool): Whether to show retry button (default: True)
        parent (QWidget, optional): Parent widget
    """
    
    retry_clicked = pyqtSignal()
    
    def __init__(self, title="Something Went Wrong", 
                 message="Failed to load data. Please try again.",
                 show_retry=True, parent=None):
        super().__init__(parent)
        
        self.title = title
        self.message = message
        self.show_retry = show_retry
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the error state UI"""
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setSpacing(20)
        
        # Error icon using IconLoader (fallback to emoji)
        error_icon = self._create_error_icon()
        if error_icon:
            main_layout.addWidget(error_icon)
        
        # Title
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Poppins", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #d9534f;")  # Red color for errors
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Message
        message_label = QLabel(self.message)
        message_label.setFont(QFont("Poppins", 12))
        message_label.setStyleSheet("color: #666666;")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setWordWrap(True)
        message_label.setMaximumWidth(400)
        main_layout.addWidget(message_label)
        
        # Retry button (optional)
        if self.show_retry:
            retry_btn = QPushButton("Retry")
            retry_btn.setFont(QFont("Poppins", 12, QFont.Weight.Bold))
            retry_btn.setStyleSheet("""
                QPushButton {
                    background-color: #d9534f;
                    color: white;
                    padding: 12px 24px;
                    border: none;
                    border-radius: 6px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #c9302c;
                }
                QPushButton:pressed {
                    background-color: #ac2925;
                }
            """)
            retry_btn.clicked.connect(self.retry_clicked.emit)
            main_layout.addWidget(retry_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Add stretch to push content to center
        main_layout.addStretch()
        
        self.setLayout(main_layout)
    
    def _create_error_icon(self):
        """
        Create error icon using IconLoader with fallback to emoji.
        
        Tries to load error-related icons, falls back to warning emoji if not found.
        """
        # Try multiple common error icon names
        error_icons = ['error.png', 'warning.png', 'alert.png', 'exclamation.png']
        
        for icon_name in error_icons:
            pixmap = IconLoader.load_icon(icon_name, size=(64, 64))
            if pixmap:
                error_label = QLabel()
                error_label.setPixmap(pixmap)
                error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Add error-themed styling
                error_label.setStyleSheet("""
                    QLabel {
                        border-radius: 32px;
                        background-color: rgba(217, 83, 79, 0.1);
                        padding: 16px;
                    }
                """)
                return error_label
        
        # Fallback to emoji if no icon found
        error_label = QLabel("⚠️")
        error_label.setFont(QFont("Segoe UI Emoji", 64))
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return error_label
