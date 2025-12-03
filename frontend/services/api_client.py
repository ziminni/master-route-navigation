"""
API Client for Django Backend Integration

This module provides a centralized HTTP client for communicating with the Django REST API.
All frontend services should use this client for backend operations.
"""

import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json


@dataclass
class APIConfig:
    """Configuration for API connection"""
    base_url: str = "http://localhost:8000/api"
    timeout: int = 30


class APIClient:
    """
    Centralized HTTP client for Django REST API communication.
    Handles authentication, error handling, and request/response formatting.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure one client instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.config = APIConfig()
        self.token: Optional[str] = None
        self.session = requests.Session()
        self._initialized = True
    
    def set_token(self, token: str):
        """Set authentication token for API requests"""
        self.token = token
        self.session.headers.update({
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json'
        })
    
    def set_base_url(self, base_url: str):
        """Update base URL for API requests"""
        self.config.base_url = base_url.rstrip('/')
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Token {self.token}'
        return headers
    
    def _handle_response(self, response: requests.Response) -> Dict:
        """Handle API response and errors"""
        try:
            if response.status_code == 204:  # No content
                return {'success': True}
            
            data = response.json()
            
            if response.status_code >= 400:
                error_msg = data.get('detail', str(data))
                print(f"[API ERROR] {response.status_code}: {error_msg}")
                return {'error': error_msg, 'status_code': response.status_code}
            
            return data
            
        except json.JSONDecodeError:
            return {'error': 'Invalid JSON response', 'status_code': response.status_code}
        except Exception as e:
            return {'error': str(e), 'status_code': getattr(response, 'status_code', 500)}
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make GET request to API"""
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.get(
                url, 
                params=params, 
                headers=self._get_headers(),
                timeout=self.config.timeout
            )
            return self._handle_response(response)
        except requests.ConnectionError:
            print(f"[API] Connection error - is Django server running?")
            return {'error': 'Connection failed. Is the server running?', 'offline': True}
        except Exception as e:
            print(f"[API] Request error: {e}")
            return {'error': str(e)}
    
    def post(self, endpoint: str, data: Dict) -> Dict:
        """Make POST request to API"""
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.post(
                url, 
                json=data, 
                headers=self._get_headers(),
                timeout=self.config.timeout
            )
            return self._handle_response(response)
        except requests.ConnectionError:
            return {'error': 'Connection failed. Is the server running?', 'offline': True}
        except Exception as e:
            return {'error': str(e)}
    
    def put(self, endpoint: str, data: Dict) -> Dict:
        """Make PUT request to API"""
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.put(
                url, 
                json=data, 
                headers=self._get_headers(),
                timeout=self.config.timeout
            )
            return self._handle_response(response)
        except requests.ConnectionError:
            return {'error': 'Connection failed. Is the server running?', 'offline': True}
        except Exception as e:
            return {'error': str(e)}
    
    def patch(self, endpoint: str, data: Dict) -> Dict:
        """Make PATCH request to API"""
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.patch(
                url, 
                json=data, 
                headers=self._get_headers(),
                timeout=self.config.timeout
            )
            return self._handle_response(response)
        except requests.ConnectionError:
            return {'error': 'Connection failed. Is the server running?', 'offline': True}
        except Exception as e:
            return {'error': str(e)}
    
    def delete(self, endpoint: str) -> Dict:
        """Make DELETE request to API"""
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.delete(
                url, 
                headers=self._get_headers(),
                timeout=self.config.timeout
            )
            return self._handle_response(response)
        except requests.ConnectionError:
            return {'error': 'Connection failed. Is the server running?', 'offline': True}
        except Exception as e:
            return {'error': str(e)}


# Global API client instance
api_client = APIClient()


def get_api_client() -> APIClient:
    """Get the global API client instance"""
    return api_client
