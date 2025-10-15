from PyQt6.QtCore import QObject, pyqtSignal
from .component_item import ComponentItem
from .term_rubric import TermRubric

class GradingSystemModel(QObject):
    """Main model for the grading system"""
    data_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.midterm_rubric = TermRubric("Midterm", 33)
        self.final_rubric = TermRubric("Final", 67)
        self.load_default_rubrics()
    
    def load_default_rubrics(self):
        self.midterm_rubric.add_component(ComponentItem("Performance Task", 20))
        self.midterm_rubric.add_component(ComponentItem("Quiz", 30))
        self.midterm_rubric.add_component(ComponentItem("Exam", 50))
        
        self.final_rubric.add_component(ComponentItem("Performance Task", 20))
        self.final_rubric.add_component(ComponentItem("Quiz", 30))
        self.final_rubric.add_component(ComponentItem("Exam", 50))
    
    def get_rubric(self, term: str):
        if term.lower() == "midterm":
            return self.midterm_rubric
        elif term.lower() == "final":
            return self.final_rubric
        return None
    
    def validate_all(self):
        return (self.midterm_rubric.is_valid() and 
                self.final_rubric.is_valid())
    
    def to_dict(self):
        return {
            'midterm': self.midterm_rubric.to_dict(),
            'final': self.final_rubric.to_dict()
        }
