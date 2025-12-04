# frontend/model/grade_data_model.py
# MODIFIED FILE - Complete version with backend integration
from PyQt6.QtCore import QObject, pyqtSignal
from .grade_item import GradeItem
import sys
import os

# Add data directory to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from .data.grade_manager import GradeDataManager
except ImportError:
    print("Warning: Could not import GradeDataManager")
    GradeDataManager = None

# Import new backend services
try:
    from frontend.services.Academics.Classroom.enrollment_service import EnrollmentService
    from frontend.services.Academics.Classroom.grading_rubric_service import GradingRubricService
    from frontend.services.Academics.Classroom.assessment_service import AssessmentService
    from frontend.services.Academics.Classroom.score_service import ScoreService
except ImportError:
    try:
        # Try relative import
        services_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'services'))
        if services_path not in sys.path:
            sys.path.insert(0, services_path)
        from Academics.Classroom.enrollment_service import EnrollmentService
        from Academics.Classroom.grading_rubric_service import GradingRubricService
        from Academics.Classroom.assessment_service import AssessmentService
        from Academics.Classroom.score_service import ScoreService
    except ImportError:
        print("Warning: Could not import backend services")
        EnrollmentService = None
        GradingRubricService = None
        AssessmentService = None
        ScoreService = None

class GradeDataModel(QObject):
    """
    Main data model holding all application data.
    Single source of truth for students, grades, and rubric configuration.
    NOW WITH BACKEND INTEGRATION via enrollment, rubric, assessment, and score services.
    """
    data_reset = pyqtSignal()
    data_updated = pyqtSignal()
    columns_changed = pyqtSignal()

    def __init__(self, class_id=1):
        super().__init__()
        self.class_id = class_id
        self.students = []
        
        # Initialize grade manager (legacy)
        if GradeDataManager:
            self.grade_manager = GradeDataManager()
        else:
            self.grade_manager = None
        
        # Initialize new backend services
        self.enrollment_service = EnrollmentService() if EnrollmentService else None
        self.rubric_service = GradingRubricService() if GradingRubricService else None
        self.assessment_service = AssessmentService() if AssessmentService else None
        self.score_service = ScoreService() if ScoreService else None
        
        # Component types with sub-items (now loaded from assessments)
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
        
        # Load rubric from backend
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
        # Handle both midterm and finals
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

    def load_students_from_enrollment(self):
        """Load enrolled students from enrollment service"""
        if not self.enrollment_service:
            print("[GradeDataModel] No enrollment service available")
            return False
        
        try:
            enrolled = self.enrollment_service.get_enrolled_students(self.class_id)
            self.students = []
            
            for enrollment in enrolled:
                student = enrollment.get('student', {})
                self.students.append({
                    'id': str(student.get('institutional_id', student.get('id', ''))),
                    'name': f"{student.get('last_name', '')}, {student.get('first_name', '')}",
                    'username': student.get('username', ''),
                    'email': student.get('email', '')
                })
            
            # Initialize grades storage for each student
            for student in self.students:
                if student['id'] not in self.grades:
                    self.grades[student['id']] = {}
            
            # Load scores from backend
            self._load_scores_from_backend()
            
            print(f"[GradeDataModel] Loaded {len(self.students)} enrolled students")
            self.data_reset.emit()
            return True
        except Exception as e:
            print(f"[GradeDataModel] Failed to load enrolled students: {e}")
            return False

    def _load_scores_from_backend(self):
        """Load scores from score service"""
        if not self.score_service:
            return
        
        try:
            grade_matrix = self.score_service.get_class_grade_matrix(self.class_id)
            
            for student_id, scores in grade_matrix.items():
                student_id_str = str(student_id)
                if student_id_str not in self.grades:
                    self.grades[student_id_str] = {}
                
                for component_key, score_data in scores.items():
                    grade_item = GradeItem()
                    grade_item.value = str(score_data.get('score', ''))
                    grade_item.is_draft = not score_data.get('is_published', False)
                    self.grades[student_id_str][component_key] = grade_item
            
            print(f"[GradeDataModel] Loaded scores from backend")
        except Exception as e:
            print(f"[GradeDataModel] Failed to load scores: {e}")

    def load_students_from_classroom(self, students_data):
        """Load actual students from classroom data (legacy method)"""
        self.students = []
        for student in students_data:
            self.students.append({
                'id': str(student.get('institutional_id', student.get('id'))),
                'name': f"{student.get('last_name', '')}, {student.get('first_name', '')}",
                'username': student.get('username', '')
            })
        
        # Initialize grades storage for each student
        for student in self.students:
            if student['id'] not in self.grades:
                self.grades[student['id']] = {}
        
        # Load grades from persistent storage
        self._load_grades_from_storage()
        
        self.data_reset.emit()

    def _load_grades_from_storage(self):
        """Load grades from persistent storage (legacy grade manager)"""
        if not self.grade_manager:
            return
        
        class_grades = self.grade_manager.get_class_grades(self.class_id)
        
        for student_id, student_grades in class_grades.items():
            student_id_str = str(student_id)
            if student_id_str not in self.grades:
                self.grades[student_id_str] = {}
            
            for component_key, grade_data in student_grades.items():
                grade_item = GradeItem()
                grade_item.value = grade_data.get('value', '')
                grade_item.is_draft = grade_data.get('is_draft', True)
                self.grades[student_id_str][component_key] = grade_item

    def load_sample_data(self):
        """Load sample student data"""
        self.students = [
            {'id': '456456456', 'name': "Hitler, Adolf", 'username': 'Adolf'},
            {'id': '102', 'name': "Santos, Maria Elena", 'username': 'maria'},
            {'id': '103', 'name': "Garcia, Juan Pablo", 'username': 'juan'},
            {'id': '104', 'name': "Rodriguez, Ana Sofia", 'username': 'ana'}
        ]
        for student in self.students:
            self.grades[student['id']] = {}
        
        # Load grades from storage
        self._load_grades_from_storage()
        
        self.data_reset.emit()

    def get_column_state(self, key):
        """Get column expansion state"""
        return self.column_states.get(key, False)

    def set_column_state(self, key, value):
        """Set column expansion state"""
        if self.column_states.get(key) != value:
            self.column_states[key] = value
            self.columns_changed.emit()

    def set_grade(self, student_id, component_key, value, is_draft=True):
        """Set grade for a student's component"""
        student_id_str = str(student_id)
        if student_id_str not in self.grades:
            self.grades[student_id_str] = {}
        
        if component_key not in self.grades[student_id_str]:
            self.grades[student_id_str][component_key] = GradeItem()
        
        self.grades[student_id_str][component_key].value = value
        self.grades[student_id_str][component_key].is_draft = is_draft
        
        # Save to new score service (preferred)
        if self.score_service:
            try:
                # Parse component_key to extract assessment info
                self.score_service.save_score(
                    student_id=student_id_str,
                    assessment_id=None,  # Will be looked up by component_key
                    score=float(value) if value else 0,
                    component_key=component_key,
                    class_id=self.class_id,
                    is_published=not is_draft
                )
            except Exception as e:
                print(f"[GradeDataModel] Failed to save score to backend: {e}")
        
        # Also save to legacy grade manager for backwards compatibility
        if self.grade_manager:
            self.grade_manager.save_student_grade(
                student_id_str, self.class_id, component_key, value, is_draft
            )
        
        self.data_updated.emit()

    def get_grade(self, student_id, component_key):
        """Get grade item for a student's component"""
        student_id_str = str(student_id)
        if student_id_str in self.grades and component_key in self.grades[student_id_str]:
            return self.grades[student_id_str][component_key]
        return GradeItem()

    def bulk_set_grades(self, component_key, value):
        """Set grade value for all students in a component"""
        for student_id in self.grades.keys():
            self.set_grade(student_id, component_key, value, is_draft=True)

    def upload_grades(self, component_key):
        """Mark grades as uploaded (not draft) for a component - this publishes grades"""
        for student_id in self.grades.keys():
            if component_key in self.grades[student_id]:
                self.grades[student_id][component_key].is_draft = False
        
        # Publish in score service
        if self.score_service:
            try:
                self.score_service.publish_scores(self.class_id, component_key)
            except Exception as e:
                print(f"[GradeDataModel] Failed to publish scores: {e}")
        
        # Bulk upload in legacy storage
        if self.grade_manager:
            self.grade_manager.bulk_upload_grades(self.class_id, component_key)
        
        self.data_updated.emit()

    def get_assessments_for_component(self, component_name, term):
        """Get assessments linked to a specific rubric component"""
        if not self.assessment_service:
            return []
        
        try:
            grouped = self.assessment_service.get_assessments_grouped_by_component(self.class_id, term)
            return grouped.get(component_name.lower(), [])
        except Exception as e:
            print(f"[GradeDataModel] Failed to get assessments for component: {e}")
            return []

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
        if self.assessment_service and component_name:
            try:
                # Get all assessments for this class
                all_assessments = self.assessment_service.get_assessments_by_class(self.class_id)
                
                # Determine the academic period for matching
                period = 'midterm' if term == 'midterm' else 'final'
                if term == 'finalterm':
                    period = 'final'
                
                # EXACT matching - only assessments that match BOTH:
                # 1. rubric_component_name matches component_name (case-insensitive)
                # 2. academic_period matches the period
                items = []
                comp_name_lower = component_name.lower().strip()
                
                for assessment in all_assessments:
                    assessment_component = assessment.get('rubric_component_name', '').lower().strip()
                    assessment_period = assessment.get('academic_period', '').lower().strip()
                    
                    # Handle 'finals' vs 'final' variations
                    if assessment_period == 'finals':
                        assessment_period = 'final'
                    
                    # EXACT match required
                    if assessment_component == comp_name_lower and assessment_period == period:
                        items.append({
                            'name': assessment.get('title', 'Untitled'),
                            'max_score': assessment.get('max_points', 100),
                            'assessment_id': assessment.get('id')
                        })
                
                if items:
                    print(f"[GradeDataModel] Found {len(items)} assessments for component='{component_name}', period='{period}'")
                    return items
                else:
                    print(f"[GradeDataModel] No assessments found for component='{component_name}', period='{period}'")
                    
            except Exception as e:
                print(f"[GradeDataModel] Failed to get assessments: {e}")
        
        # Return empty list - no assessments created yet for this component/term
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

    def get_uploaded_grades_for_student(self, student_id):
        """Get only uploaded (published) grades for a student (for student view)"""
        uploaded_grades = {}
        student_id_str = str(student_id)
        
        if student_id_str in self.grades:
            for component_key, grade_item in self.grades[student_id_str].items():
                if not grade_item.is_draft:
                    uploaded_grades[component_key] = grade_item
        
        return uploaded_grades
    
    def refresh_data(self):
        """Refresh all data from backend services"""
        self._load_rubric_from_backend()
        self.load_students_from_enrollment()
        self.data_reset.emit()
    
    def set_class_id(self, class_id):
        """Update the class ID and reload data"""
        if self.class_id != class_id:
            self.class_id = class_id
            self.students = []
            self.grades = {}
            self._load_rubric_from_backend()
            self.load_students_from_enrollment()