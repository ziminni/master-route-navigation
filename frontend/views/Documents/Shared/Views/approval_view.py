from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                             QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QHeaderView, QLineEdit, QStackedWidget, QMessageBox,
                             QTextEdit, QDialog, QDialogButtonBox)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal
from ...controller.document_controller import DocumentController
from ...utils.icon_utils import create_back_button, create_search_button
from ...widgets.empty_state import EmptyStateWidget


class ApprovalDialog(QDialog):
    """Dialog for approving/rejecting a file with comments"""
    
    def __init__(self, parent, file_data, action='approve'):
        super().__init__(parent)
        self.file_data = file_data
        self.action = action
        self.result_data = None
        
        self.setWindowTitle(f"{'Approve' if action == 'approve' else 'Reject'} File")
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # File info
        info_label = QLabel(f"<b>File:</b> {self.file_data.get('filename')}<br>"
                           f"<b>Uploaded by:</b> {self.file_data.get('uploader')}<br>"
                           f"<b>Upload date:</b> {self.file_data.get('uploaded_date')}<br>"
                           f"<b>Category:</b> {self.file_data.get('category')}")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Comments/Reason input
        if self.action == 'approve':
            comment_label = QLabel("Comments (optional):")
            self.text_input = QTextEdit()
            self.text_input.setPlaceholderText("Add any comments for the uploader...")
        else:
            comment_label = QLabel("Rejection Reason (required):")
            self.text_input = QTextEdit()
            self.text_input.setPlaceholderText("Please provide a reason for rejection...")
        
        layout.addWidget(comment_label)
        layout.addWidget(self.text_input)
        
        # Buttons
        button_box = QDialogButtonBox()
        
        if self.action == 'approve':
            approve_btn = button_box.addButton("Approve", QDialogButtonBox.ButtonRole.AcceptRole)
            approve_btn.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    font-weight: bold;
                    padding: 8px 16px;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
        else:
            reject_btn = button_box.addButton("Reject", QDialogButtonBox.ButtonRole.AcceptRole)
            reject_btn.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    font-weight: bold;
                    padding: 8px 16px;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """)
        
        cancel_btn = button_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        
        button_box.accepted.connect(self.handle_accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        self.setLayout(layout)
    
    def handle_accept(self):
        """Handle approve/reject action"""
        text = self.text_input.toPlainText().strip()
        
        # Validate rejection reason
        if self.action == 'reject' and not text:
            QMessageBox.warning(self, "Validation Error", "Rejection reason is required.")
            return
        
        self.result_data = {
            'text': text,
            'action': self.action
        }
        self.accept()


class ApprovalView(QWidget):
    """
    Approval View - displays pending file uploads for admin/faculty approval
    """
    file_approved = pyqtSignal(dict)
    file_rejected = pyqtSignal(dict)
    
    def __init__(self, username, roles, primary_role, token, stack=None):
        super().__init__()

        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        
        # Only admins and faculty can access approval view
        if self.primary_role.lower() not in ['admin', 'faculty']:
            QMessageBox.warning(None, "Access Denied", 
                              "You don't have permission to approve files.")
            return
        
        # Initialize controller
        self.controller = DocumentController(username, roles, primary_role, token)

        self.stack: QStackedWidget = stack
        self.setWindowTitle("File Upload Approvals")
        
        # Track file data for efficient operations
        self.file_data_cache = {}
        
        main_layout = QVBoxLayout()

        # Header with back button
        header_layout = QHBoxLayout()
        back_btn = create_back_button(callback=self.go_back)
        
        header = QLabel("File Upload Approvals")
        header.setFont(QFont("Arial", 16))

        search_bar = QLineEdit()
        search_button = create_search_button(callback=self.handle_search)
        search_bar.setPlaceholderText("Search pending files...")
        search_bar.setMinimumWidth(200)
        search_bar.textChanged.connect(self.handle_search)
        self.search_bar = search_bar

        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(search_bar)
        header_layout.addWidget(search_button)
        header_layout.addWidget(back_btn)
        main_layout.addLayout(header_layout)

        # Table for pending files
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Filename", "Uploader", "Upload Date", "Category", "Collection", "Actions"
        ])
        
        # Set column widths
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.itemClicked.connect(self.handle_item_clicked)
        self.table.itemDoubleClicked.connect(self.handle_item_double_clicked)

        # Create container for table and empty state
        self.table_container = QWidget()
        self.table_container_layout = QVBoxLayout(self.table_container)
        self.table_container_layout.setContentsMargins(0, 0, 0, 0)

        # Load pending files
        self.load_pending_files()
        
        self.table_container_layout.addWidget(self.table)
        main_layout.addWidget(self.table_container)

        self.setLayout(main_layout)
    
    def load_pending_files(self):
        """Load pending approval files from controller"""
        pending_files = self.controller.get_pending_approvals()
        
        # Handle empty state
        if len(pending_files) == 0:
            self.table.setVisible(False)
            if not hasattr(self, 'empty_state'):
                self.empty_state = EmptyStateWidget(
                    icon_name="folder1.png",
                    title="No Pending Approvals",
                    message="All file uploads have been reviewed.",
                    action_text=None
                )
                self.table_container_layout.addWidget(self.empty_state)
            else:
                self.empty_state.setVisible(True)
        else:
            if hasattr(self, 'empty_state'):
                self.empty_state.setVisible(False)
            self.table.setVisible(True)
            
            # Populate table
            self.table.setRowCount(0)
            self.file_data_cache.clear()
            
            for idx, file_data in enumerate(pending_files):
                self.add_file_row(idx, file_data)
        
        print(f"Loaded {len(pending_files)} pending files for approval")
    
    def add_file_row(self, row_idx, file_data):
        """Add a file row to the table with approve/reject buttons"""
        self.table.insertRow(row_idx)
        
        file_id = file_data.get('file_id')
        filename = file_data.get('filename', 'Unknown')
        uploader = file_data.get('uploader', 'Unknown')
        upload_date = file_data.get('uploaded_date', file_data.get('time', 'N/A'))
        category = file_data.get('category', 'None')
        collection = file_data.get('collection', 'None')
        
        # Add file data
        self.table.setItem(row_idx, 0, QTableWidgetItem(filename))
        self.table.setItem(row_idx, 1, QTableWidgetItem(uploader))
        self.table.setItem(row_idx, 2, QTableWidgetItem(upload_date))
        self.table.setItem(row_idx, 3, QTableWidgetItem(category))
        self.table.setItem(row_idx, 4, QTableWidgetItem(collection))
        
        # Actions widget with Reject and Accept buttons
        actions_widget = self.create_actions_widget(file_id, file_data)
        self.table.setCellWidget(row_idx, 5, actions_widget)
        
        # Cache file data
        self.file_data_cache[file_id] = {
            'filename': filename,
            'file_data': file_data,
            'row_index': row_idx
        }
    
    def create_actions_widget(self, file_id, file_data):
        """Create action buttons widget with Reject and Accept buttons"""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        reject_btn = QPushButton("Reject")
        reject_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
                padding: 4px 12px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        reject_btn.clicked.connect(lambda: self.handle_reject(file_id))
        
        accept_btn = QPushButton("Accept")
        accept_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 4px 12px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        accept_btn.clicked.connect(lambda: self.handle_approve(file_id))
        
        layout.addWidget(reject_btn)
        layout.addWidget(accept_btn)
        widget.setLayout(layout)
        return widget

    def handle_approve(self, file_id):
        """Handle approve button click"""
        cached = self.file_data_cache.get(file_id)
        if not cached:
            QMessageBox.warning(self, "Error", "File data not found")
            return
        
        file_data = cached['file_data']
        
        # Show approval dialog
        dialog = ApprovalDialog(self, file_data, action='approve')
        if dialog.exec() == QDialog.DialogCode.Accepted:
            result = dialog.result_data
            comments = result.get('text') if result else None
            
            # Call controller to approve
            success, message = self.controller.approve_file(file_id, comments)
            
            if success:
                QMessageBox.information(self, "Success", message)
                self.file_approved.emit(file_data)
                # Refresh the view
                self.load_pending_files()
            else:
                QMessageBox.critical(self, "Error", message)
    
    def handle_reject(self, file_id):
        """Handle reject button click"""
        cached = self.file_data_cache.get(file_id)
        if not cached:
            QMessageBox.warning(self, "Error", "File data not found")
            return
        
        file_data = cached['file_data']
        
        # Show rejection dialog
        dialog = ApprovalDialog(self, file_data, action='reject')
        if dialog.exec() == QDialog.DialogCode.Accepted:
            result = dialog.result_data
            reason = result.get('text') if result else ""
            
            # Call controller to reject
            success, message = self.controller.reject_file(file_id, reason)
            
            if success:
                QMessageBox.information(self, "Success", message)
                self.file_rejected.emit(file_data)
                # Refresh the view
                self.load_pending_files()
            else:
                QMessageBox.critical(self, "Error", message)

    def handle_item_clicked(self, item):
        """Handle table item click"""
        # Skip actions column (5)
        if item.column() != 5:
            filename = self.table.item(item.row(), 0).text()
            print(f"File row clicked: {filename}")
    
    def handle_item_double_clicked(self, item):
        """Handle table item double-click - show file details"""
        # Skip actions column (5)
        if item.column() != 5:
            filename = self.table.item(item.row(), 0).text()
            
            # Find file_id from cache
            file_id = None
            for fid, cached in self.file_data_cache.items():
                if cached.get('filename') == filename:
                    file_id = fid
                    break
            
            if file_id:
                file_data = self.file_data_cache[file_id]['file_data']
                from ...Shared.Dialogs.file_details_dialog import FileDetailsDialog
                dialog = FileDetailsDialog(
                    self, 
                    file_data=file_data, 
                    controller=self.controller,
                    is_deleted=False
                )
                dialog.exec()
    
    def handle_search(self):
        """Handle search functionality - filter pending files"""
        search_text = self.search_bar.text().lower().strip()
        
        # If search is empty, show all files
        if not search_text:
            self.load_pending_files()
            return
        
        # Get all pending files and filter by search
        pending_files = self.controller.get_pending_approvals()
        filtered_files = [
            f for f in pending_files 
            if search_text in f.get('filename', '').lower() or 
               search_text in f.get('uploader', '').lower() or
               search_text in f.get('category', '').lower()
        ]
        
        # Update table with filtered results
        self.table.setRowCount(0)
        self.file_data_cache.clear()
        
        for row_idx, file_data in enumerate(filtered_files):
            self.add_file_row(row_idx, file_data)
    
    def go_back(self):
        """Navigate back to previous view"""
        print("Back button clicked")
        if self.stack:
            self.stack.removeWidget(self)
            self.deleteLater()
