from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QApplication, QMenu, QScrollArea
from PyQt6.QtGui import QAction, QPixmap
from PyQt6.QtCore import Qt, pyqtSignal
import os

class ViewAssessment(QWidget):
    back_clicked = pyqtSignal()  # Signal to return to main page

    def __init__(self, assessment_data, user_role, parent=None):
        super().__init__(parent)
        self.assessment_data = assessment_data
        self.user_role = user_role  # Store user role (e.g., "student", "faculty", "admin")
        self.load_ui()
        self.populate_data()

    def load_ui(self):
        """Load the ViewAssessment UI file and wrap it in a scroll area"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(current_dir, '../../../../../ui/Classroom/view_assessment.ui')
        
        # Load the UI into a temporary widget
        ui_widget = QWidget()
        uic.loadUi(ui_file, ui_widget)
        
        # Create a scroll area and set the UI widget as its content
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidget(ui_widget)
        self.scroll_area.setWidgetResizable(True)  # Resize the content to fit the scroll area
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; }")  # No border for seamless look
        
        # Set up the main layout to include the scroll area
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scroll_area)
        
        # Assign references to UI elements from the loaded widget
        self.title_label = ui_widget.findChild(QWidget, "title_label") or ui_widget.findChild(QLabel, "title_label")
        self.instructor_label = ui_widget.findChild(QWidget, "instructor_label") or ui_widget.findChild(QLabel, "instructor_label")
        self.date_label = ui_widget.findChild(QWidget, "date_label") or ui_widget.findChild(QLabel, "date_label")
        self.descriptionEdit = ui_widget.findChild(QWidget, "descriptionEdit") or ui_widget.findChild(QTextEdit, "descriptionEdit")
        self.attachmentName = ui_widget.findChild(QWidget, "attachmentName") or ui_widget.findChild(QLabel, "attachmentName")
        self.attachmentType = ui_widget.findChild(QWidget, "attachmentType") or ui_widget.findChild(QLabel, "attachmentType")
        self.score_label = ui_widget.findChild(QWidget, "score_label") or ui_widget.findChild(QLabel, "score_label")
        self.backButton = ui_widget.findChild(QWidget, "backButton") or ui_widget.findChild(QLabel, "backButton")
        self.attachmentFrame = ui_widget.findChild(QWidget, "attachmentFrame") or ui_widget.findChild(QFrame, "attachmentFrame")
        self.menuButton = ui_widget.findChild(QWidget, "menuButton") or ui_widget.findChild(QPushButton, "menuButton")
        self.commentBox = ui_widget.findChild(QWidget, "commentBox") or ui_widget.findChild(QTextEdit, "commentBox")
        self.pushButton = ui_widget.findChild(QWidget, "pushButton") or ui_widget.findChild(QPushButton, "pushButton")

    def populate_data(self):
        """Populate the UI with assessment data"""
        if self.title_label:
            self.title_label.setText(self.assessment_data.get("title", "Assessment Title"))
        if self.instructor_label:
            self.instructor_label.setText(self.assessment_data.get("instructor", "Carlos Fidel Castro"))
        if self.date_label:
            self.date_label.setText("• " + self.assessment_data.get("date", "August 18, 2025"))
        if self.descriptionEdit:
            self.descriptionEdit.setText(self.assessment_data.get("description", "This is the assessment description..."))
            self.descriptionEdit.setReadOnly(True)  # Ensure non-editable
        attachment = self.assessment_data.get("attachment", "assessment.pdf")
        if self.attachmentName:
            self.attachmentName.setText(attachment.split('.')[0])  # Filename without extension
        if self.attachmentType:
            self.attachmentType.setText("." + attachment.split('.')[-1])  # File type
        if self.score_label:
            self.score_label.setText(self.assessment_data.get("score", "10") + " points")
        if self.backButton:
            self.backButton.mousePressEvent = self.go_back  # Back button click
        if self.attachmentFrame:
            self.attachmentFrame.mousePressEvent = self.preview_attachment
        if self.menuButton:
            self.menuButton.clicked.connect(self.show_menu)
        if self.pushButton:
            self.pushButton.clicked.connect(self.send_comment)

        # Ensure backButton icon is displayed (it's a QLabel with pixmap in UI)
        if self.backButton:
            self.backButton.setScaledContents(True)
            pixmap = QPixmap(":/icons/back2.png")
            if pixmap.isNull():
                print("Warning: back2.png not found or invalid in resources!")
                self.backButton.setText("< Back")  # Fallback to text if icon fails
            else:
                self.backButton.setPixmap(pixmap)
                print("back2.png loaded successfully")

    def go_back(self, event):
        """Handle back button click to emit back_clicked signal"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.back_clicked.emit()

    def preview_attachment(self, event):
        """Handle click to preview attachment"""
        if event.button() == Qt.MouseButton.LeftButton:
            attachment = self.assessment_data.get("attachment", "assessment.pdf")
            print(f"Previewing {attachment}...")  # Replace with actual preview logic

    def show_menu(self):
        """Show options menu based on user role"""
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
        if self.user_role in ["faculty", "admin"]:
            edit_action = QAction("Edit", self)
            delete_action = QAction("Delete", self)
            menu.addAction(edit_action)
            menu.addAction(delete_action)
        # Optionally, add other actions for all roles here
        if self.menuButton:
            button_pos = self.menuButton.mapToGlobal(self.menuButton.rect().bottomLeft())
            menu.exec(button_pos)

    def send_comment(self):
        """Handle send button click for comments (placeholder)"""
        if self.commentBox:
            comment = self.commentBox.toPlainText().strip()
            if comment:
                print(f"Sending comment: {comment}")  # Replace with actual comment submission logic
                self.commentBox.clear()

    def update_data(self, assessment_data):
        """Update the widget with new assessment data"""
        self.assessment_data = assessment_data
        self.populate_data()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    assessment_data = {
        "title": "Quiz 1",
        "instructor": "Carlos Fidel Castro",
        "date": "August 18, 2025",
        "description": "Please ensure that the task is completed according to the requirements...",
        "attachment": "quiz1.pdf",
        "score": "10"
    }
    view_assessment = ViewAssessment(assessment_data, "faculty")
    view_assessment.setFixedSize(940, 530)  # Match main window size for testing
    view_assessment.show()
    sys.exit(app.exec())