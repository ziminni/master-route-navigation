import os
import sys
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6 import uic


class Schedule(QWidget):
    def __init__(self, username: str = "", roles=None, primary_role: str = "", token: str = ""):
        super().__init__()
        # Determine role and choose the appropriate Module 3 window
        is_faculty = (primary_role == "faculty") or (roles and "faculty" in roles)
        base_dir = os.path.dirname(__file__)
        # Choose the module3 view implementation based on role and import it
        users_folder = os.path.join(base_dir, "Users", "Faculty" if is_faculty else "Student")
        # Ensure project root is available for services imports used by the view
        project_root = os.path.abspath(os.path.join(base_dir, "..", "..", ".."))
        try:
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
        except Exception:
            pass

        # Attempt to import the view module from file to get its ScheduleWindow class
        try:
            import importlib.util
            module_filename = "module3_faculty_schedule.py" if is_faculty else "module3_student_schedule.py"
            module_path = os.path.join(users_folder, module_filename)
            spec = importlib.util.spec_from_file_location("module3_schedule_view", module_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            loaded = getattr(mod, "ScheduleWindow")()
        except Exception:
            # Fallback to loading the shared UI directly (older behavior)
            ui_path = os.path.join(project_root, "ui", "Academic Schedule", "schedule.ui")
            loaded = uic.loadUi(ui_path)

        # Embed the loaded widget into this container
        container = QVBoxLayout(self)
        container.setContentsMargins(0, 0, 0, 0)
        container.addWidget(loaded)

        # Ensure frontend root is on sys.path so controller/services imports resolve
        try:
            import sys as _sys
            frontend_root = project_root
            if frontend_root not in _sys.path:
                _sys.path.insert(0, frontend_root)
        except Exception:
            pass

        # Tag role and student context on the loaded UI widget (view classes may already set this)
        try:
            setattr(loaded, "user_role", "faculty" if is_faculty else "student")
            if not is_faculty:
                # Prefer a valid student_id; if username isn't an id, fallback to first student in JSON
                from services.students_service import list_students, get_student_year
                
                #This calls the username instead of the actual user_id, Is actually useless if backend is considered
                
                student_id = username if (isinstance(username, str) and username and username.count("-") == 1) else None
                # Find a way to get the user id data from the json from the backend
                
                #We currently have username and token, we need to get the student_id from the backend using the username and token
                #Let's refer to the login process. Login process does not return student_id, only username, roles, primary_role and token
                #It's ideal to make a service, but for now, we'll put the code here
                #This is a temporary solution, ideally we should have a service to get the student_id. This uses the auth_service as reference
                ###########################3 Move this to a service if possible

                #########################333
                if not student_id:
                    try:
                        students = list_students() or []
                        if students:
                            student_id = students[0].get("studentId")#This will default to the first student id in students.json
                    except Exception:
                        student_id = None
                if student_id:
                    setattr(loaded, "student_id", student_id)
                    # Optionally tag student_year to help controller restrict years
                    try:
                        year = get_student_year(student_id)
                        if year:
                            setattr(loaded, "student_year", year)
                    except Exception:
                        pass
        except Exception:
            pass

        # Wire signals via Module 3 controller if the view didn't already
        try:
            from controller.module3.schedule_controller import wire_schedule_signals
            wire_schedule_signals(loaded)
        except Exception as e:
            # Best-effort: ignore wiring errors to avoid crashing the whole app
            print(f"Schedule: warning wiring controller signals failed: {e}")



