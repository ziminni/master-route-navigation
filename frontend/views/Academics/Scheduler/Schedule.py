import os
import sys
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt6 import uic

#TODO
class Schedule(QWidget):
    def __init__(self, username: str = "", roles=None, primary_role: str = "", token: str = ""):
        super().__init__()
        # Determine role and choose the appropriate Module 3 window
        # Normalize roles to a set of strings for robust checks
        normalized_roles = set(roles or [])
        is_faculty = "faculty" in normalized_roles
        is_admin = "admin" in normalized_roles  # Check for admin role
        
        # TREAT ADMIN AS FACULTY
        if is_admin:
            is_faculty = True
            
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

        # HIDE CURRICULUM BUTTON - Target the specific button name
        self._hide_curriculum_button(loaded)

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
            print(f"Schedule: warning wiring controller signals failed: {e}")

    def _hide_curriculum_button(self, widget):
        """Hide the viewCurriculum button specifically"""
        try:
            # Method 1: Direct attribute access - this should work based on your code
            if hasattr(widget, 'viewCurriculum'):
                button = getattr(widget, 'viewCurriculum')
                if isinstance(button, QPushButton):
                    button.hide()
                    button.setEnabled(False)
                    print("✓ Curriculum button 'viewCurriculum' hidden and disabled")
                    return
                else:
                    print(f"⚠ viewCurriculum exists but is not a QPushButton: {type(button)}")

            # Method 2: Search by object name
            curriculum_buttons = widget.findChildren(QPushButton, "viewCurriculum")
            if curriculum_buttons:
                for button in curriculum_buttons:
                    button.hide()
                    button.setEnabled(False)
                print(f"✓ Found {len(curriculum_buttons)} curriculum button(s) by object name 'viewCurriculum'")
                return

            # Method 3: Search by text content
            all_buttons = widget.findChildren(QPushButton)
            curriculum_text_buttons = []
            for button in all_buttons:
                text = button.text().lower()
                if any(keyword in text for keyword in ['curriculum', 'syllabus']):
                    curriculum_text_buttons.append(button)
            
            if curriculum_text_buttons:
                for button in curriculum_text_buttons:
                    button.hide()
                    button.setEnabled(False)
                print(f"✓ Found {len(curriculum_text_buttons)} curriculum button(s) by text")
                return

            # Debug: List all buttons if not found
            if not hasattr(widget, 'viewCurriculum') and not curriculum_buttons:
                all_buttons = widget.findChildren(QPushButton)
                print(f"🔍 All buttons found: {len(all_buttons)}")
                for i, button in enumerate(all_buttons):
                    print(f"  {i+1}. ObjectName: '{button.objectName()}', Text: '{button.text()}'")

            print("⚠ Could not find curriculum button to hide")

        except Exception as e:
            print(f"Error hiding curriculum button: {e}")