# post_details.py - Add menu button with Edit and Delete options
from PyQt6.QtWidgets import QWidget, QLabel, QMenu, QMessageBox
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction, QFont
from widgets.Academics.Ui_viewContent import Ui_viewContent

class PostDetails(QWidget):
    back_clicked = pyqtSignal()
    post_edited = pyqtSignal(dict)  # New signal for edit
    post_deleted = pyqtSignal(dict)  # New signal for delete
    syllabus_deleted = pyqtSignal(dict)

    def __init__(self, post, username, roles, primary_role, parent=None):
        super().__init__(parent)
        self.post = post
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        
        self.setStyleSheet("background-color: white;")
        self.ui = Ui_viewContent()
        self.ui.setupUi(self, content_type=post.get("type", "material"))
        self.load_post(post)
        self.setup_menu_button()
        self.ui.backButton.clicked.connect(self.back_clicked.emit)

    def setup_menu_button(self):
        """Setup menu button with Edit and Delete options for faculty/admin"""
        if self.primary_role in ["faculty", "admin"]:
            # Style the menu button
            self.ui.menuButton.setStyleSheet("""
                QPushButton {
                    border: none;
                    background-color: transparent;
                    color: #656d76;
                    border-radius: 15px;
                    font-weight: bold;
                    font-family: "Poppins", Arial, sans-serif;
                }
                QPushButton:hover {
                    background-color: #F3F4F6;
                }
            """)
            
            # Set font for menu button
            menu_font = QFont("Poppins")
            menu_font.setPointSize(16)
            self.ui.menuButton.setFont(menu_font)
            
            # Connect menu button click
            self.ui.menuButton.clicked.connect(self.show_post_menu)
        else:
            # Hide menu button for students
            self.ui.menuButton.hide()

    def show_post_menu(self):
        """Show context menu for post actions (Edit, Delete)"""
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
                font-size: 14px;
            }
            QMenu::item:selected {
                background-color: #f5f5f5;
            }
        """)
        
        edit_action = QAction("Edit", self)
        delete_action = QAction("Delete", self)
        
        edit_action.triggered.connect(self.edit_post)
        delete_action.triggered.connect(self.delete_post)
        
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        
        # Show menu at button position
        button_pos = self.ui.menuButton.mapToGlobal(self.ui.menuButton.rect().bottomLeft())
        menu.exec(button_pos)

    def edit_post(self):
        """Handle edit post action"""
        print(f"Edit post: {self.post['title']}")
        # Emit signal to parent to handle editing
        self.post_edited.emit(self.post)
        # You can also implement inline editing here if preferred

    def delete_post(self):
        """Handle delete post action - REMOVED confirmation dialog"""
        print(f"Delete post: {self.post['title']}")
        
        # Check if this is a syllabus post
        if self.post.get("type") == "syllabus":
            print("DEBUG: This is a syllabus post, emitting syllabus_deleted signal")
            self.syllabus_deleted.emit(self.post)
        else:
            # Regular post deletion
            self.post_deleted.emit(self.post)
    
    # DON'T close the view here - let ClassroomMain handle it after confirmation
    # self.back_clicked.emit()  # REMOVE THIS LINE

    def load_post(self, post):
        try:
            self.ui.title_label.setText(post.get("title", "No Title"))
            self.ui.instructor_label.setText(post.get("author", "Unknown"))
            
            # Handle date formatting
            date_str = post.get("date", "")
            if date_str:
                formatted_date = self.format_date_for_display(date_str)
                self.ui.date_label.setText("• " + formatted_date)
            else:
                self.ui.date_label.setText("• No date")
            
            # Set maximum height for description edit
            self.ui.descriptionEdit.setMaximumHeight(200)
            self.ui.descriptionEdit.setHtml(post.get("content", ""))
            
            # Handle attachment
            attachment = post.get("attachment")
            if attachment:
                self.ui.attachmentName.setText(attachment.get("name", "No name"))
                self.ui.attachmentType.setText(attachment.get("type", "Unknown"))
                # Show attachment frame
                if hasattr(self.ui, 'attachmentFrame'):
                    self.ui.attachmentFrame.show()
            else:
                self.ui.attachmentName.setText("No attachment")
                self.ui.attachmentType.setText("")
                # Hide attachment frame if no attachment
                if hasattr(self.ui, 'attachmentFrame'):
                    self.ui.attachmentFrame.hide()
            
            # Handle score for assessments
            if post.get("type") == "assessment" and post.get("score") is not None:
                self.ui.score_label.setText(f"{post['score']} points")
                if hasattr(self.ui, 'score_label'):
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