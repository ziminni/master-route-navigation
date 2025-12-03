import os
import re
import contextlib
import requests
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QFileDialog, QMessageBox, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from controller.HouseController import HouseController


class AdminCreateHousePage(QDialog):
    """Simple admin UI to create a House and upload logo to backend."""

    def __init__(self, token=None, api_base=None, parent=None, parent_manager=None):
        super().__init__(parent)
        self.token = token
        self.parent_manager = parent_manager
        self.api_base = api_base or "http://127.0.0.1:8000"
        self.controller = HouseController(self)
        self.logo_path = None

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Create New House")
        self.setFixedSize(520, 700)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()
        
        back_btn = QPushButton("← Cancel")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666666;
                border: none;
                font-family: 'Inter', sans-serif;
                font-size: 14px;
                font-weight: 500;
                padding: 8px 0;
            }
            QPushButton:hover {
                color: #084924;
            }
        """)
        back_btn.clicked.connect(self.go_back)
        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Title
        title = QLabel("Create New House")
        title.setStyleSheet("""
            font-family: 'Poppins', sans-serif;
            font-size: 24px;
            font-weight: 800;
            color: #084924;
        """)
        main_layout.addWidget(title)

        # Form container
        form_frame = QFrame()
        form_frame.setObjectName("formFrame")
        form_frame.setStyleSheet("""
            QFrame#formFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
            QFrame#formFrame QLabel {
                border: none;
                background: transparent;
            }
            QFrame#formFrame QLineEdit {
                border: 1px solid #e0e0e0;
            }
            QFrame#formFrame QTextEdit {
                border: 1px solid #e0e0e0;
            }
        """)
        form_shadow = QGraphicsDropShadowEffect()
        form_shadow.setBlurRadius(15)
        form_shadow.setXOffset(0)
        form_shadow.setYOffset(4)
        form_shadow.setColor(QColor(0, 0, 0, 20))
        form_frame.setGraphicsEffect(form_shadow)
        
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(24, 24, 24, 24)
        form_layout.setSpacing(20)

        # House Name
        name_label = QLabel("House Name")
        name_label.setStyleSheet("""
            font-family: 'Inter', sans-serif;
            font-size: 13px;
            font-weight: 600;
            color: #333333;
            border: none;
        """)
        form_layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter house name...")
        self.name_input.setStyleSheet("""
            QLineEdit {
                padding: 12px 16px;
                font-family: 'Inter', sans-serif;
                font-size: 14px;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: #fafafa;
                color: #333333;
            }
            QLineEdit:focus {
                border: 2px solid #084924;
                background-color: white;
            }
            QLineEdit::placeholder {
                color: #999999;
            }
        """)
        self.name_input.textChanged.connect(self.on_name_changed)
        form_layout.addWidget(self.name_input)

        # Slug
        slug_label = QLabel("Slug (optional)")
        slug_label.setStyleSheet("""
            font-family: 'Inter', sans-serif;
            font-size: 13px;
            font-weight: 600;
            color: #333333;
            border: none;
        """)
        form_layout.addWidget(slug_label)
        
        self.slug_input = QLineEdit()
        self.slug_input.setPlaceholderText("leave blank to auto-generate")
        self.slug_input.setStyleSheet("""
            QLineEdit {
                padding: 12px 16px;
                font-family: 'Inter', sans-serif;
                font-size: 14px;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: #fafafa;
                color: #333333;
            }
            QLineEdit:focus {
                border: 2px solid #084924;
                background-color: white;
            }
            QLineEdit::placeholder {
                color: #999999;
            }
        """)
        form_layout.addWidget(self.slug_input)

        # Description
        desc_label = QLabel("Description")
        desc_label.setStyleSheet("""
            font-family: 'Inter', sans-serif;
            font-size: 13px;
            font-weight: 600;
            color: #333333;
            border: none;
        """)
        form_layout.addWidget(desc_label)
        
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Enter house description...")
        self.desc_input.setFixedHeight(100)
        self.desc_input.setStyleSheet("""
            QTextEdit {
                padding: 12px 16px;
                font-family: 'Inter', sans-serif;
                font-size: 14px;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: #fafafa;
                color: #333333;
            }
            QTextEdit:focus {
                border: 2px solid #084924;
                background-color: white;
            }
        """)
        form_layout.addWidget(self.desc_input)

        # Logo selector
        logo_label = QLabel("House Logo")
        logo_label.setStyleSheet("""
            font-family: 'Inter', sans-serif;
            font-size: 13px;
            font-weight: 600;
            color: #333333;
            border: none;
        """)
        form_layout.addWidget(logo_label)

        logo_row = QHBoxLayout()
        logo_row.setSpacing(16)
        
        self.logo_btn = QPushButton("Select Logo")
        self.logo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.logo_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #084924;
                border: 2px solid #084924;
                border-radius: 8px;
                padding: 10px 20px;
                font-family: 'Inter', sans-serif;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #084924;
                color: white;
            }
        """)
        self.logo_btn.clicked.connect(self.select_logo)
        logo_row.addWidget(self.logo_btn)
        
        self.logo_preview = QLabel()
        self.logo_preview.setFixedSize(80, 80)
        self.logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_preview.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border: 1px dashed #cccccc;
                border-radius: 8px;
                color: #999999;
                font-size: 11px;
            }
        """)
        self.logo_preview.setText("No logo")
        logo_row.addWidget(self.logo_preview)
        logo_row.addStretch()
        
        form_layout.addLayout(logo_row)
        main_layout.addWidget(form_frame)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666666;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px 24px;
                font-family: 'Inter', sans-serif;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                border-color: #999999;
                color: #333333;
            }
        """)
        cancel_btn.clicked.connect(self.go_back)
        btn_row.addWidget(cancel_btn)
        
        create_btn = QPushButton("Create House")
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #084924;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-family: 'Inter', sans-serif;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #0a5c2e;
            }
        """)
        create_btn.clicked.connect(self.on_create)
        btn_row.addWidget(create_btn)
        
        main_layout.addLayout(btn_row)

    def select_logo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Logo Image", 
            os.path.expanduser("~"), 
            "Images (*.png *.jpg *.jpeg)"
        )
        if path:
            self.logo_path = path
            pix = QPixmap(path)
            if not pix.isNull():
                scaled = pix.scaled(
                    76, 76, 
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.logo_preview.setPixmap(scaled)
                self.logo_preview.setStyleSheet("""
                    QLabel {
                        background-color: white;
                        border: 1px solid #e0e0e0;
                        border-radius: 8px;
                    }
                """)

    def on_create(self):
        name = self.name_input.text().strip()
        desc = self.desc_input.toPlainText().strip()
        slug = self.slug_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Validation", "Please provide a house name.")
            return

        data = {"name": name, "description": desc}
        if slug:
            data["slug"] = slug

        try:
            token = self.token
            if not token:
                token = getattr(self.controller, "token", None)

            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"

            url = f"{self.api_base}/api/house/houses/"
            with contextlib.ExitStack() as stack:
                files = {}
                if self.logo_path:
                    files["logo"] = stack.enter_context(open(self.logo_path, "rb"))

                resp = requests.post(url, data=data, files=files or None, headers=headers)

            if resp.status_code in (200, 201):
                QMessageBox.information(self, "Success", "House created successfully.")
                if self.parent_manager and hasattr(self.parent_manager, 'load_houses'):
                    self.parent_manager.load_houses()
                self.accept()
            else:
                try:
                    err = resp.json()
                except Exception:
                    err = resp.text
                QMessageBox.critical(self, "Error", f"Failed to create house: {resp.status_code}\n{err}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error: {e}")

    def on_name_changed(self, text: str):
        slug = text.strip().lower()
        slug = re.sub(r"[^a-z0-9\-]+", "-", slug)
        slug = re.sub(r"-+", "-", slug).strip("-")
        self.slug_input.setPlaceholderText(f"e.g. {slug}" if slug else "leave blank to auto-generate")

    def go_back(self):
        """Close the dialog"""
        self.reject()
