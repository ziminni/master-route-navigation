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
            
            # Handle date formatting - NEW: Format as "August 18, 2025"
            date_str = post.get("date", "")
            if date_str:
                formatted_date = self.format_date_for_display(date_str)
                self.ui.date_label.setText("• " + formatted_date)
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

    def format_date_for_display(self, date_str):
        """Format date string for display in post details as 'August 18, 2025'"""
        if not date_str:
            return ""
        
        print(f"DEBUG PostDetails: Formatting date: '{date_str}'")
        
        # If it's already in "Aug 18" format, convert to full format
        if len(date_str) <= 6 and any(month in date_str.lower() for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
            try:
                from datetime import datetime
                current_year = datetime.now().year
                dt = datetime.strptime(f"{date_str} {current_year}", "%b %d %Y")
                formatted = dt.strftime("%B %d, %Y")  # "August 18, 2025"
                print(f"DEBUG PostDetails: Converted short format to: '{formatted}'")
                return formatted
            except Exception as e:
                print(f"DEBUG PostDetails: Error converting short format: {e}")
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
                formatted = dt.strftime("%B %d, %Y")  # Format to "August 18, 2025"
                print(f"DEBUG PostDetails: Successfully formatted to: '{formatted}' using format '{fmt}'")
                return formatted
            except ValueError:
                continue
        
        # If all parsing fails, return the original string
        print(f"DEBUG PostDetails: All parsing failed, returning original: '{date_str}'")
        return date_str           

    def clear(self):
        pass