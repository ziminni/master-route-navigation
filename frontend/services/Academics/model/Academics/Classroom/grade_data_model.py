from PyQt6.QtCore import QObject, pyqtSignal
from .grade_item import GradeItem
import sys
import os
import json

# Add data directory to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from frontend.services.Academics.data.grade_manager import GradeDataManager
except ImportError:
    print("Warning: Could not import GradeDataManager")
    GradeDataManager = None

# Import backend services for rubric persistence
try:
    from frontend.services.Academics.Classroom.grading_rubric_service import GradingRubricService
except ImportError:
    print("Warning: Could not import GradingRubricService")
    GradingRubricService = None

# Import Score API service for backend integration
try:
    from frontend.services.Academics.Classroom.score_api_service import ScoreAPIService
    SCORE_API_AVAILABLE = True
except ImportError:
    print("Warning: Could not import ScoreAPIService")
    ScoreAPIService = None
    SCORE_API_AVAILABLE = False

class GradeDataModel(QObject):
    """
    Main data model holding all application data.
    FLEXIBLE: Adapts to any users from Django backend or JSON files
    FUTURE-READY: Prepared for PostgreSQL integration
    WITH BACKEND INTEGRATION: Loads rubrics from persistent storage
    NOW USES: Score API for backend grade storage
    """
    data_reset = pyqtSignal()
    data_updated = pyqtSignal()
    columns_changed = pyqtSignal()

    def __init__(self, class_id=1):
        super().__init__()
        self.class_id = class_id
        self.students = []
        self.current_user = None  # Store current logged-in user
        
        # Initialize grade manager (JSON fallback)
        if GradeDataManager:
            self.grade_manager = GradeDataManager()
        else:
            self.grade_manager = None
        
        # Initialize Score API service for backend integration
        self.score_service = None
        self.use_score_api = False
        if SCORE_API_AVAILABLE and ScoreAPIService:
            try:
                self.score_service = ScoreAPIService(class_id)
                self.use_score_api = True
                print(f"[GradeDataModel] Score API service initialized for class {class_id}")
            except Exception as e:
                print(f"[GradeDataModel] Failed to initialize Score API: {e}")
        
        # Initialize rubric service
        self.rubric_service = GradingRubricService() if GradingRubricService else None
        
        # Component types with sub-items
        self.components = {
            'performance_tasks': ['PT1', 'PT2', 'PT3'],
            'quizzes': ['Quiz 1', 'Quiz 2', 'Quiz 3', 'Quiz 4'],
            'exams_midterm': ['Midterm Exam'],
            'exams_final': ['Final Exam', 'Removal Exam']
        }
        
        # Max scores for each component type
        self.component_max_scores = {
            'performance_tasks': 50,
            'quizzes': 40,
            'exams_midterm': 100,
            'exams_final': 100
        }
        
        # Rubric configuration (will be loaded from backend)
        self.rubric_config = {
            'midterm': {
                'term_percentage': 33,
                'components': {
                    'performance task': 20,
                    'quiz': 30,
                    'exam': 50
                }
            },
            'final': {
                'term_percentage': 67,
                'components': {
                    'performance task': 20,
                    'quiz': 30,
                    'exam': 50
                }
            }
        }
        
        # Component type mapping
        self.component_type_mapping = {
            'performance task': 'performance_tasks',
            'quiz': 'quizzes',
            'exam': 'exams'
        }
        
        # Column expansion states
        self.column_states = {
            'midterm_expanded': False,
            'finalterm_expanded': False,
        }
        self._initialize_component_states()
        
        # Grade storage: {student_id: {component_key: GradeItem}}
        self.grades = {}
        
        # Load rubrics from backend
        self._load_rubric_from_backend()

    def _initialize_component_states(self):
        """Initialize column states for all component types"""
        for term in ['midterm', 'finalterm']:
            term_key = 'midterm' if term == 'midterm' else 'final'
            for comp_name in self.rubric_config[term_key]['components'].keys():
                comp_key = comp_name.replace(' ', '_')
                state_key = f'{comp_key}_{term}_expanded'
                if state_key not in self.column_states:
                    self.column_states[state_key] = False

    def _load_rubric_from_backend(self):
        """Load rubric configuration from backend service"""
        if not self.rubric_service:
            print("[GradeDataModel] No rubric service available")
            return
        
        try:
            rubrics = self.rubric_service.get_class_rubrics(self.class_id)
            if rubrics:
                self._apply_rubric_from_backend(rubrics)
                print(f"[GradeDataModel] Loaded rubric for class {self.class_id}")
            else:
                print(f"[GradeDataModel] No rubrics found for class {self.class_id}, using defaults")
        except Exception as e:
            print(f"[GradeDataModel] Failed to load rubric: {e}")

    def _apply_rubric_from_backend(self, rubrics: dict):
        """
        Apply rubric data from backend to internal config.
        
        Args:
            rubrics: Dict with structure:
                {
                    "midterm": {"term_percentage": 33, "components": [...]},
                    "finals": {"term_percentage": 67, "components": [...]}
                }
        """
        for term_key in ["midterm", "finals"]:
            if term_key not in rubrics:
                continue
            
            rubric = rubrics[term_key]
            internal_key = "midterm" if term_key == "midterm" else "final"
            
            self.rubric_config[internal_key]['term_percentage'] = rubric.get('term_percentage', 50)
            self.rubric_config[internal_key]['components'] = {}
            
            for component in rubric.get('components', []):
                comp_name = component.get('name', '').lower()
                comp_percentage = component.get('percentage', 0)
                self.rubric_config[internal_key]['components'][comp_name] = comp_percentage
                
                # Update component type mapping
                self._update_component_type_mapping(comp_name)
        
        self._initialize_component_states()
        print(f"[GradeDataModel] Applied rubric config: {self.rubric_config}")

    def _update_component_type_mapping(self, comp_name):
        """Update component type mapping based on component name"""
        comp_lower = comp_name.lower()
        if 'task' in comp_lower or 'pt' in comp_lower or 'performance' in comp_lower:
            self.component_type_mapping[comp_lower] = 'performance_tasks'
        elif 'quiz' in comp_lower:
            self.component_type_mapping[comp_lower] = 'quizzes'
        elif 'exam' in comp_lower:
            self.component_type_mapping[comp_lower] = 'exams'
        else:
            self.component_type_mapping[comp_lower] = 'performance_tasks'

    def set_current_user(self, username, user_data=None):
        """Set the current logged-in user"""
        self.current_user = {
            'username': username,
            'data': user_data or {}
        }

    def load_students_from_django_api(self, api_response):
        """
        Load students from Django API response
        Expected format from backend API:
        {
            "students": [
                {
                    "id": 1,
                    "username": "Marcus",
                    "first_name": "Marcus",
                    "last_name": "Mercer",
                    "institutional_id": "456456456",
                    "email": "immarcusmercer@gmail.com"
                }
            ]
        }
        """
        self.students = []
        students_data = api_response.get('students', [])
        
        for student in students_data:
            self.students.append({
                'id': str(student.get('institutional_id', student.get('id', ''))),
                'name': f"{student.get('last_name', '')}, {student.get('first_name', '')}",
                'username': student.get('username', ''),
                'email': student.get('email', ''),
                'django_id': student.get('id', None)  # Keep Django DB ID for future API calls
            })
        
        # Initialize grades storage for each student
        for student in self.students:
            if student['id'] not in self.grades:
                self.grades[student['id']] = {}
        
        # Load grades from persistent storage
        self._load_grades_from_storage()
        
        print(f"[GRADE MODEL] Loaded {len(self.students)} students from Django API")
        self.data_reset.emit()

    def load_students_from_json(self, json_file_path='data/users_data.json'):
        """
        Load students from JSON file (fallback or development mode)
        """
        try:
            with open(json_file_path, 'r') as f:
                data = json.load(f)
            
            self.students = []
            users = data.get('users', [])
            
            for user in users:
                # Only include students
                if user.get('role_type') == 'student' or user.get('role') == 'student':
                    self.students.append({
                        'id': str(user.get('institutional_id', user.get('id', ''))),
                        'name': f"{user.get('last_name', '')}, {user.get('first_name', '')}",
                        'username': user.get('username', ''),
                        'email': user.get('email', ''),
                        'django_id': user.get('id', None)
                    })
            
            # Initialize grades storage
            for student in self.students:
                if student['id'] not in self.grades:
                    self.grades[student['id']] = {}
            
            # Load grades from persistent storage
            self._load_grades_from_storage()
            
            print(f"[GRADE MODEL] Loaded {len(self.students)} students from JSON file")
            self.data_reset.emit()
            
        except FileNotFoundError:
            print(f"[GRADE MODEL] JSON file not found: {json_file_path}")
            print("[GRADE MODEL] Falling back to sample data")
            self.load_sample_data()
        except json.JSONDecodeError:
            print(f"[GRADE MODEL] Error decoding JSON file: {json_file_path}")
            print("[GRADE MODEL] Falling back to sample data")
            self.load_sample_data()

    def _load_grades_from_storage(self):
        """Load grades from persistent storage"""
        if not self.grade_manager:
            return
        
        class_grades = self.grade_manager.get_class_grades(self.class_id)
        
        for student_id, student_grades in class_grades.items():
            if student_id not in self.grades:
                self.grades[student_id] = {}
            
            for component_key, grade_data in student_grades.items():
                grade_item = GradeItem()
                grade_item.value = grade_data.get('value', '')
                grade_item.is_draft = grade_data.get('is_draft', True)
                self.grades[student_id][component_key] = grade_item

    def load_sample_data(self):
        """Load sample student data (fallback)"""
        print("[GRADE MODEL] Loading sample data")
        
        # Try to load from script.py created users first
        sample_users = self._get_sample_users_from_script()
        
        if sample_users:
            self.students = sample_users
        else:
            # Ultimate fallback
            self.students = [
                {'id': '456456456', 'name': "Mercer, Marcus", 'username': 'Marcus', 'email': 'immarcusmercer@gmail.com'},
                {'id': '102', 'name': "Santos, Maria Elena", 'username': 'maria', 'email': 'maria@example.com'},
                {'id': '103', 'name': "Garcia, Juan Pablo", 'username': 'juan', 'email': 'juan@example.com'},
                {'id': '104', 'name': "Rodriguez, Ana Sofia", 'username': 'ana', 'email': 'ana@example.com'}
            ]
        
        for student in self.students:
            self.grades[student['id']] = {}
        
        # Load grades from storage
        self._load_grades_from_storage()
        
        print(f"[GRADE MODEL] Sample data loaded with {len(self.students)} students")
        self.data_reset.emit()

    def _get_sample_users_from_script(self):
        """Extract sample users from script.py pattern"""
        # This matches the users created in your script.py
        return [
            {
                'id': '456456456', 
                'name': "Mercer, Marcus", 
                'username': 'Marcus', 
                'email': 'immarcusmercer@gmail.com',
                'first_name': 'Marcus',
                'last_name': 'Mercer'
            }
        ]

    def get_column_state(self, key):
        """Get column expansion state"""
        return self.column_states.get(key, False)

    def set_column_state(self, key, value):
        """Set column expansion state"""
        if self.column_states.get(key) != value:
            self.column_states[key] = value
            self.columns_changed.emit()

    def set_grade(self, student_id, component_key, value, is_draft=True, assessment_id=None):
        """Set grade for a student's component"""
        if student_id not in self.grades:
            self.grades[student_id] = {}
        
        if component_key not in self.grades[student_id]:
            self.grades[student_id][component_key] = GradeItem()
        
        self.grades[student_id][component_key].value = value
        self.grades[student_id][component_key].is_draft = is_draft
        
        # Parse score value for API
        points = 0
        if value:
            if '/' in str(value):
                try:
                    points = float(str(value).split('/')[0])
                except ValueError:
                    points = 0
            else:
                try:
                    points = float(value)
                except ValueError:
                    points = 0
        
        # Save to Score API first (if available and we have assessment_id)
        if self.use_score_api and self.score_service and assessment_id:
            try:
                # Get django_id from student data
                student_data = self.get_student_by_id(student_id)
                django_student_id = student_data.get('django_id') if student_data else None
                
                if django_student_id:
                    self.score_service.update_score_by_student_assessment(
                        django_student_id, 
                        assessment_id, 
                        points,
                        self.class_id
                    )
                    print(f"[GradeDataModel] Saved score via API: student={django_student_id}, assessment={assessment_id}, points={points}")
            except Exception as e:
                print(f"[GradeDataModel] Failed to save score via API: {e}")
        
        # Also save to persistent JSON storage (as fallback)
        if self.grade_manager:
            self.grade_manager.save_student_grade(
                student_id, self.class_id, component_key, value, is_draft
            )
        
        self.data_updated.emit()

    def get_grade(self, student_id, component_key):
        """Get grade item for a student's component"""
        if student_id in self.grades and component_key in self.grades[student_id]:
            return self.grades[student_id][component_key]
        return GradeItem()

    def bulk_set_grades(self, component_key, value):
        """Set grade value for all students in a component"""
        for student_id in self.grades.keys():
            self.set_grade(student_id, component_key, value, is_draft=True)

    def upload_grades(self, component_key):
        """Mark grades as uploaded (not draft) for a component"""
        for student_id in self.grades.keys():
            if component_key in self.grades[student_id]:
                self.grades[student_id][component_key].is_draft = False
        
        # Bulk upload in storage
        if self.grade_manager:
            self.grade_manager.bulk_upload_grades(self.class_id, component_key)
        
        self.data_updated.emit()

    def get_component_type_key(self, component_name, term=None):
        """Get the component type key for a component name"""
        comp_name_lower = component_name.lower()
        
        if 'exam' in comp_name_lower:
            if term == 'midterm':
                return 'exams_midterm'
            elif term == 'finalterm' or term == 'final':
                return 'exams_final'
            return 'exams_midterm'
        
        return self.component_type_mapping.get(comp_name_lower, 'performance_tasks')

    def get_rubric_components(self, term):
        """Get list of component names for a term"""
        term_key = 'midterm' if term == 'midterm' else 'final'
        return list(self.rubric_config[term_key]['components'].keys())

    def get_component_percentage(self, component_name, term):
        """Get percentage for a component in a term"""
        term_key = 'midterm' if term == 'midterm' else 'final'
        comp_name_lower = component_name.lower()
        return self.rubric_config[term_key]['components'].get(comp_name_lower, 0)

    def get_component_items_with_scores(self, type_key, term=None, component_name=None):
        """
        Get list of component items (assessments) with their max scores.
        Now loads from assessment service instead of static mock data.
        
        Args:
            type_key: The component type key (e.g., 'quizzes', 'performance_tasks')
            term: The academic term ('midterm' or 'finalterm')
            component_name: The rubric component name (e.g., 'quiz', 'performance task')
        
        Returns:
            List of dicts with 'name', 'max_score', and optionally 'assessment_id'
        """
        # Try to load from assessment service first
        if not component_name:
            return []
            
        try:
            from frontend.services.Academics.Classroom.assessment_service import AssessmentService
            assessment_service = AssessmentService(class_id=self.class_id)
            
            # Get all assessments for this class
            all_assessments = assessment_service.get_assessments_by_class(self.class_id)
            print(f"[GradeDataModel] ===== get_component_items_with_scores =====")
            print(f"[GradeDataModel] class_id={self.class_id}, term='{term}', component_name='{component_name}'")
            print(f"[GradeDataModel] Loaded {len(all_assessments)} total assessments for class {self.class_id}")
            
            # Determine the academic period for matching
            period = 'midterm' if term == 'midterm' else 'final'
            if term == 'finalterm':
                period = 'final'
            
            print(f"[GradeDataModel] Looking for: period='{period}', component='{component_name}'")
            
            # EXACT matching - only assessments that match BOTH:
            # 1. rubric_component_name matches component_name (case-insensitive)
            # 2. academic_period matches the period
            items = []
            comp_name_lower = component_name.lower().strip()
            
            for assessment in all_assessments:
                assessment_component = assessment.get('rubric_component_name', '').lower().strip()
                assessment_period = assessment.get('academic_period', '').lower().strip()
                
                print(f"[GradeDataModel]   Checking: '{assessment.get('title')}' - component='{assessment_component}', period='{assessment_period}'")
                
                # Handle 'finals' vs 'final' variations
                if assessment_period == 'finals':
                    assessment_period = 'final'
                
                # EXACT match required
                if assessment_component == comp_name_lower and assessment_period == period:
                    print(f"[GradeDataModel]   -> MATCH!")
                    items.append({
                        'name': assessment.get('title', 'Untitled'),
                        'max_score': assessment.get('max_points', 100),
                        'assessment_id': assessment.get('id')
                    })
                else:
                    print(f"[GradeDataModel]   -> No match ('{assessment_component}' vs '{comp_name_lower}', '{assessment_period}' vs '{period}')")
            
            if items:
                print(f"[GradeDataModel] Found {len(items)} assessments for component='{component_name}', period='{period}'")
                return items
            else:
                print(f"[GradeDataModel] No assessments for component='{component_name}', period='{period}'")
                
        except Exception as e:
            print(f"[GradeDataModel] Failed to get assessments: {e}")
            import traceback
            traceback.print_exc()
        
        # Return empty list - no assessments created yet
        return []
        
        # Return empty list - no assessments created yet
        return []

    def update_rubric_config(self, rubric_data):
        """Update rubric configuration from grading system dialog"""
        # Handle both 'final' and 'finals' keys from different sources
        midterm_data = rubric_data.get('midterm', {})
        final_data = rubric_data.get('final', rubric_data.get('finals', {}))
        
        self.rubric_config = {
            'midterm': {
                'term_percentage': midterm_data.get('term_percentage', 33),
                'components': {}
            },
            'final': {
                'term_percentage': final_data.get('term_percentage', 67),
                'components': {}
            }
        }
        
        for comp in midterm_data.get('components', []):
            comp_name = comp.get('name', '').lower()
            self.rubric_config['midterm']['components'][comp_name] = comp.get('percentage', 0)
        
        for comp in final_data.get('components', []):
            comp_name = comp.get('name', '').lower()
            self.rubric_config['final']['components'][comp_name] = comp.get('percentage', 0)
        
        self.component_type_mapping = {}
        all_component_names = set()
        for term_key in ['midterm', 'final']:
            for comp_name in self.rubric_config[term_key]['components'].keys():
                all_component_names.add(comp_name)
        
        for comp_name in all_component_names:
            if 'task' in comp_name or 'pt' in comp_name or 'performance' in comp_name:
                self.component_type_mapping[comp_name] = 'performance_tasks'
            elif 'quiz' in comp_name:
                self.component_type_mapping[comp_name] = 'quizzes'
            elif 'exam' in comp_name:
                self.component_type_mapping[comp_name] = 'exams'
            else:
                self.component_type_mapping[comp_name] = 'performance_tasks'
        
        self._initialize_component_states()
        self.columns_changed.emit()
        print(f"[GradeDataModel] Updated rubric config: {self.rubric_config}")

    def get_student_by_username(self, username):
        """Get student data by username"""
        for student in self.students:
            if student.get('username', '').lower() == username.lower():
                return student
        return None

    def get_student_by_id(self, student_id):
        """Get student data by ID"""
        for student in self.students:
            if str(student.get('id')) == str(student_id):
                return student
        return None

    def get_uploaded_grades_for_student(self, student_id):
        """Get only uploaded grades for a student (for student view)"""
        uploaded_grades = {}
        
        if student_id in self.grades:
            for component_key, grade_item in self.grades[student_id].items():
                if not grade_item.is_draft:
                    uploaded_grades[component_key] = grade_item
        
        return uploaded_grades

    def get_all_students(self):
        """Get list of all students"""
        return self.students.copy()

    def refresh_from_backend(self, api_url=None, token=None):
        """
        Refresh data from Django backend via Score API service.
        Loads grades from the database and updates local state.
        """
        if not self.use_score_api or not self.score_service:
            print("[GradeDataModel] Score API not available for refresh")
            return False
        
        try:
            # Get all scores for this class from the API
            all_scores = self.score_service.get_all_scores(self.class_id)
            
            if not all_scores:
                print("[GradeDataModel] No scores found in backend")
                return True
            
            # Map scores to local grades structure
            for score in all_scores:
                student_id = score.get('student_id')
                assessment_id = score.get('assessment_id')
                points = score.get('points', 0)
                max_points = score.get('max_points', 100)
                is_published = score.get('is_published', False)
                
                # Find student by django_id
                student = None
                for s in self.students:
                    if s.get('django_id') == student_id:
                        student = s
                        break
                
                if not student:
                    continue
                
                local_student_id = student.get('id')
                
                # Build component key from assessment info
                # This would need assessment data to build proper key
                component_key = f"assessment_{assessment_id}"
                
                if local_student_id not in self.grades:
                    self.grades[local_student_id] = {}
                
                grade_item = GradeItem()
                grade_item.value = f"{points}/{max_points}"
                grade_item.is_draft = not is_published
                self.grades[local_student_id][component_key] = grade_item
            
            print(f"[GradeDataModel] Refreshed {len(all_scores)} scores from backend")
            self.data_reset.emit()
            return True
            
        except Exception as e:
            print(f"[GradeDataModel] Failed to refresh from backend: {e}")
            return False

    def sync_grades_to_backend(self, api_url=None, token=None):
        """
        Sync all local grades to Django backend via Score API service.
        Pushes local changes to the database.
        """
        if not self.use_score_api or not self.score_service:
            print("[GradeDataModel] Score API not available for sync")
            return False
        
        try:
            # Collect all grades to sync
            scores_to_sync = []
            
            for student_id, student_grades in self.grades.items():
                student = self.get_student_by_id(student_id)
                if not student or not student.get('django_id'):
                    continue
                
                django_student_id = student.get('django_id')
                
                for component_key, grade_item in student_grades.items():
                    if not grade_item.value:
                        continue
                    
                    # Extract assessment_id from component_key if available
                    # This is a simplified version - in production, would need proper mapping
                    if 'assessment_' in component_key:
                        try:
                            assessment_id = int(component_key.replace('assessment_', ''))
                        except ValueError:
                            continue
                    else:
                        continue
                    
                    # Parse points from value
                    points = 0
                    if '/' in str(grade_item.value):
                        try:
                            points = float(str(grade_item.value).split('/')[0])
                        except ValueError:
                            continue
                    else:
                        try:
                            points = float(grade_item.value)
                        except ValueError:
                            continue
                    
                    scores_to_sync.append({
                        'student_id': django_student_id,
                        'assessment_id': assessment_id,
                        'points': points
                    })
            
            # Bulk sync to backend
            if scores_to_sync:
                success = self.score_service.bulk_create_scores(scores_to_sync, self.class_id)
                print(f"[GradeDataModel] Synced {len(scores_to_sync)} scores to backend: {'success' if success else 'failed'}")
                return success
            
            return True
            
        except Exception as e:
            print(f"[GradeDataModel] Failed to sync to backend: {e}")
            return False
