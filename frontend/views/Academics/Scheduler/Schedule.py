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
        mod3_dir = os.path.join(base_dir, "Module-3_Academic_Schedule", "Users", "Faculty" if is_faculty else "Student")
        sys.path.insert(0, mod3_dir)

        # Load the shared schedule.ui directly into this widget
        project_root = os.path.abspath(os.path.join(base_dir, "..", "..", ".."))
        ui_path = os.path.join(project_root, "ui", "Academic Schedule", "schedule.ui")
        # Load QMainWindow-based UI as a child widget and embed it
        loaded = uic.loadUi(ui_path)
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

        # Tag role and student context on the loaded UI widget
        try:
            setattr(loaded, "user_role", "faculty" if is_faculty else "student")
            if not is_faculty:
                # Prefer a valid student_id; if username isn't an id, fallback to first student in JSON
                from services.students_service import list_students, get_student_year
                student_id = username if (isinstance(username, str) and username and username.count("-") == 1) else None
                if not student_id:
                    try:
                        students = list_students() or []
                        if students:
                            student_id = students[0].get("studentId")
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

        # Wire signals via Module 3 controller
        try:
            from controller.module3.schedule_controller import wire_schedule_signals
            wire_schedule_signals(loaded)
        except Exception as e:
            # Best-effort: ignore wiring errors to avoid crashing the whole app
            print(f"Schedule: warning wiring controller signals failed: {e}")



