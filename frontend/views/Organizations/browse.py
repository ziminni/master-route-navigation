from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import QSettings

from .BrowseView import Student, Officer, Admin, Faculty, Dean
from services.organization_api_service import OrganizationAPIService


class Browse(QWidget):
    def __init__(self, username="", roles=None, primary_role="", token=""):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Fetch user profile ID from database using username
        student_profile_id = self._fetch_and_store_profile_id(username)

        if primary_role == "admin":
            self.view = Admin(admin_name=username)
        elif primary_role == "dean":
            self.view = Dean(dean_name=username)
        elif primary_role == "faculty":
            self.view = Faculty(faculty_name=username)
        elif primary_role == "student":
            if "org_officer" in (roles or []):
                self.view = Officer(officer_name=username, user_id=student_profile_id)
            else:
                self.view = Student(student_name=username, user_id=student_profile_id)
        else:
            self.view = Faculty(faculty_name=username)

        self.layout.addWidget(self.view)
    
    def _fetch_and_store_profile_id(self, username):
        """Fetch user profile from backend using username and store profile_id"""
        try:
            # Use the current-user endpoint to get profile IDs by username
            response = OrganizationAPIService.get_current_user_by_username(username)
            
            if response.get('success'):
                user_data = response.get('data', {})
                profile_id = user_data.get('profile_id')  # BaseUser.id
                student_profile_id = user_data.get('student_profile_id')  # StudentProfile.id (for students)
                faculty_profile_id = user_data.get('faculty_profile_id')  # FacultyProfile.id (for faculty)
                profile_type = user_data.get('profile_type')
                
                # Store in QSettings for later use
                settings = QSettings("CISC", "MasterRoute")
                if profile_id:
                    settings.setValue("user_profile_id", profile_id)
                if student_profile_id:
                    settings.setValue("student_profile_id", student_profile_id)
                if faculty_profile_id:
                    settings.setValue("faculty_profile_id", faculty_profile_id)
                
                # Return student_profile_id for student views
                return student_profile_id
            else:
                return None
                
        except Exception:
            return None