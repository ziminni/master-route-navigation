# score_service.py
"""
Service for managing student scores on assessments.
Handles draft/publish functionality for grades.
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional


class ScoreService:
    """
    Service for managing student scores.
    Each score links a student to an assessment with points earned.
    Scores can be in draft mode (not visible to students) or published.
    """
    
    def __init__(self, data_file: str = None):
        if data_file is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.data_file = os.path.join(base_dir, "data", "scores.json")
        else:
            self.data_file = data_file
        self._ensure_data_file()
    
    def _ensure_data_file(self):
        """Ensure the data file exists with default structure"""
        if not os.path.exists(self.data_file):
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            initial_data = {
                "scores": [],
                "last_id": 0,
                "last_updated": datetime.now().isoformat()
            }
            self._save_data(initial_data)
    
    def _load_data(self) -> Dict:
        """Load scores data from JSON file"""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"scores": [], "last_id": 0, "last_updated": datetime.now().isoformat()}
    
    def _save_data(self, data: Dict):
        """Save scores data to JSON file"""
        data["last_updated"] = datetime.now().isoformat()
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    def get_score(self, student_id: str, assessment_id: int) -> Optional[Dict]:
        """Get a specific score for a student on an assessment"""
        data = self._load_data()
        for score in data.get("scores", []):
            if (str(score.get("student_id")) == str(student_id) and 
                score.get("assessment_id") == assessment_id):
                return score
        return None
    
    def get_scores_by_student(self, student_id: str, class_id: int) -> List[Dict]:
        """Get all scores for a student in a class"""
        data = self._load_data()
        return [s for s in data.get("scores", []) 
                if str(s.get("student_id")) == str(student_id) 
                and s.get("class_id") == class_id]
    
    def get_scores_by_assessment(self, assessment_id: int) -> List[Dict]:
        """Get all scores for an assessment"""
        data = self._load_data()
        return [s for s in data.get("scores", []) 
                if s.get("assessment_id") == assessment_id]
    
    def get_scores_by_class(self, class_id: int) -> List[Dict]:
        """Get all scores for a class"""
        data = self._load_data()
        return [s for s in data.get("scores", []) 
                if s.get("class_id") == class_id]
    
    def get_published_scores_for_student(self, student_id: str, class_id: int) -> List[Dict]:
        """Get only published scores for a student (visible to student)"""
        scores = self.get_scores_by_student(student_id, class_id)
        return [s for s in scores if s.get("is_published", False)]
    
    def save_score(self, class_id: int, student_id: str, assessment_id: int,
                   points: int, max_points: int, is_draft: bool = True,
                   uploaded_by: Optional[str] = None) -> Optional[Dict]:
        """
        Save or update a score for a student.
        
        Args:
            class_id: The class ID
            student_id: The student's institutional ID
            assessment_id: The assessment ID
            points: Points earned
            max_points: Maximum possible points
            is_draft: True if draft (not visible to student)
            uploaded_by: Username of the faculty member
        
        Returns:
            The saved score dict
        """
        try:
            data = self._load_data()
            
            # Check if score already exists
            existing_score = None
            for i, score in enumerate(data.get("scores", [])):
                if (str(score.get("student_id")) == str(student_id) and 
                    score.get("assessment_id") == assessment_id):
                    existing_score = (i, score)
                    break
            
            now = datetime.now().isoformat()
            
            if existing_score:
                # Update existing score
                idx, score = existing_score
                score.update({
                    "points": points,
                    "max_points": max_points,
                    "is_published": not is_draft,
                    "updated_at": now,
                    "uploaded_by": uploaded_by
                })
                data["scores"][idx] = score
                print(f"[SCORE SERVICE] Updated score for student {student_id} on assessment {assessment_id}")
            else:
                # Create new score
                new_id = data.get("last_id", 0) + 1
                data["last_id"] = new_id
                
                score = {
                    "id": new_id,
                    "class_id": class_id,
                    "student_id": student_id,
                    "assessment_id": assessment_id,
                    "points": points,
                    "max_points": max_points,
                    "is_published": not is_draft,
                    "created_at": now,
                    "updated_at": now,
                    "uploaded_by": uploaded_by
                }
                data["scores"].append(score)
                print(f"[SCORE SERVICE] Created score for student {student_id} on assessment {assessment_id}")
            
            self._save_data(data)
            return score
            
        except Exception as e:
            print(f"[SCORE SERVICE] Error saving score: {e}")
            return None
    
    def bulk_save_scores(self, class_id: int, assessment_id: int, 
                         scores_data: List[Dict], is_draft: bool = True,
                         uploaded_by: Optional[str] = None) -> int:
        """
        Save scores for multiple students at once.
        
        Args:
            class_id: The class ID
            assessment_id: The assessment ID
            scores_data: List of {"student_id": str, "points": int, "max_points": int}
            is_draft: Whether scores are drafts
            uploaded_by: Username of faculty member
        
        Returns:
            Number of scores saved
        """
        count = 0
        for score_data in scores_data:
            result = self.save_score(
                class_id=class_id,
                student_id=score_data["student_id"],
                assessment_id=assessment_id,
                points=score_data["points"],
                max_points=score_data["max_points"],
                is_draft=is_draft,
                uploaded_by=uploaded_by
            )
            if result:
                count += 1
        return count
    
    def publish_scores(self, assessment_id: int) -> int:
        """
        Publish all scores for an assessment (make them visible to students).
        
        Returns:
            Number of scores published
        """
        try:
            data = self._load_data()
            count = 0
            now = datetime.now().isoformat()
            
            for score in data.get("scores", []):
                if score.get("assessment_id") == assessment_id and not score.get("is_published"):
                    score["is_published"] = True
                    score["updated_at"] = now
                    count += 1
            
            if count > 0:
                self._save_data(data)
                print(f"[SCORE SERVICE] Published {count} scores for assessment {assessment_id}")
            
            return count
            
        except Exception as e:
            print(f"[SCORE SERVICE] Error publishing scores: {e}")
            return 0
    
    def unpublish_scores(self, assessment_id: int) -> int:
        """Unpublish all scores for an assessment (hide from students)"""
        try:
            data = self._load_data()
            count = 0
            now = datetime.now().isoformat()
            
            for score in data.get("scores", []):
                if score.get("assessment_id") == assessment_id and score.get("is_published"):
                    score["is_published"] = False
                    score["updated_at"] = now
                    count += 1
            
            if count > 0:
                self._save_data(data)
                print(f"[SCORE SERVICE] Unpublished {count} scores for assessment {assessment_id}")
            
            return count
            
        except Exception as e:
            print(f"[SCORE SERVICE] Error unpublishing scores: {e}")
            return 0
    
    def delete_score(self, student_id: str, assessment_id: int) -> bool:
        """Delete a specific score"""
        try:
            data = self._load_data()
            scores = data.get("scores", [])
            
            for i, score in enumerate(scores):
                if (str(score.get("student_id")) == str(student_id) and 
                    score.get("assessment_id") == assessment_id):
                    del scores[i]
                    self._save_data(data)
                    print(f"[SCORE SERVICE] Deleted score for student {student_id}")
                    return True
            
            return False
            
        except Exception as e:
            print(f"[SCORE SERVICE] Error deleting score: {e}")
            return False
    
    def get_class_grade_matrix(self, class_id: int) -> Dict[str, Dict[int, Dict]]:
        """
        Get all scores for a class organized by student and assessment.
        Useful for displaying in a grades table.
        
        Returns:
            {
                "student_id": {
                    assessment_id: {"points": 85, "max_points": 100, "is_published": True},
                    ...
                },
                ...
            }
        """
        scores = self.get_scores_by_class(class_id)
        matrix = {}
        
        for score in scores:
            student_id = str(score.get("student_id"))
            assessment_id = score.get("assessment_id")
            
            if student_id not in matrix:
                matrix[student_id] = {}
            
            matrix[student_id][assessment_id] = {
                "points": score.get("points", 0),
                "max_points": score.get("max_points", 0),
                "is_published": score.get("is_published", False),
                "updated_at": score.get("updated_at")
            }
        
        return matrix
    
    def calculate_component_average(self, student_id: str, class_id: int,
                                     assessment_ids: List[int]) -> Optional[float]:
        """
        Calculate average percentage for a list of assessments (same component).
        
        Returns:
            Average percentage (0-100) or None if no scores
        """
        scores = self.get_scores_by_student(student_id, class_id)
        
        total_points = 0
        total_max = 0
        
        for score in scores:
            if score.get("assessment_id") in assessment_ids:
                total_points += score.get("points", 0)
                total_max += score.get("max_points", 0)
        
        if total_max > 0:
            return (total_points / total_max) * 100
        
        return None
