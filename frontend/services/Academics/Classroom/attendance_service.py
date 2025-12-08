# attendance_service.py
import json
import os
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path


class AttendanceService:
    """Service layer for attendance data operations"""
    
    def __init__(self, data_file_path: str = None):
        if data_file_path:
            self.data_file = data_file_path
        else:
            # Try multiple possible paths for the data file
            possible_paths = [
                # Relative to project structure
                Path(__file__).parent.parent.parent.parent / "services" / "Academics" / "data" / "attendance_data.json",
                Path(__file__).parent.parent.parent.parent / "data" / "attendance_data.json",
                # Fallback to current directory
                Path("attendance_data.json")
            ]
            
            for path in possible_paths:
                if path.parent.exists():
                    self.data_file = str(path)
                    break
            else:
                # Create in current directory if none found
                self.data_file = "attendance_data.json"
        
        # Ensure directory exists
        os.makedirs(Path(self.data_file).parent, exist_ok=True)
    
    def _load_data(self) -> Dict:
        """Load attendance data from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading attendance data: {e}")
        
        # Return default structure
        return {
            "classes": {},
            "students": {},
            "attendance_records": {},
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            }
        }
    
    def _save_data(self, data: Dict) -> bool:
        """Save attendance data to file"""
        try:
            # Update metadata
            data["metadata"]["last_updated"] = datetime.now().isoformat()
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except (IOError, TypeError) as e:
            print(f"Error saving attendance data: {e}")
            return False
    
    # ========== Class Management ==========
    
    def get_class(self, class_id: int) -> Optional[Dict]:
        """Get class information by ID"""
        data = self._load_data()
        return data.get("classes", {}).get(str(class_id))
    
    def save_class(self, class_id: int, class_data: Dict) -> bool:
        """Save or update class information"""
        data = self._load_data()
        
        # Ensure classes dict exists
        if "classes" not in data:
            data["classes"] = {}
        
        # Update class data
        data["classes"][str(class_id)] = {
            **class_data,
            "id": class_id,
            "updated_at": datetime.now().isoformat()
        }
        
        return self._save_data(data)
    
    # ========== Student Management ==========
    
    def get_students_for_class(self, class_id: int) -> List[Dict]:
        """Get all students enrolled in a class"""
        data = self._load_data()
        
        # Check if we have class-specific students
        class_data = data.get("classes", {}).get(str(class_id), {})
        if "students" in class_data:
            return class_data["students"]
        
        # Check global students registry
        class_students = []
        all_students = data.get("students", {})
        
        for student_id, student_data in all_students.items():
            if student_data.get("class_id") == class_id:
                class_students.append({
                    "id": int(student_id),
                    "name": student_data.get("name", ""),
                    "student_code": student_data.get("student_code", ""),
                    "email": student_data.get("email", ""),
                    "enrollment_date": student_data.get("enrollment_date", "")
                })
        
        # If no students found, try to get from classroom service
        if not class_students:
            class_students = self._get_students_from_classroom_service(class_id)
            
            # Save these students for future use
            if class_students:
                self._save_students_for_class(class_id, class_students)
        
        return class_students
    
    def _get_students_from_classroom_service(self, class_id: int) -> List[Dict]:
        """Try to get students from the classroom service"""
        try:
            from frontend.services.Academics.Classroom.classroom_service import ClassroomService
            classroom_service = ClassroomService()
            classroom_data = classroom_service.load_classes()
            
            for class_data in classroom_data:
                if class_data.get("id") == class_id:
                    students = class_data.get("students", [])
                    # Format students consistently
                    formatted_students = []
                    for i, student in enumerate(students):
                        if isinstance(student, dict):
                            formatted_students.append({
                                "id": student.get("id", i + 1),
                                "name": student.get("name", f"Student {i + 1}"),
                                "student_code": student.get("student_code", f"S{i+1:03d}"),
                                "email": student.get("email", ""),
                                "enrollment_date": student.get("enrollment_date", "")
                            })
                        else:
                            # If student is just a name string
                            formatted_students.append({
                                "id": i + 1,
                                "name": str(student),
                                "student_code": f"S{i+1:03d}",
                                "email": "",
                                "enrollment_date": ""
                            })
                    return formatted_students
        except ImportError:
            print("ClassroomService not available, using sample data")
        
        # Fallback to sample data
        sample_names = [
            "Castro, Carlos Fidel", "Dela Cruz, Maria Santos", "Reyes, Juan Pablo",
            "Santos, Ana Marie", "Garcia, Jose Miguel", "Tan, Michael Johnson",
            "Lim, Samantha Rose", "Nguyen, Andrew Kim", "Smith, Jennifer Lynn",
            "Johnson, Robert James"
        ]
        
        return [
            {
                "id": i + 1,
                "name": name,
                "student_code": f"S{i+1:03d}",
                "email": f"student{i+1}@example.com",
                "enrollment_date": "2024-09-01"
            }
            for i, name in enumerate(sample_names)
        ]
    
    def _save_students_for_class(self, class_id: int, students: List[Dict]) -> bool:
        """Save students for a class"""
        data = self._load_data()
        
        # Ensure structure exists
        if "classes" not in data:
            data["classes"] = {}
        
        if str(class_id) not in data["classes"]:
            data["classes"][str(class_id)] = {}
        
        # Save students in class data
        data["classes"][str(class_id)]["students"] = students
        
        # Also update global students registry
        if "students" not in data:
            data["students"] = {}
        
        for student in students:
            student_id = student["id"]
            data["students"][str(student_id)] = {
                **student,
                "class_id": class_id,
                "updated_at": datetime.now().isoformat()
            }
        
        return self._save_data(data)
    
    def add_student_to_class(self, class_id: int, student_data: Dict) -> bool:
        """Add a new student to a class"""
        data = self._load_data()
        
        # Get current students
        current_students = self.get_students_for_class(class_id)
        
        # Generate new student ID
        new_id = max([s["id"] for s in current_students], default=0) + 1
        
        # Create student record
        student = {
            "id": new_id,
            "name": student_data.get("name", f"Student {new_id}"),
            "student_code": student_data.get("student_code", f"S{new_id:03d}"),
            "email": student_data.get("email", ""),
            "enrollment_date": datetime.now().date().isoformat()
        }
        
        # Add to current students
        current_students.append(student)
        
        # Save updated list
        return self._save_students_for_class(class_id, current_students)
    
    # ========== Attendance Records ==========
    
    def get_attendance_for_date(self, class_id: int, date: str) -> Dict[str, Dict]:
        """Get attendance records for a specific class and date"""
        data = self._load_data()
        
        attendance_records = data.get("attendance_records", {})
        class_records = attendance_records.get(str(class_id), {})
        
        return class_records.get(date, {})
    
    def save_attendance_for_date(self, class_id: int, date: str, 
                               attendance_data: List[Dict]) -> bool:
        """Save attendance records for a specific date"""
        data = self._load_data()
        
        # Initialize structures if they don't exist
        if "attendance_records" not in data:
            data["attendance_records"] = {}
        
        if str(class_id) not in data["attendance_records"]:
            data["attendance_records"][str(class_id)] = {}
        
        # Convert attendance data to dict format
        date_records = {}
        for record in attendance_data:
            student_id = str(record.get("student_id"))
            student_name = record.get("student_name", "")
            is_present = record.get("is_present", False)
            
            date_records[student_id] = {
                "is_present": is_present,
                "student_name": student_name,
                "timestamp": datetime.now().isoformat(),
                "class_id": class_id,
                "date": date
            }
        
        # Save the records
        data["attendance_records"][str(class_id)][date] = date_records
        
        return self._save_data(data)
    
    def get_attendance_history(self, class_id: int, 
                             start_date: Optional[str] = None,
                             end_date: Optional[str] = None) -> List[Dict]:
        """Get attendance history for a class within date range"""
        data = self._load_data()
        attendance_records = data.get("attendance_records", {})
        class_records = attendance_records.get(str(class_id), {})
        
        history = []
        for date, records in sorted(class_records.items()):
            # Filter by date range if specified
            if start_date and date < start_date:
                continue
            if end_date and date > end_date:
                continue
            
            # Calculate summary for this date
            present_count = sum(1 for r in records.values() if r.get("is_present", False))
            absent_count = len(records) - present_count
            attendance_rate = (present_count / len(records) * 100) if records else 0
            
            history.append({
                "date": date,
                "total_students": len(records),
                "present_count": present_count,
                "absent_count": absent_count,
                "attendance_rate": round(attendance_rate, 1)
            })
        
        return history
    
    def get_student_attendance_history(self, class_id: int, student_id: int) -> List[Dict]:
        """Get attendance history for a specific student"""
        data = self._load_data()
        attendance_records = data.get("attendance_records", {})
        class_records = attendance_records.get(str(class_id), {})
        
        history = []
        for date, records in sorted(class_records.items()):
            student_record = records.get(str(student_id))
            if student_record:
                history.append({
                    "date": date,
                    "is_present": student_record.get("is_present", False),
                    "timestamp": student_record.get("timestamp")
                })
        
        return history
    
    # ========== Statistics and Reports ==========
    
    def get_attendance_stats(self, class_id: int) -> Dict:
        """Get attendance statistics for a class"""
        # Get all attendance records for this class
        history = self.get_attendance_history(class_id)
        
        if not history:
            return {
                "total_students": 0,
                "total_days": 0,
                "average_attendance": 0,
                "perfect_attendance_count": 0
            }
        
        # Get student count
        students = self.get_students_for_class(class_id)
        total_students = len(students)
        
        # Calculate overall statistics
        total_days = len(history)
        total_possible_attendance = total_days * total_students
        
        if total_possible_attendance == 0:
            return {
                "total_students": total_students,
                "total_days": total_days,
                "average_attendance": 0,
                "perfect_attendance_count": 0
            }
        
        total_present = sum(day["present_count"] for day in history)
        overall_attendance_rate = (total_present / total_possible_attendance) * 100
        
        # Count students with perfect attendance
        perfect_attendance_count = 0
        for student in students:
            student_history = self.get_student_attendance_history(class_id, student["id"])
            if student_history and all(record["is_present"] for record in student_history):
                perfect_attendance_count += 1
        
        return {
            "total_students": total_students,
            "total_days": total_days,
            "total_present": total_present,
            "total_absent": total_possible_attendance - total_present,
            "average_attendance": round(overall_attendance_rate, 1),
            "perfect_attendance_count": perfect_attendance_count,
            "attendance_rate_by_day": [
                {"date": day["date"], "rate": day["attendance_rate"]}
                for day in history[-10:]  # Last 10 days
            ]
        }
    
    def generate_attendance_report(self, class_id: int, 
                                 start_date: str, 
                                 end_date: str) -> Dict:
        """Generate detailed attendance report for a date range"""
        # Get data within date range
        history = self.get_attendance_history(class_id, start_date, end_date)
        students = self.get_students_for_class(class_id)
        
        # Initialize report structure
        report = {
            "class_id": class_id,
            "report_period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_days": len(history),
                "total_students": len(students),
                "days_with_attendance": len([d for d in history if d["total_students"] > 0])
            },
            "daily_attendance": history,
            "student_performance": []
        }
        
        # Calculate individual student performance
        for student in students:
            student_id = student["id"]
            student_history = self.get_student_attendance_history(class_id, student_id)
            
            # Filter to report period
            period_history = [
                record for record in student_history 
                if start_date <= record["date"] <= end_date
            ]
            
            if period_history:
                present_days = sum(1 for record in period_history if record["is_present"])
                total_days = len(period_history)
                attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0
                
                report["student_performance"].append({
                    "student_id": student_id,
                    "student_name": student["name"],
                    "student_code": student["student_code"],
                    "present_days": present_days,
                    "absent_days": total_days - present_days,
                    "attendance_rate": round(attendance_rate, 1),
                    "status": self._get_attendance_status(attendance_rate)
                })
        
        # Sort students by attendance rate (descending)
        report["student_performance"].sort(
            key=lambda x: x["attendance_rate"], 
            reverse=True
        )
        
        # Calculate category counts
        excellent = sum(1 for s in report["student_performance"] if s["status"] == "Excellent")
        good = sum(1 for s in report["student_performance"] if s["status"] == "Good")
        needs_improvement = sum(1 for s in report["student_performance"] if s["status"] == "Needs Improvement")
        
        report["summary"]["performance_categories"] = {
            "excellent": excellent,
            "good": good,
            "needs_improvement": needs_improvement
        }
        
        return report
    
    def _get_attendance_status(self, rate: float) -> str:
        """Determine attendance status based on rate"""
        if rate >= 90:
            return "Excellent"
        elif rate >= 75:
            return "Good"
        else:
            return "Needs Improvement"
        
    def get_student_by_user_id(self, class_id: int, user_id: int) -> Optional[Dict]:
        """Get a specific student by user ID"""
        students = self.get_students_for_class(class_id)
        
        for student in students:
            if student.get("user_id") == user_id:
                return student
        
        return None