import sys
import os

from PyQt6.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget
from views.Login.login import LoginWidget
from services.auth_service import AuthService
from widgets.layout_manager import LayoutManager
from router.router import Router
from views.Login.resetpassword import ResetPasswordWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.auth_service = AuthService()
        self.user_session = None
        self.router = None
        self.layout_manager = None
        self._show_login()

    # ---------- safe resize ----------
    def resizeEvent(self, event):
        lm = getattr(self, "layout_manager", None)
        if lm is not None:
            try:
                lm.update_layout(self.width())
            except Exception:
                pass
        return super().resizeEvent(event)

    # ---------- login screen ----------
    def _show_login(self):
        old = self.takeCentralWidget()
        if old: old.deleteLater()
        self.layout_manager = None
        self.router = None

        self.login_widget = LoginWidget()
        self.setCentralWidget(self.login_widget)
        self.setWindowTitle("CISC Virtual Hub - Login")
        self.setGeometry(100, 100, 900, 600)

        # ADD THIS: go to reset screen
        self.login_widget.forgot_password_requested.connect(self._show_reset_password)

        # existing: proceed to dashboard on success
        self.login_widget.login_successful.connect(self.open_dashboard)

    def _show_reset_password(self):
        # swap central widget to the reset screen
        old = self.takeCentralWidget()
        if old: old.deleteLater()
        self.layout_manager = None
        self.router = None

        self.reset_widget = ResetPasswordWidget()
        self.reset_widget.back_to_signin_requested.connect(self._show_login)
        self.setCentralWidget(self.reset_widget)
        self.setWindowTitle("CISC Virtual Hub - Reset Password")

    # callback used by Router on logout
    def _return_to_login(self):
        self._show_login()

    # ---------- post-login ----------
    def open_dashboard(self, result):
        self.user_session = {
            "username": result.username,
            "roles": result.roles,
            "primary_role": result.primary_role,
            "token": result.token,
        }

        self.router = Router(
            user_role=self.user_session["primary_role"],
            user_session=self.user_session,
            on_logout=self._return_to_login,   # critical
        )

        container = QWidget()
        grid = QGridLayout(container)

        self.layout_manager = LayoutManager(
            main_layout=grid,
            content=self.router.stack,
            router=self.router,
            user_role=self.user_session["primary_role"],
        )

        self.setCentralWidget(container)
        self.layout_manager.update_layout(self.width())  # one-time kick
        self.router.navigate(page_id=1, is_modular=False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
