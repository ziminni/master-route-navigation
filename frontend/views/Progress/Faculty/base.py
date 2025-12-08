# frontend/views/Progress/Faculty/base.py
"""
Base classes for Faculty widgets following Admin/Student patterns.
"""
import threading
import traceback
import requests
from PyQt6.QtCore import QObject, pyqtSignal, QMetaObject, Qt, Q_ARG, pyqtSlot
from PyQt6.QtWidgets import QMessageBox


class FacultyAPIClient(QObject):
    """
    Base API client for Faculty widgets using same pattern as Admin/Student.
    This should be used as a COMPOSITION (not inheritance) in widgets.
    """
    api_error = pyqtSignal(str)  # Emits error messages
    show_message = pyqtSignal(str, str)  # Emits (title, message)
    
    def __init__(self, token=None, api_base="http://127.0.0.1:8000"):
        super().__init__()
        self.token = token or ""
        self.api_base = api_base.rstrip("/")
    
    def _build_headers(self):
        """Build authentication headers (same as Admin/Student)"""
        token = (self.token or "").strip()
        if not token:
            return {}
        if token.startswith("Bearer ") or token.startswith("Token "):
            return {"Authorization": token}
        if len(token) > 40:
            return {"Authorization": f"Bearer {token}"}
        return {"Authorization": f"Token {token}"}
    
    def api_get(self, endpoint, callback=None):
        """Thread-safe GET request"""
        url = f"{self.api_base}{endpoint}"
        headers = self._build_headers()
        
        def fetch():
            try:
                print(f"DEBUG [Faculty]: GET {url}")
                r = requests.get(url, headers=headers, timeout=15)
                
                if r.status_code == 200:
                    data = r.json()
                    print(f"DEBUG [Faculty]: Response received")
                    
                    if callback:
                        # ✅ Use invokeMethod to run callback in main thread
                        QMetaObject.invokeMethod(
                            self, 
                            "_execute_callback",
                            Qt.ConnectionType.QueuedConnection,
                            Q_ARG(object, callback),
                            Q_ARG(object, data)
                        )
                    else:
                        print("WARNING [Faculty]: No callback provided for API response")
                        
                elif r.status_code == 403:
                    print(f"ERROR [Faculty]: Access denied (403)")
                    self.api_error.emit("Access denied. You don't have permission to view this resource.")
                elif r.status_code == 404:
                    print(f"ERROR [Faculty]: Resource not found (404)")
                    self.api_error.emit("Resource not found.")
                else:
                    error_msg = f"API Error {r.status_code}"
                    try:
                        error_data = r.json()
                        if "detail" in error_data:
                            error_msg += f": {error_data['detail']}"
                    except:
                        pass
                    print(f"ERROR [Faculty]: {error_msg}")
                    self.api_error.emit(error_msg)
                    
            except requests.exceptions.Timeout:
                error_msg = "Request timeout. Please try again."
                print(f"ERROR [Faculty]: {error_msg}")
                self.api_error.emit(error_msg)
            except requests.exceptions.ConnectionError:
                error_msg = "Cannot connect to server. Please check your connection."
                print(f"ERROR [Faculty]: {error_msg}")
                self.api_error.emit(error_msg)
            except Exception as e:
                print(f"❌ Exception [Faculty]: {e}")
                traceback.print_exc()
                self.api_error.emit(f"Error: {str(e)}")
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def api_post(self, endpoint, data, callback=None):
        """Thread-safe POST request"""
        url = f"{self.api_base}{endpoint}"
        headers = self._build_headers()
        headers["Content-Type"] = "application/json"
        
        def send():
            try:
                print(f"DEBUG [Faculty]: POST {url}")
                print(f"DEBUG [Faculty]: Data: {data}")
                r = requests.post(url, json=data, headers=headers, timeout=15)
                
                if r.status_code in [200, 201]:
                    response_data = r.json()
                    if callback:
                        # ✅ Use invokeMethod to run callback in main thread
                        QMetaObject.invokeMethod(
                            self, 
                            "_execute_callback",
                            Qt.ConnectionType.QueuedConnection,
                            Q_ARG(object, callback),
                            Q_ARG(object, response_data)
                        )
                    # ✅ Emit show_message signal (already thread-safe)
                    self.show_message.emit("Success", "Operation completed successfully.")
                    
                elif r.status_code == 403:
                    print(f"ERROR [Faculty]: Access denied (403)")
                    self.api_error.emit("Access denied. You don't have permission.")
                    
                elif r.status_code == 400:
                    error_msg = "Bad request"
                    try:
                        error_data = r.json()
                        if "detail" in error_data:
                            error_msg = error_data['detail']
                    except:
                        pass
                    self.api_error.emit(error_msg)
                    
                else:
                    error_msg = f"API Error {r.status_code}"
                    try:
                        error_data = r.json()
                        if "detail" in error_data:
                            error_msg += f": {error_data['detail']}"
                    except:
                        pass
                    self.api_error.emit(error_msg)
                    
            except requests.exceptions.Timeout:
                error_msg = "Request timeout. Please try again."
                self.api_error.emit(error_msg)
            except requests.exceptions.ConnectionError:
                error_msg = "Cannot connect to server."
                self.api_error.emit(error_msg)
            except Exception as e:
                print(f"❌ Exception [Faculty]: {e}")
                traceback.print_exc()
                self.api_error.emit(f"Error: {str(e)}")
        
        threading.Thread(target=send, daemon=True).start()
    
    @pyqtSlot(object, object)
    def _execute_callback(self, callback, data):
        """Execute callback in main thread (slot method)"""
        try:
            if callback:
                callback(data)
        except Exception as e:
            print(f"❌ Error in callback execution: {e}")
            traceback.print_exc()