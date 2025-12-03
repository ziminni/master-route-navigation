# material_service.py
"""
Service for managing class materials (learning resources, documents, etc.)
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional


class MaterialService:
    """
    Service for managing class materials.
    Materials are non-graded content like documents, links, and resources.
    """
    
    def __init__(self, data_file: str = None):
        if data_file is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.data_file = os.path.join(base_dir, "data", "materials.json")
        else:
            self.data_file = data_file
        self._ensure_data_file()
    
    def _ensure_data_file(self):
        """Ensure the data file exists with default structure"""
        if not os.path.exists(self.data_file):
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            initial_data = {
                "materials": [],
                "last_id": 0,
                "last_updated": datetime.now().isoformat()
            }
            self._save_data(initial_data)
    
    def _load_data(self) -> Dict:
        """Load materials data from JSON file"""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"materials": [], "last_id": 0, "last_updated": datetime.now().isoformat()}
    
    def _save_data(self, data: Dict):
        """Save materials data to JSON file"""
        data["last_updated"] = datetime.now().isoformat()
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    def get_materials_by_class(self, class_id: int) -> List[Dict]:
        """Get all materials for a class"""
        data = self._load_data()
        return [m for m in data.get("materials", []) 
                if m.get("class_id") == class_id]
    
    def get_materials_by_topic(self, class_id: int, topic_id: int) -> List[Dict]:
        """Get all materials for a specific topic"""
        data = self._load_data()
        return [m for m in data.get("materials", []) 
                if m.get("class_id") == class_id 
                and m.get("topic_id") == topic_id]
    
    def get_material_by_id(self, material_id: int) -> Optional[Dict]:
        """Get a specific material by ID"""
        data = self._load_data()
        for material in data.get("materials", []):
            if material.get("id") == material_id:
                return material
        return None
    
    def create_material(self, class_id: int, title: str,
                        description: str = "", topic_id: Optional[int] = None,
                        attachment: Optional[Dict] = None,
                        created_by: Optional[str] = None,
                        is_published: bool = True) -> Optional[Dict]:
        """
        Create a new material.
        
        Args:
            class_id: The class ID
            title: Material title
            description: Optional description
            topic_id: Optional topic ID
            attachment: Optional attachment dict {"filename": "", "file_type": "", "file_path": ""}
            created_by: Username of creator
            is_published: Whether students can see this material
        
        Returns:
            The created material dict or None on error
        """
        try:
            data = self._load_data()
            
            new_id = data.get("last_id", 0) + 1
            data["last_id"] = new_id
            
            now = datetime.now().isoformat()
            
            material = {
                "id": new_id,
                "class_id": class_id,
                "title": title,
                "description": description,
                "topic_id": topic_id,
                "attachment": attachment,
                "is_published": is_published,
                "created_at": now,
                "created_by": created_by,
                "updated_at": now
            }
            
            data["materials"].append(material)
            self._save_data(data)
            
            print(f"[MATERIAL SERVICE] Created material: {title} (ID: {new_id})")
            return material
            
        except Exception as e:
            print(f"[MATERIAL SERVICE] Error creating material: {e}")
            return None
    
    def update_material(self, material_id: int, updates: Dict) -> bool:
        """Update an existing material"""
        try:
            data = self._load_data()
            
            for material in data.get("materials", []):
                if material.get("id") == material_id:
                    protected_fields = ["id", "class_id", "created_at", "created_by"]
                    for field in protected_fields:
                        updates.pop(field, None)
                    
                    material.update(updates)
                    material["updated_at"] = datetime.now().isoformat()
                    self._save_data(data)
                    
                    print(f"[MATERIAL SERVICE] Updated material ID: {material_id}")
                    return True
            
            return False
            
        except Exception as e:
            print(f"[MATERIAL SERVICE] Error updating material: {e}")
            return False
    
    def delete_material(self, material_id: int) -> bool:
        """Delete a material"""
        try:
            data = self._load_data()
            materials = data.get("materials", [])
            
            for i, material in enumerate(materials):
                if material.get("id") == material_id:
                    del materials[i]
                    self._save_data(data)
                    print(f"[MATERIAL SERVICE] Deleted material ID: {material_id}")
                    return True
            
            return False
            
        except Exception as e:
            print(f"[MATERIAL SERVICE] Error deleting material: {e}")
            return False
    
    def publish_material(self, material_id: int) -> bool:
        """Publish a material"""
        return self.update_material(material_id, {"is_published": True})
    
    def unpublish_material(self, material_id: int) -> bool:
        """Unpublish a material"""
        return self.update_material(material_id, {"is_published": False})
    
    def get_published_materials(self, class_id: int) -> List[Dict]:
        """Get all published materials for a class"""
        materials = self.get_materials_by_class(class_id)
        return [m for m in materials if m.get("is_published", False)]
