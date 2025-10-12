import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget
from views.Login.login import LoginWidget
from services.auth_service import AuthService
from widgets.layout_manager import LayoutManager
from router.router import Router

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.auth_service = AuthService()
        self.login_widget = LoginWidget()
        # Store session data
        self.user_session = None

        self.setCentralWidget(self.login_widget)

        self.setWindowTitle("CISC Virtual Hub - Login")
        self.setGeometry(100, 100, 900, 600)

        self.login_widget.login_successful.connect(self.open_dashboard)

    def open_dashboard(self, result):
        print(f"Login OK for {result.username} | roles={result.roles} | primary={result.primary_role}")
        # Store user session data
        self.user_session = {
            "username": result.username,
            "roles": result.roles,
            "primary_role": result.primary_role,
            "token": result.token
        }

        # Initialize Router with user session data
        router = Router(
            user_role=self.user_session["primary_role"],
            user_session=self.user_session
        )

        # Create main layout and content widget for LayoutManager
        main_layout = QGridLayout()
        content = router.stack
        content.setStyleSheet("QStackedWidget { background: #ffffff; }")

        # Create a container widget for the LayoutManager
        container = QWidget()
        container.setLayout(main_layout)

        # Initialize LayoutManager with the dynamic user_role
        self.layout_manager = LayoutManager(
            main_layout=main_layout,
            content=content,
            router=router,
            user_role=self.user_session["primary_role"]
        )

        # Update layout based on initial window width
        self.layout_manager.update_layout(self.width())
        print(f"MainWindow: Initialized layout, sidebar collapsed: {self.layout_manager.navbar.is_collapsed}")

        # Set the container as the central widget
        self.setCentralWidget(container)

        # Connect resize event to update layout dynamically
        self.resizeEvent = lambda event: self.layout_manager.update_layout(self.width())

        # Navigate to the Dashboard page (main_id=1 in navbar.json)
        router.navigate(page_id=1, is_modular=False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())