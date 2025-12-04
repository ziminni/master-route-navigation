"""
Assessment Service - Django Backend Integration

This service handles all assessment operations through the Django REST API.
Supports both online (API) and offline (JSON fallback) modes.
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

# Try to import API client
try:
    from frontend.services.api_client import get_api_client, APIClient
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False


class AssessmentAPIService:
    """
    Service for managing assessments.
    Uses Django backend API with JSON file fallback for offline mode.
    """
    
    def __init__(self, class_id: Optional[int] = None):
        self.class_id = class_id
        self.api_client: Optional[APIClient] = None
        self.offline_mode = False
        
        # JSON fallback path
        self.json_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "assessments.json"
        )
        
        # Initialize API client
        if API_AVAILABLE:
            self.api_client = get_api_client()
        else:
            self.offline_mode = True
            print("[ASSESSMENT SERVICE] API client not available, using offline mode")
    
    def set_class(self, class_id: int):
        """Set the class ID for assessment operations"""
        self.class_id = class_id
    
    # ==================== ASSESSMENT OPERATIONS ====================
    
    def get_all_assessments(self, class_id: Optional[int] = None) -> List[Dict]:
        """Get all assessments for a class"""
        cid = class_id or self.class_id
        if not cid:
            print("[ASSESSMENT SERVICE] No class ID provided")
            return []
        
        if self.api_client and not self.offline_mode:
            result = self.api_client.get(f"academics/classes/{cid}/assessments/")
            if not result.get('error'):
                return result if isinstance(result, list) else result.get('results', [])
            self.offline_mode = True
        
        return self._get_assessments_from_json(cid)
    
    def get_assessment(self, assessment_id: int) -> Optional[Dict]:
        """Get a specific assessment by ID"""
        if self.api_client and not self.offline_mode:
            result = self.api_client.get(f"academics/assessments/{assessment_id}/")
            if not result.get('error'):
                return result
            self.offline_mode = True
        
        return self._get_assessment_from_json(assessment_id)
    
    def get_assessments_by_period(self, academic_period: str, 
                                   class_id: Optional[int] = None) -> List[Dict]:
        """Get assessments for a specific academic period (midterm/finals)"""
        assessments = self.get_all_assessments(class_id)
        return [a for a in assessments if a.get('academic_period') == academic_period]
    
    def get_assessments_by_component(self, rubric_component_id: int, 
                                      class_id: Optional[int] = None) -> List[Dict]:
        """Get assessments for a specific rubric component"""
        assessments = self.get_all_assessments(class_id)
        return [a for a in assessments if a.get('rubric_component_id') == rubric_component_id]
    
    def get_assessments_by_topic(self, topic_id: int, 
                                  class_id: Optional[int] = None) -> List[Dict]:
        """Get assessments for a specific topic"""
        assessments = self.get_all_assessments(class_id)
        return [a for a in assessments if a.get('topic_id') == topic_id]
    
    def create_assessment(self, data: Dict, class_id: Optional[int] = None) -> Optional[Dict]:
        """
        Create a new assessment.
        
        Required data fields:
        - title: str
        - rubric_component_id: int (linked to RubricComponent)
        
        Optional fields:
        - description: str
        - academic_period: str ('midterm' or 'finals')
        - topic_id: int
        - max_points: float (default 100)
        - points_possible: float
        - due_date: str (ISO format)
        - attachments: list of file paths
        """
        cid = class_id or self.class_id
        if not cid:
            print("[ASSESSMENT SERVICE] No class ID provided")
            return None
        
        # Ensure required fields
        if 'title' not in data:
            print("[ASSESSMENT SERVICE] Title is required")
            return None
        
        # rubric_component_id is optional, default to 0
        rubric_component_id = data.get('rubric_component_id', 0)
        
        # Set defaults
        assessment_data = {
            'title': data['title'],
            'rubric_component_id': rubric_component_id,
            'rubric_component_name': data.get('rubric_component_name', ''),
            'description': data.get('description', ''),
            'academic_period': data.get('academic_period', 'midterm'),
            'max_points': data.get('max_points', 100),
            'points_possible': data.get('points_possible', data.get('max_points', 100)),
            'due_date': data.get('due_date'),
            'topic_id': data.get('topic_id'),
        }
        
        if self.api_client and not self.offline_mode:
            result = self.api_client.post(f"academics/classes/{cid}/assessments/", assessment_data)
            if not result.get('error'):
                return result
            self.offline_mode = True
        
        return self._create_assessment_in_json(cid, assessment_data)
    
    def update_assessment(self, assessment_id: int, data: Dict) -> bool:
        """Update an assessment"""
        if self.api_client and not self.offline_mode:
            result = self.api_client.patch(f"academics/assessments/{assessment_id}/", data)
            if not result.get('error'):
                return True
            self.offline_mode = True
        
        return self._update_assessment_in_json(assessment_id, data)
    
    def delete_assessment(self, assessment_id: int) -> bool:
        """Delete an assessment"""
        if self.api_client and not self.offline_mode:
            result = self.api_client.delete(f"academics/assessments/{assessment_id}/")
            if not result.get('error'):
                return True
            self.offline_mode = True
        
        return self._delete_assessment_from_json(assessment_id)
    
    # ==================== GROUPED DATA ====================
    
    def get_assessments_grouped_by_component(self, academic_period: str,
                                              class_id: Optional[int] = None) -> Dict[str, List[Dict]]:
        """
        Get assessments grouped by rubric component for a specific period.
        Returns: {'Quiz': [...], 'Performance Task': [...], 'Exam': [...]}
        """
        assessments = self.get_assessments_by_period(academic_period, class_id)
        
        grouped = {}
        for assessment in assessments:
            component_name = assessment.get('rubric_component_name', 'Unknown')
            if component_name not in grouped:
                grouped[component_name] = []
            grouped[component_name].append(assessment)
        
        return grouped
    
    def get_assessments_with_scores(self, assessment_id: int) -> Dict:
        """Get assessment with all student scores"""
        if self.api_client and not self.offline_mode:
            result = self.api_client.get(f"academics/assessments/{assessment_id}/scores/")
            if not result.get('error'):
                return result
            self.offline_mode = True
        
        # For offline, get assessment and merge with scores from grades.json
        assessment = self.get_assessment(assessment_id)
        if assessment:
            scores = self._get_scores_from_json(assessment_id)
            assessment['scores'] = scores
        return assessment or {}
    
    # ==================== JSON FALLBACK METHODS ====================
    
    def _load_json(self) -> Dict:
        """Load data from JSON file"""
        try:
            if os.path.exists(self.json_path):
                with open(self.json_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[ASSESSMENT SERVICE] Error loading JSON: {e}")
        return {'assessments': [], 'last_id': 0}
    
    def _save_json(self, data: Dict):
        """Save data to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
            with open(self.json_path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"[ASSESSMENT SERVICE] Error saving JSON: {e}")
    
    def _get_assessments_from_json(self, class_id: int) -> List[Dict]:
        """Get assessments from JSON file"""
        data = self._load_json()
        return [a for a in data.get('assessments', []) if a.get('class_id') == class_id]
    
    def _get_assessment_from_json(self, assessment_id: int) -> Optional[Dict]:
        """Get single assessment from JSON file"""
        data = self._load_json()
        for assessment in data.get('assessments', []):
            if assessment.get('id') == assessment_id:
                return assessment
        return None
    
    def _create_assessment_in_json(self, class_id: int, assessment_data: Dict) -> Optional[Dict]:
        """Create assessment in JSON file"""
        data = self._load_json()
        new_id = data.get('last_id', 0) + 1
        
        assessment = {
            'id': new_id,
            'class_id': class_id,
            **assessment_data,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        data.setdefault('assessments', []).append(assessment)
        data['last_id'] = new_id
        self._save_json(data)
        return assessment
    
    def _update_assessment_in_json(self, assessment_id: int, updates: Dict) -> bool:
        """Update assessment in JSON file"""
        data = self._load_json()
        for assessment in data.get('assessments', []):
            if assessment.get('id') == assessment_id:
                assessment.update(updates)
                assessment['updated_at'] = datetime.now().isoformat()
                self._save_json(data)
                return True
        return False
    
    def _delete_assessment_from_json(self, assessment_id: int) -> bool:
        """Delete assessment from JSON file"""
        data = self._load_json()
        assessments = data.get('assessments', [])
        data['assessments'] = [a for a in assessments if a.get('id') != assessment_id]
        self._save_json(data)
        return True
    
    def _get_scores_from_json(self, assessment_id: int) -> List[Dict]:
        """Get scores for an assessment from grades.json"""
        grades_path = os.path.join(
            os.path.dirname(self.json_path), "grades.json"
        )
        try:
            if os.path.exists(grades_path):
                with open(grades_path, 'r') as f:
                    grades_data = json.load(f)
                # Filter scores for this assessment
                return [s for s in grades_data.get('scores', []) 
                        if s.get('assessment_id') == assessment_id]
        except Exception as e:
            print(f"[ASSESSMENT SERVICE] Error loading scores: {e}")
        return []
