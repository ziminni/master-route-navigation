from PyQt6 import uic
from PyQt6.QtWidgets import QFrame, QMenu, QWidget, QGridLayout, QScrollArea, QVBoxLayout, QLabel, QStackedWidget, QApplication, QTabWidget
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QAction
import os
import sys

# Try importing dependencies with logging
try:
    from classroom_stream_content import ClassroomStreamContent
    print("Successfully imported ClassroomStreamContent")
except ImportError as e:
    print(f"Failed to import ClassroomStreamContent: {e}")
    ClassroomStreamContent = None

try:
    from classroom_classworks_content import ClassroomClassworksContent
    print("Successfully imported ClassroomClassworksContent")
except ImportError as e:
    print(f"Failed to import ClassroomClassworksContent: {e}")
    ClassroomClassworksContent = None

class ClassCard(QFrame):
    card_clicked = pyqtSignal(dict)
    restore_clicked = pyqtSignal(dict)
    delete_clicked = pyqtSignal(dict)
    
    def __init__(self, class_data, user_role="student"):
        super().__init__()
        self.class_data = class_data
        self.user_role = user_role
        try:
            self.load_ui()
            self.populate_data()
            self.setup_role_based_ui()
            self.connect_signals()
        except Exception as e:
            print(f"ClassCard initialization failed: {e}")
            raise

    def load_ui(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(current_dir, '../../../../ui/Classroom/classroom_home.ui')
        print(f"ClassCard: Attempting to load UI file: {ui_file}, exists: {os.path.exists(ui_file)}")
        if not os.path.exists(ui_file):
            raise FileNotFoundError(f"UI file not found at {ui_file}")
        try:
            uic.loadUi(ui_file, self)
            print(f"ClassCard: Successfully loaded UI file: {ui_file}")
        except Exception as e:
            print(f"ClassCard: Failed to load UI file: {e}")
            raise
    
    def populate_data(self):
        try:
            code = self.class_data.get('code', 'CODE')
            self.course_code_label.setText(f"{code}")
            section = self.class_data.get('section', 'Section')
            self.course_code_section_label.setText(f"{section}")
            instructor = self.class_data.get('instructor', 'Instructor Name')
            self.instructor_label.setText(instructor)
            if instructor:
                initial = instructor[0].upper()
                self.profile_pic_label.setText(initial)
            recent_posts = self.class_data.get('recent_posts', 'No recent posts')
            self.recent_posts_label.setText(recent_posts)
            print("ClassCard: Successfully populated data")
        except AttributeError as e:
            print(f"ClassCard: Failed to populate data, missing UI elements: {e}")
            raise
    
    def setup_role_based_ui(self):
        try:
            if self.user_role == "student":
                self.options_button.hide()
            else:
                self.options_button.show()
            print(f"ClassCard: Set up role-based UI for {self.user_role}")
        except AttributeError as e:
            print(f"ClassCard: Failed to set up role-based UI, missing options_button: {e}")
            raise
    
    def connect_signals(self):
        try:
            self.options_button.clicked.connect(self.show_options_menu)
            self.mousePressEvent = self.card_clicked_event
            print("ClassCard: Successfully connected signals")
        except AttributeError as e:
            print(f"ClassCard: Failed to connect signals, missing options_button: {e}")
            raise
    
    def show_options_menu(self):
        try:
            menu = QMenu(self)
            menu.setStyleSheet("""
                QMenu {
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 4px 0px;
                }
                QMenu::item {
                    padding: 8px 16px;
                    font-size: 13px;
                }
                QMenu::item:selected {
                    background-color: #f5f5f5;
                }
            """)
            restore_action = QAction("Restore", self)
            delete_action = QAction("Delete", self)
            restore_action.triggered.connect(self.on_restore_clicked)
            delete_action.triggered.connect(self.on_delete_clicked)
            menu.addAction(restore_action)
            menu.addSeparator()
            menu.addAction(delete_action)
            button_pos = self.options_button.mapToGlobal(self.options_button.rect().bottomLeft())
            menu.exec(button_pos)
            print("ClassCard: Successfully showed options menu")
        except Exception as e:
            print(f"ClassCard: Failed to show options menu: {e}")
            raise
    
    def card_clicked_event(self, event):
        self.card_clicked.emit(self.class_data)
        super().mousePressEvent(event)
    
    def on_restore_clicked(self):
        self.restore_clicked.emit(self.class_data)
        print(f"ClassCard: Restore clicked: {self.class_data}")
    
    def on_delete_clicked(self):
        self.delete_clicked.emit(self.class_data)
        print(f"ClassCard: Delete clicked: {self.class_data}")

class ClassPage(QWidget):
    def __init__(self, class_data, user_role):
        super().__init__()
        self.class_data = class_data
        self.user_role = user_role
        self.setup_ui()

    def setup_ui(self):
        try:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            tab_widget = QTabWidget(self)
            tab_widget.setStyleSheet("""
                QTabWidget::pane {
                    border: none;
                }
                QTabBar::tab {
                    background: transparent;
                    border-bottom: 2px solid transparent;
                    padding: 8px 16px;
                    font-size: 16px;
                }
                QTabBar::tab:selected {
                    border-bottom: 2px solid #084924;
                    font-weight: bold;
                }
            """)
            if ClassroomStreamContent is None:
                raise ImportError("ClassroomStreamContent module not available")
            stream_tab = ClassroomStreamContent(self.class_data, self.user_role)
            tab_widget.addTab(stream_tab, "Stream")
            if ClassroomClassworksContent is None:
                raise ImportError("ClassroomClassworksContent module not available")
            classworks_tab = ClassroomClassworksContent(self.class_data, self.user_role)
            tab_widget.addTab(classworks_tab, "Classworks")
            layout.addWidget(tab_widget)
            print("ClassPage: Successfully set up UI")
        except Exception as e:
            print(f"ClassPage: Failed to set up UI: {e}")
            raise

class HomePage(QWidget):
    def __init__(self, user_role="student"):
        super().__init__()
        self.user_role = user_role
        try:
            self.setup_ui()
            print("HomePage: Successfully initialized")
        except Exception as e:
            print(f"HomePage: Initialization failed: {e}")
            raise
        
    def setup_ui(self):
        self.setMinimumSize(940, 530)
        self.stacked_widget = QStackedWidget(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stacked_widget)
        self.setStyleSheet("QWidget { background-color: white; }")
        home_widget = QWidget()
        home_layout = QVBoxLayout(home_widget)
        home_layout.setContentsMargins(20, 20, 20, 20)
        title = QLabel("My Classes")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #333;
                margin-bottom: 20px;
            }
        """)
        home_layout.addWidget(title)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: white; }")
        cards_container = QWidget()
        cards_layout = QGridLayout(cards_container)
        cards_layout.setSpacing(20)
        sample_classes = [
            {"code": "ITSD81", "section": "BSIT 3C", "instructor": "Neil John Jomaya", "class_id": 1},
            {"code": "IT59", "section": "BSIT 3A", "instructor": "John Doe", "class_id": 2},
            {"code": "IT95", "section": "BSIT 3A", "instructor": "JInky", "class_id": 3}
        ]
        row, col = 0, 0
        max_cols = 2
        for class_data in sample_classes:
            try:
                card = ClassCard(class_data, self.user_role)
                card.card_clicked.connect(self.on_card_clicked)
                card.restore_clicked.connect(self.on_restore_clicked)
                card.delete_clicked.connect(self.on_delete_clicked)
                cards_layout.addWidget(card, row, col)
                print(f"HomePage: Added ClassCard for {class_data['code']}")
            except Exception as e:
                print(f"HomePage: Failed to create ClassCard for {class_data['code']}: {e}")
                raise
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        scroll_area.setWidget(cards_container)
        home_layout.addWidget(scroll_area)
        self.stacked_widget.addWidget(home_widget)
        print("HomePage: Successfully set up UI")
    
    def on_card_clicked(self, class_data):
        try:
            class_page = ClassPage(class_data, self.user_role)
            self.stacked_widget.addWidget(class_page)
            self.stacked_widget.setCurrentWidget(class_page)
            print(f"HomePage: Navigated to ClassPage for {class_data['code']}")
        except Exception as e:
            print(f"HomePage: Failed to navigate to ClassPage: {e}")
            raise
    
    def on_restore_clicked(self, class_data):
        print(f"HomePage: Restore clicked: {class_data}")
    
    def on_delete_clicked(self, class_data):
        print(f"HomePage: Delete clicked: {class_data}")