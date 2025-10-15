
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
        self.user_role = "faculty"
        # Resolve `frontend` root and load shared UI from Academic Schedule
        def _find_project_root_with_ui(start_dir: str) -> str:
            cur = os.path.abspath(start_dir)
            while True:
                if os.path.isdir(os.path.join(cur, "ui")):
                    return cur
                parent = os.path.dirname(cur)
                if parent == cur:
                    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
                cur = parent

        project_root = None
        try:
            from services.json_paths import get_project_root
            project_root = get_project_root()
        except Exception:
            project_root = _find_project_root_with_ui(os.path.dirname(__file__))

        ui_file = os.path.join(project_root, "ui", "Academic Schedule", "schedule.ui")
        uic.loadUi(ui_file, self)

        # Apply QSS to this widget only
        qss_path = os.path.join(project_root, "assets", "qss", "module3_styles.qss")
        if os.path.exists(qss_path):
            with open(qss_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())

        # Ensure /frontend is importable for 'controller.*' modules
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        # Wire signals via controller
        try:
            from controller.module3.schedule_controller import wire_schedule_signals
            wire_schedule_signals(self)
        except Exception as e:
            print(f"Error wiring Module 3 faculty signals: {e}")
            # Fallback: manually connect the buttons
            if hasattr(self, "viewCurriculum") and hasattr(self, "show_curriculum_page"):
                self.viewCurriculum.clicked.connect(self.show_curriculum_page)
            if hasattr(self, "Return") and hasattr(self, "show_schedule_page"):
                self.Return.clicked.connect(self.show_schedule_page)

        # Ensure all QTableWidgets' columns fit the table width
        self.WeekTable_2.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tableWidget_2.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sem1.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sem2frame.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Make curriculum tables scrollable (vertical scrolling for long lists)
        try:
            # vertical scrollbars as needed, use per-pixel scrolling for smoother behavior
            self.sem1.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.sem2frame.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.sem1.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.sem2frame.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.sem1.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
            self.sem2frame.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
            # Prevent text wrapping inside cells which can expand row height unexpectedly
            self.sem1.setWordWrap(False)
            self.sem2frame.setWordWrap(False)
            # Set per-column resize modes to make headers fit
            # columns: 0=Codes, 1=Subject Titles, 2=Grades, 3=Units, 4=Pre-requisite(s)
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
        project_root = os.path.dirname(
            os.path.dirname(
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
        )
    qss_path = os.path.join(project_root, "assets", "qss", "module3_styles.qss")
    if os.path.exists(qss_path):
        with open(qss_path, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    window = ScheduleWindow()
    window.show()
    app.exec()
