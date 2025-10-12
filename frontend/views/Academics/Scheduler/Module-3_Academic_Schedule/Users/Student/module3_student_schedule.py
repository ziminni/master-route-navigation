import os
import sys
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QWidget, QHeaderView
from datetime import datetime

class ScheduleWindow(QWidget):
    def __init__(self):
        super().__init__()
        # Tag role for controller visibility logic
        self.user_role = "student"
        # Example logged-in student id for personal schedule loading
        self.student_id = "2025-00001"
        # Example: this student is in 2nd Year; restrict YearBox to 1st-2nd
        self.student_year = "2nd Year"
        try:
            from services.json_paths import get_project_root
            project_root = get_project_root()
        except Exception:
            project_root = os.path.dirname(
                os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(
                            os.path.dirname(
                                os.path.dirname(__file__)
                            )
                        )
                    )
                )
            )
        ui_file = os.path.abspath(
            os.path.join(project_root, "ui", "Academic Schedule", "schedule.ui")
        )
        uic.loadUi(ui_file, self)

        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        # Wire signals via controller
        try:
            from controller.module3.schedule_controller import wire_schedule_signals
            wire_schedule_signals(self)
        except Exception as e:
            print(f"Error wiring Module 3 student signals: {e}")
            # Fallback: manually connect the buttons
            if hasattr(self, "viewCurriculum") and hasattr(self, "show_curriculum_page"):
                self.viewCurriculum.clicked.connect(self.show_curriculum_page)
            if hasattr(self, "Return") and hasattr(self, "show_schedule_page"):
                self.Return.clicked.connect(self.show_schedule_page)
            # Fallback: hide search controls for students
            if hasattr(self, "Search"):
                self.Search.setVisible(False)
            if hasattr(self, "StudentSearch"):
                self.StudentSearch.setVisible(False)

        # Apply QSS to this widget only using project root helper (stable path)
        try:
            from services.json_paths import get_project_root
            project_root = get_project_root()
            qss_path = os.path.join(project_root, "assets", "qss", "module3_styles.qss")
            if os.path.exists(qss_path):
                with open(qss_path, 'r', encoding='utf-8') as f:
                    self.setStyleSheet(f.read())
        except Exception:
            pass

        # Ensure all QTableWidgets' columns fit the table width
        self.WeekTable_2.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tableWidget_2.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sem1.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sem2frame.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Apply UI helpers to prevent clipping (buttons/tables)
        try:
            from services.ui_utils import fit_all_buttons, auto_resize_all_tables
            fit_all_buttons(self)
            auto_resize_all_tables(self)
        except Exception:
            pass

        # Set labelTodayHeader_2 to today's day name
        today_name = datetime.now().strftime("%A")
        self.labelTodayHeader_2.setText(today_name)

    def show_curriculum_page(self):
        self.stackedWidget.setCurrentIndex(1)  # Curriculum page

    def show_schedule_page(self):
        self.stackedWidget.setCurrentIndex(0)  # Schedule page


if __name__ == "__main__":
    app = QApplication([])
    try:
        from services.json_paths import get_project_root
        project_root = get_project_root()
    except Exception:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))) )
    qss_path = os.path.join(project_root, "assets", "qss", "module3_styles.qss")
    if os.path.exists(qss_path):
        with open(qss_path, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    window = ScheduleWindow()
    window.show()
    app.exec()