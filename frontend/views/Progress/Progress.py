import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont

# Import the student views of the Progress page
from .Student.grades import GradesWidget


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

        # ✅ Create layout first
        layout = QVBoxLayout(self)

        # ✅ Load role-specific page (for now, student only)
        if primary_role == "student":
            progress_widget = GradesWidget(user_role="student")
        else:
            progress_widget = self._create_default_widget(
                "Progress", f"No progress page available for role: {primary_role}"
            )

        layout.addWidget(progress_widget)

        self.setLayout(layout)
        self.load_styles()

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

    # ---------------------------------------------------------
    def load_styles(self):
        """Loads stylesheet from /frontend/views/Progress/Styles/styles.qss"""
        try:
            styles_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "Styles", "styles.qss"
            )
            if os.path.exists(styles_path):
                with open(styles_path, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
                print(f"✅ Progress: Loaded styles from {styles_path}")
            else:
                print(f"⚠️ Progress: Stylesheet not found at {styles_path}")
        except Exception as e:
            print(f"❌ Progress: Error loading styles: {e}")