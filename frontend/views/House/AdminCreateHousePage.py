import os
import re
import contextlib
import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QFileDialog, QMessageBox
)
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt

from controller.HouseController import HouseController


class AdminCreateHousePage(QWidget):
    """Simple admin UI to create a House and upload banner/logo to backend."""

    def __init__(self, token=None, api_base=None, parent=None):
        super().__init__(parent)
        self.token = token
        # default API base if not provided
        self.api_base = api_base or "http://127.0.0.1:8000"

        # controller used for helper methods (keeps consistency with other pages)
        self.controller = HouseController(self)

        self.banner_path = None
        self.logo_path = None

        self.init_ui()

    def init_ui(self):
        self.setMinimumSize(640, 480)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Create New House")
        title.setStyleSheet("font-size:20px; font-weight:800; color:#084924;")
        layout.addWidget(title)

        # Name + slug
        name_label = QLabel("House Name")
        self.name_input = QLineEdit()
        self.name_input.textChanged.connect(self.on_name_changed)
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)

        slug_label = QLabel("Slug (optional)")
        self.slug_input = QLineEdit()
        self.slug_input.setPlaceholderText("leave blank to auto-generate")
        layout.addWidget(slug_label)
        layout.addWidget(self.slug_input)

        # Description
        desc_label = QLabel("Description")
        self.desc_input = QTextEdit()
        self.desc_input.setFixedHeight(140)
        layout.addWidget(desc_label)
        layout.addWidget(self.desc_input)

        # Banner & Logo selectors and previews
        row = QHBoxLayout()

        left_col = QVBoxLayout()
        self.banner_btn = QPushButton("Select Banner")
        self.banner_btn.clicked.connect(self.select_banner)
        left_col.addWidget(self.banner_btn)
        self.banner_preview = QLabel()
        self.banner_preview.setFixedHeight(120)
        self.banner_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_col.addWidget(self.banner_preview)

        right_col = QVBoxLayout()
        self.logo_btn = QPushButton("Select Logo")
        self.logo_btn.clicked.connect(self.select_logo)
        right_col.addWidget(self.logo_btn)
        self.logo_preview = QLabel()
        self.logo_preview.setFixedHeight(120)
        self.logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_col.addWidget(self.logo_preview)

        row.addLayout(left_col)
        row.addLayout(right_col)
        layout.addLayout(row)

        # Create button
        create_btn = QPushButton("Create House")
        create_btn.setStyleSheet("background:#084924; color:white; padding:10px; border-radius:8px;")
        create_btn.clicked.connect(self.on_create)
        layout.addWidget(create_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def select_banner(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Banner Image", os.path.expanduser("~"), "Images (*.png *.jpg *.jpeg)")
        if path:
            self.banner_path = path
            self.update_preview(path)

    def select_logo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Logo Image", os.path.expanduser("~"), "Images (*.png *.jpg *.jpeg)")
        if path:
            self.logo_path = path
            self.update_preview(path)

    def update_preview(self, path):
        pix = QPixmap(path)
        if not pix.isNull():
            scaled = pix.scaledToHeight(120, Qt.TransformationMode.SmoothTransformation)
            # assign to both previews depending on which file was set last
            if path == self.banner_path:
                self.banner_preview.setPixmap(scaled)
            elif path == self.logo_path:
                self.logo_preview.setPixmap(scaled)

    def on_create(self):
        name = self.name_input.text().strip()
        desc = self.desc_input.toPlainText().strip()
        slug = self.slug_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Validation", "Please provide a house name.")
            return

        # Prepare data and files
        data = {"name": name, "description": desc}
        if slug:
            data["slug"] = slug
        # Use ExitStack to ensure files are closed after request
        try:
            # Use controller helper if available
            token = self.token
            if not token:
                # try reading token from controller attribute if present
                token = getattr(self.controller, "token", None)

            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"

            url = f"{self.api_base}/api/house/houses/"
            with contextlib.ExitStack() as stack:
                files = {}
                if self.banner_path:
                    files["banner"] = stack.enter_context(open(self.banner_path, "rb"))
                if self.logo_path:
                    files["logo"] = stack.enter_context(open(self.logo_path, "rb"))

                resp = requests.post(url, data=data, files=files or None, headers=headers)

            if resp.status_code in (200, 201):
                QMessageBox.information(self, "Success", "House created successfully.")
                # optionally clear form
                self.name_input.clear()
                self.desc_input.clear()
                # clear slug input and previews
                try:
                    self.slug_input.clear()
                except Exception:
                    pass
                try:
                    self.banner_preview.clear()
                except Exception:
                    pass
                try:
                    self.logo_preview.clear()
                except Exception:
                    pass
                self.banner_path = None
                self.logo_path = None
            else:
                try:
                    err = resp.json()
                except Exception:
                    err = resp.text
                QMessageBox.critical(self, "Error", f"Failed to create house: {resp.status_code}\n{err}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error: {e}")

    def on_name_changed(self, text: str):
        # simple slugify preview locally (backend will ensure uniqueness)
        slug = text.strip().lower()
        slug = re.sub(r"[^a-z0-9\-]+", "-", slug)
        slug = re.sub(r"-+", "-", slug).strip("-")
        self.slug_input.setPlaceholderText(f"e.g. {slug}")
