# enrollment_service.py
"""
Service for managing student enrollments in classes.
Handles which students are enrolled in which classes.
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional


class EnrollmentService:
    """
    Service for managing class enrollments.
    Links students to classes they are enrolled in.
    """
    
    def __init__(self, data_file: str = None, users_file: str = None):
        if data_file is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.data_file = os.path.join(base_dir, "data", "enrollments.json")
        else:
            self.data_file = data_file
        
        if users_file is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.users_file = os.path.join(base_dir, "data", "users_data.json")
        else:
            self.users_file = users_file
        
        self._ensure_data_file()
    
    def _ensure_data_file(self):
        """Ensure the data file exists with default structure"""
        if not os.path.exists(self.data_file):
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            # Default enrollment: Marcus is enrolled in class 1
            initial_data = {
                "enrollments": [
                    {
                        "id": 1,
                        "class_id": 1,
                        "student_id": "456456456",  # Marcus's institutional ID
                        "enrolled_at": datetime.now().isoformat(),
                        "enrolled_by": "admin"
                    }
                ],
                "last_id": 1,
                "last_updated": datetime.now().isoformat()
            }
            self._save_data(initial_data)
    
    def _load_data(self) -> Dict:
        """Load enrollments data from JSON file"""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"enrollments": [], "last_id": 0, "last_updated": datetime.now().isoformat()}
    
    def _save_data(self, data: Dict):
        """Save enrollments data to JSON file"""
        data["last_updated"] = datetime.now().isoformat()
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    def _load_users(self) -> List[Dict]:
        """Load users from users_data.json"""
        try:
            with open(self.users_file, 'r') as f:
                data = json.load(f)
                return data.get("users", [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def get_enrolled_students(self, class_id: int) -> List[Dict]:
        """
        Get all students enrolled in a class with their details.
        
        Returns:
            List of student dicts with full details:
            [{
                "id": "456456456",
                "name": "Mercer, Marcus",
                "username": "Marcus",
                "email": "immarcusmercer@gmail.com",
                "enrollment_id": 1,
                "enrolled_at": "..."
            }, ...]
        """
        data = self._load_data()
        users = self._load_users()
        
        # Get enrollments for this class
        class_enrollments = [e for e in data.get("enrollments", []) 
                           if e.get("class_id") == class_id]
        
        # Build student list with details
        students = []
        for enrollment in class_enrollments:
            student_id = enrollment.get("student_id")
            
            # Find user details
            user = next((u for u in users 
                        if str(u.get("institutional_id")) == str(student_id)), None)
            
            if user and user.get("role_type") == "student":
                students.append({
                    "id": str(user.get("institutional_id", user.get("id"))),
                    "name": f"{user.get('last_name', '')}, {user.get('first_name', '')}",
                    "username": user.get("username", ""),
                    "email": user.get("email", ""),
                    "enrollment_id": enrollment.get("id"),
                    "enrolled_at": enrollment.get("enrolled_at"),
                    "django_id": user.get("id")
                })
        
        return students
    
    def get_student_classes(self, student_id: str) -> List[int]:
        """Get all class IDs a student is enrolled in"""
        data = self._load_data()
        return [e.get("class_id") for e in data.get("enrollments", []) 
                if str(e.get("student_id")) == str(student_id)]
    
    def is_student_enrolled(self, class_id: int, student_id: str) -> bool:
        """Check if a student is enrolled in a class"""
        data = self._load_data()
        for enrollment in data.get("enrollments", []):
            if (enrollment.get("class_id") == class_id and 
                str(enrollment.get("student_id")) == str(student_id)):
                return True
        return False
    
    def enroll_student(self, class_id: int, student_id: str, 
                       enrolled_by: Optional[str] = None) -> Optional[Dict]:
        """
        Enroll a student in a class.
        
        Args:
            class_id: The class ID
            student_id: The student's institutional ID
            enrolled_by: Username of the person enrolling the student
        
        Returns:
            The enrollment dict or None if already enrolled
        """
        if self.is_student_enrolled(class_id, student_id):
            print(f"[ENROLLMENT SERVICE] Student {student_id} already enrolled in class {class_id}")
            return None
        
        try:
            data = self._load_data()
            
            new_id = data.get("last_id", 0) + 1
            data["last_id"] = new_id
            
            enrollment = {
                "id": new_id,
                "class_id": class_id,
                "student_id": student_id,
                "enrolled_at": datetime.now().isoformat(),
                "enrolled_by": enrolled_by
            }
            
            data["enrollments"].append(enrollment)
            self._save_data(data)
            
            print(f"[ENROLLMENT SERVICE] Enrolled student {student_id} in class {class_id}")
            return enrollment
            
        except Exception as e:
            print(f"[ENROLLMENT SERVICE] Error enrolling student: {e}")
            return None
    
    def unenroll_student(self, class_id: int, student_id: str) -> bool:
        """Remove a student from a class"""
        try:
            data = self._load_data()
            enrollments = data.get("enrollments", [])
            
            for i, enrollment in enumerate(enrollments):
                if (enrollment.get("class_id") == class_id and 
                    str(enrollment.get("student_id")) == str(student_id)):
                    del enrollments[i]
                    self._save_data(data)
                    print(f"[ENROLLMENT SERVICE] Unenrolled student {student_id} from class {class_id}")
                    return True
            
            return False
            
        except Exception as e:
            print(f"[ENROLLMENT SERVICE] Error unenrolling student: {e}")
            return False
    
    def bulk_enroll(self, class_id: int, student_ids: List[str], 
                    enrolled_by: Optional[str] = None) -> int:
        """
        Enroll multiple students in a class.
        
        Returns:
            Number of successfully enrolled students
        """
        count = 0
        for student_id in student_ids:
            if self.enroll_student(class_id, student_id, enrolled_by):
                count += 1
        return count
    
    def get_enrollment_count(self, class_id: int) -> int:
        """Get the number of students enrolled in a class"""
        data = self._load_data()
        return len([e for e in data.get("enrollments", []) 
                   if e.get("class_id") == class_id])
