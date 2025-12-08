"""
Upload Dialog - File Upload Interface

Allows users to:
- Select multiple files to upload
- Set document metadata (category, folder, document type)
- See upload progress for each file
- Cancel individual or all uploads

Usage:
    dialog = UploadDialog(categories, folders, document_service)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        print("Upload completed")
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QComboBox, QProgressBar,
    QFileDialog, QMessageBox, QFormLayout, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from typing import List


class FileUploadItem(QWidget):
    """
    Widget representing a single file in the upload queue.
    Shows filename, size, and progress bar.
    """
    
    def __init__(self, filename: str, filesize: int, parent=None):
        """
        Initialize file upload item.
        
        Args:
            filename (str): Name of the file
            filesize (int): File size in bytes
            parent: Parent widget
        """
        super().__init__(parent)
        self.filename = filename
        self.filesize = filesize
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # File info
        size_mb = self.filesize / (1024 * 1024)
        info_label = QLabel(f"{self.filename} ({size_mb:.2f} MB)")
        layout.addWidget(info_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Ready to upload")
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.status_label)
    
    def set_progress(self, value: int):
        """
        Update progress bar value.
        
        Args:
            value (int): Progress percentage (0-100)
        """
        self.progress_bar.setValue(value)
        if value < 100:
            self.progress_bar.setFormat(f"{value}%")
        else:
            self.progress_bar.setFormat("Upload complete")
            self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }")
    
    def set_status(self, status: str, is_error: bool = False):
        """
        Update status label.
        
        Args:
            status (str): Status message
            is_error (bool): True if this is an error message
        """
        self.status_label.setText(status)
        if is_error:
            self.status_label.setStyleSheet("color: #F44336; font-size: 11px; font-weight: bold;")
        else:
            self.status_label.setStyleSheet("color: #4CAF50; font-size: 11px;")


class UploadDialog(QDialog):
    """
    Dialog for uploading files with metadata selection.
    
    Signals:
        upload_completed: Emitted when all uploads finish successfully
    """
    
    upload_completed = pyqtSignal()
    
    def __init__(self, categories: list, folders: list, document_service, 
                 current_folder_id: int = None, current_folder_name: str = None, parent=None):
        """
        Initialize upload dialog.
        
        Args:
            categories (list): List of category dicts from API
            folders (list): List of folder dicts for finding current folder name
            document_service: DocumentService instance for uploads
            current_folder_id (int): Current folder ID (upload destination)
            current_folder_name (str): Current folder name (for display)
            parent: Parent widget
        """
        super().__init__(parent)
        self.categories = categories
        self.folders = folders
        self.document_service = document_service
        self.current_folder_id = current_folder_id
        self.current_folder_name = current_folder_name or "Root Directory"
        self.selected_files = []  # List of file paths
        self.file_widgets = {}    # Map filepath -> FileUploadItem widget
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI."""
        self.setWindowTitle("Upload Files")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        layout = QVBoxLayout(self)
        
        # ========== Title ==========
        title_label = QLabel("Upload Files")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(title_label)
        
        # ========== Upload Destination Display ==========
        destination_widget = QWidget()
        destination_widget.setStyleSheet("""
            QWidget {
                background-color: #E3F2FD;
                border: 1px solid #2196F3;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        dest_layout = QVBoxLayout(destination_widget)
        dest_layout.setContentsMargins(10, 8, 10, 8)
        
        dest_title = QLabel("Upload Destination:")
        dest_title.setStyleSheet("font-weight: bold; color: #1976D2; background: transparent; border: none;")
        dest_layout.addWidget(dest_title)
        
        # Get folder name
        if self.current_folder_id is not None:
            current_folder = next((f for f in self.folders if f.get('id') == self.current_folder_id), None)
            if current_folder:
                self.current_folder_name = current_folder.get('name', 'Unknown')
        
        dest_location = QLabel(f"{self.current_folder_name}")
        dest_location.setStyleSheet("font-size: 14px; color: #333; background: transparent; border: none; padding-left: 10px;")
        dest_layout.addWidget(dest_location)
        
        layout.addWidget(destination_widget)
        
        # ========== File Selection ==========
        select_layout = QHBoxLayout()
        
        self.btn_select_files = QPushButton("Select Files")
        self.btn_select_files.clicked.connect(self._select_files)
        select_layout.addWidget(self.btn_select_files)
        
        self.files_label = QLabel("No files selected")
        self.files_label.setStyleSheet("color: #666;")
        select_layout.addWidget(self.files_label)
        select_layout.addStretch()
        
        layout.addLayout(select_layout)
        
        # ========== File List (with progress bars) ==========
        list_label = QLabel("Files to Upload:")
        list_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(list_label)
        
        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(200)
        layout.addWidget(self.file_list)
        
        # ========== Metadata Form ==========
        form_label = QLabel("Document Metadata:")
        form_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(form_label)
        
        form_layout = QFormLayout()
        
        # Category dropdown (required)
        self.category_combo = QComboBox()
        self.category_combo.addItem("-- Select Category --", None)
        for cat in self.categories:
            icon = cat.get('icon', '📂')
            name = cat.get('name', 'Unknown')
            self.category_combo.addItem(f"{icon} {name}", cat['id'])
        form_layout.addRow("Category *:", self.category_combo)
        
        layout.addLayout(form_layout)
        
        # ========== Buttons ==========
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)
        
        self.btn_upload = QPushButton("Upload All")
        self.btn_upload.setEnabled(False)
        self.btn_upload.clicked.connect(self._start_upload)
        self.btn_upload.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        button_layout.addWidget(self.btn_upload)
        
        layout.addLayout(button_layout)
    
    def _select_files(self):
        """Open file dialog to select files."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files to Upload",
            "",
            "All Files (*.*)"
        )
        
        if file_paths:
            self.selected_files = file_paths
            self.files_label.setText(f"{len(file_paths)} file(s) selected")
            self.btn_upload.setEnabled(True)
            self._display_files()
    
    def _display_files(self):
        """Display selected files in the list with progress bars."""
        self.file_list.clear()
        self.file_widgets.clear()
        
        import os
        for filepath in self.selected_files:
            filename = os.path.basename(filepath)
            filesize = os.path.getsize(filepath)
            
            # Create file upload item widget
            item_widget = FileUploadItem(filename, filesize)
            self.file_widgets[filepath] = item_widget
            
            # Add to list
            list_item = QListWidgetItem()
            list_item.setSizeHint(item_widget.sizeHint())
            self.file_list.addItem(list_item)
            self.file_list.setItemWidget(list_item, item_widget)
    
    def _start_upload(self):
        """Start uploading all selected files."""
        # Validate category selection
        category_id = self.category_combo.currentData()
        if category_id is None:
            QMessageBox.warning(
                self,
                "Missing Category",
                "Please select a category before uploading."
            )
            return
        
        # Use current folder ID (upload destination)
        folder_id = self.current_folder_id
        
        # Show loading state
        self.btn_upload.setText("Uploading...")
        self.btn_upload.setEnabled(False)
        self.btn_select_files.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.category_combo.setEnabled(False)
        
        # Upload each file
        import os
        success_count = 0
        error_count = 0
        
        for filepath in self.selected_files:
            filename = os.path.basename(filepath)
            item_widget = self.file_widgets[filepath]
            
            # Update status
            item_widget.set_status("Uploading...")
            item_widget.set_progress(0)
            
            # Simulate upload progress (in real app, connect to service signals)
            for progress in range(0, 101, 20):
                item_widget.set_progress(progress)
                # In production, this would be driven by actual upload progress
            
            # Perform upload
            result = self.document_service.upload_document(
                file_path=filepath,
                title=filename,
                category_id=category_id,
                folder_id=folder_id,
                description=""
            )
            
            if result['success']:
                item_widget.set_progress(100)
                item_widget.set_status("Uploaded successfully")
                success_count += 1
            else:
                error_msg = result.get('error', 'Unknown error')
                item_widget.set_status(f"Error: {error_msg}", is_error=True)
                item_widget.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #F44336; }")
                error_count += 1
        
        # Re-enable buttons and reset state
        self.btn_upload.setText("Upload All")
        self.btn_select_files.setEnabled(True)
        self.btn_cancel.setEnabled(True)
        self.btn_cancel.setText("Close")
        self.category_combo.setEnabled(True)
        
        # Show summary
        if error_count == 0:
            QMessageBox.information(
                self,
                "Upload Complete",
                f"Successfully uploaded {success_count} file(s)!"
            )
            self.upload_completed.emit()
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Upload Complete with Errors",
                f"Uploaded: {success_count}\nFailed: {error_count}\n\nPlease check the error messages above."
            )
