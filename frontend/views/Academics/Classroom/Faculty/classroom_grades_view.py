"""
Faculty Grades View - Full grade management interface
Features: bulk input, draft/upload status, expandable columns, grading system management
UPDATED: Now connected to actual users and persistent storage
"""
import os
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
    QLabel, QPushButton, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from frontend.services.Academics.model.Academics.Classroom.grade_data_model import GradeDataModel      # noqa: E402
from frontend.controller.Academics.Classroom.grade_controller import GradeController  # noqa: E402

# Import local modules
try:
    from frontend.services.Academics.model.Academics.Classroom.grade_data_model import GradeDataModel
    from frontend.controller.Academics.Classroom.grade_controller import GradeController
    from frontend.views.Academics.Classroom.Faculty.table_model import EnhancedGradesTableView
except ImportError:
    # Fallback for development
    from frontend.services.Academics.model import GradeDataModel
    from .....controller.Academics.Classroom.grade_controller import GradeController
    from .table_model import EnhancedGradesTableView

# Import grading dialog if available
try:
    from frontend.views.Academics.Classroom.Faculty.grading_system_dialog import connect_grading_button
except ImportError:
    def connect_grading_button(window, label):
        label.setEnabled(False)
        print("Warning: grading_system_dialog.py not found")

class FacultyGradesView(QWidget):
    
    def __init__(self, cls, username, roles, primary_role, token, parent=None):
        super().__init__(parent)
        
        self.cls = cls
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token

        self.setMinimumSize(940, 530)
        
        # Initialize models and controllers with class ID
        class_id = cls.get('id', 1)
        self.grade_model = GradeDataModel(class_id=class_id)
        self.grade_controller = GradeController(self.grade_model)
        
        # Set current user context
        self.grade_model.set_current_user(username, {'roles': roles, 'primary_role': primary_role})
        
        # Setup UI
        self.setup_ui()
        
        # Connect signals
        self.grade_controller.columns_changed.connect(self.rebuild_table)
        
        # Load data with flexible loading strategy
        self.load_students_data()
        self.rebuild_table()
    
    def load_students_data(self):
        """
        Flexible student loading with multiple strategies:
        1. Try Django API (if available)
        2. Try JSON file (development/fallback)
        3. Use sample data (ultimate fallback)
        """
        print(f"[FACULTY GRADES] Starting flexible data load for class {self.cls.get('id')}")
        
        # Strategy 1: Try Django API (future implementation)
        if self.token and self._try_load_from_api():
            print("[FACULTY GRADES] Successfully loaded from Django API")
            return
        
        # Strategy 2: Try JSON file
        if self._try_load_from_json():
            print("[FACULTY GRADES] Successfully loaded from JSON file")
            return
        
        # Strategy 3: Sample data (ultimate fallback)
        print("[FACULTY GRADES] Using sample data (fallback)")
        self.grade_model.load_sample_data()
        
        # Log loaded students
        print(f"[FACULTY GRADES] Loaded {len(self.grade_model.students)} students:")
        for student in self.grade_model.students:
            print(f"  - {student['name']} (ID: {student['id']}, Username: {student.get('username', 'N/A')})")
    
    def _try_load_from_api(self):
        """Try to load students from Django API"""
        # TODO: Implement when Django backend is ready
        # Example:
        # try:
        #     import requests
        #     headers = {'Authorization': f'Bearer {self.token}'}
        #     response = requests.get(
        #         f'http://127.0.0.1:8000/api/classes/{self.cls.get("id")}/students/',
        #         headers=headers,
        #         timeout=5
        #     )
        #     if response.status_code == 200:
        #         self.grade_model.load_students_from_django_api(response.json())
        #         return True
        # except Exception as e:
        #     print(f"[FACULTY GRADES] API load failed: {e}")
        return False
    
    def _try_load_from_json(self):
        """Try to load students from JSON file"""
        try:
            # Try multiple possible JSON file locations
            json_paths = [
                'data/users_data.json',
                '../data/users_data.json',
                '../../data/users_data.json',
                os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'data', 'users_data.json')
            ]
            
            for json_path in json_paths:
                if os.path.exists(json_path):
                    print(f"[FACULTY GRADES] Found JSON file at: {json_path}")
                    self.grade_model.load_students_from_json(json_path)
                    return True
            
            print("[FACULTY GRADES] No JSON file found in expected locations")
            return False
            
        except Exception as e:
            print(f"[FACULTY GRADES] JSON load failed: {e}")
            return False
    
    def setup_ui(self):
        """Setup the faculty interface"""
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor("white"))
        self.setPalette(pal)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        header_layout = self._create_header()
        
        self.grades_table = EnhancedGradesTableView(
            self.grade_model,
            self.grade_controller
        )
        
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.grades_table)
        
        self.setLayout(main_layout)
    
    def _create_header(self):
        """Create header with faculty controls"""
        header_layout = QHBoxLayout()
        
        self.rubrics_combo = QComboBox()
        self.rubrics_combo.addItems(["Overall Lecture", "Performance Task", "Quiz", "Exam"])
        self.rubrics_combo.setFixedWidth(150)
        self.rubrics_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #E0E0E0;
                border-radius: 5px;
                font-size: 12px;
                color: #084924;
                background-color: white;
                font-weight: bold;
            }
            QComboBox:focus {
                border: 2px solid #084924;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: #084924;
                selection-background-color: #E8F5E8;
            }
        """)
        
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        self.grading_label = QLabel("Grading System")
        self.grading_label.setStyleSheet("""
            QLabel {
                background-color: #FDC601;
                color: white;
                border-radius: 3px;
                padding: 8px 12px;
                font-weight: bold;
                font-size: 12px;
            }
            QLabel:hover {
                background-color: #E5B200;
            }
        """)
        self.grading_label.setCursor(Qt.CursorShape.PointingHandCursor)
        connect_grading_button(self, self.grading_label)
        
        download_button = QPushButton("📥 Download")
        download_button.setStyleSheet("""
            QPushButton {
                background-color: #084924;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0A5A2A;
            }
        """)
        
        header_layout.addWidget(self.rubrics_combo)
        header_layout.addItem(spacer)
        header_layout.addWidget(self.grading_label)
        header_layout.addWidget(download_button)
        
        return header_layout
    
    def rebuild_table(self):
        """Rebuild table structure"""
        columns_info = self._build_columns_info()
        self.grades_table.load_data(columns_info)
    
    def _build_columns_info(self):
        """Build column information"""
        columns = [
            {'name': 'No.', 'type': 'fixed', 'width': 60},
            {'name': 'Sort by Last Name', 'type': 'fixed', 'width': 220}
        ]
        
        # MIDTERM SECTION
        columns.append({
            'name': 'Midterm Grade',
            'type': 'expandable_main',
            'width': 140,
            'target': 'midterm'
        })
        
        if self.grade_model.get_column_state('midterm_expanded'):
            for comp_name in self.grade_model.get_rubric_components('midterm'):
                comp_key = comp_name.replace(' ', '_')
                comp_display_name = comp_name.title()
                
                columns.append({
                    'name': comp_display_name,
                    'type': 'expandable_component',
                    'width': 150,
                    'term': 'midterm',
                    'component': comp_key
                })
                
                state_key = f'{comp_key}_midterm_expanded'
                if self.grade_model.get_column_state(state_key):
                    type_key = self.grade_model.get_component_type_key(comp_name, 'midterm')
                    sub_items = self.grade_model.get_component_items_with_scores(type_key)
                    
                    for item in sub_items:
                        item_name = item['name']
                        max_score = item['max_score']
                        columns.append({
                            'name': f'{item_name} (M)',
                            'type': 'grade_input',
                            'width': 130,
                            'term': 'midterm',
                            'component': comp_key,
                            'component_key': f"{item_name.lower().replace(' ', '')}_midterm",
                            'max_score': max_score
                        })
        
        # FINAL TERM SECTION
        columns.append({
            'name': 'Final Term Grade',
            'type': 'expandable_main',
            'width': 150,
            'target': 'finalterm'
        })
        
        if self.grade_model.get_column_state('finalterm_expanded'):
            for comp_name in self.grade_model.get_rubric_components('final'):
                comp_key = comp_name.replace(' ', '_')
                comp_display_name = comp_name.title()
                
                columns.append({
                    'name': comp_display_name,
                    'type': 'expandable_component',
                    'width': 150,
                    'term': 'finalterm',
                    'component': comp_key
                })
                
                state_key = f'{comp_key}_finalterm_expanded'
                if self.grade_model.get_column_state(state_key):
                    type_key = self.grade_model.get_component_type_key(comp_name, 'finalterm')
                    sub_items = self.grade_model.get_component_items_with_scores(type_key)
                    
                    for item in sub_items:
                        item_name = item['name']
                        max_score = item['max_score']
                        columns.append({
                            'name': f'{item_name} (F)',
                            'type': 'grade_input',
                            'width': 130,
                            'term': 'finalterm',
                            'component': comp_key,
                            'component_key': f"{item_name.lower().replace(' ', '')}_finalterm",
                            'max_score': max_score
                        })
        
        # FINAL GRADE
        columns.append({
            'name': 'Final Grade',
            'type': 'calculated',
            'width': 110
        })
        
        return columns
    
    def clear(self):
        """Clear the view"""
        pass


# Test runner
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication, QMainWindow
    
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setWindowTitle("Faculty Grades View Test")
    window.setGeometry(100, 100, 1000, 700)
    
    mock_cls = {
        'id': 1,
        'name': 'Desktop Application Development',
        'section': 'BSCS-3C'
    }
    
    widget = FacultyGradesView(
        cls=mock_cls,
        username='admin',
        roles=['faculty'],
        primary_role='faculty',
        token='test_token'
    )
    
    window.setCentralWidget(widget)
    window.show()
    
    sys.exit(app.exec())