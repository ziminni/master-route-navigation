"""
Bulk Operations Panel Widget

Provides bulk document management operations including:
- Bulk delete
- Bulk move
- Bulk category assignment
- Bulk permission updates
- Bulk download
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QFrame, QPushButton, QComboBox,
    QCheckBox, QMessageBox, QProgressDialog
)
from PyQt6.QtCore import Qt, pyqtSignal


class BulkOperationsWidget(QWidget):
    """
    Bulk operations panel for admin document management.
    
    Allows performing operations on multiple documents at once.
    """
    
    bulk_operation_requested = pyqtSignal(str, dict)  # (operation_type, params)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_count = 0
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Content area
        content = QWidget()
        content.setStyleSheet("background-color: #FAFAFA;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)
        
        # Selection info
        self.selection_info = QLabel("No documents selected")
        self.selection_info.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #333;
            padding: 10px;
            background-color: white;
            border: 1px solid #E0E0E0;
            border-radius: 4px;
        """)
        content_layout.addWidget(self.selection_info)
        
        # Operations sections
        content_layout.addWidget(self._create_file_operations())
        content_layout.addWidget(self._create_organization_operations())
        content_layout.addWidget(self._create_permission_operations())
        content_layout.addWidget(self._create_danger_operations())
        
        content_layout.addStretch()
        
        main_layout.addWidget(content)
    
    def _create_header(self) -> QWidget:
        """Create header."""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #FF9800;
                border-bottom: 3px solid #F57C00;
            }
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 15, 20, 15)
        
        title = QLabel("Bulk Operations")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        return header
    
    def _create_file_operations(self) -> QGroupBox:
        """Create file operation buttons."""
        group = QGroupBox("File Operations")
        group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                color: #FF9800;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        # Download selected
        download_layout = QHBoxLayout()
        download_btn = QPushButton("Download Selected")
        download_btn.setStyleSheet(self._get_button_style("#2196F3"))
        download_btn.clicked.connect(lambda: self._request_operation('bulk_download'))
        download_layout.addWidget(download_btn)
        
        download_desc = QLabel("Download all selected documents as ZIP")
        download_desc.setStyleSheet("color: #666; font-size: 12px;")
        download_layout.addWidget(download_desc, stretch=1)
        
        layout.addLayout(download_layout)
        
        # Feature/Unfeature
        feature_layout = QHBoxLayout()
        feature_btn = QPushButton("Feature Selected")
        feature_btn.setStyleSheet(self._get_button_style("#FFC107"))
        feature_btn.clicked.connect(lambda: self._request_operation('bulk_feature'))
        feature_layout.addWidget(feature_btn)
        
        unfeature_btn = QPushButton("Remove Featured")
        unfeature_btn.setStyleSheet(self._get_button_style("#9E9E9E"))
        unfeature_btn.clicked.connect(lambda: self._request_operation('bulk_unfeature'))
        feature_layout.addWidget(unfeature_btn)
        
        layout.addLayout(feature_layout)
        
        return group
    
    def _create_organization_operations(self) -> QGroupBox:
        """Create organization operation buttons."""
        group = QGroupBox("Organization")
        group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                color: #FF9800;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        # Move to folder
        move_layout = QHBoxLayout()
        move_btn = QPushButton("Move Selected")
        move_btn.setStyleSheet(self._get_button_style("#4CAF50"))
        move_btn.clicked.connect(lambda: self._request_operation('bulk_move'))
        move_layout.addWidget(move_btn)
        
        move_desc = QLabel("Move all selected documents to a folder")
        move_desc.setStyleSheet("color: #666; font-size: 12px;")
        move_layout.addWidget(move_desc, stretch=1)
        
        layout.addLayout(move_layout)
        
        # Change category
        category_layout = QHBoxLayout()
        category_btn = QPushButton("Change Category")
        category_btn.setStyleSheet(self._get_button_style("#9C27B0"))
        category_btn.clicked.connect(lambda: self._request_operation('bulk_category'))
        category_layout.addWidget(category_btn)
        
        category_desc = QLabel("Assign category to selected documents")
        category_desc.setStyleSheet("color: #666; font-size: 12px;")
        category_layout.addWidget(category_desc, stretch=1)
        
        layout.addLayout(category_layout)
        
        return group
    
    def _create_permission_operations(self) -> QGroupBox:
        """Create permission operation buttons."""
        group = QGroupBox("Permissions")
        group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                color: #FF9800;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        # Make public/private
        visibility_layout = QHBoxLayout()
        public_btn = QPushButton("Make Public")
        public_btn.setStyleSheet(self._get_button_style("#00BCD4"))
        public_btn.clicked.connect(lambda: self._request_operation('bulk_public'))
        visibility_layout.addWidget(public_btn)
        
        private_btn = QPushButton("Make Private")
        private_btn.setStyleSheet(self._get_button_style("#607D8B"))
        private_btn.clicked.connect(lambda: self._request_operation('bulk_private'))
        visibility_layout.addWidget(private_btn)
        
        layout.addLayout(visibility_layout)
        
        # Share with users
        share_layout = QHBoxLayout()
        share_btn = QPushButton("Share With...")
        share_btn.setStyleSheet(self._get_button_style("#673AB7"))
        share_btn.clicked.connect(lambda: self._request_operation('bulk_share'))
        share_layout.addWidget(share_btn)
        
        share_desc = QLabel("Share selected documents with users/groups")
        share_desc.setStyleSheet("color: #666; font-size: 12px;")
        share_layout.addWidget(share_desc, stretch=1)
        
        layout.addLayout(share_layout)
        
        return group
    
    def _create_danger_operations(self) -> QGroupBox:
        """Create dangerous operation buttons."""
        group = QGroupBox("Danger Zone")
        group.setStyleSheet("""
            QGroupBox {
                background-color: #FFEBEE;
                border: 2px solid #F44336;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                color: #F44336;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        # Delete selected
        delete_layout = QHBoxLayout()
        delete_btn = QPushButton("Move to Trash")
        delete_btn.setStyleSheet(self._get_button_style("#F44336"))
        delete_btn.clicked.connect(lambda: self._request_operation('bulk_delete'))
        delete_layout.addWidget(delete_btn)
        
        delete_desc = QLabel("Move all selected documents to trash")
        delete_desc.setStyleSheet("color: #D32F2F; font-size: 12px; font-weight: bold;")
        delete_layout.addWidget(delete_desc, stretch=1)
        
        layout.addLayout(delete_layout)
        
        # Permanent delete
        permanent_layout = QHBoxLayout()
        permanent_btn = QPushButton("Permanent Delete")
        permanent_btn.setStyleSheet(self._get_button_style("#B71C1C"))
        permanent_btn.clicked.connect(lambda: self._request_operation('bulk_permanent_delete'))
        permanent_layout.addWidget(permanent_btn)
        
        permanent_desc = QLabel("PERMANENTLY delete selected (CANNOT BE UNDONE)")
        permanent_desc.setStyleSheet("color: #B71C1C; font-size: 12px; font-weight: bold;")
        permanent_layout.addWidget(permanent_desc, stretch=1)
        
        layout.addLayout(permanent_layout)
        
        return group
    
    def _get_button_style(self, color: str) -> str:
        """Get button stylesheet."""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
                min-width: 150px;
            }}
            QPushButton:hover {{
                background-color: {self._darken_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {self._darken_color(color, 0.8)};
            }}
            QPushButton:disabled {{
                background-color: #CCCCCC;
                color: #666666;
            }}
        """
    
    def _darken_color(self, hex_color: str, factor: float = 0.9) -> str:
        """Darken a hex color."""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = int(r * factor), int(g * factor), int(b * factor)
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def _request_operation(self, operation_type: str):
        """Request a bulk operation."""
        if self.selected_count == 0:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select documents first before performing bulk operations."
            )
            return
        
        # Confirmation for dangerous operations
        if operation_type in ['bulk_delete', 'bulk_permanent_delete']:
            operation_name = "move to trash" if operation_type == 'bulk_delete' else "PERMANENTLY DELETE"
            reply = QMessageBox.warning(
                self,
                "Confirm Bulk Operation",
                f"Are you sure you want to {operation_name} {self.selected_count} document(s)?\n\n"
                f"{'This action CANNOT be undone!' if 'permanent' in operation_type else 'You can restore them from trash later.'}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        # Emit signal with operation type
        self.bulk_operation_requested.emit(operation_type, {})
    
    def update_selection_count(self, count: int):
        """Update the selected document count."""
        self.selected_count = count
        
        if count == 0:
            self.selection_info.setText("No documents selected")
            self.selection_info.setStyleSheet("""
                font-size: 14px;
                font-weight: bold;
                color: #999;
                padding: 10px;
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
            """)
        else:
            self.selection_info.setText(f"{count} document(s) selected")
            self.selection_info.setStyleSheet("""
                font-size: 14px;
                font-weight: bold;
                color: #4CAF50;
                padding: 10px;
                background-color: #E8F5E9;
                border: 2px solid #4CAF50;
                border-radius: 4px;
            """)
