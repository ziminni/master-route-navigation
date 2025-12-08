# C:\Users\Jairuz\Desktop\momod4\frontend\views\Progress\Progress.py
import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication
from PyQt6.QtGui import QFont

# Import role-specific widgets. They now accept token in constructors.
try:
    from .Student.grades import GradesWidget
    try:
        # Faculty/Admin sections may not exist in the Student folder; safe import
        from .Faculty.sections import SectionsWidget as FacultySectionsWidget
    except Exception:
        FacultySectionsWidget = None

    try:
        from .Admin.sections import SectionsWidget as AdminSectionsWidget
    except Exception:
        AdminSectionsWidget = None

except Exception as import_error:
    import traceback
    traceback.print_exc()
    error_msg = str(import_error)

    # Fallback placeholder widgets when imports fail
    from PyQt6.QtWidgets import QVBoxLayout

    class GradesWidget(QWidget):
        def __init__(self, username=None, user_role="student", token=None):
            super().__init__()
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel(f"Error loading GradesWidget: {error_msg}"))

    class FacultySectionsWidget(QWidget):
        def __init__(self, username=None, token=None):
            super().__init__()
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel(f"Error loading Faculty SectionsWidget: {error_msg}"))

    class AdminSectionsWidget(QWidget):
        def __init__(self, username=None, token=None):
            super().__init__()
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel(f"Error loading Admin SectionsWidget: {error_msg}"))


class Progress(QWidget):
    """
    Router entry for the Progress page. Instantiates the role-specific widget and
    forwards the auth token so those widgets call the backend API instead of
    reading local JSON files.
    """

    def __init__(self, username: str, roles: list, primary_role: str, token: str | None):
        super().__init__()
        self.username = username
        self.roles = roles or []
        self.primary_role = primary_role
        self.token = token

        layout = QVBoxLayout(self)

        # Role-based routing. Pass username and token into widgets that need them.
        if primary_role == "student":
            progress_widget = GradesWidget(username=username, user_role="student", token=token)

        elif primary_role == "faculty":
            if FacultySectionsWidget is not None:
                # FacultySectionsWidget should accept (username, token) if implemented.
                try:
                    progress_widget = FacultySectionsWidget(username=username, user_role="faculty", token=token)
                except TypeError:
                    progress_widget = FacultySectionsWidget()
            else:
                progress_widget = self._create_default_widget(
                    "Faculty Progress",
                    "Faculty sections view not implemented."
                )

        elif primary_role == "admin":
            if AdminSectionsWidget is not None:
                try:
                    progress_widget = AdminSectionsWidget(username=username, user_role="admin",token=token)
                except TypeError:
                    progress_widget = AdminSectionsWidget()
            else:
                progress_widget = self._create_default_widget(
                    "Admin Progress",
                    "Admin sections view not implemented."
                )

        else:
            progress_widget = self._create_default_widget(
                "Progress",
                f"No progress page available for role: {primary_role}"
            )

        layout.addWidget(progress_widget)

        # Apply QSS stylesheet recursively if present in Styles/styles.qss
        try:
            qss_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Styles", "styles.qss")
            if os.path.exists(qss_path):
                with open(qss_path, "r", encoding="utf-8") as f:
                    qss = f.read()

                self.setStyleSheet(qss)
                progress_widget.setStyleSheet(qss)

                # Apply to children of the role widget
                for child in progress_widget.findChildren(QWidget):
                    try:
                        child.setStyleSheet(qss)
                    except Exception:
                        pass

                app = QApplication.instance()
                if app is not None:
                    try:
                        app.setStyleSheet(qss)
                    except Exception:
                        pass
            # If stylesheet missing, continue silently
        except Exception:
            # Do not block UI creation on stylesheet errors
            pass

        self.setLayout(layout)

    def _create_default_widget(self, title: str, desc: str) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 18, 75))
        desc_label = QLabel(desc)
        desc_label.setFont(QFont("Arial", 12))
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addStretch()
        widget.setLayout(layout)
        return widget