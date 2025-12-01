from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import QSettings

from .BrowseView import Student, Officer, Admin, Faculty, Dean

print(f"Browse: Imported Student={Student is not None}, Faculty={Faculty is not None}, Officer={Officer is not None}, Admin={Admin is not None}, Dean={Dean is not None}")

class Browse(QWidget):
    def __init__(self, username="", roles=None, primary_role="", token=""):
        super().__init__()
        print(f"Browse: Initializing for username={username}, primary_role={primary_role}, roles={roles}")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Store user profile ID in settings for later use
        self._fetch_and_store_profile_id(token)

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
                print("Browse: Loading Officer view")
                self.view = Officer(officer_name=username)
            else:
                print("Browse: Loading Student view")
                self.view = Student(student_name=username)
        else:
            print("Browse: Loading default Faculty view")
            self.view = Faculty(faculty_name=username)

        print(f"Browse: View created, type={type(self.view)}, ui={hasattr(self.view, 'ui')}")
        self.layout.addWidget(self.view)
        print("Browse: Widget added to layout")
    
    def _fetch_and_store_profile_id(self, token):
        """Fetch user profile from backend and store profile_id"""
        try:
            import requests
            from services.auth_service import AuthService
            
            base_url = AuthService.BASE_URL.replace('/auth', '')
            url = f"{base_url}/users/me/"
            
            headers = {'Authorization': f'Bearer {token}'} if token else {}
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                user_data = response.json()
                profile_id = user_data.get('profile_id')
                
                if profile_id:
                    # Store in QSettings
                    settings = QSettings("CISC", "MasterRoute")
                    settings.setValue("user_profile_id", profile_id)
                    print(f"DEBUG: Stored profile_id={profile_id} in QSettings")
                else:
                    print("WARNING: No profile_id in user data")
            else:
                print(f"WARNING: Failed to fetch user profile: {response.status_code}")
                
        except Exception as e:
            print(f"WARNING: Could not fetch user profile: {e}")