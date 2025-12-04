"""
Analytics Widget - Document Statistics Dashboard

Displays comprehensive document analytics including:
- Total documents count
- Storage usage
- Category distribution
- Upload trends
- Most active users
- Popular documents
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime


class StatCard(QFrame):
    """Single statistic card widget."""
    
    def __init__(self, title: str, value: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            StatCard {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 15px;
            }
            StatCard:hover {
                border: 1px solid #2196F3;
                box-shadow: 0 2px 8px rgba(33, 150, 243, 0.2);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #666; font-size: 13px;")
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(24)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setStyleSheet("color: #2196F3;")
        layout.addWidget(value_label)
        
        # Subtitle (optional)
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet("color: #999; font-size: 11px;")
            layout.addWidget(subtitle_label)
        
        layout.addStretch()


class AnalyticsWidget(QWidget):
    """
    Document analytics dashboard widget.
    
    Displays various statistics and charts about document usage.
    """
    
    refresh_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.analytics_data = {}
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        
        # Overview Stats Grid
        overview_label = QLabel("Overview")
        overview_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        content_layout.addWidget(overview_label)
        
        self.overview_grid = QGridLayout()
        self.overview_grid.setSpacing(15)
        content_layout.addLayout(self.overview_grid)
        
        # Category Distribution
        category_label = QLabel("Category Distribution")
        category_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333; margin-top: 20px;")
        content_layout.addWidget(category_label)
        
        self.category_container = QVBoxLayout()
        content_layout.addLayout(self.category_container)
        
        # Top Documents
        top_docs_label = QLabel("Most Viewed Documents")
        top_docs_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333; margin-top: 20px;")
        content_layout.addWidget(top_docs_label)
        
        self.top_docs_container = QVBoxLayout()
        content_layout.addLayout(self.top_docs_container)
        
        content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
    
    def _create_header(self) -> QWidget:
        """Create header with title and refresh button."""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #2196F3;
                border-bottom: 3px solid #1976D2;
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: white;
                color: #2196F3;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E3F2FD;
            }
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 15, 20, 15)
        
        title = QLabel("Document Analytics")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        from PyQt6.QtWidgets import QPushButton
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        layout.addWidget(refresh_btn)
        
        return header
    
    def update_analytics(self, data: dict):
        """
        Update analytics display with new data.
        
        Args:
            data (dict): Analytics data from API
                {
                    'total_documents': int,
                    'total_size_mb': float,
                    'total_users': int,
                    'total_downloads': int,
                    'categories': [{'name': str, 'count': int, 'size_mb': float}],
                    'top_documents': [{'title': str, 'views': int, 'downloads': int}],
                    'recent_uploads': int (last 7 days),
                    'active_users': int (last 7 days)
                }
        """
        self.analytics_data = data
        
        # Clear existing widgets
        self._clear_layout(self.overview_grid)
        self._clear_layout(self.category_container)
        self._clear_layout(self.top_docs_container)
        
        # Update overview stats
        total_docs = data.get('total_documents', 0)
        total_size = data.get('total_size_mb', 0)
        total_users = data.get('total_users', 0)
        total_downloads = data.get('total_downloads', 0)
        recent_uploads = data.get('recent_uploads', 0)
        active_users = data.get('active_users', 0)
        
        # Create stat cards
        cards = [
            ("Total Documents", str(total_docs), f"{recent_uploads} new this week"),
            ("Storage Used", f"{total_size:.1f} MB", "Across all files"),
            ("Total Users", str(total_users), f"{active_users} active this week"),
            ("Total Downloads", str(total_downloads), "All time"),
        ]
        
        for i, (title, value, subtitle) in enumerate(cards):
            card = StatCard(title, value, subtitle)
            row = i // 2
            col = i % 2
            self.overview_grid.addWidget(card, row, col)
        
        # Update category distribution
        categories = data.get('categories', [])
        if categories:
            for cat in categories:
                cat_widget = self._create_category_bar(
                    cat.get('name', 'Unknown'),
                    cat.get('count', 0),
                    cat.get('size_mb', 0),
                    total_docs
                )
                self.category_container.addWidget(cat_widget)
        else:
            no_data = QLabel("No category data available")
            no_data.setStyleSheet("color: #999; padding: 20px;")
            self.category_container.addWidget(no_data)
        
        # Update top documents
        top_docs = data.get('top_documents', [])
        if top_docs:
            for doc in top_docs[:10]:  # Top 10
                doc_widget = self._create_document_row(
                    doc.get('title', 'Untitled'),
                    doc.get('views', 0),
                    doc.get('downloads', 0)
                )
                self.top_docs_container.addWidget(doc_widget)
        else:
            no_data = QLabel("No document data available")
            no_data.setStyleSheet("color: #999; padding: 20px;")
            self.top_docs_container.addWidget(no_data)
    
    def _create_category_bar(self, name: str, count: int, size_mb: float, total: int) -> QWidget:
        """Create a horizontal bar for category distribution."""
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Category name
        name_label = QLabel(name)
        name_label.setMinimumWidth(150)
        name_label.setStyleSheet("font-weight: bold; color: #333;")
        layout.addWidget(name_label)
        
        # Progress bar (visual representation)
        bar_container = QWidget()
        bar_container.setStyleSheet("background-color: #F5F5F5; border-radius: 4px;")
        bar_container.setMinimumHeight(20)
        bar_layout = QHBoxLayout(bar_container)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        
        percentage = (count / total * 100) if total > 0 else 0
        bar_fill = QWidget()
        bar_fill.setStyleSheet(f"""
            background-color: #2196F3;
            border-radius: 4px;
        """)
        bar_fill.setFixedWidth(int(bar_container.width() * percentage / 100))
        
        layout.addWidget(bar_container, stretch=1)
        
        # Stats
        stats_label = QLabel(f"{count} docs • {size_mb:.1f} MB • {percentage:.1f}%")
        stats_label.setStyleSheet("color: #666;")
        layout.addWidget(stats_label)
        
        return widget
    
    def _create_document_row(self, title: str, views: int, downloads: int) -> QWidget:
        """Create a row for top document."""
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 8px;
            }
            QFrame:hover {
                background-color: #F5F5F5;
            }
        """)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 8, 10, 8)
        
        # Document icon and title
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #333; font-weight: bold;")
        layout.addWidget(title_label, stretch=1)
        
        # Views
        views_label = QLabel(f"Views: {views}")
        views_label.setStyleSheet("color: #666;")
        layout.addWidget(views_label)
        
        # Downloads
        downloads_label = QLabel(f"Downloads: {downloads}")
        downloads_label.setStyleSheet("color: #666; margin-left: 15px;")
        layout.addWidget(downloads_label)
        
        return widget
    
    def _clear_layout(self, layout):
        """Remove all widgets from layout."""
        if layout is None:
            return
        
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
    
    def show_loading(self):
        """Show loading state."""
        # Clear existing
        self._clear_layout(self.overview_grid)
        self._clear_layout(self.category_container)
        self._clear_layout(self.top_docs_container)
        
        # Show loading message
        loading = QLabel("Loading analytics...")
        loading.setStyleSheet("color: #666; padding: 20px; font-size: 14px;")
        loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.category_container.addWidget(loading)
    
    def show_error(self, message: str):
        """Show error state."""
        self._clear_layout(self.overview_grid)
        self._clear_layout(self.category_container)
        self._clear_layout(self.top_docs_container)
        
        error = QLabel(f"Error loading analytics:\n{message}")
        error.setStyleSheet("color: #F44336; padding: 20px; font-size: 14px;")
        error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.category_container.addWidget(error)
