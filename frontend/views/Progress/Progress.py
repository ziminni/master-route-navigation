import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication
from PyQt6.QtGui import QFont

# Import views in Progress folder
from .Student.grades import GradesWidget
# from .Faculty.(homepage file here) import (homepage file class name)
# from .Admin.(homepage file here) import (homepage file class name)


class Progress(QWidget):
    """
    Acts as the router entry for the Progress page.
    Chooses which role-specific Progress view to show.
    """
    def __init__(self, username, roles, primary_role, token):
        super().__init__()
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token

        layout = QVBoxLayout(self)

        # Load role-specific page (for now, student only)
        if primary_role == "student":
            progress_widget = GradesWidget(user_role="student")

        # ------------------------------------------------
        #                 FOR USER ROLES
        # ------------------------------------------------
        # if primary_role == "faculty":
        #     progress_widget = (Faculty)Widget(user_role="faculty")
        # if primary_role == "admin":
        #     progress_widget = (Admin)Widget(user_role="admin")

        else:
            progress_widget = self._create_default_widget(
                "Progress", f"No progress page available for role: {primary_role}"
            )

        layout.addWidget(progress_widget)

        # ------------------------------------------------
        # Apply Progress QSS stylesheet recursively
        # ------------------------------------------------
        try:
            qss_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "Styles", "styles.qss"
            )
            if os.path.exists(qss_path):
                with open(qss_path, "r", encoding="utf-8") as f:
                    qss = f.read()

                    # Apply to Progress
                    self.setStyleSheet(qss)

                    # Apply to GradesWidget and all its child widgets
                    progress_widget.setStyleSheet(qss)
                    for child in progress_widget.findChildren(QWidget):
                        child.setStyleSheet(qss)

                    # Force a style refresh
                    app = QApplication.instance()
                    if app is not None:
                        app.setStyleSheet(qss)

                print(f"✅ Progress: QSS applied from {qss_path}")
            else:
                print(f"⚠️ Progress: Stylesheet not found at {qss_path}")
        except Exception as e:
            print(f"❌ Progress: Error applying QSS: {e}")

        self.setLayout(layout)

    # ---------------------------------------------------------
    def _create_default_widget(self, title, desc):
        """Fallback placeholder when no role-specific view exists."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        desc_label = QLabel(desc)
        desc_label.setFont(QFont("Arial", 12))
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addStretch()
        widget.setLayout(layout)
        return widget