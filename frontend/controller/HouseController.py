
import os
import json
import requests
from typing import List, Dict, Tuple
from PyQt6.QtCore import QObject, pyqtSignal

class HouseController(QObject):
    members_updated = pyqtSignal(list)
    house_created = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.members = []
        self.filtered_members = []
        print(f"Current working directory: {os.getcwd()}")
        self.load_members()

    def load_members(self):
        """Load members from members.json."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        members_path = os.path.join(base_dir, "..", "..", "frontend", "Mock", "members.json")
        print(f"Resolved members.json path: {os.path.abspath(members_path)}")
        try:
            with open(members_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.members = data.get("members", [])
                self.filtered_members = self.members.copy()
        except FileNotFoundError:
            print(f"Error: members.json not found at {members_path}. Using default members.")
            self.members = [
                {"name": "John Doe", "role": "Developer", "avatar": "man1.png", "year_level": "Senior"},
                {"name": "Jane Smith", "role": "Designer", "avatar": "man1.png", "year_level": "Junior"},
                {"name": "Alice Johnson", "role": "Manager", "avatar": "man1.png", "year_level": "Senior"}
            ]
            self.filtered_members = self.members.copy()
        except Exception as e:
            print(f"Error loading members.json: {e}")
            self.members = []
            self.filtered_members = []
        print(f"Loaded {len(self.members)} members")
        self.members_updated.emit(self.filtered_members)

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
        
        print(f"Filter applied: {filter_type}, {len(self.filtered_members)} members")
        self.members_updated.emit(self.filtered_members)

    def get_filtered_members(self) -> List[Dict]:
        """Return the current filtered member list."""
        return self.filtered_members

    def create_house(self, name: str, description: str = "", banner_path: str = None, logo_path: str = None, token: str = None, api_base: str = None) -> Tuple[bool, dict]:
        """Create a house by POSTing to the backend API.

        Returns (success, response_json_or_text)
        """
        api_base = api_base or "http://127.0.0.1:8000"
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
    
    
    