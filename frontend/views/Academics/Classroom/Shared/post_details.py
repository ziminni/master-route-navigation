# post_details.py - Add better error handling
from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtCore import pyqtSignal
from widgets.Academics.Ui_viewContent import Ui_viewContent

class PostDetails(QWidget):
    back_clicked = pyqtSignal()

    def __init__(self, post, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: white;")
        self.ui = Ui_viewContent()
        self.ui.setupUi(self, content_type=post.get("type", "material"))
        self.load_post(post)
        self.ui.backButton.clicked.connect(self.back_clicked.emit)

    def load_post(self, post):
        try:
            self.ui.title_label.setText(post.get("title", "No Title"))
            self.ui.instructor_label.setText(post.get("author", "Unknown"))
            
            # Handle date formatting
            date_str = post.get("date", "")
            if date_str:
                date_part = date_str.split(" ")[0]
                self.ui.date_label.setText("• " + date_part)
            else:
                self.ui.date_label.setText("• No date")
            
            self.ui.descriptionEdit.setHtml(post.get("content", ""))
            
            # Handle attachment
            attachment = post.get("attachment")
            if attachment:
                self.ui.attachmentName.setText(attachment.get("name", "No name"))
                self.ui.attachmentType.setText(attachment.get("type", "Unknown"))
            else:
                self.ui.attachmentName.setText("No attachment")
                self.ui.attachmentType.setText("")
            
            # Handle score for assessments
            if post.get("type") == "assessment" and post.get("score") is not None:
                self.ui.score_label.setText(f"{post['score']} points")
            else:
                self.ui.score_label.setText("")
                
        except Exception as e:
            print(f"Error loading post: {e}")

    def load_post(self, post):
        try:
            self.ui.title_label.setText(post.get("title", "No Title"))
            self.ui.instructor_label.setText(post.get("author", "Unknown"))
            
            # Handle date formatting
            date_str = post.get("date", "")
            if date_str:
                date_part = date_str.split(" ")[0]
                self.ui.date_label.setText("• " + date_part)
            else:
                self.ui.date_label.setText("• No date")
            
            self.ui.descriptionEdit.setHtml(post.get("content", ""))
            
            # Hide attachment and score sections for syllabus
            if post.get("type") == "syllabus":
                if hasattr(self.ui, 'attachmentFrame'):
                    self.ui.attachmentFrame.hide()
                if hasattr(self.ui, 'score_label'):
                    self.ui.score_label.hide()
            else:
                # Handle attachment for regular posts
                attachment = post.get("attachment")
                if attachment and hasattr(self.ui, 'attachmentFrame'):
                    self.ui.attachmentFrame.show()
                    self.ui.attachmentName.setText(attachment.get("name", "No name"))
                    self.ui.attachmentType.setText(attachment.get("type", "Unknown"))
                elif hasattr(self.ui, 'attachmentFrame'):
                    self.ui.attachmentFrame.hide()
                
                # Handle score for assessments
                if post.get("type") == "assessment" and post.get("score") is not None and hasattr(self.ui, 'score_label'):
                    self.ui.score_label.setText(f"{post['score']} points")
                    self.ui.score_label.show()
                elif hasattr(self.ui, 'score_label'):
                    self.ui.score_label.hide()
                    
        except Exception as e:
            print(f"Error loading post: {e}")        

    def clear(self):
        pass