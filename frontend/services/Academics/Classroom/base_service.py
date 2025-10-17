# base_service.py
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseService(ABC):
    def __init__(self, json_path: str):
        self.json_path = json_path
        self.logger = logging.getLogger(self.__class__.__name__)
        self.data = self.load_data()
    
    def load_data(self) -> Dict[str, Any]:
        """Load data from JSON file with error handling."""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning(f"Data file not found, creating empty structure: {self.json_path}")
            return self.get_default_data()
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding JSON from {self.json_path}: {e}")
            return self.get_default_data()
    
    def get_default_data(self) -> Dict[str, Any]:
        """Return default data structure when file doesn't exist."""
        return {"posts": [], "topics": []}
    
    def save_data(self) -> bool:
        """Save data to JSON file with error handling."""
        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"Error saving data to {self.json_path}: {e}")
            return False
    
    def generate_id(self, collection_name: str) -> int:
        """Generate a new ID for a collection."""
        items = self.data.get(collection_name, [])
        existing_ids = [item.get("id", 0) for item in items if item.get("id")]
        return max(existing_ids) + 1 if existing_ids else 1