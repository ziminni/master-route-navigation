import os
import sys
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QWidget, QHeaderView, QAbstractItemView
from PyQt6.QtCore import Qt
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
        def _find_project_root_with_ui(start_dir: str) -> str:
            """Walk upward from start_dir until a directory that contains a 'ui' folder is found.

            Returns the found directory or falls back to the nearest frontend parent.
            """
            cur = os.path.abspath(start_dir)
            while True:
                if os.path.isdir(os.path.join(cur, "ui")):
                    return cur
                parent = os.path.dirname(cur)
                if parent == cur:
                    # give up — return closest reasonable fallback
                    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
                cur = parent

        project_root = None
        try:
            from services.json_paths import get_project_root
            project_root = get_project_root()
        except Exception:
            # Fall back to searching upward for a directory that contains 'ui'
            project_root = _find_project_root_with_ui(os.path.dirname(__file__))

        ui_file = os.path.join(project_root, "ui", "Academic Schedule", "schedule.ui")
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

        # Make curriculum tables scrollable
        try:
            self.sem1.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.sem2frame.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.sem1.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.sem2frame.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.sem1.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
            self.sem2frame.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
            self.sem1.setWordWrap(False)
            self.sem2frame.setWordWrap(False)
        except Exception:
            pass

        # Set per-column resize modes to make headers fit
        try:
            self.sem1.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            self.sem1.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            self.sem1.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            self.sem1.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            self.sem1.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
            self.sem1.horizontalHeader().setMinimumSectionSize(60)

            self.sem2frame.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            self.sem2frame.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            self.sem2frame.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            self.sem2frame.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            self.sem2frame.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
            self.sem2frame.horizontalHeader().setMinimumSectionSize(60)
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