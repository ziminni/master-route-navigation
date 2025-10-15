"""
PyQt6 Login UI (Wide Rectangular Card with Logo + Header Text)
Wired to backend/User AuthService (PostgreSQL + bcrypt)
"""
from .Dashboard import Dashboard
from .resetpassword import ResetPasswordWidget


from pathlib import Path
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPalette, QColor, QFont, QPixmap
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpacerItem,
    QSizePolicy, QLineEdit, QPushButton, QFrame,
    QGraphicsDropShadowEffect, QMessageBox
)


from services.auth_service import AuthService

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parents[2] 
ASSETS_DIR = BASE_DIR / "assets" / "images"

class LoginWidget(QWidget):
    forgot_password_requested = pyqtSignal()
    login_successful = pyqtSignal(object)  # Emits username (or email) on success

    def __init__(self, parent=None):
        super().__init__(parent)
        self.auth_service = AuthService() 

        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor("#f8f9fa"))
        self.setPalette(pal)
        self.setAutoFillBackground(True)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(40)

        # --- Left column ---
        left_layout = QVBoxLayout()
        left_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.left_logo = QLabel()
        self.left_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.left_logo.setPixmap(
            QPixmap(str(ASSETS_DIR / "cisc_logo.jpg")).scaled(
                220, 220, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
        )
        left_layout.addWidget(self.left_logo)

        self.left_label = QLabel("CISC VIRTUAL HUB")
        self.left_label.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        self.left_label.setStyleSheet("color: #6c757d;")
        self.left_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.left_label)

        left_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        main_layout.addLayout(left_layout, stretch=1)

        # --- Right column ---
        right_layout = QVBoxLayout()
        right_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        card = QFrame()
        card.setFixedWidth(500)
        shadow = QGraphicsDropShadowEffect(blurRadius=20, xOffset=0, yOffset=3, color=QColor(0, 0, 0, 40))
        card.setGraphicsEffect(shadow)
        card.setStyleSheet("QFrame { background: white; border-radius: 8px; border: none; }")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 30, 40, 30)
        card_layout.setSpacing(16)

        # Header (logo + text)
        header_layout = QHBoxLayout()
        self.uni_logo = QLabel()
        self.uni_logo.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.uni_logo.setPixmap(
            QPixmap(str(ASSETS_DIR / "cmu_cisc_logo.jpg")).scaled(
                80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
        )
        header_layout.addWidget(self.uni_logo)

        text_layout = QVBoxLayout()
        self.uni_title = QLabel("Central Mindanao University")
        self.uni_title.setStyleSheet("color: #212529;")
        self.uni_title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.uni_subtitle = QLabel("College of Information Sciences and Computing")
        self.uni_subtitle.setStyleSheet("color: #495057;")
        self.uni_subtitle.setFont(QFont("Segoe UI", 12))
        text_layout.addWidget(self.uni_title)
        text_layout.addWidget(self.uni_subtitle)
        header_layout.addLayout(text_layout)
        card_layout.addLayout(header_layout)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        divider.setStyleSheet("color: #006400;")
        card_layout.addWidget(divider)

        # Sign In
        self.card_title = QLabel("Sign In")
        self.card_title.setStyleSheet("color: #212529; margin-top: 5px;")
        self.card_title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        card_layout.addWidget(self.card_title)

        # Username/Email
        self.email_label = QLabel("Username") 
        self.email_label.setStyleSheet("color: #495057; margin-top: 5px;")
        card_layout.addWidget(self.email_label)

        self.email_input = QLineEdit(placeholderText="Enter Username")
        self.email_input.setStyleSheet("border: 1px solid #ccc; border-radius: 6px; padding: 10px;")
        card_layout.addWidget(self.email_input)

        self.email_error_label = QLabel()
        self.email_error_label.setStyleSheet("color: red; margin-left: 5px;")
        self.email_error_label.hide()
        card_layout.addWidget(self.email_error_label)

        # Password
        self.password_label = QLabel("Password")
        self.password_label.setStyleSheet("color: #495057; margin-top: 5px;")
        card_layout.addWidget(self.password_label)

        self.password_input = QLineEdit(placeholderText="Enter Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("border: 1px solid #ccc; border-radius: 6px; padding: 10px;")
        card_layout.addWidget(self.password_input)

        self.password_error_label = QLabel()
        self.password_error_label.setStyleSheet("color: red; margin-left: 5px;")
        self.password_error_label.hide()
        card_layout.addWidget(self.password_error_label)

        # Forgot Password
        self.forgot_password_link = QLabel("Forgot Password?")
        self.forgot_password_link.setStyleSheet("QLabel { color: #007bff; } QLabel:hover { text-decoration: underline; }")
        self.forgot_password_link.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.forgot_password_link.setCursor(Qt.CursorShape.PointingHandCursor)
        self.forgot_password_link.mousePressEvent = self.open_reset_password_window
        card_layout.addWidget(self.forgot_password_link)

        # Sign In button
        self.sign_in_btn = QPushButton("Sign In")
        self.sign_in_btn.setStyleSheet(
            "QPushButton { background-color: #006400; color: white; padding: 10px; "
            "border-radius: 6px; border: none; font-weight: bold; } "
            "QPushButton:hover { background-color: #228B22; }"
        )
        self.sign_in_btn.setMinimumHeight(38)
        self.sign_in_btn.clicked.connect(self.validate_login)
        card_layout.addWidget(self.sign_in_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        right_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)
        right_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        main_layout.addLayout(right_layout, stretch=3)

        self.setLayout(main_layout)

    # ------------------ Actions ------------------

    def open_reset_password_window(self, event):
        self.forgot_password_requested.emit()
        self.forgot_password = ResetPasswordWidget()
        self.forgot_password.show()
        self.close()
    
    # def closeEvent(self, event):
    #     if QMessageBox.question(self, "Exit", "Are you sure you want to exit?",
    #                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    #                             QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
    #         event.accept()
    #     else:
    #         event.ignore()

    def validate_login(self):
        self.email_error_label.hide()
        self.password_error_label.hide()

        username = (self.email_input.text() or "").strip()
        password = (self.password_input.text() or "").strip()

        if not username or not password:
            self.password_error_label.setText("Both fields are required.")
            self.password_error_label.show()
            return

        try:
            result = self.auth_service.login(username, password)
        except Exception:
            self.password_error_label.setText("Authentication error. Check DB connection.")
            self.password_error_label.show()
            return

        if not result.ok:
            self.password_error_label.setText(result.error or "Incorrect username or password.")
            self.password_error_label.show()
            return

        # SUCCESS — emit the full result for other components to use
        self.login_successful.emit(result)
        # Let MainWindow decide when to close this
        # self.close()
    



