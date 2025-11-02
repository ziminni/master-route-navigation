from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class ChartCard(QFrame):
    """
    Customizable chart card component for displaying data visualizations.
    Cleaner design: no borders on text, minimal styling.
    """
    clicked = pyqtSignal(str)
    action_clicked = pyqtSignal(str, str)  # card_title, action_name
    
    def __init__(self, title, subtitle="", width=350, height=260, 
                 bg_color="#ffffff", border_color="#e5e7eb", hover_bg="#f9fafb", 
                 hover_border="#d1d5db", show_actions=False):
        super().__init__()
        self.title = title
        self.subtitle = subtitle
        self.show_actions = show_actions
        
        # Customizable properties
        self.bg_color = bg_color
        self.border_color = border_color
        self.hover_bg = hover_bg
        self.hover_border = hover_border
        
        self._setup_ui(width, height)
        self._apply_styles()
    
    def _setup_ui(self, width, height):
        """Setup the UI components of the chart card."""
        self.setFrameShape(QFrame.Shape.NoFrame)   # ✅ no visible frame
        self.setFixedSize(width, height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        # Header section
        header_layout = QHBoxLayout()
        
        # Title and subtitle container
        text_container = QVBoxLayout()
        text_container.setSpacing(2)
        
        # Title
        self.title_label = QLabel(self.title)
        self.title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #111827; border: none;")
        
        # Subtitle
        self.subtitle_label = QLabel(self.subtitle)
        self.subtitle_label.setFont(QFont("Arial", 10))
        self.subtitle_label.setStyleSheet("color: #6b7280; border: none;")
        self.subtitle_label.setWordWrap(True)
        
        text_container.addWidget(self.title_label)
        if self.subtitle:
            text_container.addWidget(self.subtitle_label)
        
        header_layout.addLayout(text_container)
        header_layout.addStretch()
        
        # Action buttons (optional)
        if self.show_actions:
            self.actions_layout = QHBoxLayout()
            header_layout.addLayout(self.actions_layout)
        
        main_layout.addLayout(header_layout)

        # Chart content area
        self.chart_container = QVBoxLayout()
        self.chart_placeholder = QLabel("📈 Chart Area")
        self.chart_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chart_placeholder.setStyleSheet("""
            background-color: #f9fafb;
            border: 2px dashed #d1d5db;
            border-radius: 8px;
            color: #9ca3af;
            font-size: 14px;
            padding: 40px;
        """)
        
        self.chart_container.addWidget(self.chart_placeholder)
        main_layout.addLayout(self.chart_container)
        
        self.setLayout(main_layout)
    
    def _apply_styles(self):
        """Apply the default styling to the card (no inner borders)."""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.bg_color};
                border: 1px solid {self.border_color};
                border-radius: 12px;
            }}
            QFrame:hover {{
                background-color: {self.hover_bg};
                border-color: {self.hover_border};
            }}
        """)
    
    def add_action_button(self, text, action_name):
        """Add an action button to the chart card header."""
        if not self.show_actions:
            return
            
        button = QPushButton(text)
        button.setFont(QFont("Arial", 9))
        button.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                margin-left: 8px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
            }
        """)
        button.clicked.connect(lambda: self.action_clicked.emit(self.title, action_name))
        self.actions_layout.addWidget(button)
    
    def set_chart_content(self, widget):
        """Replace the chart placeholder with actual chart widget."""
        for i in reversed(range(self.chart_container.count())):
            child = self.chart_container.itemAt(i).widget()
            if child:
                child.setParent(None)
        self.chart_container.addWidget(widget)
    
    def update_content(self, title=None, subtitle=None):
        """Update the chart card content dynamically."""
        if title is not None:
            self.title = title
            self.title_label.setText(title)
        if subtitle is not None:
            self.subtitle = subtitle
            self.subtitle_label.setText(subtitle)
    
    def set_colors(self, bg_color=None, border_color=None, hover_bg=None, hover_border=None):
        """Customize the card colors."""
        if bg_color:
            self.bg_color = bg_color
        if border_color:
            self.border_color = border_color
        if hover_bg:
            self.hover_bg = hover_bg
        if hover_border:
            self.hover_border = hover_border
        self._apply_styles()

    def mousePressEvent(self, event):
        """Handle mouse press events with visual feedback."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: #e5e7eb;
                    border: 1px solid #d1d5db;
                    border-radius: 12px;
                }}
            """)
            self.clicked.emit(self.title)
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        self._apply_styles()
        super().mouseReleaseEvent(event)

class InteractiveChartCard(ChartCard):
    """ Enhanced chart card with built-in interactivity features. """
    def __init__(self, title, subtitle="", chart_type="line", **kwargs):
        self.chart_type = chart_type
        super().__init__(title, subtitle, show_actions=True, **kwargs)
        self._setup_default_actions()
    
    def _setup_default_actions(self):
        self.add_action_button("Export", "export")
        self.add_action_button("Refresh", "refresh")
        if self.chart_type in ["line", "bar"]:
            self.add_action_button("Filter", "filter")
