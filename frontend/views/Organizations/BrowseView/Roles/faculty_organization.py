from ..Base.faculty_admin_base import FacultyAdminBase
from ..Base.manager_base import ManagerBase

class Faculty(ManagerBase, FacultyAdminBase):
    """
    Faculty view. Inherits from ManagerBase (for management methods) and
    FacultyAdminBase (for the non-student UI layout and org loading).
    
    MRO: Faculty -> ManagerBase -> FacultyAdminBase -> OrganizationViewBase -> User
    This ensures manager methods (e.g., _to_members_page) are used.
    """
    
    def __init__(self, faculty_name: str):
        FacultyAdminBase.__init__(self, name=faculty_name)
        ManagerBase.__init__(self)
                
        self.load_orgs()