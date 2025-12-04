# attendance_controller.py - Updated with role-based functionality
from typing import List, Dict, Optional, Any
from datetime import datetime

from frontend.services.Academics.Classroom.attendance_service import AttendanceService


class AttendanceController:
    """Controller for handling attendance operations with role-based access"""
    
    def __init__(self, service: Optional[AttendanceService] = None):
        """Initialize with dependency injection support"""
        self.service = service or AttendanceService()
        self.current_class_id = None
        self.current_class_name = None
        self.current_user_id = None
        self.current_user_role = "viewer"  # Default role
    
    # ========== User and Role Management ==========
    
    def set_user_context(self, user_id: int, user_role: str) -> None:
        """Set current user context for role-based permissions"""
        self.current_user_id = user_id
        self.current_user_role = user_role.lower()
    
    def set_class(self, class_id: int, class_name: Optional[str] = None) -> None:
        """Set the current class context"""
        self.current_class_id = class_id
        self.current_class_name = class_name or f"Class {class_id}"
    
    def can_edit_attendance(self) -> bool:
        """Check if current user can edit attendance"""
        return self.current_user_role in ["teacher", "assistant", "admin"]
    
    def can_manage_students(self) -> bool:
        """Check if current user can manage students"""
        return self.current_user_role in ["teacher", "admin"]
    
    def can_view_all_data(self) -> bool:
        """Check if current user can view all data"""
        return self.current_user_role in ["teacher", "assistant", "admin", "parent"]
    
    def get_current_class_info(self) -> Optional[Dict]:
        """Get information about the current class"""
        if self.current_class_id is None:
            return None
        
        class_info = self.service.get_class(self.current_class_id)
        if class_info:
            return class_info
        
        # Create basic class info if not exists
        basic_info = {
            "id": self.current_class_id,
            "name": self.current_class_name,
            "created_at": datetime.now().isoformat()
        }
        self.service.save_class(self.current_class_id, basic_info)
        return basic_info
    
    # ========== Student Management ==========
    
    def get_students(self) -> List[Dict]:
        """Get students for current class - filtered for student role"""
        if self.current_class_id is None:
            return []
        
        all_students = self.service.get_students_for_class(self.current_class_id)
        
        # For student role, only return their own data
        if self.current_user_role == "student" and self.current_user_id:
            # Find student with matching user_id
            # Note: This assumes student records have a user_id field
            # You may need to adjust this based on your data structure
            for student in all_students:
                if student.get("user_id") == self.current_user_id:
                    return [student]
            
            # If student not found, return empty list
            return []
        
        return all_students
    
    def add_student(self, student_data: Dict) -> bool:
        """Add a student to current class"""
        if not self.can_manage_students():
            raise PermissionError("You do not have permission to add students")
        
        if self.current_class_id is None:
            return False
        
        # Validate required fields
        if not student_data.get("name"):
            raise ValueError("Student name is required")
        
        # Generate student code if not provided
        if not student_data.get("student_code"):
            students = self.service.get_students_for_class(self.current_class_id)
            next_number = len(students) + 1
            student_data["student_code"] = f"S{next_number:03d}"
        
        return self.service.add_student_to_class(self.current_class_id, student_data)
    
    # ========== Attendance Records ==========
    
    def get_attendance_for_date_range(self, start_date: str, end_date: str) -> Dict[str, Dict[int, bool]]:
        """Get attendance records for a date range"""
        if self.current_class_id is None:
            return {}
        
        history = self.service.get_attendance_history(
            self.current_class_id, 
            start_date, 
            end_date
        )
        
        # Format as {date: {student_id: is_present, ...}, ...}
        date_range_data = {}
        for day in history:
            date_str = day.get("date", "")
            if date_str:
                date_range_data[date_str] = {}
                for student_id_str, record in day.get("attendance", {}).items():
                    student_id = int(student_id_str)
                    date_range_data[date_str][student_id] = record.get("is_present", False)
        
        return date_range_data
    
    def save_attendance(self, date: str, attendance_records: List[Dict]) -> bool:
        """Save attendance records for a date"""
        if not self.can_edit_attendance():
            raise PermissionError("You do not have permission to save attendance")
        
        if self.current_class_id is None:
            return False
        
        # Validate input
        if not date or not attendance_records:
            raise ValueError("Date and attendance records are required")
        
        # Format records for service
        formatted_records = []
        for record in attendance_records:
            if not record.get("student_id"):
                continue
            
            formatted_records.append({
                "student_id": record["student_id"],
                "student_name": record.get("student_name", f"Student {record['student_id']}"),
                "is_present": record.get("is_present", False)
            })
        
        return self.service.save_attendance_for_date(
            self.current_class_id, 
            date, 
            formatted_records
        )
    
    # ========== Bulk Operations ==========
    
    def mark_all_present(self, date: str) -> bool:
        """Mark all students as present for a date"""
        if not self.can_edit_attendance():
            raise PermissionError("You do not have permission to mark attendance")
        
        if self.current_class_id is None:
            return False
        
        students = self.service.get_students_for_class(self.current_class_id)
        records = [
            {
                "student_id": student["id"],
                "student_name": student["name"],
                "is_present": True
            }
            for student in students
        ]
        
        return self.save_attendance(date, records)
    
    def mark_all_absent(self, date: str) -> bool:
        """Mark all students as absent for a date"""
        if not self.can_edit_attendance():
            raise PermissionError("You do not have permission to mark attendance")
        
        if self.current_class_id is None:
            return False
        
        students = self.service.get_students_for_class(self.current_class_id)
        records = [
            {
                "student_id": student["id"],
                "student_name": student["name"],
                "is_present": False
            }
            for student in students
        ]
        
        return self.save_attendance(date, records)
    
    # ========== History and Reports ==========
    
    def get_attendance_history(self, start_date: Optional[str] = None,
                             end_date: Optional[str] = None) -> List[Dict]:
        """Get attendance history for date range"""
        if self.current_class_id is None:
            return []
        
        history = self.service.get_attendance_history(
            self.current_class_id, 
            start_date, 
            end_date
        )
        
        # Filter for student role
        if self.current_user_role == "student" and self.current_user_id:
            students = self.get_students()
            if students:
                student_id = students[0]["id"]
                # Filter history to show only days where this student's attendance was recorded
                student_history = []
                for day in history:
                    if str(student_id) in day.get("attendance", {}):
                        student_day = day.copy()
                        student_att = day["attendance"][str(student_id)]
                        student_day["present_count"] = 1 if student_att["is_present"] else 0
                        student_day["absent_count"] = 0 if student_att["is_present"] else 1
                        student_day["total_students"] = 1
                        student_day["attendance_rate"] = 100 if student_att["is_present"] else 0
                        student_history.append(student_day)
                return student_history
        
        return history
    
    def get_student_attendance_history(self, student_id: int) -> List[Dict]:
        """Get attendance history for a specific student"""
        if self.current_class_id is None:
            return []
        
        # Check permissions for parent role
        if self.current_user_role == "parent":
            # In real app, check if parent is linked to this student
            pass
        
        return self.service.get_student_attendance_history(
            self.current_class_id, 
            student_id
        )
    
    def get_attendance_stats(self) -> Dict:
        """Get attendance statistics for current class"""
        if self.current_class_id is None:
            return {}
        
        return self.service.get_attendance_stats(self.current_class_id)
    
    def get_student_attendance_stats(self, student_id: int) -> Dict:
        """Get attendance statistics for a specific student"""
        if self.current_class_id is None:
            return {}
        
        # For student role, ensure they can only view their own stats
        if self.current_user_role == "student" and self.current_user_id:
            students = self.get_students()
            if not students or students[0]["id"] != student_id:
                return {"message": "Access denied"}
        
        return self.service.get_student_attendance_stats(self.current_class_id, student_id)
    
    def generate_attendance_report(self, start_date: str, end_date: str) -> Dict:
        """Generate attendance report for date range"""
        if not self.can_view_all_data():
            raise PermissionError("You do not have permission to generate reports")
        
        if self.current_class_id is None:
            return {}
        
        # Validate dates
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Dates must be in YYYY-MM-DD format")
        
        if start_date > end_date:
            raise ValueError("Start date must be before end date")
        
        return self.service.generate_attendance_report(
            self.current_class_id, 
            start_date, 
            end_date
        )
    
    # ========== Data Export ==========
    
    def export_attendance_to_csv(self, start_date: str, end_date: str) -> str:
        """Export attendance data to CSV format"""
        if not self.can_edit_attendance():
            raise PermissionError("You do not have permission to export data")
        
        report = self.generate_attendance_report(start_date, end_date)
        
        if not report:
            return ""
        
        # Build CSV content
        csv_lines = []
        
        # Header
        csv_lines.append("Attendance Report")
        csv_lines.append(f"Class: {self.current_class_name}")
        csv_lines.append(f"Period: {start_date} to {end_date}")
        csv_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        csv_lines.append(f"Generated By: {self.current_user_role}")
        csv_lines.append("")
        
        # Summary
        csv_lines.append("SUMMARY")
        csv_lines.append(f"Total Students,{report['summary']['total_students']}")
        csv_lines.append(f"Total Days,{report['summary']['total_days']}")
        csv_lines.append(f"Days with Attendance,{report['summary']['days_with_attendance']}")
        csv_lines.append("")
        
        # Student Performance
        csv_lines.append("STUDENT PERFORMANCE")
        csv_lines.append("Student ID,Name,Code,Present Days,Absent Days,Attendance Rate,Status")
        
        for student in report.get("student_performance", []):
            csv_lines.append(
                f"{student['student_id']},"
                f"{student['student_name']},"
                f"{student['student_code']},"
                f"{student['present_days']},"
                f"{student['absent_days']},"
                f"{student['attendance_rate']}%,"
                f"{student['status']}"
            )
        
        return "\n".join(csv_lines)