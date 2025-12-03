
import os
import json
import requests
from typing import List, Dict, Tuple
from PyQt6.QtCore import QObject, pyqtSignal

class HouseController(QObject):
    members_updated = pyqtSignal(list)
    house_created = pyqtSignal(dict)

    def __init__(self, parent=None, token=None, api_base=None, house_id=None):
        super().__init__(parent)
        self.members = []
        self.filtered_members = []
        self.token = token
        self.api_base = api_base or "http://127.0.0.1:8000"
        self.house_id = house_id
        
        # Load members from API if house_id is provided
        if self.house_id:
            self.load_members_from_api()

    def set_house_id(self, house_id):
        """Set the house ID and reload members"""
        self.house_id = house_id
        self.load_members_from_api()

    def set_token(self, token):
        """Set the authentication token"""
        self.token = token

    def load_members_from_api(self):
        """Load members from backend API."""
        if not self.house_id:
            print("No house_id set, cannot load members from API")
            self.members = []
            self.filtered_members = []
            self.members_updated.emit(self.filtered_members)
            return
            
        try:
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            
            url = f"{self.api_base}/api/house/memberships/?house={self.house_id}"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    memberships = data.get("results", [])
                else:
                    memberships = data
                
                # Transform membership data to member format
                self.members = []
                for m in memberships:
                    member = {
                        "id": m.get("id"),
                        "user_id": m.get("user"),
                        "name": m.get("user_display", f"User {m.get('user', 'Unknown')}"),
                        "role": m.get("role", "member").replace("_", " ").title(),
                        "year_level": m.get("year_level", ""),
                        "avatar": m.get("avatar", ""),
                        "points": m.get("points", 0),
                        "is_active": m.get("is_active", True)
                    }
                    self.members.append(member)
                
                self.filtered_members = self.members.copy()
                print(f"Loaded {len(self.members)} members from API for house {self.house_id}")
            else:
                print(f"Failed to load members: HTTP {response.status_code}")
                self.members = []
                self.filtered_members = []
        except Exception as e:
            print(f"Error loading members from API: {e}")
            self.members = []
            self.filtered_members = []
        
        self.members_updated.emit(self.filtered_members)

    def load_members(self):
        """Load members - now calls API instead of JSON file."""
        self.load_members_from_api()

    def search_members(self, query: str):
        """Filter members by name or role based on search query."""
        query = query.lower().strip()
        if not query:
            self.filtered_members = self.members.copy()
        else:
            self.filtered_members = [
                member for member in self.members
                if query in member.get("name", "").lower() or query in member.get("role", "").lower()
            ]
        print(f"Search query: '{query}', found {len(self.filtered_members)} members")
        self.members_updated.emit(self.filtered_members)

    def filter_members(self, filter_type: str):
        """Filter or sort members based on filter type."""
        self.filtered_members = self.members.copy()
        
        if filter_type == "Year Level":
            if any("year_level" in member for member in self.members):
                self.filtered_members = sorted(
                    self.filtered_members,
                    key=lambda x: x.get("year_level", "")
                )
        elif filter_type == "Position":
            self.filtered_members = sorted(
                self.filtered_members,
                key=lambda x: x.get("role", "").lower()
            )
        elif filter_type == "A-Z":
            self.filtered_members = sorted(
                self.filtered_members,
                key=lambda x: x.get("name", "").lower()
            )
        elif filter_type == "Z-A":
            self.filtered_members = sorted(
                self.filtered_members,
                key=lambda x: x.get("name", "").lower(),
                reverse=True
            )
        elif filter_type == "Points (High to Low)":
            self.filtered_members = sorted(
                self.filtered_members,
                key=lambda x: x.get("points", 0),
                reverse=True
            )
        elif filter_type == "Points (Low to High)":
            self.filtered_members = sorted(
                self.filtered_members,
                key=lambda x: x.get("points", 0)
            )
        
        print(f"Filter applied: {filter_type}, {len(self.filtered_members)} members")
        self.members_updated.emit(self.filtered_members)

    def get_filtered_members(self) -> List[Dict]:
        """Return the current filtered member list."""
        return self.filtered_members

    def create_house(self, name: str, description: str = "", banner_path: str = None, logo_path: str = None, token: str = None, api_base: str = None) -> Tuple[bool, dict]:
        """Create a house by POSTing to the backend API.

        Returns (success, response_json_or_text)
        """
        api_base = api_base or self.api_base
        token = token or self.token
        url = f"{api_base}/api/house/houses/"
        data = {"name": name, "description": description}
        files = {}
        try:
            if banner_path:
                files["banner"] = open(banner_path, "rb")
            if logo_path:
                files["logo"] = open(logo_path, "rb")

            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"

            resp = requests.post(url, data=data, files=files or None, headers=headers)

            if files:
                for f in files.values():
                    try:
                        f.close()
                    except Exception:
                        pass

            try:
                payload = resp.json()
            except Exception:
                payload = {"text": resp.text}

            if resp.status_code in (200, 201):
                # emit signal for other UI pieces
                try:
                    self.house_created.emit(payload)
                except Exception:
                    pass
                return True, payload
            else:
                return False, payload
        except Exception as e:
            return False, {"error": str(e)}

    
    
    