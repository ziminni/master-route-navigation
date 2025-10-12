#Assessment creation interface

import sys
from PyQt6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout, 
    QLabel, 
    QLineEdit, 
    QTextEdit, 
    QComboBox, 
    QPushButton, 
    QFrame, 
    QSpacerItem, 
    QSizePolicy, QGridLayout)

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPalette, QColor, QCursor
from upload_class_material_widget import UploadClassMaterialPanel

class AssessmentForm(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("Assessment")
        self.setGeometry(100, 100, 1400, 800)  # Increased window size
        self.setMinimumSize(QSize(1200, 700))   # Set minimum size
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
        """)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # header = self.create_header()
        # Left panel
        left_panel = self.create_left_panel()
        
        # Right panel
        right_panel = self.create_right_panel()
        

        main_layout.addWidget(left_panel, 3)  # Give left panel more space ratio
        main_layout.addWidget(right_panel, 1)

    def create_header(self):
        frame = QFrame()
        header_layout = QHBoxLayout(frame)

        back_button = QPushButton("<")
        back_button.setFixedSize(40, 40)  # Fixed size for back button
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

        back_label = QLabel("Assessment")
        back_label.setStyleSheet("""
            QLabel {
                font-size: 24px;  /* Increased font size */
                font-weight: bold;
                color: #333;
                border: none;
                margin-left: 15px;
            }
        """)

        header_layout.addWidget(back_button)
        header_layout.addWidget(back_label)

        return frame

        
    def create_left_panel(self):
        # Left panel container
        left_frame = QFrame()
        left_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #084924;
            }
        """)
        
        layout = QVBoxLayout(left_frame)
        layout.setSpacing(20)  # Responsive spacing
        layout.setContentsMargins(30, 25, 30, 25)
        
        # Title field
        title_layout = QVBoxLayout()
        title_layout.setSpacing(8)
        
        title_label = QLabel("Title")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;  /* Increased font size */
                font-weight: 500;
                color: #333;
                border: none;
            }
        """)
        
        title_input = QLineEdit()
        title_input.setPlaceholderText("Enter assessment title")
        title_input.setStyleSheet("""
            QLineEdit {
                padding: 15px;  /* Increased padding */
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                font-size: 14px;
                background-color: white;
                min-height: 20px;  /* Minimum height */
            }
            QLineEdit:focus {
                border-color: #0066cc;
                border-width: 2px;
            }
        """)
        
        required_label = QLabel("* Required")
        required_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 12px;
                border: none;
                margin-top: 5px;
            }
        """)
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(title_input)
        title_layout.addWidget(required_label)
        layout.addLayout(title_layout)
        
        # Instructions field
        instructions_layout = QVBoxLayout()
        instructions_layout.setSpacing(8)
        
        instructions_label = QLabel("Instructions (Optional)")
        instructions_label.setStyleSheet("""
            QLabel {
                font-size: 16px;  /* Increased font size */
                font-weight: 500;
                color: #333;
                border: none;
            }
        """)
        
        instructions_input = QTextEdit()
        instructions_input.setStyleSheet("""
            QTextEdit {
                padding: 15px;  /* Increased padding */
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                font-size: 14px;
                background-color: white;
            }
            QTextEdit:focus {
                border-color: #0066cc;
                border-width: 2px;
            }
        """)
        instructions_input.setMinimumHeight(100)
        instructions_input.setMaximumHeight(120)  # Limit max height for responsive behavior
        
        instructions_layout.addWidget(instructions_label)
        instructions_layout.addWidget(instructions_input)
        layout.addLayout(instructions_layout)
        
        # Upload file section
        upload_layout = QVBoxLayout()
        upload_layout.setSpacing(15)
        
        upload_label = QLabel("Upload File")
        upload_label.setStyleSheet("""
            QLabel {
                font-size: 16px;  /* Increased font size */
                font-weight: 500;
                color: #333;
                border: none;
            }
        """)
        
        # Upload area
        upload_frame = QFrame()
        upload_frame.setStyleSheet("""
            QFrame {
                border: 2px dashed #ccc;
                border-radius: 8px;
                background-color: #fafafa;
            }
        """)
        upload_frame.setMinimumHeight(140)  # Reduced minimum height for better fit
        upload_frame.setMaximumHeight(160)  # Responsive maximum height
        
        upload_content_layout = QVBoxLayout(upload_frame)
        upload_content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upload_content_layout.setSpacing(10)
        
        # File icon (using text as placeholder)
        file_icon = QLabel("📄")
        file_icon.setStyleSheet("""
            QLabel {
                font-size: 32px;
                border: none;
                color: #28a745;
            }
        """)
        file_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        drag_label = QLabel("Drag n Drop here")
        drag_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #666;
                border: none;
            }
        """)
        drag_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        or_label = QLabel("Or")
        or_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #666;
                border: none;
            }
        """)
        or_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        browse_btn = QPushButton("Browse")
        browse_btn.setStyleSheet("""
            QPushButton {
                color: #0066cc;
                background: none;
                border: none;
                font-size: 14px;
                text-decoration: underline;
                padding: 5px;
            }
            QPushButton:hover {
                color: #0052a3;
            }
        """)
        
        upload_content_layout.addWidget(file_icon)
        upload_content_layout.addWidget(drag_label)
        upload_content_layout.addWidget(or_label)
        upload_content_layout.addWidget(browse_btn)
        
        # Upload Now button
        upload_now_btn = QPushButton("Upload Now")
        upload_now_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;  /* Green color to match image */
                color: white;
                border: none;
                border-radius: 6px;
                padding: 15px 24px;  /* Increased padding */
                font-size: 14px;
                font-weight: 500;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        upload_now_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        upload_layout.addWidget(upload_label)
        upload_layout.addWidget(upload_frame)
        upload_layout.addWidget(upload_now_btn)
        layout.addLayout(upload_layout)
        
        # Use expanding spacer that adjusts to available space
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        return left_frame
    
    def create_right_panel(self):
        # Right panel container
        right_frame = QFrame()
        right_frame.setMinimumWidth(300)  # Set minimum width to prevent overlap
        right_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        layout = QVBoxLayout(right_frame)
        layout.setSpacing(20)  # Adjusted spacing for better fit
        layout.setContentsMargins(20, 25, 20, 25)  # Reduced horizontal margins
        
        # Category section
        category_label = QLabel("Category")
        category_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 500;
                color: #333;
                border: none;
            }
        """)
        
        category_combo = QComboBox()
        category_combo.addItem("Laboratory")
        category_combo.setMinimumHeight(45)  # Set minimum height
        category_combo.setStyleSheet("""
            QComboBox {
                padding: 12px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                font-size: 14px;
                background-color: white;
                min-height: 20px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
        """)
        
        layout.addWidget(category_label)
        layout.addWidget(category_combo)
        
        # Grade Category and Points
        grade_points_layout = QHBoxLayout()
        grade_points_layout.setSpacing(10)  # Reduced spacing to prevent overlap
        
        grade_layout = QVBoxLayout()
        grade_layout.setSpacing(5)  # Reduced vertical spacing
        grade_label = QLabel("Grade Category")
        grade_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 500;
                color: #333;
                border: none;
            }
        """)
        
        grade_combo = QComboBox()
        grade_combo.addItem("Lab Activity")
        grade_combo.setMinimumHeight(45)  # Set minimum height
        grade_combo.setMinimumWidth(120)  # Set minimum width
        grade_combo.setStyleSheet("""
            QComboBox {
                padding: 12px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                font-size: 14px;
                background-color: white;
                min-height: 20px;
            }
        """)
        
        grade_layout.addWidget(grade_label)
        grade_layout.addWidget(grade_combo)
        
        points_layout = QVBoxLayout()
        points_layout.setSpacing(5)  # Reduced vertical spacing
        points_label = QLabel("Points")
        points_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 500;
                color: #333;
                border: none;
            }
        """)
        
        points_input = QLineEdit("0")  # Changed from "50" to "0" to match image
        points_input.setMinimumHeight(45)  # Set minimum height
        points_input.setMinimumWidth(80)   # Set minimum width
        points_input.setMaximumWidth(100)  # Limit maximum width
        points_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                font-size: 14px;
                background-color: white;
                min-height: 20px;
            }
            QLineEdit:focus {
                border-color: #0066cc;
            }
        """)
        
        points_layout.addWidget(points_label)
        points_layout.addWidget(points_input)
        
        grade_points_layout.addLayout(grade_layout, 2)  # Give grade more space
        grade_points_layout.addLayout(points_layout, 1)
        layout.addLayout(grade_points_layout)
        
        # Due section
        due_label = QLabel("Due")
        due_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 500;
                color: #333;
                border: none;
            }
        """)
        
        due_combo = QComboBox()
        due_combo.addItem("No Due Date")
        due_combo.setStyleSheet("""
            QComboBox {
                padding: 12px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                font-size: 14px;
                background-color: white;
                min-height: 20px;
            }
        """)
        
        layout.addWidget(due_label)
        layout.addWidget(due_combo)
        
        # Schedule section
        schedule_label = QLabel("Schedule")
        schedule_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 500;
                color: #333;
                border: none;
            }
        """)
        
        schedule_combo = QComboBox()
        schedule_combo.addItem("Now")
        schedule_combo.setStyleSheet("""
            QComboBox {
                padding: 12px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                font-size: 14px;
                background-color: white;
                min-height: 20px;
            }
        """)
        
        layout.addWidget(schedule_label)
        layout.addWidget(schedule_combo)
        
        # Term section
        term_label = QLabel("Term")
        term_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 500;
                color: #333;
                border: none;
            }
        """)
        
        term_combo = QComboBox()
        term_combo.addItem("No Due Date")
        term_combo.setStyleSheet("""
            QComboBox {
                padding: 12px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                font-size: 14px;
                background-color: white;
                min-height: 20px;
            }
        """)
        
        layout.addWidget(term_label)
        layout.addWidget(term_combo)
        
        # Topic section
        topic_label = QLabel("Topic")
        topic_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 500;
                color: #333;
                border: none;
            }
        """)
        
        topic_combo = QComboBox()
        topic_combo.addItem("Topic 1")
        topic_combo.setStyleSheet("""
            QComboBox {
                padding: 12px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                font-size: 14px;
                background-color: white;
                min-height: 20px;
            }
        """)
        
        layout.addWidget(topic_label)
        layout.addWidget(topic_combo)
        
        layout.addStretch()
        return right_frame

def main():
    app = QApplication(sys.argv)
    window = AssessmentForm()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()