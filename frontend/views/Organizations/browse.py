from PyQt6.QtWidgets import QWidget, QVBoxLayout

from .student_organization import Student
from .faculty_organization import Faculty
from .officer_organization import Officer
from .admin_organization import Admin

print(f"Browse: Imported Student={Student is not None}, Faculty={Faculty is not None}, Officer={Officer is not None}, Admin={Admin is not None}")

class Browse(QWidget):
    def __init__(self, username="", roles=None, primary_role="", token=""):
        super().__init__()
        print(f"Browse: Initializing for username={username}, primary_role={primary_role}, roles={roles}")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        if primary_role == "admin":
            print("Browse: Loading Admin view")
            self.view = Admin(admin_name=username)
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
