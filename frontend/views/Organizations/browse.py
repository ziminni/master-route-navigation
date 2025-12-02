from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import QSettings

from .BrowseView import Student, Officer, Admin, Faculty, Dean
from services.organization_api_service import OrganizationAPIService

print(f"Browse: Imported Student={Student is not None}, Faculty={Faculty is not None}, Officer={Officer is not None}, Admin={Admin is not None}, Dean={Dean is not None}")

class Browse(QWidget):
    def __init__(self, username="", roles=None, primary_role="", token=""):
        super().__init__()
        print(f"Browse: Initializing for username={username}, primary_role={primary_role}, roles={roles}")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Fetch user profile ID from database using username
        student_profile_id = self._fetch_and_store_profile_id(username)

        if primary_role == "admin":
            print("Browse: Loading Admin view")
            self.view = Admin(admin_name=username)
        elif primary_role == "dean":
            print("Browse: Loading Dean view")
            self.view = Dean(dean_name=username)
        elif primary_role == "faculty":
            print("Browse: Loading Faculty view")
            self.view = Faculty(faculty_name=username)
        elif primary_role == "student":
            if "org_officer" in (roles or []):
                print(f"Browse: Loading Officer view with student_profile_id={student_profile_id}")
                self.view = Officer(officer_name=username, user_id=student_profile_id)
            else:
                print(f"Browse: Loading Student view with student_profile_id={student_profile_id}")
                self.view = Student(student_name=username, user_id=student_profile_id)
        else:
            print("Browse: Loading default Faculty view")
            self.view = Faculty(faculty_name=username)

        print(f"Browse: View created, type={type(self.view)}, ui={hasattr(self.view, 'ui')}")
        self.layout.addWidget(self.view)
        print("Browse: Widget added to layout")
    
    def _fetch_and_store_profile_id(self, username):
        """Fetch user profile from backend using username and store profile_id"""
        try:
            # Use the current-user endpoint to get profile IDs by username
            response = OrganizationAPIService.get_current_user_by_username(username)
            
            if response.get('success'):
                user_data = response.get('data', {})
                profile_id = user_data.get('profile_id')  # BaseUser.id
                student_profile_id = user_data.get('student_profile_id')  # StudentProfile.id (for students)
                profile_type = user_data.get('profile_type')
                
                # Store in QSettings for later use
                settings = QSettings("CISC", "MasterRoute")
                if profile_id:
                    settings.setValue("user_profile_id", profile_id)
                if student_profile_id:
                    settings.setValue("student_profile_id", student_profile_id)
                
                print(f"DEBUG: Stored profile_id={profile_id}, student_profile_id={student_profile_id}, type={profile_type} in QSettings")
                
                # Return student_profile_id for student views
                return student_profile_id
            else:
                print(f"WARNING: Failed to fetch user profile: {response.get('message')}")
                return None
                
        except Exception as e:
            print(f"WARNING: Could not fetch user profile: {e}")
            return None