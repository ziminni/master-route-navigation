import os
import sys

# Navigate 5 levels up to get to the project's root directory (MAIN_MODULE2)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


# Add the project root to the system path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# The comment below tells the linter to ignore the "E402: module level import not at top of file" warning.
# We are doing this intentionally and correctly here.
from frontend.services.Academics.model.Academics.Classroom.grading_system_model import GradingSystemModel      # noqa: E402
from frontend.services.Academics.model.Academics.Classroom.component_item import ComponentItem # noqa: E402


from PyQt6.QtCore import QObject, pyqtSignal # noqa: E402


class GradingSystemController(QObject):
    """Controller for grading system operations"""
    validation_error = pyqtSignal(str)
    save_success = pyqtSignal()
    
    def __init__(self, model: GradingSystemModel):
        super().__init__()
        self.model = model
    
    def add_component(self, term: str, name: str, percentage: int):
        rubric = self.model.get_rubric(term)
        if rubric:
            rubric.add_component(ComponentItem(name, percentage))
            self.model.data_changed.emit()
            return True
        return False
    
    def remove_component(self, term: str, index: int):
        rubric = self.model.get_rubric(term)
        if rubric:
            rubric.remove_component(index)
            self.model.data_changed.emit()
            return True
        return False
    
    def update_component(self, term: str, index: int, name: str, percentage: int):
        rubric = self.model.get_rubric(term)
        if rubric:
            rubric.update_component(index, name, percentage)
            self.model.data_changed.emit()
            return True
        return False
    
    def validate_and_save(self):
        if not self.model.validate_all():
            errors = []
            if not self.model.midterm_rubric.is_valid():
                total = self.model.midterm_rubric.get_total_percentage()
                errors.append(f"Midterm components total {total}% (must be 100%)")
            if not self.model.final_rubric.is_valid():
                total = self.model.final_rubric.get_total_percentage()
                errors.append(f"Final components total {total}% (must be 100%)")
            
            self.validation_error.emit("\n".join(errors))
            return False
        
        self.save_success.emit()
        return True