import os, sys
project_root = (os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit, QSizePolicy, QFileDialog, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal  # ADDED: pyqtSignal for signals
from PyQt6.QtGui import QCursor
from frontend.widgets.Academics.labeled_section import LabeledSection


class UploadClassMaterialPanel(QFrame):
    # ADDED: Signal to emit when upload button is clicked
    upload_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # ADDED: Track selected file
        self.selected_file_path = None
        self.selected_file_name = None
        self.initializeUI()

    def initializeUI(self):
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #084924;
            }
        """)

        self.__layout = QVBoxLayout(self)
        self.__layout.setSpacing(8)
        self.__layout.setContentsMargins(15, 15, 15, 15)

        self.setup_widgets(self.__layout)

    def setup_widgets(self, layout):
        # CHANGED: Store as instance variable to access later
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter title")
        self.title_input.setStyleSheet("""
            QLineEdit {
                padding: 15px;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                font-size: 14px;
                background-color: white;
                min-height: 20px;
            }
            QLineEdit:focus {
                border-color: #0066cc;
                border-width: 2px;
            }
        """)

        title_section = LabeledSection(label="Title", widget=self.title_input, sub_label="*Required")

        # CHANGED: Store as instance variable to access later
        self.instructions_input = QTextEdit()
        self.instructions_input.setStyleSheet("""
            QTextEdit {
                padding: 15px;
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
        self.instructions_input.setMinimumHeight(100)

        instructions_section = LabeledSection(label="Instructions (Optional)", widget=self.instructions_input)

        layout.addWidget(title_section)
        layout.addWidget(instructions_section)
        self.upload_file_section(layout)
        
        layout.addStretch()

    def upload_file_section(self, layout):
        upload_layout = QVBoxLayout()
        upload_layout.setSpacing(8)
        
        upload_label = QLabel("Upload File")
        upload_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 500;
                color: #333;
                border: none;
            }
        """)
        
        # CHANGED: Store as instance variable for updating later
        self.upload_frame = QFrame()
        self.upload_frame.setStyleSheet("""
            QFrame {
                border: 2px dashed #ccc;
                border-radius: 8px;
                background-color: #fafafa;
            }
        """)
        self.upload_frame.setMinimumHeight(140)
        
        self.upload_content_layout = QVBoxLayout(self.upload_frame)
        self.upload_content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.upload_content_layout.setSpacing(10)
        
        # File icon
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
        
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setStyleSheet("""
            QPushButton {
                color: #0066cc;
                background: none;
                font-size: 14px;
                padding: 5px;
            }
            QPushButton:hover {
                color: #0052a3;
            }
        """)
        # ADDED: Connect browse button to file dialog
        self.browse_btn.clicked.connect(self.browse_file)
        
        self.upload_content_layout.addWidget(file_icon)
        self.upload_content_layout.addWidget(drag_label)
        self.upload_content_layout.addWidget(or_label)
        self.upload_content_layout.addWidget(self.browse_btn)

        upload_layout.addWidget(self.upload_frame)
        layout.addLayout(upload_layout)
        self.setup_upload_button(upload_layout)

    def setup_upload_button(self, upload_layout):
        self.upload_now_btn = QPushButton("Upload Now")
        self.upload_now_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 15px 24px;
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
        self.upload_now_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        # ADDED: Connect upload button to emit signal
        self.upload_now_btn.clicked.connect(self.on_upload_clicked)
        upload_layout.addWidget(self.upload_now_btn)

    # ADDED: File browsing functionality
    def browse_file(self):
        """Open file dialog to select a file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            "All Files (*);;PDF Files (*.pdf);;Word Documents (*.doc *.docx);;Images (*.png *.jpg *.jpeg)"
        )
        
        if file_path:
            self.selected_file_path = file_path
            self.selected_file_name = os.path.basename(file_path)
            self.update_upload_display()

    # ADDED: Update display when file is selected
    def update_upload_display(self):
        """Update the upload area to show selected file"""
        if self.selected_file_name:
            # Clear previous widgets
            while self.upload_content_layout.count():
                item = self.upload_content_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Show file info
            file_label = QLabel(f"✓ {self.selected_file_name}")
            file_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #28a745;
                    border: none;
                    font-weight: 500;
                }
            """)
            file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            change_btn = QPushButton("Change File")
            change_btn.setStyleSheet("""
                QPushButton {
                    color: #0066cc;
                    background: none;
                    border: none;
                    font-size: 13px;
                    text-decoration: underline;
                    padding: 5px;
                }
                QPushButton:hover {
                    color: #0052a3;
                }
            """)
            change_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            change_btn.clicked.connect(self.browse_file)
            
            self.upload_content_layout.addWidget(file_label)
            self.upload_content_layout.addWidget(change_btn)
            
            # Change frame style
            self.upload_frame.setStyleSheet("""
                QFrame {
                    border: 2px solid #28a745;
                    border-radius: 8px;
                    background-color: #f0fff4;
                }
            """)

    # ADDED: Validation
    def validate_form(self):
        """Validate form fields"""
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Title is required!")
            return False
        return True

    # ADDED: Get form data
    def get_material_data(self):
        """Get all material data from the form"""
        title = self.title_input.text().strip()
        description = self.instructions_input.toPlainText().strip()
        
        attachment = None
        if self.selected_file_path and self.selected_file_name:
            ext = os.path.splitext(self.selected_file_name)[1].lower()
            file_type = "PDF" if ext == ".pdf" else "DOC" if ext in [".doc", ".docx"] else "FILE"
            
            attachment = {
                "name": self.selected_file_name,
                "type": file_type,
                "file_path": f"attachments/{self.selected_file_name}"
            }
        
        return {
            "title": title,
            "description": description,
            "attachment": attachment
        }

    # ADDED: Handle upload button click
    def on_upload_clicked(self):
        """Emit signal when upload is clicked"""
        if self.validate_form():
            self.upload_clicked.emit()

    # ADDED: Clear form
    def clear_form(self):
        """Clear all form fields"""
        self.title_input.clear()
        self.instructions_input.clear()
        self.selected_file_path = None
        self.selected_file_name = None
        
        # Reset upload area
        while self.upload_content_layout.count():
            item = self.upload_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Restore default display
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
                font-size: 14px;
                padding: 5px;
            }
            QPushButton:hover {
                color: #0052a3;
            }
        """)
        browse_btn.clicked.connect(self.browse_file)
        
        self.upload_content_layout.addWidget(file_icon)
        self.upload_content_layout.addWidget(drag_label)
        self.upload_content_layout.addWidget(or_label)
        self.upload_content_layout.addWidget(browse_btn)
        
        # Reset frame style
        self.upload_frame.setStyleSheet("""
            QFrame {
                border: 2px dashed #ccc;
                border-radius: 8px;
                background-color: #fafafa;
            }
        """)

    def set_controller(self, controller):
        """Method to set the controller and connect signals."""
        self.controller = controller
        if hasattr(self, 'browse_btn'):
            self.controller.connect_browse_button(self.browse_btn)