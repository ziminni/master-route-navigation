from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor

class UploadClassMaterialPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initializeUI()

    def initializeUI(self):
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #084924;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)  # Responsive spacing
        layout.setContentsMargins(30, 25, 30, 25)

        self.setup_widgets(layout)

    def setup_widgets(self, layout):
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

        self.upload_file_section(layout)
        

    def upload_file_section(self, layout):
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

        upload_layout.addWidget(upload_content_layout)

        layout.addWidget(upload_layout)
        self.setup_upload_button(upload_layout)

    def setup_upload_button(self, upload_layout):
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
        
        # upload_layout.addWidget(upload_label)
        # upload_layout.addWidget(upload_frame)
        # upload_layout.addWidget(upload_now_btn)
        
        # Use expanding spacer that adjusts to available space
        # layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))