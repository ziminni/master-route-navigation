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

class GradeDataModel(QObject):
    """
    Main data model holding all application data.
    FLEXIBLE: Adapts to any users from Django backend or JSON files
    FUTURE-READY: Prepared for PostgreSQL integration
    """
    data_reset = pyqtSignal()
    data_updated = pyqtSignal()
    columns_changed = pyqtSignal()

    def __init__(self, class_id=1):
        super().__init__()
        self.class_id = class_id
        self.students = []
        self.current_user = None  # Store current logged-in user
        
        # Initialize grade manager
        if GradeDataManager:
            self.grade_manager = GradeDataManager()
        else:
            self.grade_manager = None
        
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
        
        # Rubric configuration
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

    def _initialize_component_states(self):
        """Initialize column states for all component types"""
        for term in ['midterm', 'finalterm']:
            term_key = 'midterm' if term == 'midterm' else 'final'
            for comp_name in self.rubric_config[term_key]['components'].keys():
                comp_key = comp_name.replace(' ', '_')
                state_key = f'{comp_key}_{term}_expanded'
                if state_key not in self.column_states:
                    self.column_states[state_key] = False

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

    def set_grade(self, student_id, component_key, value, is_draft=True):
        """Set grade for a student's component"""
        if student_id not in self.grades:
            self.grades[student_id] = {}
        
        if component_key not in self.grades[student_id]:
            self.grades[student_id][component_key] = GradeItem()
        
        self.grades[student_id][component_key].value = value
        self.grades[student_id][component_key].is_draft = is_draft
        
        # Save to persistent storage
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

    def get_component_items_with_scores(self, type_key):
        """Get list of component items with their max scores"""
        items = self.components.get(type_key, [])
        max_score = self.component_max_scores.get(type_key, 40)
        
        return [{'name': item, 'max_score': max_score} for item in items]

    def update_rubric_config(self, rubric_data):
        """Update rubric configuration from grading system dialog"""
        self.rubric_config = {
            'midterm': {
                'term_percentage': rubric_data['midterm']['term_percentage'],
                'components': {}
            },
            'final': {
                'term_percentage': rubric_data['final']['term_percentage'],
                'components': {}
            }
        }
        
        for comp in rubric_data['midterm']['components']:
            comp_name = comp['name'].lower()
            self.rubric_config['midterm']['components'][comp_name] = comp['percentage']
        
        for comp in rubric_data['final']['components']:
            comp_name = comp['name'].lower()
            self.rubric_config['final']['components'][comp_name] = comp['percentage']
        
        self.component_type_mapping = {}
        all_component_names = set()
        for term_key in ['midterm', 'final']:
            for comp in rubric_data[term_key]['components']:
                comp_name = comp['name'].lower()
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

    def refresh_from_backend(self, api_url, token):
        """
        Future method: Refresh data from Django backend
        This will be called when integrated with PostgreSQL
        """
        # TODO: Implement API call to Django backend
        # Example structure:
        # headers = {'Authorization': f'Bearer {token}'}
        # response = requests.get(f'{api_url}/api/grades/class/{self.class_id}/students/', headers=headers)
        # if response.status_code == 200:
        #     self.load_students_from_django_api(response.json())
        pass

    def sync_grades_to_backend(self, api_url, token):
        """
        Future method: Sync grades to Django backend
        This will be called when integrated with PostgreSQL
        """
        # TODO: Implement API call to Django backend
        # Example structure:
        # headers = {'Authorization': f'Bearer {token}'}
        # payload = {'grades': self.grades}
        # response = requests.post(f'{api_url}/api/grades/class/{self.class_id}/sync/', 
        #                         json=payload, headers=headers)
        pass
