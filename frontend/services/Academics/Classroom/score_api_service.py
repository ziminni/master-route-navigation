"""
Score Service - Django Backend Integration

This service handles all score/grade operations through the Django REST API.
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


class ScoreAPIService:
    """
    Service for managing student scores/grades.
    Uses Django backend API with JSON file fallback for offline mode.
    """
    
    def __init__(self, class_id: Optional[int] = None):
        self.class_id = class_id
        self.api_client: Optional[APIClient] = None
        self.offline_mode = False
        
        # JSON fallback path
        self.json_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "grades.json"
        )
        
        # Initialize API client
        if API_AVAILABLE:
            self.api_client = get_api_client()
        else:
            self.offline_mode = True
            print("[SCORE SERVICE] API client not available, using offline mode")
    
    def set_class(self, class_id: int):
        """Set the class ID for score operations"""
        self.class_id = class_id
    
    # ==================== SCORE OPERATIONS ====================
    
    def get_all_scores(self, class_id: Optional[int] = None) -> List[Dict]:
        """Get all scores for a class"""
        cid = class_id or self.class_id
        if not cid:
            print("[SCORE SERVICE] No class ID provided")
            return []
        
        if self.api_client and not self.offline_mode:
            result = self.api_client.get(f"academics/classes/{cid}/scores/")
            if not result.get('error'):
                return result if isinstance(result, list) else result.get('results', [])
            self.offline_mode = True
        
        return self._get_scores_from_json(cid)
    
    def get_score(self, score_id: int) -> Optional[Dict]:
        """Get a specific score by ID"""
        if self.api_client and not self.offline_mode:
            result = self.api_client.get(f"academics/scores/{score_id}/")
            if not result.get('error'):
                return result
            self.offline_mode = True
        
        return self._get_score_from_json(score_id)
    
    def get_scores_for_student(self, student_id: int, 
                                class_id: Optional[int] = None) -> List[Dict]:
        """Get all scores for a specific student in a class"""
        scores = self.get_all_scores(class_id)
        return [s for s in scores if s.get('student_id') == student_id]
    
    def get_scores_for_assessment(self, assessment_id: int, 
                                   class_id: Optional[int] = None) -> List[Dict]:
        """Get all scores for a specific assessment"""
        scores = self.get_all_scores(class_id)
        return [s for s in scores if s.get('assessment_id') == assessment_id]
    
    def create_score(self, student_id: int, assessment_id: int, 
                     points: float, class_id: Optional[int] = None) -> Optional[Dict]:
        """Create a new score entry"""
        cid = class_id or self.class_id
        if not cid:
            return None
        
        score_data = {
            'student_id': student_id,
            'assessment_id': assessment_id,
            'points': points,
            'is_published': False
        }
        
        if self.api_client and not self.offline_mode:
            result = self.api_client.post(f"academics/classes/{cid}/scores/", score_data)
            if not result.get('error'):
                return result
            self.offline_mode = True
        
        return self._create_score_in_json(cid, score_data)
    
    def update_score(self, score_id: int, points: float) -> bool:
        """Update a score"""
        if self.api_client and not self.offline_mode:
            result = self.api_client.patch(f"academics/scores/{score_id}/", {
                'points': points
            })
            if not result.get('error'):
                return True
            self.offline_mode = True
        
        return self._update_score_in_json(score_id, {'points': points})
    
    def update_score_by_student_assessment(self, student_id: int, assessment_id: int,
                                           points: float, class_id: Optional[int] = None) -> bool:
        """Update or create score by student and assessment IDs"""
        cid = class_id or self.class_id
        
        # Find existing score
        scores = self.get_scores_for_assessment(assessment_id, cid)
        for score in scores:
            if score.get('student_id') == student_id:
                return self.update_score(score['id'], points)
        
        # Create new score if not exists
        result = self.create_score(student_id, assessment_id, points, cid)
        return result is not None
    
    def delete_score(self, score_id: int) -> bool:
        """Delete a score"""
        if self.api_client and not self.offline_mode:
            result = self.api_client.delete(f"academics/scores/{score_id}/")
            if not result.get('error'):
                return True
            self.offline_mode = True
        
        return self._delete_score_from_json(score_id)
    
    # ==================== BULK OPERATIONS ====================
    
    def bulk_create_scores(self, scores: List[Dict], class_id: Optional[int] = None) -> bool:
        """
        Bulk create scores.
        
        Each score dict should have:
        - student_id: int
        - assessment_id: int
        - points: float
        """
        cid = class_id or self.class_id
        if not cid:
            return False
        
        if self.api_client and not self.offline_mode:
            result = self.api_client.post(f"academics/classes/{cid}/scores/bulk-create/", {
                'scores': scores
            })
            if not result.get('error'):
                return True
            self.offline_mode = True
        
        # Fallback: create scores one by one
        success = True
        for score in scores:
            result = self._create_score_in_json(cid, score)
            if not result:
                success = False
        return success
    
    def bulk_update_scores(self, scores: List[Dict]) -> bool:
        """
        Bulk update scores.
        
        Each score dict should have:
        - id: int (score_id)
        - points: float
        """
        if self.api_client and not self.offline_mode:
            result = self.api_client.patch("academics/scores/bulk-update/", {
                'scores': scores
            })
            if not result.get('error'):
                return True
            self.offline_mode = True
        
        # Fallback: update scores one by one
        success = True
        for score in scores:
            if not self._update_score_in_json(score['id'], {'points': score['points']}):
                success = False
        return success
    
    # ==================== PUBLISH OPERATIONS ====================
    
    def publish_score(self, score_id: int) -> bool:
        """Publish a score to make it visible to students"""
        if self.api_client and not self.offline_mode:
            result = self.api_client.patch(f"academics/scores/{score_id}/", {
                'is_published': True
            })
            if not result.get('error'):
                return True
            self.offline_mode = True
        
        return self._update_score_in_json(score_id, {'is_published': True})
    
    def unpublish_score(self, score_id: int) -> bool:
        """Unpublish a score"""
        if self.api_client and not self.offline_mode:
            result = self.api_client.patch(f"academics/scores/{score_id}/", {
                'is_published': False
            })
            if not result.get('error'):
                return True
            self.offline_mode = True
        
        return self._update_score_in_json(score_id, {'is_published': False})
    
    def publish_assessment_scores(self, assessment_id: int, class_id: Optional[int] = None) -> bool:
        """Publish all scores for an assessment"""
        scores = self.get_scores_for_assessment(assessment_id, class_id)
        success = True
        for score in scores:
            if not self.publish_score(score['id']):
                success = False
        return success
    
    # ==================== GRADE CALCULATION ====================
    
    def get_student_grade_summary(self, student_id: int, 
                                   class_id: Optional[int] = None) -> Dict:
        """
        Get grade summary for a student.
        
        Returns:
        {
            'midterm': {
                'Quiz': {'total': 85, 'max': 100, 'percentage': 85.0, 'weight': 30},
                'Performance Task': {...},
                'Exam': {...},
                'weighted_average': 83.5
            },
            'finals': {...},
            'overall_grade': 85.2
        }
        """
        scores = self.get_scores_for_student(student_id, class_id)
        
        # This would need assessment and rubric data to calculate properly
        # For now, return basic structure
        summary = {
            'midterm': {'weighted_average': 0, 'components': {}},
            'finals': {'weighted_average': 0, 'components': {}},
            'overall_grade': 0
        }
        
        # Group scores by period and component
        for score in scores:
            period = score.get('academic_period', 'midterm')
            component = score.get('rubric_component_name', 'Unknown')
            
            if period not in summary:
                summary[period] = {'weighted_average': 0, 'components': {}}
            
            if component not in summary[period]['components']:
                summary[period]['components'][component] = {
                    'total': 0, 'max': 0, 'count': 0
                }
            
            comp_data = summary[period]['components'][component]
            comp_data['total'] += score.get('points', 0)
            comp_data['max'] += score.get('max_points', 100)
            comp_data['count'] += 1
        
        return summary
    
    def get_class_grade_matrix(self, class_id: Optional[int] = None) -> Dict:
        """
        Get complete grade matrix for a class.
        Returns data structured for the grades table view.
        
        Returns:
        {
            'students': [...],
            'assessments': {
                'midterm': {'Quiz': [...], 'Performance Task': [...]},
                'finals': {...}
            },
            'scores': {
                'student_id': {
                    'assessment_id': score_value
                }
            }
        }
        """
        cid = class_id or self.class_id
        scores = self.get_all_scores(cid)
        
        # Build matrix
        matrix = {
            'students': set(),
            'assessments': {},
            'scores': {}
        }
        
        for score in scores:
            student_id = score.get('student_id')
            assessment_id = score.get('assessment_id')
            
            matrix['students'].add(student_id)
            
            if student_id not in matrix['scores']:
                matrix['scores'][student_id] = {}
            
            matrix['scores'][student_id][assessment_id] = {
                'points': score.get('points', 0),
                'max_points': score.get('max_points', 100),
                'is_published': score.get('is_published', False)
            }
        
        matrix['students'] = list(matrix['students'])
        return matrix
    
    # ==================== JSON FALLBACK METHODS ====================
    
    def _load_json(self) -> Dict:
        """Load data from JSON file"""
        try:
            if os.path.exists(self.json_path):
                with open(self.json_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[SCORE SERVICE] Error loading JSON: {e}")
        return {'scores': [], 'last_id': 0}
    
    def _save_json(self, data: Dict):
        """Save data to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
            with open(self.json_path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"[SCORE SERVICE] Error saving JSON: {e}")
    
    def _get_scores_from_json(self, class_id: int) -> List[Dict]:
        """Get scores from JSON file"""
        data = self._load_json()
        return [s for s in data.get('scores', []) if s.get('class_id') == class_id]
    
    def _get_score_from_json(self, score_id: int) -> Optional[Dict]:
        """Get single score from JSON file"""
        data = self._load_json()
        for score in data.get('scores', []):
            if score.get('id') == score_id:
                return score
        return None
    
    def _create_score_in_json(self, class_id: int, score_data: Dict) -> Optional[Dict]:
        """Create score in JSON file"""
        data = self._load_json()
        new_id = data.get('last_id', 0) + 1
        
        score = {
            'id': new_id,
            'class_id': class_id,
            **score_data,
            'is_published': score_data.get('is_published', False),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        data.setdefault('scores', []).append(score)
        data['last_id'] = new_id
        self._save_json(data)
        return score
    
    def _update_score_in_json(self, score_id: int, updates: Dict) -> bool:
        """Update score in JSON file"""
        data = self._load_json()
        for score in data.get('scores', []):
            if score.get('id') == score_id:
                score.update(updates)
                score['updated_at'] = datetime.now().isoformat()
                self._save_json(data)
                return True
        return False
    
    def _delete_score_from_json(self, score_id: int) -> bool:
        """Delete score from JSON file"""
        data = self._load_json()
        scores = data.get('scores', [])
        data['scores'] = [s for s in scores if s.get('id') != score_id]
        self._save_json(data)
        return True
