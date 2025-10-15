# classroom_classworks.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QComboBox, QDialog, QLineEdit, QTextEdit, QPushButton, QMenu, QToolButton, QFrame, QScrollArea, QSizePolicy, QSpacerItem
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QIcon, QFont, QFontDatabase, QAction
from widgets.Academics.classroom_classworks_content_ui import Ui_ClassroomClassworksContent
from widgets.Academics.topic_widget import TopicWidget
from typing import Optional, Dict
import os
import datetime

try:
    from frontend.views.Academics.Classroom.Faculty.upload_materials import MaterialForm
    from frontend.views.Academics.Classroom.Faculty.create_assessment import AssessmentForm
except ImportError:
    try:
        from upload_materials import MaterialForm
        from create_assessment import AssessmentForm
    except ImportError:
        class MaterialForm(QWidget):
            def __init__(self, cls=None, username=None, roles=None, primary_role=None, token=None, post_controller=None, parent=None):
                super().__init__(parent)
                layout = QVBoxLayout(self)
                layout.addWidget(QLabel(f"Material Form for {cls.get('title', 'Unknown Class') if cls else 'Unknown Class'}"))
                
        class AssessmentForm(QWidget):
            def __init__(self, cls=None, username=None, roles=None, primary_role=None, token=None, post_controller=None, parent=None):
                super().__init__(parent)
                layout = QVBoxLayout(self)
                layout.addWidget(QLabel(f"Assessment Form for {cls.get('title', 'Unknown Class') if cls else 'Unknown Class'}"))

