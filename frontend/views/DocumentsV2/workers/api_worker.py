"""
API Worker - Asynchronous API Call Handler

Provides QThread-based worker for non-blocking API operations.
Executes API calls in background thread and emits signals when complete.

Usage:
    worker = APIWorker(service.get_documents, filters={'category': 1})
    worker.finished.connect(self._on_data_loaded)
    worker.error.connect(self._on_error)
    worker.start()
"""

from PyQt6.QtCore import QThread, pyqtSignal
from typing import Callable, Any


class APIWorker(QThread):
    """
    Worker thread for asynchronous API calls.
    
    Executes API functions in a background thread to prevent UI blocking.
    Emits signals when operation completes or errors occur.
    
    Signals:
        finished(dict): Emitted when API call succeeds with result data
        error(str): Emitted when API call fails with error message
        progress(int): Emitted for progress updates (0-100)
    """
    
    finished = pyqtSignal(dict)  # Emits result dict from API
    error = pyqtSignal(str)      # Emits error message
    progress = pyqtSignal(int)   # Emits progress percentage
    
    def __init__(self, api_function: Callable, *args, **kwargs):
        """
        Initialize API worker.
        
        Args:
            api_function (Callable): API function to call
            *args: Positional arguments for the API function
            **kwargs: Keyword arguments for the API function
        """
        super().__init__()
        self.api_function = api_function
        self.args = args
        self.kwargs = kwargs
        self._is_cancelled = False
    
    def run(self):
        """
        Execute API call in background thread.
        
        This method runs in a separate thread and should not interact
        with UI elements directly. Use signals to communicate with main thread.
        """
        try:
            if self._is_cancelled:
                return
            
            # Execute the API function
            result = self.api_function(*self.args, **self.kwargs)
            
            if self._is_cancelled:
                return
            
            # Emit result
            if isinstance(result, dict):
                self.finished.emit(result)
            else:
                # Wrap non-dict results
                self.finished.emit({'success': True, 'data': result})
                
        except Exception as e:
            if not self._is_cancelled:
                self.error.emit(str(e))
    
    def cancel(self):
        """Cancel the operation (best effort)."""
        self._is_cancelled = True
    
    def is_cancelled(self) -> bool:
        """Check if operation was cancelled."""
        return self._is_cancelled
