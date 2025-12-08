"""
Material Service - Django Backend Integration

This service handles all material operations through the Django REST API.
Supports both online (API) and offline (JSON fallback) modes.
"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime

# Try to import API client
try:
    from frontend.services.api_client import get_api_client, APIClient
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False


class MaterialAPIService:
    """
    Service for managing class materials.
    Uses Django backend API with JSON file fallback for offline mode.
    """
    
    def __init__(self, class_id: Optional[int] = None):
        self.class_id = class_id
        self.api_client: Optional[APIClient] = None
        self.offline_mode = False
        
        # JSON fallback path
        self.json_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "materials.json"
        )
        
        # Initialize API client
        if API_AVAILABLE:
            self.api_client = get_api_client()
        else:
            self.offline_mode = True
            print("[MATERIAL SERVICE] API client not available, using offline mode")
    
    def set_class(self, class_id: int):
        """Set the class ID for material operations"""
        self.class_id = class_id
    
    # ==================== MATERIAL OPERATIONS ====================
    
    def get_all_materials(self, class_id: Optional[int] = None) -> List[Dict]:
        """Get all materials for a class"""
        cid = class_id or self.class_id
        if not cid:
            print("[MATERIAL SERVICE] No class ID provided")
            return []
        
        if self.api_client and not self.offline_mode:
            result = self.api_client.get(f"academics/classes/{cid}/materials/")
            if not result.get('error'):
                return result if isinstance(result, list) else result.get('results', [])
            self.offline_mode = True
        
        return self._get_materials_from_json(cid)
    
    def get_material(self, material_id: int) -> Optional[Dict]:
        """Get a specific material by ID"""
        if self.api_client and not self.offline_mode:
            result = self.api_client.get(f"academics/materials/{material_id}/")
            if not result.get('error'):
                return result
            self.offline_mode = True
        
        return self._get_material_from_json(material_id)
    
    def get_materials_by_topic(self, topic_id: int, 
                                class_id: Optional[int] = None) -> List[Dict]:
        """Get materials for a specific topic"""
        materials = self.get_all_materials(class_id)
        return [m for m in materials if m.get('topic_id') == topic_id]
    
    def create_material(self, data: Dict, class_id: Optional[int] = None) -> Optional[Dict]:
        """
        Create a new material.
        
        Required data fields:
        - title: str
        
        Optional fields:
        - description: str
        - topic_id: int
        - attachments: list of file info dicts [{'name': 'file.pdf', 'url': '...'}]
        - links: list of link dicts [{'title': 'Link', 'url': '...'}]
        """
        cid = class_id or self.class_id
        if not cid:
            print("[MATERIAL SERVICE] No class ID provided")
            return None
        
        if 'title' not in data:
            print("[MATERIAL SERVICE] Title is required")
            return None
        
        material_data = {
            'title': data['title'],
            'description': data.get('description', ''),
            'topic_id': data.get('topic_id'),
            'attachments': data.get('attachments', []),
            'links': data.get('links', [])
        }
        
        if self.api_client and not self.offline_mode:
            result = self.api_client.post(f"academics/classes/{cid}/materials/", material_data)
            if not result.get('error'):
                return result
            self.offline_mode = True
        
        return self._create_material_in_json(cid, material_data)
    
    def update_material(self, material_id: int, data: Dict) -> bool:
        """Update a material"""
        if self.api_client and not self.offline_mode:
            result = self.api_client.patch(f"academics/materials/{material_id}/", data)
            if not result.get('error'):
                return True
            self.offline_mode = True
        
        return self._update_material_in_json(material_id, data)
    
    def delete_material(self, material_id: int) -> bool:
        """Delete a material"""
        if self.api_client and not self.offline_mode:
            result = self.api_client.delete(f"academics/materials/{material_id}/")
            if not result.get('error'):
                return True
            self.offline_mode = True
        
        return self._delete_material_from_json(material_id)
    
    # ==================== ATTACHMENT OPERATIONS ====================
    
    def add_attachment(self, material_id: int, file_path: str, 
                       file_name: Optional[str] = None) -> bool:
        """Add attachment to a material"""
        if not os.path.exists(file_path):
            print(f"[MATERIAL SERVICE] File not found: {file_path}")
            return False
        
        name = file_name or os.path.basename(file_path)
        
        if self.api_client and not self.offline_mode:
            # For API, we would upload the file
            result = self.api_client.post(
                f"academics/materials/{material_id}/attachments/",
                {'name': name, 'file_path': file_path}
            )
            if not result.get('error'):
                return True
            self.offline_mode = True
        
        # For JSON, just store the file path
        material = self._get_material_from_json(material_id)
        if material:
            attachments = material.get('attachments', [])
            attachments.append({
                'name': name,
                'path': file_path,
                'added_at': datetime.now().isoformat()
            })
            return self._update_material_in_json(material_id, {'attachments': attachments})
        return False
    
    def remove_attachment(self, material_id: int, attachment_name: str) -> bool:
        """Remove attachment from a material"""
        material = self.get_material(material_id)
        if not material:
            return False
        
        attachments = [a for a in material.get('attachments', []) 
                       if a.get('name') != attachment_name]
        
        return self.update_material(material_id, {'attachments': attachments})
    
    # ==================== LINK OPERATIONS ====================
    
    def add_link(self, material_id: int, url: str, title: Optional[str] = None) -> bool:
        """Add a link to a material"""
        material = self.get_material(material_id)
        if not material:
            return False
        
        links = material.get('links', [])
        links.append({
            'title': title or url,
            'url': url,
            'added_at': datetime.now().isoformat()
        })
        
        return self.update_material(material_id, {'links': links})
    
    def remove_link(self, material_id: int, url: str) -> bool:
        """Remove a link from a material"""
        material = self.get_material(material_id)
        if not material:
            return False
        
        links = [l for l in material.get('links', []) if l.get('url') != url]
        return self.update_material(material_id, {'links': links})
    
    # ==================== GROUPED DATA ====================
    
    def get_materials_grouped_by_topic(self, class_id: Optional[int] = None) -> Dict[str, List[Dict]]:
        """
        Get materials grouped by topic.
        Returns: {'Topic Name': [...], 'No Topic': [...]}
        """
        materials = self.get_all_materials(class_id)
        
        grouped = {'No Topic': []}
        for material in materials:
            topic_name = material.get('topic_name', 'No Topic')
            if topic_name not in grouped:
                grouped[topic_name] = []
            grouped[topic_name].append(material)
        
        # Remove 'No Topic' if empty
        if not grouped['No Topic']:
            del grouped['No Topic']
        
        return grouped
    
    # ==================== JSON FALLBACK METHODS ====================
    
    def _load_json(self) -> Dict:
        """Load data from JSON file"""
        try:
            if os.path.exists(self.json_path):
                with open(self.json_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[MATERIAL SERVICE] Error loading JSON: {e}")
        return {'materials': [], 'last_id': 0}
    
    def _save_json(self, data: Dict):
        """Save data to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
            with open(self.json_path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"[MATERIAL SERVICE] Error saving JSON: {e}")
    
    def _get_materials_from_json(self, class_id: int) -> List[Dict]:
        """Get materials from JSON file"""
        data = self._load_json()
        return [m for m in data.get('materials', []) if m.get('class_id') == class_id]
    
    def _get_material_from_json(self, material_id: int) -> Optional[Dict]:
        """Get single material from JSON file"""
        data = self._load_json()
        for material in data.get('materials', []):
            if material.get('id') == material_id:
                return material
        return None
    
    def _create_material_in_json(self, class_id: int, material_data: Dict) -> Optional[Dict]:
        """Create material in JSON file"""
        data = self._load_json()
        new_id = data.get('last_id', 0) + 1
        
        material = {
            'id': new_id,
            'class_id': class_id,
            **material_data,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        data.setdefault('materials', []).append(material)
        data['last_id'] = new_id
        self._save_json(data)
        return material
    
    def _update_material_in_json(self, material_id: int, updates: Dict) -> bool:
        """Update material in JSON file"""
        data = self._load_json()
        for material in data.get('materials', []):
            if material.get('id') == material_id:
                material.update(updates)
                material['updated_at'] = datetime.now().isoformat()
                self._save_json(data)
                return True
        return False
    
    def _delete_material_from_json(self, material_id: int) -> bool:
        """Delete material from JSON file"""
        data = self._load_json()
        materials = data.get('materials', [])
        data['materials'] = [m for m in materials if m.get('id') != material_id]
        self._save_json(data)
        return True
