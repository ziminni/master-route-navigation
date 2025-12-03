import logging
import traceback

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWidgets import QApplication, QMainWindow

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Safe imports for local modules
try:
    from .main_chat_widget_wrapper import MainChatWidgetWrapper as StudentMainUI
except Exception:
    logger.exception("Error importing StudentMainUI (main_chat_widget_wrapper)")
    StudentMainUI = None

try:
    from .faculty_app import FacultyMainUI
except Exception:
    logger.exception("Error importing FacultyMainUI (faculty_app)")
    FacultyMainUI = None

try:
    from .admin_wrapper import AdminMainUI
except Exception:
    logger.exception("Error importing AdminMainUI (admin_wrapper)")
    AdminMainUI = None

try:
    from .org_wrapper import OrgMainUI
except Exception:
    logger.exception("Error importing OrgMainUI (org_wrapper)")
    OrgMainUI = None

try:
    from .data_manager import DataManager
except Exception:
    logger.exception("Error importing DataManager (data_manager)")
    DataManager = None

m = None
def _short_token(tok: str, max_len: int = 20) -> str:
    """Helper for logging: show only start/end of token."""
    if not tok:
        return "<EMPTY>"
    tok = str(tok)
    if len(tok) <= max_len:
        return tok
    half = max_len // 2
    return f"{tok[:half]}...{tok[-half:]}"


