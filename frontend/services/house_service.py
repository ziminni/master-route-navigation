"""
House Service - handles all house-related API calls and image loading.
"""
import requests
import threading
from typing import Optional, Callable, List, Dict, Any
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QTimer


API_BASE = "http://127.0.0.1:8000"

# Cache for downloaded images
_image_cache: Dict[str, bytes] = {}


class HouseService:
    """Service for fetching house data and images from the backend."""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.api_base = API_BASE
    
    def _get_headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def get_houses(self) -> List[Dict[str, Any]]:
        """Fetch all houses from the API."""
        try:
            url = f"{self.api_base}/api/house/houses/"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and "results" in data:
                    return data["results"]
                return data
        except Exception as e:
            print(f"[HouseService] Error fetching houses: {e}")
        return []
    
    def get_house_by_name(self, house_name: str) -> Optional[Dict[str, Any]]:
        """Fetch a specific house by name or slug."""
        houses = self.get_houses()
        for house in houses:
            if (str(house.get("name", "")).lower() == str(house_name).lower() or
                str(house.get("slug", "")).lower() == str(house_name).lower()):
                return house
        return None
    
    def get_house_logo_url(self, house: Dict[str, Any]) -> Optional[str]:
        """Get the logo URL for a house (prefers logo over banner)."""
        logo_url = house.get("logo") or house.get("banner")
        if logo_url:
            # Handle relative URLs
            if logo_url.startswith("/"):
                logo_url = f"{self.api_base}{logo_url}"
        return logo_url
    
    def download_image(self, url: str) -> Optional[bytes]:
        """Download an image from URL. Returns bytes or None."""
        # Check cache first
        if url in _image_cache:
            print(f"[HouseService] Using cached image: {url}")
            return _image_cache[url]
        
        try:
            print(f"[HouseService] Downloading image: {url}")
            response = requests.get(url, timeout=15)
            print(f"[HouseService] Response: {response.status_code}, {len(response.content)} bytes")
            if response.status_code == 200:
                _image_cache[url] = response.content
                return response.content
        except Exception as e:
            print(f"[HouseService] Error downloading image: {e}")
        return None
    
    def load_house_logo_async(self, house_name: str, callback: Callable[[Optional[bytes]], None]):
        """
        Load house logo asynchronously.
        
        Args:
            house_name: Name or slug of the house
            callback: Function to call with image bytes (or None if failed)
        """
        def _worker():
            house = self.get_house_by_name(house_name)
            if house:
                logo_url = self.get_house_logo_url(house)
                if logo_url:
                    image_data = self.download_image(logo_url)
                    # Call callback in main thread
                    QTimer.singleShot(0, lambda: callback(image_data))
                    return
            # No house or no logo
            QTimer.singleShot(0, lambda: callback(None))
        
        threading.Thread(target=_worker, daemon=True).start()
    
    def get_memberships(self, house_id: int) -> List[Dict[str, Any]]:
        """Fetch memberships for a house."""
        try:
            url = f"{self.api_base}/api/house/memberships/?house={house_id}"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and "results" in data:
                    return data["results"]
                return data
        except Exception as e:
            print(f"[HouseService] Error fetching memberships: {e}")
        return []
    
    def get_events(self, house_id: int) -> List[Dict[str, Any]]:
        """Fetch events for a house."""
        try:
            url = f"{self.api_base}/api/house/events/?house={house_id}"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and "results" in data:
                    return data["results"]
                return data
        except Exception as e:
            print(f"[HouseService] Error fetching events: {e}")
        return []


# Singleton instance for convenience
_default_service: Optional[HouseService] = None


def get_house_service(token: Optional[str] = None) -> HouseService:
    """Get or create the default HouseService instance."""
    global _default_service
    if _default_service is None or (token and _default_service.token != token):
        _default_service = HouseService(token)
    return _default_service
