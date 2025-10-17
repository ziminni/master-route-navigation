from PyQt6.QtCore import QObject, pyqtSignal
import os
import sys

# Navigate 5 levels up to get to the project's root directory (MAIN_MODULE2)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


# Add the project root to the system path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# The comment below tells the linter to ignore the "E402: module level import not at top of file" warning.
# We are doing this intentionally and correctly here.
from frontend.services.Academics.model.Academics.Classroom.grade_data_model import GradeDataModel      # noqa: E402


class GradeController(QObject):
    """Controller for grade operations and calculations"""
    data_changed = pyqtSignal()
    columns_changed = pyqtSignal()

    def __init__(self, model: GradeDataModel):
        super().__init__()
        self.model = model
        self.model.data_reset.connect(self.data_changed.emit)
        self.model.data_updated.connect(self.data_changed.emit)
        self.model.columns_changed.connect(self.columns_changed.emit)

    def handle_header_expand_clicked(self, column_info):
        """Handle expansion/collapse of header columns"""
        col_type = column_info.get('type')
        target = column_info.get('target')
        term = column_info.get('term')
        component = column_info.get('component')

        key = None
        if col_type == 'expandable_main':
            if target == 'midterm':
                key = 'midterm_expanded'
            elif target == 'finalterm':
                key = 'finalterm_expanded'
        elif col_type == 'expandable_component':
            if component and term:
                key = f'{component}_{term}_expanded'

        if key:
            current_state = self.model.get_column_state(key)
            self.model.set_column_state(key, not current_state)

    def calculate_component_average(self, student_id, component_name, term):
        """Calculate average for a specific component (e.g., Performance Task)"""
        type_key = self.model.get_component_type_key(component_name, term)
        sub_components = self.model.components.get(type_key, [])
        
        total_score = 0
        total_max = 0
        count = 0
        
        for sub_comp in sub_components:
            component_key = f"{sub_comp.lower().replace(' ', '')}_{term}"
            grade_item = self.model.get_grade(student_id, component_key)
            
            if not grade_item.value:
                continue
            
            # Parse the score
            if '/' in grade_item.value:
                parts = grade_item.value.split('/')
                try:
                    score = float(parts[0])
                    max_score = float(parts[1])
                    total_score += score
                    total_max += max_score
                    count += 1
                except (ValueError, IndexError):
                    continue
        
        if count > 0 and total_max > 0:
            return f"{total_score:.1f}/{total_max:.1f}"
        return ""

    def calculate_grades_for_student(self, student_id):
        """Calculate weighted grades for a student"""
        midterm_component_scores = {}
        finalterm_component_scores = {}
        
        # Calculate average for each component type in each term
        for term in ['midterm', 'finalterm']:
            term_key = 'midterm' if term == 'midterm' else 'final'
            component_scores = midterm_component_scores if term == 'midterm' else finalterm_component_scores
            
            for comp_name in self.model.rubric_config[term_key]['components'].keys():
                type_key = self.model.get_component_type_key(comp_name, term)
                sub_components = self.model.components.get(type_key, [])
                
                total_score = 0
                count = 0
                
                for sub_comp in sub_components:
                    component_key = f"{sub_comp.lower().replace(' ', '')}_{term}"
                    grade_item = self.model.get_grade(student_id, component_key)
                    
                    if not grade_item.value:
                        continue
                    
                    grade = grade_item.get_numeric_score()
                    total_score += grade
                    count += 1
                
                if count > 0:
                    component_scores[comp_name] = total_score / count
                else:
                    component_scores[comp_name] = 0
        
        # Calculate weighted averages
        midterm_weighted_total = 0
        for comp_name, avg_score in midterm_component_scores.items():
            comp_percentage = self.model.get_component_percentage(comp_name, 'midterm')
            midterm_weighted_total += avg_score * (comp_percentage / 100)
        
        finalterm_weighted_total = 0
        for comp_name, avg_score in finalterm_component_scores.items():
            comp_percentage = self.model.get_component_percentage(comp_name, 'final')
            finalterm_weighted_total += avg_score * (comp_percentage / 100)
        
        # Calculate final grade using term percentages
        midterm_term_pct = self.model.rubric_config['midterm']['term_percentage'] / 100
        final_term_pct = self.model.rubric_config['final']['term_percentage'] / 100
        
        final_grade = (midterm_weighted_total * midterm_term_pct) + (finalterm_weighted_total * final_term_pct)
        
        return {
            'midterm_avg': f"{midterm_weighted_total:.2f}",
            'finalterm_avg': f"{finalterm_weighted_total:.2f}",
            'final_grade': f"{final_grade:.2f}"
        }