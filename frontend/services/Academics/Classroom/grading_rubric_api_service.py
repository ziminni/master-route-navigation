"""
Grading Rubric Service - Django Backend Integration

This service handles all grading rubric operations through the Django REST API.
Supports both online (API) and offline (JSON fallback) modes.
"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime

# Try to import API client, fallback to offline mode if not available
try:
    from frontend.services.api_client import get_api_client, APIClient
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False


class GradingRubricService:
    """
    Service for managing grading rubrics and components.
    Uses Django backend API with JSON file fallback for offline mode.
    """
    
    def __init__(self, class_id: Optional[int] = None):
        self.class_id = class_id
        self.api_client: Optional[APIClient] = None
        self.offline_mode = False
        
        # JSON fallback path
        self.json_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "Academics", "data", "grading_rubrics.json"
        )
        
        # Initialize API client
        if API_AVAILABLE:
            self.api_client = get_api_client()
        else:
            self.offline_mode = True
            print("[RUBRIC SERVICE] API client not available, using offline mode")
    
    def set_class(self, class_id: int):
        """Set the class ID for rubric operations"""
        self.class_id = class_id
    
    def _check_connection(self) -> bool:
        """Check if API is available"""
        if not self.api_client:
            return False
        
        # Try a simple request to check connection
        result = self.api_client.get(f"academics/classes/{self.class_id}/grading-rubrics/")
        if result.get('offline'):
            self.offline_mode = True
            return False
        return True
    
    # ==================== RUBRIC OPERATIONS ====================
    
    def get_rubrics_for_class(self, class_id: Optional[int] = None) -> List[Dict]:
        """Get all grading rubrics for a class"""
        cid = class_id or self.class_id
        if not cid:
            print("[RUBRIC SERVICE] No class ID provided")
            return []
        
        if self.api_client and not self.offline_mode:
            result = self.api_client.get(f"academics/classes/{cid}/grading-rubrics/")
            if not result.get('error'):
                return result if isinstance(result, list) else result.get('results', [])
            self.offline_mode = True
        
        # Fallback to JSON
        return self._get_rubrics_from_json(cid)
    
    def get_rubric_by_period(self, academic_period: str, class_id: Optional[int] = None) -> Optional[Dict]:
        """Get rubric for a specific academic period (midterm/finals)"""
        rubrics = self.get_rubrics_for_class(class_id)
        for rubric in rubrics:
            if rubric.get('academic_period') == academic_period:
                return rubric
        return None
    
    def create_rubric(self, academic_period: str, term_percentage: float, 
                      class_id: Optional[int] = None) -> Optional[Dict]:
        """Create a new grading rubric"""
        cid = class_id or self.class_id
        if not cid:
            return None
        
        data = {
            'academic_period': academic_period,
            'term_percentage': term_percentage
        }
        
        if self.api_client and not self.offline_mode:
            result = self.api_client.post(f"academics/classes/{cid}/grading-rubrics/", data)
            if not result.get('error'):
                return result
            self.offline_mode = True
        
        # Fallback to JSON
        return self._create_rubric_in_json(cid, data)
    
    def update_rubric(self, rubric_id: int, term_percentage: float) -> bool:
        """Update a grading rubric's term percentage"""
        if self.api_client and not self.offline_mode:
            result = self.api_client.patch(f"academics/grading-rubrics/{rubric_id}/", {
                'term_percentage': term_percentage
            })
            if not result.get('error'):
                return True
            self.offline_mode = True
        
        # Fallback to JSON
        return self._update_rubric_in_json(rubric_id, term_percentage)
    
    def delete_rubric(self, rubric_id: int) -> bool:
        """Delete a grading rubric"""
        if self.api_client and not self.offline_mode:
            result = self.api_client.delete(f"academics/grading-rubrics/{rubric_id}/")
            if not result.get('error'):
                return True
            self.offline_mode = True
        
        return self._delete_rubric_from_json(rubric_id)
    
    # ==================== COMPONENT OPERATIONS ====================
    
    def get_components(self, rubric_id: int) -> List[Dict]:
        """Get all components for a rubric"""
        if self.api_client and not self.offline_mode:
            result = self.api_client.get(f"academics/grading-rubrics/{rubric_id}/components/")
            if not result.get('error'):
                return result if isinstance(result, list) else result.get('results', [])
            self.offline_mode = True
        
        return self._get_components_from_json(rubric_id)
    
    def create_component(self, rubric_id: int, name: str, percentage: float) -> Optional[Dict]:
        """Create a new rubric component"""
        data = {
            'name': name,
            'percentage': percentage
        }
        
        if self.api_client and not self.offline_mode:
            result = self.api_client.post(f"academics/grading-rubrics/{rubric_id}/components/", data)
            if not result.get('error'):
                return result
            self.offline_mode = True
        
        return self._create_component_in_json(rubric_id, data)
    
    def update_component(self, component_id: int, name: Optional[str] = None, 
                         percentage: Optional[float] = None) -> bool:
        """Update a rubric component"""
        data = {}
        if name is not None:
            data['name'] = name
        if percentage is not None:
            data['percentage'] = percentage
        
        if not data:
            return False
        
        if self.api_client and not self.offline_mode:
            result = self.api_client.patch(f"academics/rubric-components/{component_id}/", data)
            if not result.get('error'):
                return True
            self.offline_mode = True
        
        return self._update_component_in_json(component_id, data)
    
    def delete_component(self, component_id: int) -> bool:
        """Delete a rubric component"""
        if self.api_client and not self.offline_mode:
            result = self.api_client.delete(f"academics/rubric-components/{component_id}/")
            if not result.get('error'):
                return True
            self.offline_mode = True
        
        return self._delete_component_from_json(component_id)
    
    # ==================== BULK OPERATIONS ====================
    
    def save_full_rubric_config(self, class_id: int, config: Dict) -> bool:
        """
        Save complete rubric configuration for a class.
        
        Config format:
        {
            'midterm': {
                'term_percentage': 33,
                'components': [
                    {'name': 'Quiz', 'percentage': 30},
                    {'name': 'Performance Task', 'percentage': 50},
                    {'name': 'Exam', 'percentage': 20}
                ]
            },
            'finals': {
                'term_percentage': 67,
                'components': [...]
            }
        }
        """
        try:
            for period_key, period_data in config.items():
                # Normalize period key
                academic_period = 'midterm' if period_key == 'midterm' else 'finals'
                
                # Check if rubric exists
                existing_rubric = self.get_rubric_by_period(academic_period, class_id)
                
                if existing_rubric:
                    # Update existing rubric
                    rubric_id = existing_rubric['id']
                    self.update_rubric(rubric_id, period_data.get('term_percentage', 50))
                    
                    # Delete existing components and recreate
                    for comp in self.get_components(rubric_id):
                        self.delete_component(comp['id'])
                else:
                    # Create new rubric
                    rubric = self.create_rubric(
                        academic_period, 
                        period_data.get('term_percentage', 50),
                        class_id
                    )
                    if not rubric:
                        continue
                    rubric_id = rubric['id']
                
                # Create components
                for comp in period_data.get('components', []):
                    self.create_component(rubric_id, comp['name'], comp['percentage'])
            
            return True
            
        except Exception as e:
            print(f"[RUBRIC SERVICE] Error saving config: {e}")
            return False
    
    def get_full_rubric_config(self, class_id: Optional[int] = None) -> Dict:
        """
        Get complete rubric configuration for a class.
        Returns format matching save_full_rubric_config input.
        """
        cid = class_id or self.class_id
        config = {
            'midterm': {'term_percentage': 33, 'components': []},
            'finals': {'term_percentage': 67, 'components': []}
        }
        
        rubrics = self.get_rubrics_for_class(cid)
        
        for rubric in rubrics:
            period = rubric.get('academic_period', 'midterm')
            period_key = 'midterm' if period == 'midterm' else 'finals'
            
            config[period_key]['term_percentage'] = float(rubric.get('term_percentage', 50))
            
            # Get components
            components = self.get_components(rubric['id'])
            config[period_key]['components'] = [
                {'name': c['name'], 'percentage': float(c['percentage'])}
                for c in components
            ]
        
        return config
    
    # ==================== JSON FALLBACK METHODS ====================
    
    def _load_json(self) -> Dict:
        """Load data from JSON file"""
        try:
            if os.path.exists(self.json_path):
                with open(self.json_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[RUBRIC SERVICE] Error loading JSON: {e}")
        return {'rubrics': [], 'components': [], 'last_id': 0}
    
    def _save_json(self, data: Dict):
        """Save data to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
            with open(self.json_path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"[RUBRIC SERVICE] Error saving JSON: {e}")
    
    def _get_rubrics_from_json(self, class_id: int) -> List[Dict]:
        """Get rubrics from JSON file"""
        data = self._load_json()
        return [r for r in data.get('rubrics', []) if r.get('class_id') == class_id]
    
    def _create_rubric_in_json(self, class_id: int, rubric_data: Dict) -> Optional[Dict]:
        """Create rubric in JSON file"""
        data = self._load_json()
        new_id = data.get('last_rubric_id', 0) + 1
        
        rubric = {
            'id': new_id,
            'class_id': class_id,
            'academic_period': rubric_data['academic_period'],
            'term_percentage': rubric_data['term_percentage'],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        data.setdefault('rubrics', []).append(rubric)
        data['last_rubric_id'] = new_id
        self._save_json(data)
        return rubric
    
    def _update_rubric_in_json(self, rubric_id: int, term_percentage: float) -> bool:
        """Update rubric in JSON file"""
        data = self._load_json()
        for rubric in data.get('rubrics', []):
            if rubric.get('id') == rubric_id:
                rubric['term_percentage'] = term_percentage
                rubric['updated_at'] = datetime.now().isoformat()
                self._save_json(data)
                return True
        return False
    
    def _delete_rubric_from_json(self, rubric_id: int) -> bool:
        """Delete rubric from JSON file"""
        data = self._load_json()
        rubrics = data.get('rubrics', [])
        data['rubrics'] = [r for r in rubrics if r.get('id') != rubric_id]
        # Also delete associated components
        components = data.get('components', [])
        data['components'] = [c for c in components if c.get('rubric_id') != rubric_id]
        self._save_json(data)
        return True
    
    def _get_components_from_json(self, rubric_id: int) -> List[Dict]:
        """Get components from JSON file"""
        data = self._load_json()
        return [c for c in data.get('components', []) if c.get('rubric_id') == rubric_id]
    
    def _create_component_in_json(self, rubric_id: int, comp_data: Dict) -> Optional[Dict]:
        """Create component in JSON file"""
        data = self._load_json()
        new_id = data.get('last_component_id', 0) + 1
        
        component = {
            'id': new_id,
            'rubric_id': rubric_id,
            'name': comp_data['name'],
            'percentage': comp_data['percentage'],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        data.setdefault('components', []).append(component)
        data['last_component_id'] = new_id
        self._save_json(data)
        return component
    
    def _update_component_in_json(self, component_id: int, updates: Dict) -> bool:
        """Update component in JSON file"""
        data = self._load_json()
        for comp in data.get('components', []):
            if comp.get('id') == component_id:
                comp.update(updates)
                comp['updated_at'] = datetime.now().isoformat()
                self._save_json(data)
                return True
        return False
    
    def _delete_component_from_json(self, component_id: int) -> bool:
        """Delete component from JSON file"""
        data = self._load_json()
        components = data.get('components', [])
        data['components'] = [c for c in components if c.get('id') != component_id]
        self._save_json(data)
        return True