class LauncherWindow(QtWidgets.QWidget):
    """
    CISC Virtual Hub Launcher (Unified Window Version)

    - Used as a QWidget so Router can embed it in its QStackedWidget.
    - Can also be run standalone in a QMainWindow.
    """

    def __init__(self, username, roles, primary_role, token, user_id=None, parent=None):
        logger.debug(
            "Initializing LauncherWindow | username=%r roles=%r primary_role=%r token_snip=%s user_id=%r",
            username,
            roles,
            primary_role,
            _short_token(token),
            user_id,
        )
        super().__init__(parent)

        logger.info(
            "LAUNCHER: init | username=%r primary_role=%r token_snip=%s",
            username,
            primary_role,
            _short_token(token),
        )

        self.username = username
        self.roles = roles or []
        self.primary_role = primary_role
        self.token = token

        # Initialize shared DataManager with session info
        if DataManager is None:
            logger.error("DataManager is None, likely failed to import.")
            self.data_manager = None
        else:
            try:
                logger.debug(
                    "Creating DataManager with username=%r primary_role=%r token_snip=%s",
                    username,
                    primary_role,
                    _short_token(token),
                )
                self.data_manager = DataManager(
                    username=username,
                    roles=self.roles,
                    primary_role=primary_role,
                    token=token,
                )
                self.user_id = self.data_manager.get_current_user_id()  # numeric id of logged-in user, if you have it
                logger.debug(
                    "DataManager initialized successfully (token_snip=%s).",
                    _short_token(self.data_manager.token if hasattr(self.data_manager, 'token') else token),
                )

            except Exception:
                logger.exception("Failed to initialize DataManager.")
                self.data_manager = None

        self.setStyleSheet("background-color: #f8f9fa;")

        # Main stacked layout on this widget
        try:
            self.main_layout = QtWidgets.QStackedLayout(self)
            self.setLayout(self.main_layout)
        except Exception:
            logger.exception("Failed to create main QStackedLayout.")
            raise

        # Role-specific screens (lazy created)
        self.student_widget = None
        self.faculty_widget = None
        self.admin_widget = None
        self.org_widget = None

        # Placeholder launcher_widget if you have a menu screen
        self.launcher_widget = QtWidgets.QWidget(self)
        self.main_layout.addWidget(self.launcher_widget)

        # Auto-open based on primary_role (fallback to roles list)
        try:
            self.auto_open_for_role()
        except Exception:
            logger.exception("Error during auto_open_for_role().")

    # ------------------------------------------------------------
    # Auto-open portal based on role
    # ------------------------------------------------------------
    def auto_open_for_role(self):
        role = (self.primary_role or "").lower()
        roles_lower = [str(r).lower() for r in self.roles]
        logger.debug(
            "auto_open_for_role called | primary_role=%r roles=%r token_snip=%s",
            role,
            roles_lower,
            _short_token(self.token),
        )

        if role == "student" or "student" in roles_lower:
            logger.info("Auto-opening Student portal.")
            self.toggle_student_portal(open_only=True)
        elif role == "faculty" or "faculty" in roles_lower:
            logger.info("Auto-opening Faculty portal.")
            self.toggle_faculty_portal(open_only=True)
        elif role == "admin" or "admin" in roles_lower:
            logger.info("Auto-opening Admin portal.")
            self.toggle_admin_portal(open_only=True)
        elif role == "org officer" or "org officer" in roles_lower:
            logger.info("Auto-opening Org Officer portal.")
            self.toggle_org_portal(open_only=True)
        else:
            logger.info("No matching role found; staying on launcher.")
            self.main_layout.setCurrentWidget(self.launcher_widget)

    # ------------------------------------------------------------
    # Button style helper
    # ------------------------------------------------------------
    def button_style(self, color, small=False):
        padding = "10px 20px" if small else "15px 30px"
        font_size = "14px" if small else "18px"
        try:
            darker1 = self.darken(color, 0.15)
            darker2 = self.darken(color, 0.3)
        except Exception:
            logger.exception("Error darkening color %r; using fallback.", color)
            darker1 = color
            darker2 = color

        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                font-size: {font_size};
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: {padding};
                min-height: 50px;
            }}
            QPushButton:hover {{
                background-color: {darker1};
            }}
            QPushButton:pressed {{
                background-color: {darker2};
            }}
        """

    def darken(self, hex_color, factor):
        logger.debug("darken called with color=%r factor=%r", hex_color, factor)
        try:
            c = int(hex_color.lstrip("#"), 16)
            r, g, b = (c >> 16) & 255, (c >> 8) & 255, c & 255
            r = max(0, int(r * (1 - factor)))
            g = max(0, int(g * (1 - factor)))
            b = max(0, int(b * (1 - factor)))
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            logger.exception("Failed to darken color %r", hex_color)
            return hex_color

    # ------------------------------------------------------------
    # Safe wrappers for button slots
    # ------------------------------------------------------------
    def _safe_toggle_student(self):
        try:
            self.toggle_student_portal()
        except Exception:
            logger.exception("Exception in _safe_toggle_student.")
            traceback.print_exc()

    def _safe_toggle_faculty(self):
        try:
            self.toggle_faculty_portal()
        except Exception:
            logger.exception("Exception in _safe_toggle_faculty.")
            traceback.print_exc()

    def _safe_toggle_admin(self):
        try:
            self.toggle_admin_portal()
        except Exception:
            logger.exception("Exception in _safe_toggle_admin.")
            traceback.print_exc()

    def _safe_toggle_org(self):
        try:
            self.toggle_org_portal()
        except Exception:
            logger.exception("Exception in _safe_toggle_org.")
            traceback.print_exc()

    # ------------------------------------------------------------
    # Toggling between launcher / student / faculty / admin / org
    # ------------------------------------------------------------
    def toggle_student_portal(self, open_only=False):
        logger.debug(
            "toggle_student_portal called | open_only=%r token_snip=%s",
            open_only,
            _short_token(self.token),
        )

        if StudentMainUI is None:
            logger.error("StudentMainUI is None; cannot open Student portal.")
            return

        if self.student_widget is None:
            try:
                logger.debug(
                    "Creating StudentMainUI with token_snip=%s",
                    _short_token(self.token),
                )
                self.student_widget = StudentMainUI(
                    parent=self,
                    current_user_id=self.user_id,
                    current_username=self.username,
                    current_token=self.token,
                    data_manager=self.data_manager,
                    layout_manager = None #pass shared DataManager
                )
                self.main_layout.addWidget(self.student_widget)
                logger.info("StudentMainUI created and added to layout.")
                if hasattr(self.student_widget, "go_back"):
                    self.student_widget.go_back.connect(self.return_to_launcher)
            except Exception:
                logger.exception("Failed to create or add StudentMainUI.")
                return

        if open_only:
            self.main_layout.setCurrentWidget(self.student_widget)
            return

        if self.main_layout.currentWidget() == self.launcher_widget:
            self.main_layout.setCurrentWidget(self.student_widget)
        else:
            self.return_to_launcher()

    def toggle_faculty_portal(self, open_only=False):
        logger.debug(
            "toggle_faculty_portal called | open_only=%r token_snip=%s",
            open_only,
            _short_token(self.token),
        )

        if FacultyMainUI is None:
            logger.error("FacultyMainUI is None; cannot open Faculty portal.")
            return

        if self.faculty_widget is None:
            try:
                logger.debug(
                    "Creating FacultyMainUI with token_snip=%s",
                    _short_token(self.token),
                )
                self.faculty_widget = FacultyMainUI(
                    username=self.username,
                    roles=self.roles,
                    primary_role="faculty",
                    token=self.token,
                    data_manager=self.data_manager,
                    parent=self,
                    layout_manager=None
                )
                self.main_layout.addWidget(self.faculty_widget)
                logger.info("FacultyMainUI created and added to layout.")
                if hasattr(self.faculty_widget, "go_back"):
                    self.faculty_widget.go_back.connect(self.return_to_launcher)
            except Exception:
                logger.exception("Failed to create or add FacultyMainUI.")
                return

        if open_only:
            self.main_layout.setCurrentWidget(self.faculty_widget)
            return

        if self.main_layout.currentWidget() == self.launcher_widget:
            self.main_layout.setCurrentWidget(self.faculty_widget)
        else:
            self.return_to_launcher()

    def toggle_admin_portal(self, open_only=False):
        logger.debug(
            "toggle_admin_portal called | open_only=%r token_snip=%s",
            open_only,
            _short_token(self.token),
        )

        if AdminMainUI is None:
            logger.error("AdminMainUI is None; cannot open Admin portal.")
            return

        if self.admin_widget is None:
            try:
                logger.debug(
                    "Creating AdminMainUI with token_snip=%s",
                    _short_token(self.token),
                )
                self.admin_widget = AdminMainUI(
                    username=self.username,
                    roles=self.roles,
                    primary_role=self.primary_role,
                    token=self.token,
                    data_manager=self.data_manager,
                    parent=self,

                )
                self.main_layout.addWidget(self.admin_widget)
                logger.info("AdminMainUI created and added to layout.")
            except Exception:
                logger.exception("Failed to create or add AdminMainUI.")
                return

        if open_only:
            self.main_layout.setCurrentWidget(self.admin_widget)
            return

        if self.main_layout.currentWidget() == self.launcher_widget:
            self.main_layout.setCurrentWidget(self.admin_widget)
        else:
            self.return_to_launcher()

    def toggle_org_portal(self, open_only=False):
        logger.debug(
            "toggle_org_portal called | open_only=%r token_snip=%s",
            open_only,
            _short_token(self.token),
        )

        if OrgMainUI is None:
            logger.error("OrgMainUI is None; cannot open Org Officer portal.")
            return

        if self.org_widget is None:
            try:
                logger.debug(
                    "Creating OrgMainUI with token_snip=%s",
                    _short_token(self.token),
                )
                self.org_widget = OrgMainUI(
                    username=self.username,
                    roles=self.roles,
                    primary_role="org officer",
                    token=self.token,
                    data_manager=self.data_manager,
                    parent=self,
                    layout_manager = m
                )
                self.main_layout.addWidget(self.org_widget)
                logger.info("OrgMainUI created and added to layout.")
            except Exception:
                logger.exception("Failed to create or add OrgMainUI.")
                return

        if open_only:
            self.main_layout.setCurrentWidget(self.org_widget)
            return

        if self.main_layout.currentWidget() == self.launcher_widget:
            self.main_layout.setCurrentWidget(self.org_widget)
        else:
            self.return_to_launcher()

    # ------------------------------------------------------------
    # Return to launcher
    # ------------------------------------------------------------
    def return_to_launcher(self):
        logger.debug(
            "return_to_launcher called | token_snip=%s",
            _short_token(self.token),
        )
        try:
            self.main_layout.setCurrentWidget(self.launcher_widget)
        except Exception:
            logger.exception("Failed to switch back to launcher_widget.")
