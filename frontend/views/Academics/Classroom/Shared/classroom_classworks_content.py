from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QScrollArea, QSizePolicy, QSpacerItem, QMenu, QFrame, QStackedWidget, QComboBox
from PyQt6.QtGui import QAction, QPixmap
from PyQt6.QtCore import Qt, pyqtSignal
import os
from view_materials import ViewMaterial
from view_assessment import ViewAssessment

class ItemWidget(QWidget):
    def __init__(self, icon_path, title_text, date_text, parent=None):
        super().__init__(parent)
        self.setup_ui(icon_path, title_text, date_text)

    def setup_ui(self, icon_path, title_text, date_text):
        layout = QHBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        # Icon Label
        icon_label = QLabel(self)
        icon_label.setMinimumSize(32, 32)
        icon_label.setMaximumSize(38, 38)
        icon_label.setStyleSheet("""
            QLabel {
                background-color: #084924;
                border-radius: 19px;
                border: 2px solid white;
                overflow: hidden;
            }
        """)
        icon_label.setPixmap(QPixmap(icon_path).scaled(38, 38, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        icon_label.setScaledContents(True)
        layout.addWidget(icon_label)

        # Title Label
        title_label = QLabel(title_text, self)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 400;
                color: #24292f;
                border: none;
                background: transparent;
            }
        """)
        layout.addWidget(title_label)

        # Spacer
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout.addItem(spacer)

        # Date Label
        date_label = QLabel(date_text, self)
        date_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #656d76;
                border: none;
                background: transparent;
            }
        """)
        date_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(date_label)

        # Menu Button
        menu_button = QPushButton("⋮", self)
        menu_button.setMinimumSize(24, 24)
        menu_button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                font-size: 34px;
                color: #656d76;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #F3F4F6;
            }
        """)
        layout.addWidget(menu_button)

class TopicFrame(QFrame):
    post_clicked = pyqtSignal(dict)  # Signal to emit item data when clicked

    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.setObjectName(f"topicItemFrame_{id(self)}")  # Unique object name
        self.setMinimumSize(800, 70)
        self.setMaximumHeight(70)  # Limit height per item
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #084924;
                border-radius: 20px;
                margin-left: 20px;
            }
            QFrame:hover {
                background-color: #F8F9FA;
                border-color: #D0D7DE;
            }
        """)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.icon_path, self.title, self.date = item_data  # Store item data
        self.setup_ui(item_data)

    def setup_ui(self, item_data):
        layout = QHBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(10, 5, 10, 5)  # Match UI margins

        # Icon Label
        icon_label = QLabel(self)
        icon_label.setMinimumSize(32, 32)
        icon_label.setMaximumSize(38, 38)
        icon_label.setStyleSheet("""
            QLabel {
                background-color: #084924;
                border-radius: 19px;
                border: 2px solid white;
                overflow: hidden;
            }
        """)
        icon_label.setPixmap(QPixmap(self.icon_path).scaled(38, 38, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        icon_label.setScaledContents(True)
        layout.addWidget(icon_label)

        # Title Label
        title_label = QLabel(self.title, self)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 400;
                color: #24292f;
                border: none;
                background: transparent;
            }
        """)
        layout.addWidget(title_label)

        # Spacer
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout.addItem(spacer)

        # Date Label
        date_label = QLabel(self.date, self)
        date_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #656d76;
                border: none;
                background: transparent;
            }
        """)
        date_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(date_label)

        # Menu Button
        menu_button = QPushButton("⋮", self)
        menu_button.setMinimumSize(24, 24)
        menu_button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                font-size: 34px;
                color: #656d76;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #F3F4F6;
            }
        """)
        layout.addWidget(menu_button)

        # Make the entire frame clickable
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        """Emit signal when the frame is clicked"""
        if event.button() == Qt.MouseButton.LeftButton:
            print(f"Clicked: {self.title}")  # Debug print
            post_type = "material" if "Guidelines" in self.title or "Chapter" in self.title else "assessment"
            post_data = {
                "type": post_type,
                "title": self.title,
                "instructor": "Carlos Fidel Castro",
                "date": self.date.replace("Posted ", ""),
                "description": f"Details for {self.title}",
                "attachment": f"{self.title.lower().replace(' ', '_')}.pdf",
                "score": "10" if post_type == "assessment" else None
            }
            self.post_clicked.emit(post_data)
        super().mousePressEvent(event)

class TopicWidget(QWidget):
    def __init__(self, topic_title, items_data, parent_content, parent=None):
        super().__init__(parent)
        self.parent_content = parent_content  # Reference to ClassroomClassworksContent
        self.title_label = None  # Store reference to title label
        self.frames = []  # Store frames for filtering
        self.setup_ui(topic_title, items_data)

    def setup_ui(self, topic_title, items_data):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove extra margin, handled by frame

        # Topic Title (match topicTitle from UI)
        self.title_label = QLabel(topic_title, self)
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 40px;
                font-weight: 400;
                margin-left: 20px;
                margin-top: 20px;
                margin-bottom: -10px;
            }
        """)
        layout.addWidget(self.title_label)

        # Separator (mimic UI separator)
        separator = QFrame(self)
        separator.setMinimumSize(800, 1)
        separator.setMaximumHeight(1)
        separator.setStyleSheet("""
            QFrame {
                border: 1px solid #A9A9A9;
                background-color: transparent;
                margin-left: 20px;
            }
        """)
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # Add item frames
        for item_data in items_data:
            topic_frame = TopicFrame(item_data)
            self.frames.append(topic_frame)
            layout.addWidget(topic_frame)
            topic_frame.post_clicked.connect(self.parent_content.open_post_details)

