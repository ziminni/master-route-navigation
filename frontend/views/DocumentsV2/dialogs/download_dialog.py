"""
Download Progress Dialog

Shows download progress with:
- Progress bar
- File name
- Download speed/size
- Cancel button

Usage:
    dialog = DownloadDialog(filename, parent)
    dialog.show()
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer
from datetime import datetime


class DownloadDialog(QDialog):
    """
    Dialog showing download progress.
    
    Displays:
    - Filename being downloaded
    - Progress bar with percentage
    - Download status
    - Cancel button
    """
    
    def __init__(self, filename: str, parent=None):
        """
        Initialize download dialog.
        
        Args:
            filename (str): Name of file being downloaded
            parent: Parent widget
        """
        super().__init__(parent)
        print(f"[DownloadDialog] Initializing with filename: {filename}")
        self.filename = filename
        self.start_time = datetime.now()
        self.is_cancelled = False
        
        self.init_ui()
        print("[DownloadDialog] Dialog initialized")
    
    def init_ui(self):
        """Initialize the dialog UI."""
        self.setWindowTitle("Downloading File")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Downloading Document")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Filename
        self.filename_label = QLabel(f"📄 {self.filename}")
        self.filename_label.setWordWrap(True)
        self.filename_label.setStyleSheet("color: #555; padding: 10px; background: #f5f5f5; border-radius: 5px;")
        layout.addWidget(self.filename_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 5px;
                text-align: center;
                height: 25px;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Starting download...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self._on_cancel)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
                border-color: #f44336;
            }
        """)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def update_progress(self, percentage: int):
        """
        Update progress bar.
        
        Args:
            percentage (int): Progress percentage (0-100)
        """
        print(f"[DownloadDialog] Updating progress: {percentage}%")
        self.progress_bar.setValue(percentage)
        
        if percentage < 100:
            self.status_label.setText(f"Downloading... {percentage}%")
        else:
            self.status_label.setText("Download complete!")
    
    def set_completed(self, file_path: str):
        """
        Mark download as completed.
        
        Args:
            file_path (str): Path where file was saved
        """
        print(f"[DownloadDialog] Setting completed state: {file_path}")
        self.progress_bar.setValue(100)
        self.status_label.setText(f"Saved to: {file_path}")
        self.status_label.setStyleSheet("color: #4CAF50; font-size: 12px; font-weight: bold;")
        
        self.cancel_button.setText("Close")
        self.cancel_button.disconnect()
        self.cancel_button.clicked.connect(self.accept)
    
    def set_error(self, error_message: str):
        """
        Mark download as failed.
        
        Args:
            error_message (str): Error message
        """
        print(f"[DownloadDialog] Setting error state: {error_message}")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #f44336;
                border-radius: 5px;
                text-align: center;
                height: 25px;
                background-color: #ffebee;
            }
            QProgressBar::chunk {
                background-color: #f44336;
                border-radius: 3px;
            }
        """)
        
        self.status_label.setText(f"Download failed: {error_message}")
        self.status_label.setStyleSheet("color: #f44336; font-size: 12px; font-weight: bold;")
        
        self.cancel_button.setText("Close")
        self.cancel_button.disconnect()
        self.cancel_button.clicked.connect(self.reject)
    
    def _on_cancel(self):
        """Handle cancel button click."""
        self.is_cancelled = True
        self.status_label.setText("Cancelling download...")
        self.cancel_button.setEnabled(False)
        self.reject()
    
    def closeEvent(self, event):
        """Prevent closing during download unless cancelled."""
        if self.progress_bar.value() < 100 and not self.is_cancelled:
            self._on_cancel()
        event.accept()
