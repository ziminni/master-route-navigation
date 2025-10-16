# topic_widget.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from .topic_frame import TopicFrame

class TopicWidget(QWidget):
    post_selected = pyqtSignal(dict)
    
    def __init__(self, topic_title, posts, controller, user_role, parent=None):
        super().__init__(parent)
        self.topic_title = topic_title if topic_title is not None else "Untitled"
        self.posts = posts
        self.controller = controller
        self.user_role = user_role
        self.frames = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)

        # Only show title if it's not empty
        if self.topic_title:
            # Topic Title with consistent styling
            self.title_label = QLabel(self.topic_title, self)
            font = QFont("Poppins")
            font.setPointSize(16)
            font.setWeight(QFont.Weight.Normal)
            self.title_label.setFont(font)
            self.title_label.setStyleSheet("""
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
            self.title_label.setMinimumHeight(40)
            layout.addWidget(self.title_label)

            # Separator
            separator = QFrame(self)
            separator.setMinimumHeight(1)
            separator.setMaximumHeight(1)
            separator.setStyleSheet("""
                QFrame {
                    background-color: #A9A9A9;
                    border: none;
                    margin-left: 20px;
                    margin-right: 20px;
                }
            """)
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setFrameShadow(QFrame.Shadow.Sunken)
            layout.addWidget(separator)

        # Add TopicFrame for each post
        for post in self.posts:
            topic_frame = TopicFrame(post, self.controller, self.user_role)
            topic_frame.post_clicked.connect(self.post_selected.emit)
            self.frames.append(topic_frame)
            layout.addWidget(topic_frame)