class ClassroomClassworks(QWidget):
    post_selected = pyqtSignal(dict)
    post_created = pyqtSignal() 
    navigate_to_form = pyqtSignal(str, object)
    syllabus_created = pyqtSignal()  # ADD THIS NEW SIGNAL

    def __init__(self, cls, username, roles, primary_role, token, post_controller, parent=None):
        super().__init__(parent)
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        self.ui = Ui_ClassroomClassworksContent()
        self.ui.setupUi(self)
        self.cls = cls
        self.post_controller = post_controller
        self.post_controller.set_class(cls["id"])
        self.topic_widgets = []
        self.untitled_frames = []
        
        # Load Poppins font
        self.load_poppins_font()
        
        self.setup_styles()
        self.setup_role_based_ui()
        self.setup_filter()
        self.connect_signals()
        self.initialize_layout()
        self.load_posts()

    def setup_styles(self):
        """Setup consistent styling matching Students layout"""
        self.setStyleSheet("""
            ClassroomClassworks {
                background-color: white;
                font-family: "Poppins", Arial, sans-serif;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QToolButton {
                background-color: #084924;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 5px;
                font-weight: 400;
                font-size: 11px;
                font-family: "Poppins", Arial, sans-serif;
            }
            QToolButton:hover {
                background-color: #1B5E20;
            }
            QToolButton:pressed {
                background-color: #0D4E12;
            }
            QComboBox {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 8px 12px;
                background-color: white;
                font-size: 12px;
                font-family: "Poppins", Arial, sans-serif;
                min-height: 35px;
            }
            QComboBox:hover {
                border-color: #A8A8A8;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            QComboBox::down-arrow {
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #666;
            }
        """)

    def load_poppins_font(self):
        """Load Poppins font if available"""
        try:
            font_paths = [
                "frontend/assets/fonts/Poppins-Regular.ttf",
                "assets/fonts/Poppins-Regular.ttf",
                "fonts/Poppins-Regular.ttf",
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font_id = QFontDatabase.addApplicationFont(font_path)
                    if font_id != -1:
                        print(f"Successfully loaded Poppins font from {font_path}")
                    break
            else:
                print("Poppins font not found, using system font")
        except Exception as e:
            print(f"Error loading Poppins font: {e}")

    def initialize_layout(self):
        """Properly initialize the scroll area layout"""
        scroll_widget = self.ui.scrollAreaWidgetContents
        if scroll_widget.layout() is None:
            scroll_widget.setLayout(QVBoxLayout())
        else:
            layout = scroll_widget.layout()
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

    def _load_icon(self, path):
        icon = QIcon()
        full_path = os.path.join("frontend", "assets", "icons", path)
        if os.path.exists(full_path):
            icon.addPixmap(QPixmap(full_path), QIcon.Mode.Normal, QIcon.State.Off)
        else:
            print(f"Icon file not found: {full_path}")
            icon = QIcon.fromTheme("list-add")
        return icon
    

    def setup_role_based_ui(self):
        if self.primary_role == "student":
            self.ui.createButton.hide()
        else:
            self.ui.createButton.show()
            self.ui.createButton.setIcon(self._load_icon("baseline-add.svg"))
            self.ui.createButton.setIconSize(QSize(19, 19))
            self.ui.createButton.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
            self.ui.createButton.setStyleSheet("""
                QToolButton {
                    background-color: #084924;
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 23px;
                    font-weight: 600;
                    font-size: 16px;
                    min-width: 90px;
                    min-height: 30px;
                    font-family: "Poppins", Arial, sans-serif;
                }
                QToolButton:hover {
                    background-color: #1B5E20;
                }
                QToolButton:pressed {
                    background-color: #0D4E12;
                }
                QToolButton::menu-arrow {
                    image: none;
                    width: 0px;
                }
                QToolButton::menu-button {
                    border: none;
                    background: transparent;
                    width: 0px;
                }
            """)

    def connect_signals(self):
        self.ui.filterComboBox.currentTextChanged.connect(self.filter_posts)
        self.ui.createButton.clicked.connect(self.show_create_menu)

    def setup_filter(self):
        """Setup filter combo box using PostController"""
        self.ui.filterComboBox.clear()
        self.ui.filterComboBox.addItem("All items")
        self.ui.filterComboBox.addItem("Material")
        self.ui.filterComboBox.addItem("Assessment")
        
        topics = self.post_controller.get_available_topics()
        unique_topics = sorted(list(set(topics)))
        
        for topic in unique_topics:
            if topic:
                self.ui.filterComboBox.addItem(topic)

    def show_create_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 4px 0px;
                font-family: "Poppins", Arial, sans-serif;
            }
            QMenu::item {
                padding: 8px 16px;
                font-size: 13px;
                color: black;
            }
            QMenu::item:selected {
                background-color: #f5f5f5;
            }
        """)
        
        material_action = QAction("Material", self)
        assessment_action = QAction("Assessment", self)
        syllabus_action = QAction("Syllabus", self)
        topic_action = QAction("Topic", self)
        
        material_action.triggered.connect(lambda: self.create_item("material"))
        assessment_action.triggered.connect(lambda: self.create_item("assessment"))
        syllabus_action.triggered.connect(lambda: self.create_item("syllabus"))
        topic_action.triggered.connect(lambda: self.create_item("topic"))
        
        menu.addAction(material_action)
        menu.addAction(assessment_action)
        menu.addAction(syllabus_action)
        menu.addAction(topic_action)
        
        button_pos = self.ui.createButton.mapToGlobal(self.ui.createButton.rect().bottomLeft())
        menu.exec(button_pos)

    def create_item(self, item_type):
        if item_type == "topic":
            self.create_topic()
        elif item_type == "syllabus":
            self.create_syllabus()
        else:
            self.navigate_to_create_form(item_type)

    def create_syllabus(self):
        """Create syllabus dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Create Syllabus")
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
                font-family: "Poppins", Arial, sans-serif;
            }
        """)
        dialog.setModal(True)
        dialog.setFixedSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        title_label = QLabel("Syllabus Title:")
        title_label.setStyleSheet("font-family: 'Poppins', Arial, sans-serif;")
        title_input = QLineEdit()
        title_input.setText("Syllabus")
        title_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 8px;
                font-family: "Poppins", Arial, sans-serif;
            }
        """)
        layout.addWidget(title_label)
        layout.addWidget(title_input)
        
        content_label = QLabel("Syllabus Content:")
        content_label.setStyleSheet("font-family: 'Poppins', Arial, sans-serif;")
        content_input = QTextEdit()
        content_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 8px;
                font-family: "Poppins", Arial, sans-serif;
            }
        """)
        layout.addWidget(content_label)
        layout.addWidget(content_input)
        
        button_layout = QHBoxLayout()
        create_btn = QPushButton("Create Syllabus")
        cancel_btn = QPushButton("Cancel")
        
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #084924;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-family: "Poppins", Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #1B5E20;
            }
        """)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #666;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-family: "Poppins", Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #777;
            }
        """)
        
        create_btn.clicked.connect(lambda: self.handle_create_syllabus(
            title_input.text(), 
            content_input.toPlainText(), 
            dialog
        ))
        cancel_btn.clicked.connect(dialog.reject)
        
        button_layout.addWidget(create_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        dialog.exec()

    def navigate_to_create_form(self, form_type):
        """Navigate to the appropriate creation form"""
        self.navigate_to_form.emit(form_type, self.cls)
        print(f"Requesting {form_type} form for class: {self.cls.get('title', 'Unknown')}")

    def create_topic(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Create Topic")
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
                font-family: "Poppins", Arial, sans-serif;
            }
        """)
        dialog.setModal(True)
        dialog.setFixedSize(400, 200)
        
        layout = QVBoxLayout(dialog)
        
        title_label = QLabel("Title:")
        title_label.setStyleSheet("font-family: 'Poppins', Arial, sans-serif;")
        title_input = QLineEdit()
        title_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 8px;
                font-family: "Poppins", Arial, sans-serif;
            }
        """)
        layout.addWidget(title_label)
        layout.addWidget(title_input)
        
        type_label = QLabel("Type:")
        type_label.setStyleSheet("font-family: 'Poppins', Arial, sans-serif;")
        type_combo = QComboBox()
        type_combo.addItems(["material", "assessment"])
        type_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 8px;
                font-family: "Poppins", Arial, sans-serif;
            }
        """)
        layout.addWidget(type_label)
        layout.addWidget(type_combo)
        
        button_layout = QHBoxLayout()
        create_btn = QPushButton("Create")
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #084924;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-family: "Poppins", Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #1B5E20;
            }
        """)
        create_btn.clicked.connect(lambda: self.handle_create_topic(title_input.text(), type_combo.currentText(), dialog))
        button_layout.addWidget(create_btn)
        
        layout.addLayout(button_layout)
        dialog.exec()

    def handle_create_syllabus(self, title, content, dialog):
        """Handle syllabus creation"""
        if not title or not content:
            print("Syllabus title and content are required")
            return
        
        if self.post_controller.create_syllabus(
            title=title,
            content=content,
            author=self.username
        ):
            print("Syllabus created successfully")
            self.refresh_posts()
            # EMIT THE SYLLABUS CREATED SIGNAL
            self.syllabus_created.emit()
            if hasattr(self, 'stream_view'):
                self.stream_view.refresh_syllabus()
            dialog.accept()
        else:
            print("Failed to create syllabus")

    def handle_create_topic(self, title, type_, dialog):
        if not title:
            print("Topic title is required")
            return
        
        if self.post_controller.create_topic(title, type_):
            print("Topic created successfully")
            self.setup_filter()
            self.load_posts()
            dialog.accept()
        else:
            print("Failed to create topic")

    def set_stream_reference(self, stream_view):
        self.stream_view = stream_view

    def handle_create_content(self, title, content, type_, topic_name, dialog):
        if not title or not content:
            print("Title and content are required")
            return
        
        author = self.username
        
        if self.post_controller.create_post(title, content, type_, author, topic_name):
            print(f"{type_.capitalize()} created successfully")
            self.load_posts(self.ui.filterComboBox.currentText())
            self.post_created.emit()
            dialog.accept()
        else:
            print(f"Failed to create {type_}")

    def refresh_posts(self):
        """Refresh posts when new ones are created"""
        self.load_posts(self.ui.filterComboBox.currentText())

    # classroom_classworks.py

    def format_date(self, date_str):
        """Format date string for display - same as in classroom_stream.py"""
        if not date_str:
            return ""
        
        # If it's already in "Oct 14" format, return as is
        if len(date_str) <= 6 and any(month in date_str.lower() for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
            return date_str
        
        # Try multiple date formats
        date_formats = [
            "%Y-%m-%d %H:%M:%S",    # 2025-08-18 10:00:00
            "%Y-%m-%dT%H:%M:%S",    # 2025-10-10T01:35:06 (ISO format)
            "%Y-%m-%d",             # 2025-08-18
            "%b %d",                # Oct 14 (already formatted)
            "%d/%m/%Y",             # 16/10/2025
            "%m/%d/%Y"              # 10/16/2025
        ]
        
        for fmt in date_formats:
            try:
                from datetime import datetime
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%b %d")  # Format to "Oct 16"
            except ValueError:
                continue
        
        # If all parsing fails, return the original string or part of it
        return date_str.split(" ")[0] if " " in date_str else date_str    

    def load_posts(self, filter_topic=None):
        """Load posts using PostController with clean layout"""
        filter_type = None
        topic_name = None
        if filter_topic == "Material":
            filter_type = "material"
        elif filter_topic == "Assessment":
            filter_type = "assessment"
        elif filter_topic not in ["All items", "Material", "Assessment"]:
            topic_name = filter_topic
        
        self.post_controller.set_filters(filter_type=filter_type, topic_name=topic_name)
        posts = self.post_controller.get_classwork_posts()

        # Format dates for display
        for post in posts:
            if 'date' in post:
                post['display_date'] = self.format_date(post['date'])
            elif 'date_posted' in post:
                post['display_date'] = self.format_date(post['date_posted'])
            else:
                post['display_date'] = ""
        
        try:
            posts.sort(key=lambda x: x.get('date', ''), reverse=True)
        except:
            pass
        
        scroll_widget = self.ui.scrollAreaWidgetContents
        layout = scroll_widget.layout()
        
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.topic_widgets.clear()
        self.untitled_frames.clear()
        
        if posts:
            grouped = {}
            for post in posts:
                topic_title = "Untitled"
                if post.get("topic_id"):
                    topic = self.post_controller.get_topic_by_id(post["topic_id"])
                    if topic:
                        topic_title = topic.get("title", "Untitled")
                
                grouped.setdefault(topic_title, []).append(post)
            
            for topic_title in grouped:
                grouped[topic_title].sort(key=lambda x: x.get('date', ''), reverse=True)
            
            sorted_groups = sorted(grouped.items(), 
                                key=lambda x: (x[0] != "Untitled", x[0] if x[0] != "Untitled" else ""))
            
            for topic_title, topic_posts in sorted_groups:
                if topic_title == "Untitled":
                    for post in topic_posts:
                        from frontend.widgets.Academics.topic_frame import TopicFrame
                        frame = TopicFrame(post, self.post_controller, self.primary_role)
                        frame.post_clicked.connect(self.post_selected.emit)
                        
                        # Apply consistent styling
                        frame.setStyleSheet("""
                            QFrame {
                                background-color: white;
                                border: 1px solid #E0E0E0;
                                border-radius: 20px;
                                margin-left: 20px;
                            }
                            QFrame:hover {
                                background-color: #F8F9FA;
                                border-color: #D0D7DE;
                            }
                        """)
                        
                        layout.addWidget(frame)
                        self.untitled_frames.append(frame)
                else:
                    from frontend.widgets.Academics.topic_widget import TopicWidget
                    topic_widget = TopicWidget(topic_title, topic_posts, self.post_controller, self.primary_role)
                    
                    # Apply consistent topic header styling
                    topic_widget.title_label.setStyleSheet("""
                        QLabel {
                            font-size: 24px;
                            font-weight: 400;
                            margin-left: 20px;
                            margin-top: 10px;
                            margin-bottom: 5px;
                            color: #000000;
                            background-color: transparent;
                            font-family: "Poppins", Arial, sans-serif;
                        }
                    """)
                    
                    for frame in topic_widget.frames:
                        frame.post_clicked.connect(self.post_selected.emit)
                        # Apply consistent frame styling
                        frame.setStyleSheet("""
                            QFrame {
                                background-color: white;
                                border: 1px solid #E0E0E0;
                                border-radius: 20px;
                                margin-left: 20px;
                            }
                            QFrame:hover {
                                background-color: #F8F9FA;
                                border-color: #D0D7DE;
                            }
                        """)
                    
                    layout.addWidget(topic_widget)
                    self.topic_widgets.append(topic_widget)
        
        else:
            # No posts message
            no_posts_label = QLabel("No classworks available")
            no_posts_label.setStyleSheet("""
                QLabel {
                    color: #666;
                    font-size: 16px;
                    padding: 50px;
                    text-align: center;
                    font-family: "Poppins", Arial, sans-serif;
                }
            """)
            no_posts_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_posts_label)
        
        layout.addStretch()

    def filter_posts(self, filter_text):
        """Filter posts based on selection"""
        if not filter_text:
            return
        
        # Show all first
        for topic_widget in self.topic_widgets:
            topic_widget.setVisible(True)
            for frame in topic_widget.frames:
                frame.setVisible(True)
        
        for frame in self.untitled_frames:
            frame.setVisible(True)
        
        # Apply filters
        if filter_text == "All items":
            return
        
        elif filter_text == "Material":
            for frame in self.untitled_frames:
                frame.setVisible(frame.post["type"] == "material")
            
            for widget in self.topic_widgets:
                has_materials = any(f.post["type"] == "material" for f in widget.frames)
                widget.setVisible(has_materials)
                if widget.isVisible():
                    for frame in widget.frames:
                        frame.setVisible(frame.post["type"] == "material")
        
        elif filter_text == "Assessment":
            for frame in self.untitled_frames:
                frame.setVisible(frame.post["type"] == "assessment")
            
            for widget in self.topic_widgets:
                has_assessments = any(f.post["type"] == "assessment" for f in widget.frames)
                widget.setVisible(has_assessments)
                if widget.isVisible():
                    for frame in widget.frames:
                        frame.setVisible(frame.post["type"] == "assessment")
        
        else:  # Topic filter
            for frame in self.untitled_frames:
                frame.setVisible(False)
            
            for widget in self.topic_widgets:
                widget.setVisible(widget.title_label.text() == filter_text)
                if widget.isVisible():
                    for frame in widget.frames:
                        frame.setVisible(True)

    def clear(self):
        """Clean up method"""
        self.ui.filterComboBox.clear()
        layout = self.ui.scrollAreaWidgetContents.layout()
        if layout:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()