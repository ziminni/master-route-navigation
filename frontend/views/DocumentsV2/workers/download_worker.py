"""
Download Worker - Asynchronous File Download

Provides QThread-based worker for downloading files without blocking UI.
Shows progress and saves files to the Downloads directory.
"""

from PyQt6.QtCore import QThread, pyqtSignal, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import os
from pathlib import Path


class DownloadWorker(QThread):
    """
    Worker thread for downloading files asynchronously.
    
    Signals:
        progress(int): Download progress percentage (0-100)
        finished(str): Download completed with file path
        error(str): Download failed with error message
    """
    
    progress = pyqtSignal(int)  # percentage
    finished = pyqtSignal(str)  # file_path
    error = pyqtSignal(str)     # error_message
    
    def __init__(self, url: str, filename: str, token: str = None):
        """
        Initialize the download worker.
        
        Args:
            url (str): URL to download from
            filename (str): Filename to save as
            token (str): Optional auth token for request
        """
        super().__init__()
        self.url = url
        self.filename = filename
        self.token = token
        self.download_path = None
        self._cancelled = False
        
        # Network manager - will be created in run() on the worker thread
        self.manager = None
        self.reply = None
        
        # File handle
        self.file = None
    
    def run(self):
        """Execute the download."""
        try:
            print("[DownloadWorker] Starting download process")
            print(f"[DownloadWorker] URL: {self.url}")
            print(f"[DownloadWorker] Filename: {self.filename}")
            
            # Create QNetworkAccessManager in this thread (must be in thread with event loop)
            self.manager = QNetworkAccessManager()
            print("[DownloadWorker] Network manager created in worker thread")
            
            # Get Downloads directory
            downloads_dir = self._get_downloads_directory()
            print(f"[DownloadWorker] Downloads directory: {downloads_dir}")
            
            # Handle duplicate filenames
            self.download_path = self._get_unique_filepath(downloads_dir, self.filename)
            print(f"[DownloadWorker] Target file path: {self.download_path}")
            
            # Open file for writing
            self.file = open(self.download_path, 'wb')
            print("[DownloadWorker] File opened for writing")
            
            # Create network request
            request = QNetworkRequest(QUrl(self.url))
            if self.token:
                request.setRawHeader(b'Authorization', f'Bearer {self.token}'.encode())
                print("[DownloadWorker] Authorization header added")
            
            # Start download
            print("[DownloadWorker] Starting network request...")
            self.reply = self.manager.get(request)
            self.reply.downloadProgress.connect(self._on_progress)
            self.reply.readyRead.connect(self._on_ready_read)
            self.reply.finished.connect(self._on_finished)
            self.reply.errorOccurred.connect(self._on_error)
            print("[DownloadWorker] Network request initiated")
            
            # Run event loop for this thread
            self.exec()
            
        except Exception as e:
            print(f"[DownloadWorker] ERROR in run(): {str(e)}")
            import traceback
            traceback.print_exc()
            self._cleanup()
            self.error.emit(f"Download setup failed: {str(e)}")
    
    def _get_downloads_directory(self) -> str:
        """
        Get the user's Downloads directory path.
        
        Returns:
            str: Path to Downloads directory
        """
        # Try to get Downloads directory in a cross-platform way
        home = Path.home()
        downloads = home / "Downloads"
        
        if not downloads.exists():
            # Fallback to home directory
            downloads = home
        
        return str(downloads)
    
    def _get_unique_filepath(self, directory: str, filename: str) -> str:
        """
        Get a unique filepath by adding numbers if file exists.
        
        Args:
            directory (str): Directory path
            filename (str): Desired filename
            
        Returns:
            str: Unique file path
            
        Examples:
            file.pdf -> file.pdf
            file.pdf -> file (1).pdf (if exists)
            file.pdf -> file (2).pdf (if exists)
        """
        filepath = os.path.join(directory, filename)
        
        if not os.path.exists(filepath):
            return filepath
        
        # Split name and extension
        name, ext = os.path.splitext(filename)
        counter = 1
        
        while True:
            new_filename = f"{name} ({counter}){ext}"
            new_filepath = os.path.join(directory, new_filename)
            
            if not os.path.exists(new_filepath):
                return new_filepath
            
            counter += 1
            
            # Safety check to prevent infinite loop
            if counter > 9999:
                raise ValueError("Too many duplicate files")
    
    def _on_progress(self, bytes_received: int, bytes_total: int):
        """Handle download progress update."""
        if bytes_total > 0 and not self._cancelled:
            percentage = int((bytes_received / bytes_total) * 100)
            print(f"[DownloadWorker] Progress: {percentage}% ({bytes_received}/{bytes_total} bytes)")
            self.progress.emit(percentage)
    
    def _on_ready_read(self):
        """Write downloaded data to file."""
        if self.reply and self.file and not self._cancelled:
            data = self.reply.readAll()
            bytes_written = len(data.data())
            print(f"[DownloadWorker] Writing {bytes_written} bytes to file")
            self.file.write(data.data())
    
    def _on_finished(self):
        """Handle download completion."""
        print("[DownloadWorker] Download finished callback triggered")
        
        if self._cancelled:
            print("[DownloadWorker] Download was cancelled")
            self._cleanup()
            self.error.emit("Download cancelled")
            return
        
        if self.reply.error() == QNetworkReply.NetworkError.NoError:
            print("[DownloadWorker] Download completed successfully")
            # Write any remaining data
            if self.reply.bytesAvailable() > 0:
                remaining = self.reply.bytesAvailable()
                print(f"[DownloadWorker] Writing {remaining} remaining bytes")
                data = self.reply.readAll()
                self.file.write(data.data())
            
            self._cleanup()
            print(f"[DownloadWorker] File saved to: {self.download_path}")
            self.finished.emit(self.download_path)
        else:
            print(f"[DownloadWorker] Download finished with error: {self.reply.error()}")
            self._cleanup()
            # Error will be handled by _on_error
        
        self.quit()
    
    def _on_error(self, error_code):
        """Handle download error."""
        print(f"[DownloadWorker] Error occurred: {error_code}")
        if not self._cancelled and self.reply:
            error_msg = self.reply.errorString()
            print(f"[DownloadWorker] Error message: {error_msg}")
            self._cleanup()
            self.error.emit(f"Network error: {error_msg}")
            self.quit()
    
    def _cleanup(self):
        """Clean up resources."""
        if self.file:
            self.file.close()
            self.file = None
        
        if self.reply:
            self.reply.deleteLater()
            self.reply = None
        
        # Delete incomplete file on error/cancel
        if self._cancelled and self.download_path and os.path.exists(self.download_path):
            try:
                os.remove(self.download_path)
            except:
                pass
    
    def cancel(self):
        """Cancel the download."""
        self._cancelled = True
        if self.reply:
            self.reply.abort()
