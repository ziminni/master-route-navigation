from PyQt6 import QtWidgets, QtCore
from widgets.Academics.classroom_home_ui import Ui_ClassCard
from controller.Academics.Classroom.classroom_controller import ClassroomController

from frontend.controller.Academics.Tagging.classes_controller import ClassesController
from frontend.controller.Academics.controller_manager import ControllerManager


class ClassroomHome(QtWidgets.QWidget):
    class_selected = QtCore.pyqtSignal(dict)  # Signal to emit when a class is clicked

    def __init__(self, username, roles, primary_role, token, parent=None):
        super().__init__(parent)
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        self.controller = ClassroomController()

        manager = ControllerManager()
        controller = manager.get_classes_controller()
        # connect signals to automatically update home if Admin modifies classes in Tagging
        controller.class_created.connect(self.on_class_changed)
        controller.class_updated.connect(self.on_class_changed)
        controller.class_deleted.connect(self.on_class_changed)

        self.setup_ui()
        self.load_classes()

    def on_class_changed(self, data=None):
        """
        Called when admin creates/updates/deletes a class.
        Auto-refreshes the classroom home view.
        """
        print(f"[ClassroomHome] Detected class change, refreshing...")
        self.load_classes()

    def setup_ui(self):
        self.setMinimumSize(940, 530)
        self.setStyleSheet("background-color: white;")
        
        # Main layout
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Scroll area
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea { border: none; }
            QScrollBar:vertical {
                border: none;
                background: #F1F1F1;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #C1C1C1;
                border-radius: 4px;
                min-height: 20px;
            }
        """)
        self.scroll_content = QtWidgets.QWidget()
        self.scroll_layout = QtWidgets.QGridLayout(self.scroll_content)
        self.scroll_layout.setSpacing(20)
        self.scroll_area.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll_area)

    def load_classes(self):
        self.clear()

        classes = self.controller.get_classes()
        print(f"[ClassroomHome] Classes loaded: {classes}")
        row, col = 0, 0
        max_columns = 3

        for cls in classes:
            card_widget = QtWidgets.QFrame()  # Changed from QWidget to QFrame
            card_ui = Ui_ClassCard()
            card_ui.setupUi(card_widget)

            # Set card info
            card_ui.course_code_label.setText(cls['code'])  # e.g., "IT 2A"
            card_ui.course_code_section_label.setText(cls.get('section_name', 'N/A'))
            card_ui.instructor_label.setText(cls['instructor'])

            # Connect click event
            card_widget.mousePressEvent = lambda event, c=cls: self.class_selected.emit(c)

            self.scroll_layout.addWidget(card_widget, row, col)
            col += 1
            if col >= max_columns:
                col = 0
                row += 1

    def clear(self):
        # Clear scroll area to prevent memory leaks
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()