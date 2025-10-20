# data/grade_manager.py
"""
Grade data manager for persistent storage of grades
Handles reading/writing grades to JSON file
"""
import json
import os
from datetime import datetime

class GradeDataManager:
    def __init__(self, data_file='services/Academics/data/grades_data.json'):
        self.data_file = data_file
        self.ensure_data_file()
    
    def ensure_data_file(self):
        """Ensure grades data file exists"""
        if not os.path.exists(self.data_file):
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            initial_data = {
                "grades": {},
                "last_updated": datetime.now().isoformat()
            }
            with open(self.data_file, 'w') as f:
                json.dump(initial_data, f, indent=4)
    
    def load_grades(self):
        """Load all grades from file"""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                return data.get('grades', {})
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_grades(self, grades_data):
        """Save all grades to file"""
        data = {
            "grades": grades_data,
            "last_updated": datetime.now().isoformat()
        }
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    def get_student_grades(self, student_id, class_id):
        """Get grades for a specific student in a class"""
        all_grades = self.load_grades()
        class_key = f"class_{class_id}"
        
        if class_key in all_grades and student_id in all_grades[class_key]:
            return all_grades[class_key][student_id]
        return {}
    
    def save_student_grade(self, student_id, class_id, component_key, value, is_draft=True):
        """Save a single grade for a student"""
        all_grades = self.load_grades()
        class_key = f"class_{class_id}"
        
        if class_key not in all_grades:
            all_grades[class_key] = {}
        
        if student_id not in all_grades[class_key]:
            all_grades[class_key][student_id] = {}
        
        all_grades[class_key][student_id][component_key] = {
            'value': value,
            'is_draft': is_draft,
            'updated_at': datetime.now().isoformat()
        }
        
        self.save_grades(all_grades)
    
    def get_class_grades(self, class_id):
        """Get all grades for a class"""
        all_grades = self.load_grades()
        class_key = f"class_{class_id}"
        return all_grades.get(class_key, {})
    
    def save_class_grades(self, class_id, class_grades):
        """Save all grades for a class"""
        all_grades = self.load_grades()
        class_key = f"class_{class_id}"
        all_grades[class_key] = class_grades
        self.save_grades(all_grades)
    
    def bulk_upload_grades(self, class_id, component_key):
        """Mark all grades for a component as uploaded"""
        all_grades = self.load_grades()
        class_key = f"class_{class_id}"
        
        if class_key in all_grades:
            for student_id in all_grades[class_key]:
                if component_key in all_grades[class_key][student_id]:
                    all_grades[class_key][student_id][component_key]['is_draft'] = False
                    all_grades[class_key][student_id][component_key]['updated_at'] = datetime.now().isoformat()
        
        self.save_grades(all_grades)
    
    def get_uploaded_grades_for_student(self, student_id, class_id):
        """Get only uploaded (non-draft) grades for a student"""
        all_grades = self.get_student_grades(student_id, class_id)
        uploaded_grades = {}
        
        for component_key, grade_data in all_grades.items():
            if not grade_data.get('is_draft', True):
                uploaded_grades[component_key] = grade_data
        
        return uploaded_grades