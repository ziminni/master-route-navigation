# classroom_attendance.py - Updated for student view
import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFrame, QMessageBox, QSizePolicy)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from frontend.widgets.Academics.classroom_attendance_ui import AttendanceWidget
from frontend.controller.Academics.Classroom.attendance_controller import AttendanceController


class ClassroomAttendanceView(QWidget):
    """Attendance view widget - Overview for students, Mark Attendance for teachers"""
    
    def __init__(self, cls, username, roles, primary_role, token, 
                 classroom_controller=None, parent=None):
        super().__init__(parent)
        
        # Extract class info
        self.class_id = cls.get("id")
        self.class_name = cls.get("name", "Unknown Class")
        
        # Store user info
        self.username = username
        self.roles = roles
        self.primary_role = primary_role.lower()
        self.token = token
        
        # Map role
        self.user_role = self.map_role_to_attendance_role()
        
        # Track if user is a student
        self.is_student = self.user_role == "student"
        
        # Initialize controller
        self.attendance_controller = AttendanceController()
        if self.class_id:
            self.attendance_controller.set_class(self.class_id, self.class_name)
            self.attendance_controller.set_user_context(
                user_id=self.get_user_id(),
                user_role=self.user_role
            )
        
        self.students_data = []
        
        self.init_ui()
        self.connect_signals()
        self.load_class_data()
        
    def map_role_to_attendance_role(self):
        """Map ClassroomView roles to attendance roles"""
        role_mapping = {
            "faculty": "teacher",
            "teacher": "teacher",
            "instructor": "teacher",
            "professor": "teacher",
            "assistant": "assistant",
            "ta": "assistant",
            "student": "student",
            "learner": "student",
            "parent": "parent",
            "guardian": "parent",
            "admin": "teacher",
            "staff": "assistant"
        }
        
        return role_mapping.get(self.primary_role, "student")
    
    def can_edit_attendance(self):
        """Check if user can edit attendance based on role"""
        return self.user_role in ["teacher", "assistant"]
    
    def get_user_id(self):
        """Extract user ID from token or username"""
        return hash(self.username) % 1000
    
    def get_current_student_id(self):
        """Get the current student's ID - for student role"""
        if not self.is_student:
            return None
        return self.get_user_id()
    
    def init_ui(self):
        # Make the widget responsive
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Use minimal styling
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                font-family: 'Poppins';
            }
        """)
        
        # Main layout with minimal margins
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)
        
        # Add attendance widget directly
        self.attendance_widget = AttendanceWidget()
        
        # Make the attendance widget responsive
        self.attendance_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Add to layout with stretch factor
        main_layout.addWidget(self.attendance_widget, 1)
        
        # Apply role restrictions
        self.apply_role_restrictions()
    
    def apply_role_restrictions(self):
        """Apply role-based restrictions to the UI"""
        can_edit = self.can_edit_attendance()
        
        if self.is_student:
            # For students: hide all editing controls
            self.attendance_widget.save_btn.hide()
            self.attendance_widget.mark_all_present_btn.hide()
            self.attendance_widget.mark_all_absent_btn.hide()
            
            # Set default view to Overview for students
            self.attendance_widget.show_overview_view()
            self.attendance_widget.view_combo.setCurrentText("Overview")
        else:
            # For teachers/assistants: enable editing controls
            self.attendance_widget.save_btn.setEnabled(can_edit)
            self.attendance_widget.mark_all_present_btn.setEnabled(can_edit)
            self.attendance_widget.mark_all_absent_btn.setEnabled(can_edit)
            
            # Set default view to Mark Attendance for teachers
            self.attendance_widget.show_mark_attendance_view()
            self.attendance_widget.view_combo.setCurrentText("Mark Attendance")
    
    def connect_signals(self):
        """Connect signals from attendance widget"""
        # Connect save button only if user can edit
        if self.can_edit_attendance():
            self.attendance_widget.save_btn.clicked.connect(self.save_attendance_data)
        
        # Connect date changes
        self.attendance_widget.date_picker.dateChanged.connect(self.on_date_changed)
    
    def load_class_data(self):
        """Load class data - filtered for student role"""
        if not self.class_id:
            return
        
        try:
            # Get students through controller
            all_students = self.attendance_controller.get_students()
            
            if not all_students:
                # Use sample data for demo
                self.load_sample_data()
                return
            
            # Filter students based on role
            if self.is_student:
                # For students, find their own record
                student_id = self.get_current_student_id()
                filtered_students = []
                
                for student in all_students:
                    if student.get("id") == student_id:
                        filtered_students.append(student)
                        break
                
                # If student not found in list, create a placeholder
                if not filtered_students:
                    filtered_students = [{
                        "id": student_id,
                        "name": f"{self.username} (You)",
                        "student_code": f"S{student_id:03d}"
                    }]
            else:
                # For teachers/assistants/parents, show all students
                filtered_students = all_students
            
            # Format students for the widget
            colors = ["#4db8a0", "#6b9bd1", "#f4a261", "#e76f51", "#8e7cc3", 
                     "#5da271", "#d4a574", "#c44569", "#778beb", "#cf6a87"]
            
            self.students_data = []
            for i, student in enumerate(filtered_students):
                self.students_data.append({
                    "id": student.get("id", i + 1),
                    "no": i + 1,
                    "name": student.get("name", f"Student {i + 1}"),
                    "color": colors[i % len(colors)],
                    "student_code": student.get("student_code", f"S{i+1:03d}")
                })
            
            # Update widget with filtered students
            self.update_attendance_widget_with_students()
            
            # Load attendance data
            self.load_attendance_data()
            
        except Exception as e:
            print(f"Error loading class data: {e}")
            self.load_sample_data()
    
    def load_sample_data(self):
        """Load sample data for demo purposes"""
        colors = ["#4db8a0", "#6b9bd1", "#f4a261", "#e76f51", "#8e7cc3", 
                 "#5da271", "#d4a574", "#c44569", "#778beb", "#cf6a87"]
        
        if self.is_student:
            # For students, only show their own record
            sample_names = [f"{self.username} (You)"]
        else:
            # For others, show multiple students
            sample_names = [
                "Castro, Carlos", "Dela Cruz, Maria", "Reyes, Juan",
                "Santos, Ana", "Garcia, Jose", "Tan, Michael",
                "Lim, Samantha", "Nguyen, Andrew", "Smith, Jennifer",
                "Johnson, Robert"
            ]
        
        self.students_data = []
        for i, name in enumerate(sample_names, 1):
            self.students_data.append({
                "id": i,
                "no": i,
                "name": name,
                "color": colors[i % len(colors)],
                "student_code": f"S{i:03d}"
            })
        
        self.update_attendance_widget_with_students()
        self.load_attendance_data()
    
    def load_attendance_data(self):
        """Load attendance data for current view"""
        if not self.students_data:
            return
        
        if self.is_student:
            # For students in Overview view, load multiple dates
            self.load_attendance_for_date_range()
        else:
            # For teachers, load current date
            self.load_attendance_for_current_date()
    
    def load_attendance_for_current_date(self):
        """Load attendance for the currently selected date"""
        current_date = self.attendance_widget.date_picker.date().toString("yyyy-MM-dd")
        
        try:
            # Get attendance records for all students
            all_attendance_records = self.attendance_controller.get_attendance_for_date(current_date)
            
            # Update widget's internal attendance data
            for student in self.students_data:
                student_id = student["id"]
                if student_id not in self.attendance_widget.attendance_data:
                    self.attendance_widget.attendance_data[student_id] = {}
                
                # Set attendance status
                is_present = all_attendance_records.get(student_id, True)
                self.attendance_widget.attendance_data[student_id][current_date] = is_present
            
            # Update the display for Mark Attendance view
            if hasattr(self.attendance_widget, 'student_rows'):
                for row in self.attendance_widget.student_rows:
                    student_id = row.student_data["id"]
                    is_present = self.attendance_widget.attendance_data.get(student_id, {}).get(current_date, True)
                    row.update_attendance(current_date, is_present)
            
            self.attendance_widget.update_statistics()
            
        except Exception as e:
            print(f"Error loading attendance: {e}")
    
    def load_attendance_for_date_range(self):
        """Load attendance for multiple dates for Overview view"""
        # Generate last 7 days for overview
        from datetime import datetime, timedelta
        
        dates = []
        for i in range(-7, 1):  # Last 7 days including today
            date = QDate.currentDate().addDays(i)
            if date.dayOfWeek() < 6:  # Monday to Friday
                dates.append((date.toString("MMM d"), "Present"))
        
        # Update overview widget with dates
        if hasattr(self.attendance_widget, 'overview_widget'):
            self.attendance_widget.overview_widget.load_data(self.students_data, dates)
            
            # Load attendance data for each date
            for date_str, _ in dates:
                try:
                    # Parse date string to proper format
                    date_obj = QDate.fromString(date_str, "MMM d")
                    full_date = date_obj.toString("yyyy-MM-dd")
                    
                    # Get attendance for this date
                    attendance_records = self.attendance_controller.get_attendance_for_date(full_date)
                    
                    # Update student attendance data
                    for student in self.students_data:
                        student_id = student["id"]
                        if student_id not in self.attendance_widget.attendance_data:
                            self.attendance_widget.attendance_data[student_id] = {}
                        
                        is_present = attendance_records.get(student_id, True)
                        self.attendance_widget.attendance_data[student_id][date_str] = is_present
                        
                except Exception as e:
                    print(f"Error loading attendance for {date_str}: {e}")
    
    def update_attendance_widget_with_students(self):
        """Update the attendance widget with filtered students"""
        self.attendance_widget.students = self.students_data
        self.attendance_widget.attendance_data = {}
        
        # Populate based on current view
        if self.is_student:
            # Students see overview by default
            self.attendance_widget.populate_overview_view()
        else:
            # Teachers see mark attendance by default
            self.attendance_widget.populate_student_list()
        
        # Update view mode combo based on role
        if self.is_student:
            # Students can only see Overview
            self.attendance_widget.view_combo.clear()
            self.attendance_widget.view_combo.addItems(["Overview"])
            self.attendance_widget.view_combo.setEnabled(False)
        else:
            # Teachers can switch between views
            self.attendance_widget.view_combo.setEnabled(True)
    
    def on_date_changed(self, date):
        """Handle date change - only for teachers in Mark Attendance view"""
        if not self.is_student:
            self.load_attendance_for_current_date()
    
    def save_attendance_data(self):
        """Save attendance data through controller - only for teachers"""
        if not self.can_edit_attendance():
            return
        
        if not self.class_id:
            self.show_warning("No Class", "No class selected for saving attendance.")
            return
        
        try:
            current_date = self.attendance_widget.date_picker.date().toString("yyyy-MM-dd")
            
            attendance_records = []
            for student in self.students_data:
                student_id = student["id"]
                is_present = self.attendance_widget.attendance_data.get(student_id, {}).get(current_date, True)
                
                attendance_records.append({
                    "student_id": student_id,
                    "student_name": student["name"],
                    "is_present": is_present
                })
            
            success = self.attendance_controller.save_attendance(
                date=current_date,
                attendance_records=attendance_records
            )
            
            if success:
                QMessageBox.information(self, "Attendance Saved", 
                                      f"Attendance for {current_date} saved successfully.")
            else:
                QMessageBox.critical(self, "Save Failed", "Failed to save attendance data.")
                
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Error saving attendance: {str(e)}")
    
    # Utility message methods
    def show_info(self, title, message):
        QMessageBox.information(self, title, message)
    
    def show_warning(self, title, message):
        QMessageBox.warning(self, title, message)
    
    def show_error(self, title, message):
        QMessageBox.critical(self, title, message)
    
    def show_success(self, title, message):
        QMessageBox.information(self, title, message)