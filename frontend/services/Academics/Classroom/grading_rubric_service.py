# grading_rubric_service.py
"""
Service for managing grading rubrics - integrates with backend models
Handles CRUD operations for GradingRubric and RubricComponent

Now integrated with Django backend API with JSON fallback for offline mode.
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

# Try to import the new API service
try:
    from frontend.services.Academics.Classroom.grading_rubric_api_service import GradingRubricService as GradingRubricAPIService
    API_SERVICE_AVAILABLE = True
except ImportError:
    API_SERVICE_AVAILABLE = False
    GradingRubricAPIService = None


class GradingRubricService:
    """
    Service for managing grading rubrics for a class.
    Each class has two rubrics: midterm and finals.
    Each rubric has components (Performance Task, Quiz, Exam, etc.)
    
    Now uses Django backend API as primary storage with JSON fallback.
    """
    
    def __init__(self, data_file: str = None, class_id: int = None):
        # Initialize API service if available
        self.api_service = None
        self.use_api = False
        
        if API_SERVICE_AVAILABLE:
            try:
                self.api_service = GradingRubricAPIService(class_id)
                self.use_api = True
                print("[RUBRIC SERVICE] Using Django backend API")
            except Exception as e:
                print(f"[RUBRIC SERVICE] API service initialization failed: {e}")
        
        # JSON fallback
        if data_file is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.data_file = os.path.join(base_dir, "data", "grading_rubrics.json")
        else:
            self.data_file = data_file
        self._ensure_data_file()
    
    def _ensure_data_file(self):
        """Ensure the data file exists with default structure"""
        if not os.path.exists(self.data_file):
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            initial_data = {
                "rubrics": {},  # Key: class_id, Value: {midterm: {...}, finals: {...}}
                "last_updated": datetime.now().isoformat()
            }
            self._save_data(initial_data)
    
    def _load_data(self) -> Dict:
        """Load rubrics data from JSON file"""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"rubrics": {}, "last_updated": datetime.now().isoformat()}
    
    def _save_data(self, data: Dict):
        """Save rubrics data to JSON file"""
        data["last_updated"] = datetime.now().isoformat()
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    def get_class_rubrics(self, class_id: int) -> Optional[Dict]:
        """
        Get all rubrics for a class.
        Returns: {
            "midterm": {"term_percentage": 33, "components": [...]},
            "finals": {"term_percentage": 67, "components": [...]}
        }
        """
        # Try API first
        if self.use_api and self.api_service:
            try:
                return self.api_service.get_full_rubric_config(class_id)
            except Exception as e:
                print(f"[RUBRIC SERVICE] API call failed, using JSON fallback: {e}")
        
        # JSON fallback
        data = self._load_data()
        class_key = str(class_id)
        return data.get("rubrics", {}).get(class_key)
    
    def get_rubric(self, class_id: int, academic_period: str) -> Optional[Dict]:
        """
        Get a specific rubric (midterm or finals) for a class.
        
        Args:
            class_id: The class ID
            academic_period: "midterm" or "finals"
        
        Returns:
            Rubric dict with term_percentage and components
        """
        class_rubrics = self.get_class_rubrics(class_id)
        if class_rubrics:
            return class_rubrics.get(academic_period.lower())
        return None
    
    def create_or_update_rubrics(self, class_id: int, rubrics_data: Dict) -> bool:
        """
        Create or update rubrics for a class.
        
        Args:
            class_id: The class ID
            rubrics_data: {
                "midterm": {
                    "term_percentage": 33,
                    "components": [
                        {"id": 1, "name": "Performance Task", "percentage": 20},
                        {"id": 2, "name": "Quiz", "percentage": 30},
                        {"id": 3, "name": "Exam", "percentage": 50}
                    ]
                },
                "finals": {...}
            }
        
        Returns:
            True if successful
        """
        try:
            # Validate components sum to 100 for each term
            for term in ["midterm", "finals"]:
                if term in rubrics_data:
                    components = rubrics_data[term].get("components", [])
                    total = sum(c.get("percentage", 0) for c in components)
                    if abs(total - 100) > 0.01:
                        print(f"[RUBRIC SERVICE] Warning: {term} components sum to {total}%, should be 100%")
            
            # Try API first
            if self.use_api and self.api_service:
                try:
                    if self.api_service.save_full_rubric_config(class_id, rubrics_data):
                        print(f"[RUBRIC SERVICE] Saved rubrics via API for class {class_id}")
                        return True
                except Exception as e:
                    print(f"[RUBRIC SERVICE] API save failed, using JSON fallback: {e}")
            
            # JSON fallback
            data = self._load_data()
            class_key = str(class_id)
            
            if "rubrics" not in data:
                data["rubrics"] = {}
            
            # Add timestamps and IDs
            now = datetime.now().isoformat()
            for term in ["midterm", "finals"]:
                if term in rubrics_data:
                    rubrics_data[term]["updated_at"] = now
                    if "created_at" not in rubrics_data[term]:
                        rubrics_data[term]["created_at"] = now
                    
                    # Ensure component IDs
                    for i, comp in enumerate(rubrics_data[term].get("components", [])):
                        if "id" not in comp:
                            comp["id"] = i + 1
            
            data["rubrics"][class_key] = rubrics_data
            self._save_data(data)
            
            print(f"[RUBRIC SERVICE] Saved rubrics for class {class_id}")
            return True
            
        except Exception as e:
            print(f"[RUBRIC SERVICE] Error saving rubrics: {e}")
            return False
    
    def get_component_by_id(self, class_id: int, component_id: int) -> Optional[Dict]:
        """Get a specific rubric component by ID"""
        class_rubrics = self.get_class_rubrics(class_id)
        if not class_rubrics:
            return None
        
        for term in ["midterm", "finals"]:
            rubric = class_rubrics.get(term, {})
            for comp in rubric.get("components", []):
                if comp.get("id") == component_id:
                    return {**comp, "academic_period": term}
        
        return None
    
    def get_component_by_name(self, class_id: int, component_name: str, 
                              academic_period: str) -> Optional[Dict]:
        """Get a rubric component by name and period"""
        rubric = self.get_rubric(class_id, academic_period)
        if not rubric:
            return None
        
        for comp in rubric.get("components", []):
            if comp.get("name", "").lower() == component_name.lower():
                return {**comp, "academic_period": academic_period}
        
        return None
    
    def get_all_components(self, class_id: int) -> List[Dict]:
        """
        Get all rubric components for a class with their academic period.
        Useful for populating dropdowns in assessment creation.
        
        Returns:
            List of components with academic_period added
        """
        class_rubrics = self.get_class_rubrics(class_id)
        if not class_rubrics:
            return []
        
        components = []
        for term in ["midterm", "finals"]:
            rubric = class_rubrics.get(term, {})
            for comp in rubric.get("components", []):
                components.append({
                    **comp,
                    "academic_period": term,
                    "term_percentage": rubric.get("term_percentage", 0)
                })
        
        return components
    
    def create_default_rubrics(self, class_id: int) -> Dict:
        """
        Create default rubrics for a class if none exist.
        
        Returns:
            The created rubrics data
        """
        existing = self.get_class_rubrics(class_id)
        if existing:
            return existing
        
        default_rubrics = {
            "midterm": {
                "term_percentage": 33,
                "components": [
                    {"id": 1, "name": "Performance Task", "percentage": 20},
                    {"id": 2, "name": "Quiz", "percentage": 30},
                    {"id": 3, "name": "Exam", "percentage": 50}
                ]
            },
            "finals": {
                "term_percentage": 67,
                "components": [
                    {"id": 4, "name": "Performance Task", "percentage": 20},
                    {"id": 5, "name": "Quiz", "percentage": 30},
                    {"id": 6, "name": "Exam", "percentage": 50}
                ]
            }
        }
        
        self.create_or_update_rubrics(class_id, default_rubrics)
        return default_rubrics
    
    def add_component(self, class_id: int, academic_period: str, 
                      name: str, percentage: int) -> Optional[Dict]:
        """Add a new component to a rubric"""
        class_rubrics = self.get_class_rubrics(class_id) or {}
        
        if academic_period not in class_rubrics:
            class_rubrics[academic_period] = {
                "term_percentage": 33 if academic_period == "midterm" else 67,
                "components": []
            }
        
        # Generate new ID
        all_ids = []
        for term in ["midterm", "finals"]:
            rubric = class_rubrics.get(term, {})
            all_ids.extend([c.get("id", 0) for c in rubric.get("components", [])])
        
        new_id = max(all_ids, default=0) + 1
        new_component = {
            "id": new_id,
            "name": name,
            "percentage": percentage,
            "created_at": datetime.now().isoformat()
        }
        
        class_rubrics[academic_period]["components"].append(new_component)
        self.create_or_update_rubrics(class_id, class_rubrics)
        
        return new_component
    
    def update_component(self, class_id: int, component_id: int, 
                         updates: Dict) -> bool:
        """Update a rubric component"""
        class_rubrics = self.get_class_rubrics(class_id)
        if not class_rubrics:
            return False
        
        for term in ["midterm", "finals"]:
            rubric = class_rubrics.get(term, {})
            for comp in rubric.get("components", []):
                if comp.get("id") == component_id:
                    comp.update(updates)
                    comp["updated_at"] = datetime.now().isoformat()
                    self.create_or_update_rubrics(class_id, class_rubrics)
                    return True
        
        return False
    
    def delete_component(self, class_id: int, component_id: int) -> bool:
        """Delete a rubric component"""
        class_rubrics = self.get_class_rubrics(class_id)
        if not class_rubrics:
            return False
        
        for term in ["midterm", "finals"]:
            rubric = class_rubrics.get(term, {})
            components = rubric.get("components", [])
            for i, comp in enumerate(components):
                if comp.get("id") == component_id:
                    del components[i]
                    self.create_or_update_rubrics(class_id, class_rubrics)
                    return True
        
        return False
