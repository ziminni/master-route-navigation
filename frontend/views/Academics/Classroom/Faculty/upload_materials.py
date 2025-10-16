import sys
import os
import json
from datetime import datetime

project_root = (os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PyQt6.QtWidgets import (
    QApplication, 
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout, 
    QLabel, 
    QPushButton, 
    QFrame, 
    QSizePolicy, 
    QScrollArea,
    QMessageBox  # ADDED for success/error messages
)

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
from frontend.widgets.Academics.labeled_section import LabeledSection
from frontend.widgets.Academics.dropdown import DropdownMenu
from frontend.widgets.Academics.upload_class_material_widget import UploadClassMaterialPanel

class MaterialForm(QWidget):
    back_clicked = pyqtSignal()
    material_created = pyqtSignal(dict)  # ADDED: Signal when material is created

    def __init__(self, cls=None, username=None, roles=None, primary_role=None, token=None, post_controller=None, parent=None):
        super().__init__(parent)
        self.cls = cls
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        self.post_controller = post_controller
        
        # ADDED: Data file paths
        self.classroom_data_path = "services/Academics/data/classroom_data.json"
        self.posts_data_path = "services/Academics/data/classroom_data.json"
        
        self.initUI()
        self.load_topics()  # ADDED: Load topics for dropdown
        
    def initUI(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("QScrollArea {\n"
        "       border: none;\n"
        "       background-color: transparent;\n"
        "   }\n"
        "   QScrollBar:vertical {\n"
        "       border: none;\n"
        "       background: #F1F1F1;\n"
        "       width: 8px;\n"
        "       border-radius: 4px;\n"
        "   }\n"
        "   QScrollBar::handle:vertical {\n"
        "       background: #C1C1C1;\n"
        "       border-radius: 4px;\n"
        "       min-height: 20px;\n"
        "   }")
        
        content_widget = QWidget()
        content_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        header = self.create_header()
        body = self.create_body()
        
        content_layout.addWidget(header)
        content_layout.addWidget(body, 1)
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

    def create_header(self):
        frame = QFrame()
        header_layout = QHBoxLayout(frame)
        header_layout.setContentsMargins(0, 0, 0, 0)

        back_button = QPushButton("<")
        back_button.setFixedSize(40, 40)
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #000000;
                font-size: 20px;
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 5px;
            }               
            QPushButton:hover {
                background-color: #f0f0f0;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
            }
        """)
        back_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        back_button.clicked.connect(self.back_clicked)

        back_label = QLabel("Material")
        back_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #333;
                border: none;
                margin-left: 15px;
            }
        """)

        header_layout.addWidget(back_button)
        header_layout.addWidget(back_label)
        header_layout.addStretch()

        return frame
    
    def create_body(self):
        body_widget = QWidget()
        body_layout = QHBoxLayout(body_widget)
        body_layout.setSpacing(20)
        body_layout.setContentsMargins(0, 0, 0, 0)
        
        left_panel = self.create_left_panel()
        left_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        right_panel = self.create_right_panel()
        right_panel.setMinimumWidth(280)
        right_panel.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding)
        
        body_layout.addWidget(left_panel, 3)
        body_layout.addWidget(right_panel, 1)
        
        return body_widget
    
    def create_left_panel(self):
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(0)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # CHANGED: Store reference and connect signal
        self.upload_panel = UploadClassMaterialPanel()
        self.upload_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.upload_panel.upload_clicked.connect(self.handle_upload)  # ADDED: Connect upload signal
        
        left_layout.addWidget(self.upload_panel)
        return left_widget
    
    def create_right_panel(self):
        right_frame = QFrame()
        right_frame.setMinimumWidth(280)
        right_frame.setMaximumWidth(400)
        right_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #084924;
            } 
            LabeledSection {
                border: none;                      
            }
        """)
        
        layout = QVBoxLayout(right_frame)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 25, 20, 25)

        # Class dropdown
        class_name = self.cls.get('code', 'ITSD81') if self.cls else 'ITSD81'
        self.audience_dropdown = DropdownMenu(items=[class_name])
        layout.addWidget(LabeledSection("For", self.audience_dropdown))

        # Assigned Students Dropdown
        self.assigned_dropdown = DropdownMenu(items=["All Students"])
        layout.addWidget(LabeledSection("Assigned", self.assigned_dropdown))

        # Topic Dropdown - CHANGED: Store reference
        self.topic_dropdown = DropdownMenu(items=["No Topic"])
        layout.addWidget(LabeledSection("Topic", self.topic_dropdown))

        layout.addStretch()
        return right_frame

    # ADDED: Load topics from data file
    def load_topics(self):
        """Load topics from classroom data"""
        try:
            with open(self.classroom_data_path, 'r') as f:
                data = json.load(f)
            
            topics = data.get('topics', [])
            class_id = self.cls.get('id') if self.cls else 1
            
            # Filter topics for this class and type material
            class_topics = [t for t in topics if t.get('class_id') == class_id and t.get('type') == 'material']
            
            # Update dropdown
            topic_items = ["No Topic"] + [t.get('title', 'Untitled') for t in class_topics]
            self.topic_dropdown.clear()
            for item in topic_items:
                self.topic_dropdown.addItem(item)
                
        except Exception as e:
            print(f"Error loading topics: {e}")

    # ADDED: Handle upload
    def handle_upload(self):
        """Handle the upload when button is clicked"""
        # Get material data from the panel
        material_data = self.upload_panel.get_material_data()
        
        # Get selected topic
        selected_topic = self.topic_dropdown.currentText()
        topic_id = None
        if selected_topic != "No Topic":
            topic_id = self.get_topic_id(selected_topic)
        
        # Create post data
        new_post = self.create_post_data(material_data, topic_id)
        
        # Save to data files
        if self.save_post(new_post):
            QMessageBox.information(self, "Success", "Material uploaded successfully!")
            self.material_created.emit(new_post)
            self.upload_panel.clear_form()
            self.back_clicked.emit()
        else:
            QMessageBox.warning(self, "Error", "Failed to upload material. Please try again.")

    # ADDED: Get topic ID
    def get_topic_id(self, topic_title):
        """Get topic ID from title"""
        try:
            with open(self.classroom_data_path, 'r') as f:
                data = json.load(f)
            
            topics = data.get('topics', [])
            for topic in topics:
                if topic.get('title') == topic_title:
                    return topic.get('id')
            return None
        except:
            return None

    def format_date(self, date_str):
        """Format date string for display - same as in classroom_stream.py"""
        if not date_str:
            return ""
        try:
            # Convert "2025-08-18 10:00:00" to "Aug 18"
            from datetime import datetime
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%b %d")
        except:
            # If parsing fails, try alternative formats
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                return dt.strftime("%b %d")
            except:
                return date_str.split(" ")[0] if " " in date_str else date_str
        
    # ADDED: Create post data structure
    def create_post_data(self, material_data, topic_id):
        """Create post data matching JSON format"""
        next_id = self.get_next_post_id()
        
        now = datetime.now()
        # Use the format that works with the format_date function
        created_at = now.strftime("%Y-%m-%d %H:%M:%S")  # This format: "2025-10-16 14:30:00"
        date_posted = self.format_date(created_at)  # This should give "Oct 16"
        
        # For posts.json format
        post = {
            "post_id": next_id,
            "class_id": self.cls.get('id') if self.cls else 1,
            "topic_id": topic_id,
            "type": "material",  # or "assessment" for assessment form
            "title": material_data['title'],
            "description": material_data['description'],
            "instructor": self.username or "Unknown Instructor",
            "instructor_id": "faculty_001",
            "date_posted": date_posted,  # This should be in "Oct 16" format
            "status": "published",
            "created_at": created_at,  # Keep full format for internal use
            "updated_at": created_at
        }
        
        if material_data.get('attachment'):
            post['attachment'] = {
                "filename": material_data['attachment']['name'],
                "file_type": material_data['attachment']['type'].lower(),
                "file_path": material_data['attachment']['file_path']
            }
        
        return post
    # ADDED: Get next post ID
    def get_next_post_id(self):
        """Get the next available post ID"""
        try:
            with open(self.posts_data_path, 'r') as f:
                data = json.load(f)
            
            posts = data.get('posts', [])
            if not posts:
                return 1
            
            max_id = max(p.get('post_id', 0) for p in posts)
            return max_id + 1
        except:
            return 1

    # ADDED: Save post to files
    def save_post(self, post_data):
        """Save post to both JSON files"""
        try:
            # Save to posts.json
            with open(self.posts_data_path, 'r') as f:
                posts_data = json.load(f)
            
            posts_data['posts'].append(post_data)
            
            with open(self.posts_data_path, 'w') as f:
                json.dump(posts_data, f, indent=4)
            
            # Save to classroom_data.json
            with open(self.classroom_data_path, 'r') as f:
                classroom_data = json.load(f)
            
            classroom_post = {
                "id": post_data['post_id'],
                "topic_id": post_data['topic_id'],
                "class_id": post_data['class_id'],
                "title": post_data['title'],
                "content": post_data['description'],
                "type": post_data['type'],
                "attachment": {
                    "name": post_data['attachment']['filename'] if post_data.get('attachment') else post_data['title'],
                    "type": post_data['attachment']['file_type'].upper() if post_data.get('attachment') else "PDF"
                } if post_data.get('attachment') else None,
                "score": None,
                "date": post_data['date_posted'],  # Use the formatted date here
                "author": post_data['instructor']
            }
            
            classroom_data['posts'].append(classroom_post)
            
            with open(self.classroom_data_path, 'w') as f:
                json.dump(classroom_data, f, indent=4)
            
            return True
        except Exception as e:
            print(f"Error saving post: {e}")
            return False
    
def main():
    app = QApplication(sys.argv)
    
    sample_class = {
        "id": 1,
        "code": "ITSD81",
        "title": "Desktop Application Development",
        "section": "BSIT-3C"
    }
    
    window = MaterialForm(
        cls=sample_class,
        username="Neil John Jomaya",
        roles=["faculty"],
        primary_role="faculty",
        token="test_token"
    )
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()