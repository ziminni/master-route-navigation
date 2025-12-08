"""
User Activity Monitoring Widget

Displays real-time user activity including:
- Recent user actions
- Active users
- Document access logs
- Upload/download activity
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QLabel, QFrame, QScrollArea,
    QPushButton, QComboBox, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime


class UserActivityWidget(QWidget):
    """
    User activity monitoring widget.
    
    Displays activity logs and user statistics.
    """
    
    refresh_requested = pyqtSignal()
    filter_changed = pyqtSignal(str)  # action_type filter
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.activity_data = []
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Filters and controls
        controls = self._create_controls()
        main_layout.addWidget(controls)
        
        # Activity table
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(6)
        self.activity_table.setHorizontalHeaderLabels([
            "Timestamp", "User", "Action", "Document", "IP Address", "Details"
        ])
        
        # Table styling
        self.activity_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #E0E0E0;
                gridline-color: #F0F0F0;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #E3F2FD;
                color: #000;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #2196F3;
                font-weight: bold;
            }
        """)
        
        # Configure table
        self.activity_table.setAlternatingRowColors(True)
        self.activity_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.activity_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.activity_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Resize columns
        header = self.activity_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        
        main_layout.addWidget(self.activity_table)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("padding: 8px; background-color: #F5F5F5; color: #666;")
        main_layout.addWidget(self.status_label)
    
    def _create_header(self) -> QWidget:
        """Create header with title and controls."""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #4CAF50;
                border-bottom: 3px solid #388E3C;
            }
            QLabel {
                color: white;
            }
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 15, 20, 15)
        
        title = QLabel("User Activity Monitor")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        return header
    
    def _create_controls(self) -> QWidget:
        """Create filter and control buttons."""
        controls = QFrame()
        controls.setStyleSheet("""
            QFrame {
                background-color: #F5F5F5;
                border-bottom: 1px solid #E0E0E0;
                padding: 10px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
            QComboBox {
                padding: 6px;
                border: 1px solid #CCC;
                border-radius: 4px;
                background-color: white;
            }
        """)
        
        layout = QHBoxLayout(controls)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # Filter label
        filter_label = QLabel("Filter by Action:")
        layout.addWidget(filter_label)
        
        # Action filter dropdown
        self.action_filter = QComboBox()
        self.action_filter.addItems([
            "All Actions",
            "Upload",
            "Download",
            "View",
            "Edit",
            "Delete",
            "Share",
            "Move"
        ])
        self.action_filter.currentTextChanged.connect(self._on_filter_changed)
        layout.addWidget(self.action_filter)
        
        layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        layout.addWidget(refresh_btn)
        
        # Export button
        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self._export_activity)
        layout.addWidget(export_btn)
        
        return controls
    
    def _on_filter_changed(self, text: str):
        """Handle filter change."""
        action_type = "all" if text == "All Actions" else text.lower()
        self.filter_changed.emit(action_type)
    
    def update_activity(self, activities: list):
        """
        Update activity table with new data.
        
        Args:
            activities (list): List of activity dictionaries
                [{
                    'timestamp': str (ISO format),
                    'user_name': str,
                    'action': str,
                    'document_title': str,
                    'ip_address': str,
                    'description': str
                }]
        """
        self.activity_data = activities
        self.activity_table.setRowCount(len(activities))
        
        for row, activity in enumerate(activities):
            # Timestamp
            timestamp_str = activity.get('timestamp', '')
            try:
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                formatted_time = timestamp_str[:19] if len(timestamp_str) >= 19 else timestamp_str
            
            time_item = QTableWidgetItem(formatted_time)
            self.activity_table.setItem(row, 0, time_item)
            
            # User
            user_item = QTableWidgetItem(activity.get('user_name', 'Unknown'))
            self.activity_table.setItem(row, 1, user_item)
            
            # Action
            action = activity.get('action', 'Unknown')
            action_item = QTableWidgetItem(self._format_action(action))
            action_item.setForeground(self._get_action_color(action))
            self.activity_table.setItem(row, 2, action_item)
            
            # Document
            doc_item = QTableWidgetItem(activity.get('document_title', '-'))
            self.activity_table.setItem(row, 3, doc_item)
            
            # IP Address
            ip_item = QTableWidgetItem(activity.get('ip_address', '-'))
            ip_item.setForeground(Qt.GlobalColor.gray)
            self.activity_table.setItem(row, 4, ip_item)
            
            # Details
            details_item = QTableWidgetItem(activity.get('description', ''))
            self.activity_table.setItem(row, 5, details_item)
        
        self.status_label.setText(f"Showing {len(activities)} activities")
    
    def _format_action(self, action: str) -> str:
        """Format action type."""
        return action.title()
    
    def _get_action_color(self, action: str):
        """Get color for action type."""
        from PyQt6.QtGui import QColor
        
        colors = {
            'upload': QColor('#4CAF50'),
            'create': QColor('#4CAF50'),
            'download': QColor('#2196F3'),
            'view': QColor('#2196F3'),
            'edit': QColor('#FF9800'),
            'move': QColor('#FF9800'),
            'delete': QColor('#F44336'),
            'share': QColor('#9C27B0'),
            'restore': QColor('#00BCD4')
        }
        return colors.get(action.lower(), QColor('#666'))
    
    def _export_activity(self):
        """Export activity log to CSV."""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        import csv
        
        if not self.activity_data:
            QMessageBox.information(self, "No Data", "No activity data to export")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Activity Log",
            f"activity_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=[
                        'timestamp', 'user_name', 'action', 'document_title',
                        'ip_address', 'description'
                    ])
                    writer.writeheader()
                    writer.writerows(self.activity_data)
                
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Activity log exported to:\n{filename}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Failed",
                    f"Failed to export activity log:\n{str(e)}"
                )
    
    def show_loading(self):
        """Show loading state."""
        self.activity_table.setRowCount(0)
        self.status_label.setText("Loading activity...")
    
    def show_error(self, message: str):
        """Show error state."""
        self.activity_table.setRowCount(0)
        self.status_label.setText(f"Error: {message}")
