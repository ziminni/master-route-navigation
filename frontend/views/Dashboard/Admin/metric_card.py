from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class MetricCard(QFrame):
    """Clean metric card for KPIs (no borders inside)."""
    clicked = pyqtSignal(str)
    
    def __init__(self, title, value="", subtitle="", width=220, height=120, 
                 bg_color="#ffffff", border_color="#e5e7eb", hover_bg="#f9fafb", 
                 hover_border="#d1d5db", text_color="#6b7280", title_color="#111827"):
        super().__init__()
        self.title = title
        self.value = value
        self.subtitle = subtitle
        
        # Customizable properties
        self.bg_color = bg_color
        self.border_color = border_color
        self.hover_bg = hover_bg
        self.hover_border = hover_border
        self.text_color = text_color
        self.title_color = title_color
        
        self._setup_ui(width, height)
        self._apply_styles()
    
    def _setup_ui(self, width, height):
        self.setFrameShape(QFrame.Shape.NoFrame)  # ✅ no inner frame
        self.setFixedSize(width, height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        
        # Title
        self.title_label = QLabel(self.title)
        self.title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.title_label.setStyleSheet(f"color: {self.title_color}; border: none;")
        
        # Value
        self.value_label = QLabel(self.value)
        self.value_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.value_label.setStyleSheet(f"color: {self.title_color}; margin: 8px 0px; border: none;")
        
        # Subtitle
        self.subtitle_label = QLabel(self.subtitle)
        self.subtitle_label.setFont(QFont("Arial", 8))
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.subtitle_label.setStyleSheet(f"color: {self.text_color}; border: none;")
        self.subtitle_label.setWordWrap(True)
        
        layout.addWidget(self.title_label)
        if self.value:
            layout.addWidget(self.value_label)
        if self.subtitle:
            layout.addWidget(self.subtitle_label)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def _apply_styles(self):
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
    
    def update_metric(self, title=None, value=None, subtitle=None):
        if title is not None:
            self.title = title
            self.title_label.setText(title)
        if value is not None:
            self.value = value
            self.value_label.setText(value)
        if subtitle is not None:
            self.subtitle = subtitle
            self.subtitle_label.setText(subtitle)
    
    def set_colors(self, bg_color=None, border_color=None, hover_bg=None, 
                   hover_border=None, text_color=None, title_color=None):
        if bg_color:
            self.bg_color = bg_color
        if border_color:
            self.border_color = border_color
        if hover_bg:
            self.hover_bg = hover_bg
        if hover_border:
            self.hover_border = hover_border
        if text_color:
            self.text_color = text_color
            self.subtitle_label.setStyleSheet(f"color: {self.text_color}; border: none;")
        if title_color:
            self.title_color = title_color
            self.title_label.setStyleSheet(f"color: {self.title_color}; border: none;")
            self.value_label.setStyleSheet(f"color: {self.title_color}; margin: 8px 0px; border: none;")
        
        self._apply_styles()

    def mousePressEvent(self, event):
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

class SpecialMetricCard(MetricCard):
    """Specialized metric card with status colors."""
    def __init__(self, title, value="", subtitle="", status="normal", **kwargs):
        self.status = status
        super().__init__(title, value, subtitle, **kwargs)
        self._apply_status_styling()
    
    def _apply_status_styling(self):
        status_colors = {
            "success": {"border": "#10b981", "bg": "#f0fdf4"},
            "warning": {"border": "#f59e0b", "bg": "#fffbeb"},
            "error": {"border": "#ef4444", "bg": "#fef2f2"},
            "normal": {"border": self.border_color, "bg": self.bg_color}
        }
        colors = status_colors.get(self.status, status_colors["normal"])
        self.set_colors(bg_color=colors["bg"], border_color=colors["border"])
