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
from frontend.services.Academics.Classroom.grading_rubric_service import GradingRubricService  # noqa: E402


from PyQt6.QtCore import QObject, pyqtSignal # noqa: E402


class GradingSystemController(QObject):
    """Controller for grading system operations - now with backend integration"""
    validation_error = pyqtSignal(str)
    save_success = pyqtSignal()
    rubric_saved = pyqtSignal(dict)  # Emits saved rubric data
    
    def __init__(self, model: GradingSystemModel, class_id: int = None):
        super().__init__()
        self.model = model
        self.class_id = class_id
        self.rubric_service = GradingRubricService()
        
        # Load existing rubrics from backend if class_id is set
        if class_id:
            self.load_from_backend()
    
    def set_class_id(self, class_id: int):
        """Set the current class ID and load rubrics"""
        self.class_id = class_id
        self.load_from_backend()
    
    def load_from_backend(self):
        """Load rubrics from the backend service"""
        if not self.class_id:
            return
        
        rubrics = self.rubric_service.get_class_rubrics(self.class_id)
        if rubrics:
            # Load midterm rubric
            midterm_data = rubrics.get("midterm", {})
            self.model.midterm_rubric.term_percentage = midterm_data.get("term_percentage", 33)
            self.model.midterm_rubric.components = []
            for comp in midterm_data.get("components", []):
                self.model.midterm_rubric.add_component(
                    ComponentItem(comp["name"], comp["percentage"], comp.get("id"))
                )
            
            # Load finals rubric
            finals_data = rubrics.get("finals", {})
            self.model.final_rubric.term_percentage = finals_data.get("term_percentage", 67)
            self.model.final_rubric.components = []
            for comp in finals_data.get("components", []):
                self.model.final_rubric.add_component(
                    ComponentItem(comp["name"], comp["percentage"], comp.get("id"))
                )
            
            self.model.data_changed.emit()
            print(f"[GRADING CONTROLLER] Loaded rubrics for class {self.class_id}")
    
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
        """Validate rubrics and save to backend"""
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
        
        # Save to backend
        if self.class_id:
            rubrics_data = {
                "midterm": self.model.midterm_rubric.to_dict(),
                "finals": self.model.final_rubric.to_dict()
            }
            
            if self.rubric_service.create_or_update_rubrics(self.class_id, rubrics_data):
                print(f"[GRADING CONTROLLER] Saved rubrics for class {self.class_id}")
                self.rubric_saved.emit(rubrics_data)
                self.save_success.emit()
                return True
            else:
                self.validation_error.emit("Failed to save rubrics to backend")
                return False
        
        self.save_success.emit()
        return True
    
    def get_rubric_components_for_dropdown(self):
        """
        Get all rubric components formatted for dropdown menus.
        Used in assessment creation form.
        
        Returns:
            List of dicts with id, name, academic_period, percentage
        """
        if not self.class_id:
            return []
        
        return self.rubric_service.get_all_components(self.class_id)