class ClassroomClassworksContent(QWidget):
    def __init__(self, class_data, user_role):
        super().__init__()
        self.class_data = class_data
        self.user_role = user_role
        self.untitled_frames = []  # Store untitled frames for filtering
        self.topic_widgets = []  # Store topic widgets for filtering
        self.current_post_data = None  # Store current post data for page switching
        self.material_view = None  # Store ViewMaterial widget
        self.assessment_view = None  # Store ViewAssessment widget
        self.material_index = None
        self.assessment_index = None
        self.main_content = None
        self.load_ui()
        self.setup_role_based_ui()
        self.populate_data()

    def load_ui(self):
        """Load the ClassroomClassworksContent UI file into a main content widget"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(current_dir, '../../../../../ui/Classroom/classroom_classworks_content.ui')
        self.main_content = QWidget()
        uic.loadUi(ui_file, self.main_content)
        
        # Assign references to main widgets
        self.filterComboBox = self.main_content.findChild(QComboBox, "filterComboBox")
        self.topicScrollArea = self.main_content.findChild(QScrollArea, "topicScrollArea")
        self.createButton = self.main_content.findChild(QPushButton, "createButton")
        
        if self.filterComboBox:
            self.filterComboBox.currentTextChanged.connect(self.filter_posts)
        
        # Create stacked widget and main layout
        self.stackedWidget = QStackedWidget(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stackedWidget)
        
        # Add main content as index 0
        self.stackedWidget.addWidget(self.main_content)
        self.stackedWidget.setCurrentIndex(0)

    def setup_role_based_ui(self):
        """Setup UI elements based on user role"""
        if self.createButton:
            if self.user_role == "student":
                self.createButton.hide()
            else:
                self.createButton.show()
                self.createButton.clicked.connect(self.show_create_menu)

    def show_create_menu(self):
        """Show menu for creating material, assessment, or topic"""
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
        
        material_action = QAction("Material", self)
        assessment_action = QAction("Assessment", self)
        topic_action = QAction("Topic", self)
        
        material_action.triggered.connect(self.create_material)
        assessment_action.triggered.connect(self.create_assessment)
        topic_action.triggered.connect(self.create_topic)
        
        menu.addAction(material_action)
        menu.addAction(assessment_action)
        menu.addAction(topic_action)
        
        button_pos = self.createButton.mapToGlobal(self.createButton.rect().bottomLeft())
        menu.exec(button_pos)

    def create_material(self):
        """Handle create material (placeholder)"""
        print("Creating Material")

    def create_assessment(self):
        """Handle create assessment (placeholder)"""
        print("Creating Assessment")

    def create_topic(self):
        """Handle create topic (placeholder)"""
        print("Creating Topic")

    def populate_data(self):
        """Populate with hardcoded data and add multiple topics with items"""
        if not self.topicScrollArea:
            return
        
        # Hardcoded posts, including untitled ones
        untitled_posts = [
            (":/icons/document.svg", "Desktop Project Guidelines", "Posted Aug 18")
        ]
        topics_data = [
            ("Lecture: Topic 1", [
                (":/icons/document.svg", "Chapter 2: Basics", "Posted Aug 25")
            ]),
            ("Lecture: Topic 2", [
                (":/icons/document.svg", "Chapter 3: Advanced Concepts", "Posted Sep 1"),
                (":/icons/document.svg", "Midterm Exam", "Posted Sep 8")
            ])
        ]

        # Get the layout for adding topics (topicListLayout in topicScrollArea widget)
        scroll_widget = self.topicScrollArea.widget()
        if scroll_widget:
            topic_layout = scroll_widget.layout()  # topicListLayout
            if topic_layout:
                # Clear all existing widgets
                for i in reversed(range(topic_layout.count())):
                    item = topic_layout.itemAt(i)
                    if item:
                        widget = item.widget()
                        if widget:
                            topic_layout.removeWidget(widget)
                            widget.deleteLater()

                # Populate filter combo box
                if self.filterComboBox:
                    self.filterComboBox.clear()
                    self.filterComboBox.addItem("All")
                    self.filterComboBox.addItem("Materials")
                    self.filterComboBox.addItem("Assessments")
                    for topic_title, _ in topics_data:
                        self.filterComboBox.addItem(topic_title)

                # Add untitled posts as standalone frames at the top
                for item_data in untitled_posts:
                    topic_frame = TopicFrame(item_data)
                    self.untitled_frames.append(topic_frame)
                    topic_layout.addWidget(topic_frame)
                    topic_frame.post_clicked.connect(self.open_post_details)

                # Add topic-based posts
                for topic_title, items_data in topics_data:
                    topic_widget = TopicWidget(topic_title, items_data, self)
                    self.topic_widgets.append(topic_widget)
                    topic_layout.addWidget(topic_widget)

                # Add a spacer at the end for expansion
                spacer = QWidget()
                spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                topic_layout.addWidget(spacer)

    def filter_posts(self, filter_text):
        """Filter posts based on the selected combo box item"""
        if not filter_text:
            return

        # Show all by default
        for frame in self.untitled_frames:
            frame.setVisible(True)
        for widget in self.topic_widgets:
            widget.setVisible(True)
            for frame in widget.frames:
                frame.setVisible(True)

        # Apply filter
        if filter_text == "All":
            pass  # All are already visible
        elif filter_text == "Materials":
            for frame in self.untitled_frames:
                frame.setVisible("material" in self.get_post_type(frame.title))
            for widget in self.topic_widgets:
                has_materials = any("material" in self.get_post_type(frame.title) for frame in widget.frames)
                widget.setVisible(has_materials)
                for frame in widget.frames:
                    frame.setVisible("material" in self.get_post_type(frame.title))
        elif filter_text == "Assessments":
            for frame in self.untitled_frames:
                frame.setVisible("assessment" in self.get_post_type(frame.title))
            for widget in self.topic_widgets:
                has_assessments = any("assessment" in self.get_post_type(frame.title) for frame in widget.frames)
                widget.setVisible(has_assessments)
                for frame in widget.frames:
                    frame.setVisible("assessment" in self.get_post_type(frame.title))
        else:  # Topic filter
            for frame in self.untitled_frames:
                frame.setVisible(False)
            for widget in self.topic_widgets:
                widget.setVisible(widget.title_label.text() == filter_text)
                if widget.isVisible():
                    for frame in widget.frames:
                        frame.setVisible(True)

    def get_post_type(self, title):
        """Determine post type based on title"""
        return "material" if "Guidelines" in title or "Chapter" in title else "assessment"

    def open_post_details(self, post_data):
        """Switch to the appropriate page in the stacked widget with post details"""
        self.current_post_data = post_data

        # Initialize or update ViewMaterial page
        if post_data["type"] == "material":
            if self.material_view is None:
                self.material_view = ViewMaterial(post_data, self.user_role)
                self.material_view.back_clicked.connect(self.back_to_main)  # Connect back signal
                self.material_index = self.stackedWidget.addWidget(self.material_view)
            else:
                self.material_view.update_data(post_data)  # Update existing widget
            self.stackedWidget.setCurrentIndex(self.material_index)

        # Initialize or update ViewAssessment page
        elif post_data["type"] == "assessment":
            if self.assessment_view is None:
                self.assessment_view = ViewAssessment(post_data, self.user_role)
                self.assessment_view.back_clicked.connect(self.back_to_main)  # Connect back signal
                self.assessment_index = self.stackedWidget.addWidget(self.assessment_view)
            else:
                self.assessment_view.update_data(post_data)  # Update existing widget
            self.stackedWidget.setCurrentIndex(self.assessment_index)

    def back_to_main(self):
        """Switch back to the main content page (index 0)"""
        self.stackedWidget.setCurrentIndex(0)

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    classworks_page = ClassroomClassworksContent({"class_id": 1}, "faculty")
    classworks_page.setFixedSize(940, 530)
    classworks_page.show()
    sys.exit(app.exec())