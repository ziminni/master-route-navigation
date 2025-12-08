# assessment_service.py
"""
Service for managing assessments (quizzes, exams, performance tasks).
Each assessment is linked to a rubric component for grade calculation.

Now integrated with Django backend API with JSON fallback for offline mode.
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

# Try to import the new API service
try:
    from frontend.services.Academics.Classroom.assessment_api_service import AssessmentAPIService
    API_SERVICE_AVAILABLE = True
except ImportError:
    API_SERVICE_AVAILABLE = False
    AssessmentAPIService = None


class AssessmentService:
    """
    Service for managing class assessments.
    Assessments are linked to rubric components for weighted grade calculation.
    
    Now uses Django backend API as primary storage with JSON fallback.
    """
    
    def __init__(self, data_file: str = None, class_id: int = None):
        # Initialize API service if available
        self.api_service = None
        self.use_api = False
        
        if API_SERVICE_AVAILABLE:
            try:
                self.api_service = AssessmentAPIService(class_id)
                self.use_api = True
                print("[ASSESSMENT SERVICE] Using Django backend API")
            except Exception as e:
                print(f"[ASSESSMENT SERVICE] API service initialization failed: {e}")
        
        # JSON fallback
        if data_file is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.data_file = os.path.join(base_dir, "data", "assessments.json")
        else:
            self.data_file = data_file
        self._ensure_data_file()
    
    def _ensure_data_file(self):
        """Ensure the data file exists with default structure"""
        if not os.path.exists(self.data_file):
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            initial_data = {
                "assessments": [],  # List of all assessments
                "last_id": 0,
                "last_updated": datetime.now().isoformat()
            }
            self._save_data(initial_data)
    
    def _load_data(self) -> Dict:
        """Load assessments data from JSON file"""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"assessments": [], "last_id": 0, "last_updated": datetime.now().isoformat()}
    
    def _save_data(self, data: Dict):
        """Save assessments data to JSON file"""
        data["last_updated"] = datetime.now().isoformat()
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    def _create_assessment_post(self, assessment: Dict):
        """Create a post entry for the assessment in classroom_data.json"""
        try:
            # Load classroom data
            classroom_data_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data", "classroom_data.json"
            )
            
            print(f"[ASSESSMENT SERVICE] Creating post in: {classroom_data_file}")
            print(f"[ASSESSMENT SERVICE] File exists: {os.path.exists(classroom_data_file)}")
            
            with open(classroom_data_file, 'r') as f:
                classroom_data = json.load(f)
            
            posts = classroom_data.get("posts", [])
            print(f"[ASSESSMENT SERVICE] Current posts count: {len(posts)}")
            
            # Generate new post ID - use 'id' field to match existing format
            max_post_id = max([p.get("id", 0) for p in posts], default=0)
            new_post_id = max_post_id + 1
            
            # Format date for display (short format like "Dec 04")
            created_at = assessment.get("created_at", datetime.now().isoformat())
            try:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                date_display = dt.strftime("%b %d")
            except Exception:
                date_display = datetime.now().strftime("%b %d")
            
            # Create the post - match existing format in classroom_data.json
            post = {
                "id": new_post_id,
                "class_id": assessment.get("class_id", 1),
                "topic_id": assessment.get("topic_id"),
                "type": "assessment",
                "title": assessment.get("title", "Untitled Assessment"),
                "content": assessment.get("description", ""),
                "author": assessment.get("created_by") or "Instructor",
                "date": date_display,
                "score": assessment.get("max_points", 100),
                "attachment": None,
                # Extra fields for assessment linking
                "assessment_id": assessment.get("id"),
                "rubric_component": assessment.get("rubric_component_name", ""),
                "academic_period": assessment.get("academic_period", "midterm")
            }
            
            print(f"[ASSESSMENT SERVICE] New post: {post}")
            
            posts.append(post)
            classroom_data["posts"] = posts
            
            with open(classroom_data_file, 'w') as f:
                json.dump(classroom_data, f, indent=4)
            
            print(f"[ASSESSMENT SERVICE] Created post for assessment: {assessment.get('title')} - Posts now: {len(posts)}")
            
        except Exception as e:
            import traceback
            print(f"[ASSESSMENT SERVICE] Failed to create assessment post: {e}")
            traceback.print_exc()
    
    def _generate_id(self) -> int:
        """Generate a new unique ID"""
        data = self._load_data()
        new_id = data.get("last_id", 0) + 1
        data["last_id"] = new_id
        self._save_data(data)
        return new_id
    
    def get_assessments_by_class(self, class_id: int) -> List[Dict]:
        """Get all assessments for a class"""
        # Try API first
        if self.use_api and self.api_service:
            try:
                result = self.api_service.get_all_assessments(class_id)
                print(f"[ASSESSMENT SERVICE] API returned {len(result)} assessments for class {class_id}")
                return result
            except Exception as e:
                print(f"[ASSESSMENT SERVICE] API call failed, using JSON fallback: {e}")
        
        # JSON fallback
        data = self._load_data()
        assessments = [a for a in data.get("assessments", []) 
                if a.get("class_id") == class_id]
        print(f"[ASSESSMENT SERVICE] JSON fallback returned {len(assessments)} assessments for class {class_id}")
        for a in assessments:
            print(f"  - {a.get('title')}: component={a.get('rubric_component_name')}, period={a.get('academic_period')}")
        return assessments
    
    def get_assessments_by_component(self, class_id: int, 
                                      rubric_component_id: int) -> List[Dict]:
        """Get all assessments linked to a specific rubric component"""
        data = self._load_data()
        return [a for a in data.get("assessments", []) 
                if a.get("class_id") == class_id 
                and a.get("rubric_component_id") == rubric_component_id]
    
    def get_assessments_by_period(self, class_id: int, 
                                   academic_period: str) -> List[Dict]:
        """Get all assessments for a specific academic period (midterm/finals)"""
        # Try API first
        if self.use_api and self.api_service:
            try:
                return self.api_service.get_assessments_by_period(academic_period, class_id)
            except Exception as e:
                print(f"[ASSESSMENT SERVICE] API call failed, using JSON fallback: {e}")
        
        # JSON fallback
        data = self._load_data()
        return [a for a in data.get("assessments", []) 
                if a.get("class_id") == class_id 
                and a.get("academic_period", "").lower() == academic_period.lower()]
    
    def get_assessment_by_id(self, assessment_id: int) -> Optional[Dict]:
        """Get a specific assessment by ID"""
        # Try API first
        if self.use_api and self.api_service:
            try:
                return self.api_service.get_assessment(assessment_id)
            except Exception as e:
                print(f"[ASSESSMENT SERVICE] API call failed, using JSON fallback: {e}")
        
        # JSON fallback
        data = self._load_data()
        for assessment in data.get("assessments", []):
            if assessment.get("id") == assessment_id:
                return assessment
        return None
    
    def create_assessment(self, assessment_data: Dict = None, **kwargs) -> Optional[Dict]:
        """
        Create a new assessment linked to a rubric component.
        
        Can be called with a dict or keyword arguments:
            assessment_service.create_assessment({'class_id': 1, 'title': 'Quiz 1', ...})
            OR
            assessment_service.create_assessment(class_id=1, title='Quiz 1', ...)
        
        Args:
            assessment_data: Dict containing assessment data
            **kwargs: Alternative to dict - individual parameters
            
        Required fields:
            - class_id: The class ID
            - title: Assessment title
            - rubric_component_name: Name of the rubric component
            - academic_period/term: midterm or final
            - max_points/max_score: Maximum score
        
        Returns:
            The created assessment dict or None on error
        """
        try:
            # Merge dict and kwargs
            if assessment_data is None:
                assessment_data = {}
            params = {**assessment_data, **kwargs}
            
            # Extract required fields with fallbacks
            class_id = params.get('class_id', 1)
            print(f"[ASSESSMENT SERVICE] create_assessment called with class_id: {class_id}")
            print(f"[ASSESSMENT SERVICE] Full params: {params}")
            title = params.get('title', 'Untitled Assessment')
            rubric_component_id = params.get('rubric_component_id', 0)
            rubric_component_name = params.get('rubric_component_name', params.get('rubric_component_type', ''))
            academic_period = params.get('academic_period', params.get('term', 'midterm'))
            max_points = params.get('max_points', params.get('max_score', 100))
            description = params.get('description', '')
            topic_id = params.get('topic_id')
            due_date = params.get('due_date')
            created_by = params.get('created_by')
            is_published = params.get('is_published', False)
            
            # Prepare assessment data
            assessment_data_prepared = {
                "class_id": class_id,
                "title": title,
                "description": description,
                "rubric_component_id": rubric_component_id,
                "rubric_component_name": rubric_component_name,
                "academic_period": academic_period.lower() if academic_period else "midterm",
                "max_points": max_points,
                "topic_id": topic_id,
                "due_date": due_date,
                "is_published": is_published,
                "created_by": created_by
            }
            
            # Try API first
            if self.use_api and self.api_service:
                try:
                    result = self.api_service.create_assessment(assessment_data_prepared, class_id)
                    if result:
                        # Also create post for stream
                        self._create_assessment_post(result)
                        print(f"[ASSESSMENT SERVICE] Created assessment via API: {title}")
                        return result
                except Exception as e:
                    print(f"[ASSESSMENT SERVICE] API create failed, using JSON fallback: {e}")
            
            # JSON fallback
            data = self._load_data()
            
            new_id = data.get("last_id", 0) + 1
            data["last_id"] = new_id
            
            now = datetime.now().isoformat()
            
            assessment = {
                "id": new_id,
                **assessment_data_prepared,
                "created_at": now,
                "updated_at": now
            }
            
            data["assessments"].append(assessment)
            self._save_data(data)
            
            # Also create a post for the class stream/classworks
            self._create_assessment_post(assessment)
            
            print(f"[ASSESSMENT SERVICE] Created assessment: {title} (ID: {new_id})")
            print(f"  - class_id: {class_id}")
            print(f"  - rubric_component_name: {rubric_component_name}")
            print(f"  - academic_period: {academic_period.lower() if academic_period else 'midterm'}")
            print(f"  - max_points: {max_points}")
            return assessment
            
        except Exception as e:
            print(f"[ASSESSMENT SERVICE] Error creating assessment: {e}")
            return None
    
    def update_assessment(self, assessment_id: int, updates: Dict) -> bool:
        """Update an existing assessment"""
        try:
            # Don't allow changing certain fields
            protected_fields = ["id", "class_id", "created_at", "created_by"]
            for field in protected_fields:
                updates.pop(field, None)
            
            # Try API first
            if self.use_api and self.api_service:
                try:
                    if self.api_service.update_assessment(assessment_id, updates):
                        print(f"[ASSESSMENT SERVICE] Updated assessment via API ID: {assessment_id}")
                        return True
                except Exception as e:
                    print(f"[ASSESSMENT SERVICE] API update failed, using JSON fallback: {e}")
            
            # JSON fallback
            data = self._load_data()
            
            for assessment in data.get("assessments", []):
                if assessment.get("id") == assessment_id:
                    assessment.update(updates)
                    assessment["updated_at"] = datetime.now().isoformat()
                    self._save_data(data)
                    
                    print(f"[ASSESSMENT SERVICE] Updated assessment ID: {assessment_id}")
                    return True
            
            return False
            
        except Exception as e:
            print(f"[ASSESSMENT SERVICE] Error updating assessment: {e}")
            return False
    
    def delete_assessment(self, assessment_id: int) -> bool:
        """Delete an assessment"""
        try:
            # Try API first
            if self.use_api and self.api_service:
                try:
                    if self.api_service.delete_assessment(assessment_id):
                        print(f"[ASSESSMENT SERVICE] Deleted assessment via API ID: {assessment_id}")
                        return True
                except Exception as e:
                    print(f"[ASSESSMENT SERVICE] API delete failed, using JSON fallback: {e}")
            
            # JSON fallback
            data = self._load_data()
            assessments = data.get("assessments", [])
            
            for i, assessment in enumerate(assessments):
                if assessment.get("id") == assessment_id:
                    del assessments[i]
                    self._save_data(data)
                    print(f"[ASSESSMENT SERVICE] Deleted assessment ID: {assessment_id}")
                    return True
            
            return False
            
        except Exception as e:
            print(f"[ASSESSMENT SERVICE] Error deleting assessment: {e}")
            return False
    
    def publish_assessment(self, assessment_id: int) -> bool:
        """Publish an assessment so students can see it"""
        return self.update_assessment(assessment_id, {"is_published": True})
    
    def unpublish_assessment(self, assessment_id: int) -> bool:
        """Unpublish an assessment"""
        return self.update_assessment(assessment_id, {"is_published": False})
    
    def get_published_assessments(self, class_id: int) -> List[Dict]:
        """Get all published assessments for a class"""
        assessments = self.get_assessments_by_class(class_id)
        return [a for a in assessments if a.get("is_published", False)]
    
    def get_assessments_grouped_by_component(self, class_id: int) -> Dict[str, List[Dict]]:
        """
        Get assessments grouped by rubric component name and period.
        Useful for displaying in grades table.
        
        Returns:
            {
                "quiz_midterm": [assessment1, assessment2, ...],
                "performance_task_midterm": [...],
                "exam_midterm": [...],
                "quiz_finals": [...],
                ...
            }
        """
        assessments = self.get_assessments_by_class(class_id)
        grouped = {}
        
        for assessment in assessments:
            component_name = assessment.get("rubric_component_name", "").lower().replace(" ", "_")
            period = assessment.get("academic_period", "").lower()
            key = f"{component_name}_{period}"
            
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(assessment)
        
        return grouped
    
    def count_assessments_by_component(self, class_id: int, 
                                        rubric_component_id: int) -> int:
        """Count how many assessments are linked to a component"""
        assessments = self.get_assessments_by_component(class_id, rubric_component_id)
        return len(assessments)
