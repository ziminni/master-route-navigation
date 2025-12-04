"""
Approval/Rejection Dialog for Admin

Allows admin to approve or reject documents with notes.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal


class ApprovalDialog(QDialog):
    """
    Dialog for approving or rejecting documents.
    
    Signals:
        action_completed(dict): Emitted when approval/rejection is completed
    """
    
    action_completed = pyqtSignal(dict)  # approval data
    
    def __init__(self, document_data: dict, approval_id: int, action_type: str, 
                 document_service, parent=None):
        """
        Initialize approval dialog.
        
        Args:
            document_data (dict): Document information
            approval_id (int): Approval ID
            action_type (str): 'approve' or 'reject'
            document_service: DocumentService instance for API calls
            parent: Parent widget
        """
        super().__init__(parent)
        self.document_data = document_data
        self.approval_id = approval_id
        self.action_type = action_type
        self.document_service = document_service
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        action_title = "Approve" if self.action_type == 'approve' else "Reject"
        self.setWindowTitle(f"{action_title} Document")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Header
        header_color = "#4CAF50" if self.action_type == 'approve' else "#F44336"
        header = QLabel(f"{action_title} Document")
        header.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                color: {header_color};
            }}
        """)
        layout.addWidget(header)
        
        # Document info
        doc_name = self.document_data.get('title', 'Unknown')
        doc_owner = self.document_data.get('uploaded_by_name', 'Unknown')
        
        info_label = QLabel(f"Document: {doc_name}\nUploaded by: {doc_owner}")
        info_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #f5f5f5;
                border-radius: 4px;
                font-size: 13px;
            }
        """)
        layout.addWidget(info_label)
        
        # Notes section
        if self.action_type == 'approve':
            notes_label = QLabel("Approval Notes (optional):")
            notes_placeholder = "Add any notes about this approval..."
        else:
            notes_label = QLabel("Rejection Reason (required):")
            notes_placeholder = "Please explain why this document is being rejected..."
        
        notes_label.setStyleSheet("font-weight: bold; padding-top: 10px;")
        layout.addWidget(notes_label)
        
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText(notes_placeholder)
        self.notes_input.setMaximumHeight(120)
        layout.addWidget(self.notes_input)
        
        # Info text
        if self.action_type == 'approve':
            info_text = "The document will be marked as approved and will be visible to all users."
        else:
            info_text = "The document will be marked as rejected. The uploader will be notified."
        
        info = QLabel(info_text)
        info.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)
        
        btn_text = "Approve" if self.action_type == 'approve' else "Reject"
        btn_color = "#4CAF50" if self.action_type == 'approve' else "#F44336"
        btn_hover = "#45a049" if self.action_type == 'approve' else "#da190b"
        
        self.btn_action = QPushButton(btn_text)
        self.btn_action.clicked.connect(self._perform_action)
        self.btn_action.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_color};
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {btn_hover};
            }}
            QPushButton:disabled {{
                background-color: #ccc;
            }}
        """)
        button_layout.addWidget(self.btn_action)
        
        layout.addLayout(button_layout)
    
    def _perform_action(self):
        """Validate inputs and perform approval/rejection."""
        notes = self.notes_input.toPlainText().strip()
        
        # Validate rejection requires notes
        if self.action_type == 'reject' and not notes:
            QMessageBox.warning(
                self,
                "Notes Required",
                "Please provide a reason for rejecting this document."
            )
            return
        
        # Show loading state
        action_text = "Approving" if self.action_type == 'approve' else "Rejecting"
        self.btn_action.setText(f"{action_text}...")
        self.btn_action.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.notes_input.setEnabled(False)
        
        # Perform action via API
        if self.action_type == 'approve':
            result = self.document_service.approve_document(self.approval_id, notes)
        else:
            result = self.document_service.reject_document(self.approval_id, notes)
        
        # Reset button states
        action_text = "Approve" if self.action_type == 'approve' else "Reject"
        self.btn_action.setText(action_text)
        self.btn_action.setEnabled(True)
        self.btn_cancel.setEnabled(True)
        self.notes_input.setEnabled(True)
        
        if result['success']:
            action_past = "approved" if self.action_type == 'approve' else "rejected"
            QMessageBox.information(
                self,
                "Success",
                f"Document {action_past} successfully!"
            )
            
            # Emit signal with result data
            self.action_completed.emit(result['data'])
            self.accept()
        else:
            QMessageBox.critical(
                self,
                f"{action_text} Failed",
                f"Failed to {self.action_type} document:\n{result.get('error', 'Unknown error')}"
            )
