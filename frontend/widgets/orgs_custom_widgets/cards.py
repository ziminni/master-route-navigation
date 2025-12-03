from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainterPath, QColor, QPainter
from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QMessageBox
import datetime

from .styles import (
    STYLE_GREEN_BTN, STYLE_RED_BTN, STYLE_PRIMARY_BTN, 
    STYLE_YELLOW_BTN, STYLE_OFFICER_BTN
)

from views.Organizations.BrowseView.Utils.image_utils import get_image_path

def create_rounded_pixmap(source_pixmap, radius=10):
    size = source_pixmap.size()
    rounded = QPixmap(size)
    rounded.fill(Qt.GlobalColor.transparent)
    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    path = QPainterPath()
    path.addRoundedRect(0, 0, size.width(), size.height(), radius, radius)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, source_pixmap)
    painter.end()
    return rounded

class BaseCard(QtWidgets.QFrame):
    def __init__(self, blur_radius=15, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(blur_radius)
        shadow.setXOffset(5)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

        self.setStyleSheet("""
            QFrame {
                background-color: #fff;
                border: 1px solid #ccc;
                border-radius: 10px;
            }
        """)

class BaseOrgCard(BaseCard):
    def __init__(self, *args, **kwargs):
        super().__init__(blur_radius=15, *args, **kwargs)

    def _create_logo_label(self, logo_path, size=200, radius=10):
        logo_label = QtWidgets.QLabel()
        logo_label.setMaximumSize(size, size)
        logo_label.setMinimumSize(size, size)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        logo_label.setStyleSheet("border: none; background-color: transparent;")

        resolved_logo_path = get_image_path(logo_path)
        
        if resolved_logo_path != "No Photo":
            pixmap = QPixmap(resolved_logo_path).scaled(
                size, size, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            if not pixmap.isNull():
                rounded_pixmap = create_rounded_pixmap(pixmap, radius)
                logo_label.setPixmap(rounded_pixmap)
            else:
                logo_label.setText("No Logo")
        else:
            logo_label.setText("No Logo")
        return logo_label

class JoinedOrgCard(BaseOrgCard):
    def __init__(self, logo_path, org_data, main_window):
        super().__init__()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignHCenter)

        logo_label = self._create_logo_label(logo_path, size=200, radius=10)

        btn_details = QtWidgets.QPushButton("More Details")
        btn_details.setStyleSheet(STYLE_YELLOW_BTN)
        btn_details.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        btn_details.clicked.connect(lambda: main_window.show_org_details(org_data))

        layout.addWidget(logo_label, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(btn_details)

class CollegeOrgCard(BaseOrgCard):
    def __init__(self, logo_path, description, org_data, main_window):
        super().__init__()
        
        self.org_data = org_data
        self.main_window = main_window
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignBottom | QtCore.Qt.AlignmentFlag.AlignHCenter)

        # Show "Inactive" label if organization is not active
        if not org_data.get("is_active", True):
            inactive_label = QtWidgets.QLabel("INACTIVE")
            inactive_label.setStyleSheet("""
                border: none; 
                background-color: #ff6b6b; 
                color: white; 
                font-weight: bold; 
                font-size: 10px;
                padding: 2px 8px;
                border-radius: 3px;
            """)
            inactive_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(inactive_label, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

        logo_label = self._create_logo_label(logo_path, size=200, radius=10)

        # Organization name label
        name_label = QtWidgets.QLabel()
        name_label.setStyleSheet("border: none; background-color: transparent; font-weight: bold; font-size: 14px;")
        name_label.setText(org_data.get("name", "Unknown"))
        name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        name_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        name_label.setWordWrap(True)

        # Organization description label
        desc_label = QtWidgets.QLabel()
        desc_label.setStyleSheet("border: none; background-color: transparent; color: #666; font-size: 11px;")
        desc_label.setMaximumHeight(40)
        desc_label.setText(description)
        desc_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        desc_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        desc_label.setWordWrap(True)

        btn_details = QtWidgets.QPushButton("More Details")
        
        self.btn_apply = QtWidgets.QPushButton() 
        self.btn_apply.setObjectName("apply_btn")
        
        btn_details.setStyleSheet(STYLE_YELLOW_BTN)
        
        self._update_apply_button_status() 
        
        btn_details.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.btn_apply.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        
        btn_details.clicked.connect(lambda: main_window.show_org_details(org_data))

        layout.addWidget(logo_label, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(name_label)
        layout.addWidget(desc_label)
        layout.addWidget(btn_details)
        layout.addWidget(self.btn_apply)

    def _update_apply_button_status(self):
            """Checks the student's status and sets the apply button accordingly."""
            student_name = getattr(self.main_window, 'name', None)
            if not student_name:
                self.btn_apply.setVisible(False)
                return

            members = self.org_data.get("members", [])
            applicants = self.org_data.get("applicants", [])
            cooldowns = self.org_data.get("kick_cooldowns", {})

            is_member = any(member[0] == student_name for member in members)
            is_applicant = any(applicant[0] == student_name for applicant in applicants)
            
            on_kick_cooldown = False
            kick_cooldown_str = ""
            if student_name in cooldowns:
                try:
                    kick_time = datetime.datetime.fromisoformat(cooldowns[student_name])
                    cooldown_duration = datetime.timedelta(hours=1) # 1-hour kick cooldown
                    expiry_time = kick_time + cooldown_duration
                    
                    if datetime.datetime.now() < expiry_time:
                        on_kick_cooldown = True
                        remaining_time = expiry_time - datetime.datetime.now()
                        total_minutes = int(remaining_time.total_seconds() // 60)
                        kick_cooldown_str = f" ({total_minutes}m left)"
                    else:
                        pass 
                except (ValueError, TypeError):
                    pass 

            try:
                self.btn_apply.clicked.disconnect()
            except TypeError:
                pass 

            if is_member:
                self.btn_apply.setText("Joined")
                self.btn_apply.setStyleSheet(STYLE_GREEN_BTN)
                self.btn_apply.setEnabled(False)
            elif is_applicant:
                self.btn_apply.setText("Pending")
                self.btn_apply.setStyleSheet(STYLE_YELLOW_BTN)
                self.btn_apply.setEnabled(False)
            elif on_kick_cooldown:
                self.btn_apply.setText(f"Cooldown")
                self.btn_apply.setStyleSheet(STYLE_RED_BTN) 
                self.btn_apply.setEnabled(False)
                self.btn_apply.setToolTip(f"You were removed from this org. {kick_cooldown_str.strip()} left")
            else:
                self.btn_apply.setText("Apply")
                self.btn_apply.setStyleSheet(STYLE_GREEN_BTN)
                self.btn_apply.setEnabled(True)
                self.btn_apply.clicked.connect(self._apply_to_org)

    def _apply_to_org(self):
        """Handles the 'Apply' button click using API."""
        from services.organization_api_service import OrganizationAPIService
        
        # TODO: Get actual student user_id from the main window/session
        # For now, we'll need to pass user_id - this should come from login session
        student_name = self.main_window.name
        
        # Show confirmation dialog
        from PyQt6.QtWidgets import QMessageBox
        confirm = QMessageBox.question(
            self,
            "Confirm Application",
            f"Do you want to apply to {self.org_data.get('name', 'this organization')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.No:
            return
        
        # TODO: Replace with actual user_id from session/login
        # This is a placeholder - you need to store user_id when student logs in
        user_id = getattr(self.main_window, 'user_id', 1)  # Temporary fallback
        org_id = self.org_data.get('id')
        
        if not org_id:
            QMessageBox.warning(self, "Error", "Organization ID not found.")
            return
        
        # Submit application via API
        response = OrganizationAPIService.submit_membership_application(user_id, org_id)
        
        if response.get('success'):
            # Update the org_data to reflect pending status immediately
            if 'applicants' not in self.org_data:
                self.org_data['applicants'] = []
            self.org_data['applicants'].append([student_name, "Member", ""])
            
            QMessageBox.information(
                self,
                "Success",
                "Your application has been submitted successfully!"
            )
            
            # Update button status immediately
            self._update_apply_button_status()
            
            # Refresh the organization list in background
            self.main_window.load_orgs()
        else:
            error_msg = response.get('message', 'Failed to submit application')
            QMessageBox.warning(self, "Application Failed", error_msg)

class ArchivedOrgCard(CollegeOrgCard):
    """Card for displaying archived organizations. Archived orgs cannot be restored."""
    def __init__(self, logo_path, name, org_data, admin_window):
        # The CollegeOrgCard constructor expects 'main_window', which is the admin_window here.
        super().__init__(logo_path, name, org_data, admin_window)
        
        # Store the Admin instance for method calls
        self.admin_window = admin_window
        
        # Hide the apply/restore button since archived orgs cannot be restored
        self.btn_apply.hide()

class OfficerCard(BaseCard):
# ... (rest of OfficerCard is unchanged)
    def __init__(self, officer_data, main_window):
        super().__init__(blur_radius=10) 

        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignVCenter)
        top_spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        layout.addItem(top_spacer)

        image_label = QtWidgets.QLabel()
        image_label.setFixedSize(150, 150)
        image_label.setStyleSheet("border: none; ")
        image_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter | QtCore.Qt.AlignmentFlag.AlignVCenter)

        image_path = officer_data.get("card_image_path", "No Photo")
        
        # Check if it's a URL from the backend (starts with /uploads/ or http)
        if image_path and (image_path.startswith('/uploads/') or image_path.startswith('http')):
            # It's a backend URL, construct full URL
            import requests
            from io import BytesIO
            base_url = "http://127.0.0.1:8000"  # Django backend URL
            full_url = base_url + image_path if image_path.startswith('/') else image_path
            
            try:
                response = requests.get(full_url, timeout=5)
                if response.status_code == 200:
                    pixmap = QPixmap()
                    pixmap.loadFromData(response.content)
                    if not pixmap.isNull():
                        pixmap = pixmap.scaled(150, 150, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
                        image_label.setPixmap(pixmap)
                    else:
                        image_label.setText("No Image")
                else:
                    image_label.setText("No Image")
            except Exception as e:
                print(f"ERROR: Failed to load image from URL: {e}")
                image_label.setText("No Image")
        else:
            # Local file path
            resolved_image_path = get_image_path(image_path)
            
            if resolved_image_path != "No Photo":
                pixmap = QPixmap(resolved_image_path).scaled(150, 150, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
                if not pixmap.isNull():
                    image_label.setPixmap(pixmap)
                else:
                    image_label.setText("No Image")
            else:
                image_label.setText("No Image")

        name_label = QtWidgets.QLabel(officer_data.get("name", "Unknown"))
        name_label.setStyleSheet("border: none; font-weight: bold;")
        name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        position_label = QtWidgets.QLabel(officer_data.get("position", "Unknown Position"))
        position_label.setStyleSheet("border: none;")
        position_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        btn_details = QtWidgets.QPushButton("Officer Details")
        btn_details.setStyleSheet(STYLE_OFFICER_BTN)
        btn_details.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        btn_details.clicked.connect(lambda: main_window.show_officer_dialog(officer_data))

        layout.addWidget(image_label)
        layout.addWidget(name_label)
        layout.addWidget(position_label)
        layout.addWidget(btn_details)

        bottom_spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        layout.addItem(bottom_spacer)

class EventCard(QtWidgets.QFrame):
# ... (rest of EventCard is unchanged)
    def __init__(self, event_data, main_window):
        super().__init__()
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(125)
        self.setMinimumWidth(65)
        self.setStyleSheet("""
            QFrame {
                color: #084924;
                background-color: #fff;
                border: 1px solid #084924;
                border-radius: 10px;
            }
        """)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        empty_btn = QtWidgets.QPushButton()
        empty_btn.setStyleSheet("""background-color: #084924;
                                color: white;
                                border: 3px solid #084924;
                                font-weight: bold; 
                                border-top-right-radius: 8px;
                                border-top-left-radius: 8px;
                                border-bottom-right-radius: 0px;
                                border-bottom-left-radius: 0px;
                                """)
        empty_btn.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        main_layout.addWidget(empty_btn)

        header = QtWidgets.QFrame(self)
        header_layout = QtWidgets.QHBoxLayout(header)
        header.setStyleSheet("background-color: transparent; border: none;")
        header_layout.setContentsMargins(10, 5, 10, 5) 

        header_group = QtWidgets.QWidget()
        group_layout = QtWidgets.QHBoxLayout(header_group)
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(0)

        name_label = QtWidgets.QLabel(event_data.get("name", "Unknown Event"))
        name_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        date_label = QtWidgets.QLabel(event_data.get("date", "No Date"))

        group_layout.addWidget(name_label)
        
        group_layout.addItem(QtWidgets.QSpacerItem(15, 0, QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed))
        
        group_layout.addWidget(date_label)
        
        header_layout.addStretch(1) 
        
        header_layout.addWidget(header_group) 
        
        header_layout.addStretch(1) 

        main_layout.addWidget(header)

        content_label = QtWidgets.QLabel(event_data.get("description", "No Description"))
        content_label.setStyleSheet("padding: 10px; font-size: 12px; border: none;")
        content_label.setWordWrap(True)
        content_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(content_label)