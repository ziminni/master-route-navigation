"""
CISC Virtual Hub Main entry point
login → reset → profile via QStackedWidget
"""

import sys
import requests
import warnings
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QMessageBox
)
from PyQt6.QtCore import QSize

import login
import resetpassword
import user_profile

warnings.filterwarnings("ignore", category=DeprecationWarning)

START_WIDTH  = 1200
START_HEIGHT = 1080
MIN_WIDTH    = 800
MIN_HEIGHT   = 800


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CISC Virtual Hub")
        self.setMinimumSize(QSize(MIN_WIDTH, MIN_HEIGHT))
        self.resize(START_WIDTH, START_HEIGHT)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Pages
        self.login_page   = login.LoginWidget()
        self.reset_page   = resetpassword.ResetPasswordWidget()
        self.profile_page = user_profile.ProfileWidget()

        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.reset_page)
        self.stack.addWidget(self.profile_page)

        # Navigation
        self.login_page.forgot_password_requested.connect(
            lambda: self.stack.setCurrentWidget(self.reset_page))
        self.reset_page.back_to_signin_requested.connect(
            lambda: self.stack.setCurrentWidget(self.login_page))
        self.login_page.login_successful.connect(
            lambda: self.stack.setCurrentWidget(self.profile_page))

        self.stack.setCurrentWidget(self.login_page)

    def closeEvent(self, event):
        if QMessageBox.question(self, "Exit", "Are you sure you want to exit?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()