from ..Base.faculty_admin_base import FacultyAdminBase
from ..Base.manager_base import ManagerBase

class Faculty(FacultyAdminBase, ManagerBase):
    """
    Faculty view. Inherits from FacultyAdminBase (for the non-student
    UI layout and org loading) and ManagerBase (for management methods).
    
    MRO: Faculty -> FacultyAdminBase -> OrganizationViewBase -> User -> ManagerBase
    Note: ManagerBase methods will be found via MRO if FacultyAdminBase
    doesn't implement them (e.g., _to_members_page).
    
    Correction: MRO will be:
    Faculty -> FacultyAdminBase -> OrganizationViewBase -> User -> ManagerBase
    
    Let's fix that. We want ManagerBase first for method priority.
    """
    
class Faculty(ManagerBase, FacultyAdminBase):
    """
    Faculty view. Inherits from ManagerBase (for management methods) and
    FacultyAdminBase (for the non-student UI layout and org loading).
    
    MRO: Faculty -> ManagerBase -> FacultyAdminBase -> OrganizationViewBase -> User
    This ensures manager methods (e.g., _to_members_page) are used.
    """
    
    def __init__(self, faculty_name: str):
        # Initializes FacultyAdminBase -> OrganizationViewBase -> User
        # This sets up the UI and non-manager connections
        FacultyAdminBase.__init__(self, name=faculty_name)
        # Initializes ManagerBase (is_managing, etc.)
        ManagerBase.__init__(self)
        
        # self.is_managing is True by default from ManagerBase
        
        # Load initial orgs
        self.load_orgs()