from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainterPath, QColor, QPainter
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
import os
import datetime
from PyQt6.QtWidgets import QMessageBox

STYLE_GREEN_BTN = "background-color: #084924; color: white; border-radius: 5px; padding-top: 10px;padding-bottom: 10px; font-weight: bold;"
STYLE_RED_BTN = "background-color: #EB5757; color: white; border-radius: 5px; padding-top: 10px;padding-bottom: 10px; font-weight: bold;"
STYLE_PRIMARY_BTN = "background-color: #084924; color: white; border-radius: 5px;"
STYLE_YELLOW_BTN = "background-color: #FDC601; color: white; border-radius: 5px; padding-top: 10px;padding-bottom: 10px; font-weight: bold;"

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

def resolve_image_path(relative_path):
    """Resolve relative image path to absolute path in Data folder."""
    if relative_path == "No Photo" or not relative_path:
        return "No Photo"
    
    # If it's already an absolute path that exists, return it
    if os.path.isabs(relative_path) and os.path.exists(relative_path):
        return relative_path
    
    # Resolve from Data folder
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_path = os.path.join(base_dir, "views", "Organizations", "Data", relative_path)
    
    if os.path.exists(data_path):
        return data_path
    
    # Fallback to relative path
    return relative_path

class JoinedOrgCard(QtWidgets.QFrame):
    def __init__(self, logo_path, org_data, main_window):
        super().__init__()
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
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

        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignHCenter)

        logo_label = QtWidgets.QLabel()
        logo_label.setMaximumSize(200, 200)
        logo_label.setMinimumSize(200, 200)
        logo_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        logo_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        logo_label.setStyleSheet("border: none; background-color: transparent;")

        resolved_logo_path = resolve_image_path(logo_path)
        
        if resolved_logo_path != "No Photo":
            pixmap = QPixmap(resolved_logo_path).scaled(200, 200, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
            if not pixmap.isNull():
                rounded_pixmap = create_rounded_pixmap(pixmap, 10)
                logo_label.setPixmap(rounded_pixmap)
            else:
                logo_label.setText("No Logo")
        else:
            logo_label.setText("No Logo")

        btn_details = QtWidgets.QPushButton("More Details")
        btn_details.setStyleSheet(STYLE_YELLOW_BTN)
        btn_details.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        btn_details.clicked.connect(lambda: main_window.show_org_details(org_data))

        layout.addWidget(logo_label, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(btn_details)

class CollegeOrgCard(QtWidgets.QFrame):
    def __init__(self, logo_path, description, org_data, main_window):
        super().__init__()
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        
        # --- Store org_data and main_window ---
        self.org_data = org_data
        self.main_window = main_window  # This is the Student() instance
        # ---
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
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

        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignBottom | QtCore.Qt.AlignmentFlag.AlignHCenter)

        logo_label = QtWidgets.QLabel()
        logo_label.setMaximumSize(200, 200)
        logo_label.setMinimumSize(200, 200)
        logo_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter | QtCore.Qt.AlignmentFlag.AlignHCenter)
        logo_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        logo_label.setStyleSheet("border: none; background-color: transparent;")

        resolved_logo_path = resolve_image_path(logo_path)
        
        if resolved_logo_path != "No Photo":
            pixmap = QPixmap(resolved_logo_path).scaled(200, 200, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
            if not pixmap.isNull():
                rounded_pixmap = create_rounded_pixmap(pixmap, 10)
                logo_label.setPixmap(rounded_pixmap)
            else:
                logo_label.setText("No Logo")
        else:
            logo_label.setText("No Logo")

        desc_label = QtWidgets.QLabel()
        desc_label.setStyleSheet("border: none; background-color: transparent; font-weight: bold;")
        desc_label.setMaximumHeight(16)
        desc_label.setText(description)
        desc_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        desc_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        desc_label.setWordWrap(True)

        btn_details = QtWidgets.QPushButton("More Details")
        
        # --- Store apply button as self.btn_apply ---
        self.btn_apply = QtWidgets.QPushButton() 
        # --- ADDED: This is needed so findChild() works ---
        self.btn_apply.setObjectName("apply_btn")
        # ---
        
        btn_details.setStyleSheet(STYLE_YELLOW_BTN)
        
        # --- Set button state based on user status ---
        self._update_apply_button_status() 
        # ---
        
        btn_details.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.btn_apply.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        
        btn_details.clicked.connect(lambda: main_window.show_org_details(org_data))

        layout.addWidget(logo_label, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(desc_label)
        layout.addWidget(btn_details)
        layout.addWidget(self.btn_apply)

    # --- MODIFIED: This entire function is updated ---
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
            
            # Check for KICK cooldown (specific to this org)
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
                        # Kick cooldown expired, can be removed
                        pass 
                except (ValueError, TypeError):
                    pass # Invalid time format

            # Check for GLOBAL application cooldown
            is_on_global_cooldown, global_cooldown_end = self.main_window.check_application_cooldown()
            global_cooldown_str = ""
            if is_on_global_cooldown:
                remaining = global_cooldown_end - datetime.datetime.now()
                total_seconds = int(remaining.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                global_cooldown_str = f" ({hours}h {minutes}m left)"

            try:
                self.btn_apply.clicked.disconnect()
            except TypeError:
                pass # No connection to disconnect

            # This order is crucial
            if is_member:
                self.btn_apply.setText("Joined")
                self.btn_apply.setStyleSheet(STYLE_GREEN_BTN)
                self.btn_apply.setEnabled(False)
            elif is_applicant:
                self.btn_apply.setText("Pending")
                self.btn_apply.setStyleSheet(STYLE_YELLOW_BTN) # Yellow for pending
                self.btn_apply.setEnabled(False)
            elif on_kick_cooldown:
                self.btn_apply.setText(f"Cooldown{kick_cooldown_str}")
                self.btn_apply.setStyleSheet(STYLE_RED_BTN) # Red for kick
                self.btn_apply.setEnabled(False)
                self.btn_apply.setToolTip(f"You were removed from this org. {kick_cooldown_str.strip()} left")
            elif is_on_global_cooldown:
                self.btn_apply.setText(f"Cooldown{global_cooldown_str}")
                self.btn_apply.setStyleSheet(STYLE_RED_BTN) # Red for global
                self.btn_apply.setEnabled(False)
                self.btn_apply.setToolTip(f"Global cooldown active. {global_cooldown_str.strip()} left")
            else:
                self.btn_apply.setText("Apply")
                self.btn_apply.setStyleSheet(STYLE_GREEN_BTN)
                self.btn_apply.setEnabled(True)
                self.btn_apply.clicked.connect(self._apply_to_org)
    # --- END MODIFIED ---

    # --- MODIFIED: This entire function is updated ---
    def _apply_to_org(self):
        """Handles the 'Apply' button click."""
        
        # Final check for global cooldown
        is_on_cooldown, cooldown_end = self.main_window.check_application_cooldown()
        if is_on_cooldown:
            remaining = cooldown_end - datetime.datetime.now()
            total_seconds = int(remaining.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            QMessageBox.warning(
                self, 
                "Cooldown Active", 
                f"You cannot apply to another organization for {hours}h {minutes}m."
            )
            return
        
        student_name = self.main_window.name
        
        if "applicants" not in self.org_data:
            self.org_data["applicants"] = []
            
        # Add student to applicants list
        self.org_data["applicants"].append([
            student_name, 
            "Member",
            datetime.date.today().isoformat() # Add application date
        ])
        
        # Save the org data
        self.main_window.save_data_for_org(self.org_data)
            
        # 1. Set the 7-hour global cooldown
        self.main_window.set_application_cooldown(hours=7) 
        
        # 2. Show confirmation
        QMessageBox.information(
            self, 
            "Application Submitted", 
            f"You have successfully applied to {self.org_data['name']}.\n"
            "You must wait 7 hours before applying to another organization."
        )

        # 3. Update this button to "Pending"
        self._update_apply_button_status()
        
        # 4. Reload all orgs to apply global cooldown to other buttons
        if self.main_window.ui.comboBox.currentIndex() == 0:
            self.main_window.load_orgs()
        else:
            self.main_window.load_branches()
    # --- END MODIFIED ---

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
            
            # --- This section checks the KICK cooldown (1 hour) ---
            on_kick_cooldown = False
            kick_cooldown_str = ""
            if student_name in cooldowns:
                try:
                    kick_time = datetime.datetime.fromisoformat(cooldowns[student_name])
                    # You had 1 hour here, so I'll keep it
                    cooldown_duration = datetime.timedelta(hours=1) 
                    expiry_time = kick_time + cooldown_duration
                    
                    if datetime.datetime.now() < expiry_time:
                        on_kick_cooldown = True
                        remaining_time = expiry_time - datetime.datetime.now()
                        total_minutes = int(remaining_time.total_seconds() // 60)
                        kick_cooldown_str = f" ({total_minutes}m left)"
                    else:
                        # Kick cooldown expired, (logic to remove it could go here)
                        pass 
                except (ValueError, TypeError):
                    pass # Invalid time format in JSON
            
            # --- ADDED: Check Global Application Cooldown (7 hours) ---
            is_on_global_cooldown, global_cooldown_end = self.main_window.check_application_cooldown()
            global_cooldown_str = ""
            if is_on_global_cooldown:
                remaining = global_cooldown_end - datetime.datetime.now()
                total_seconds = int(remaining.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                global_cooldown_str = f" ({hours}h {minutes}m left)"
            # --- END ADDED ---

            try:
                self.btn_apply.clicked.disconnect()
            except TypeError:
                pass # No connection to disconnect

            if is_member:
                self.btn_apply.setText("Joined")
                self.btn_apply.setStyleSheet(STYLE_GREEN_BTN)
                self.btn_apply.setEnabled(False)
            elif is_applicant:
                self.btn_apply.setText("Pending")
                self.btn_apply.setStyleSheet(STYLE_YELLOW_BTN) 
                self.btn_apply.setEnabled(False)
            elif on_kick_cooldown:
                self.btn_apply.setText(f"Cooldown{kick_cooldown_str}")
                self.btn_apply.setStyleSheet(STYLE_RED_BTN) # <-- IT'S NOW YELLOW
                self.btn_apply.setEnabled(False)
                self.btn_apply.setToolTip(f"You were removed from this org. {kick_cooldown_str.strip()} left")
            elif is_on_global_cooldown:
                self.btn_apply.setText(f"Cooldown{global_cooldown_str}")
                self.btn_apply.setStyleSheet(STYLE_RED_BTN) # <-- IT'S NOW YELLOW
                self.btn_apply.setEnabled(False)
                self.btn_apply.setToolTip(f"Global cooldown active. {global_cooldown_str.strip()} left")
            else:
                self.btn_apply.setText("Apply")
                self.btn_apply.setStyleSheet(STYLE_GREEN_BTN)
                self.btn_apply.setEnabled(True)
                self.btn_apply.clicked.connect(self._apply_to_org)

    # --- MODIFIED: This entire method is updated ---
    def _apply_to_org(self):
        """Handles the 'Apply' button click."""
        
        # --- ADDED: Final check for global cooldown before applying ---
        is_on_cooldown, cooldown_end = self.main_window.check_application_cooldown()
        if is_on_cooldown:
            remaining = cooldown_end - datetime.datetime.now()
            total_seconds = int(remaining.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            QMessageBox.warning(
                self, 
                "Cooldown Active", 
                f"You cannot apply to another organization for {hours}h {minutes}m."
            )
            return
        # --- END ADDED ---

        student_name = self.main_window.name
        
        if "applicants" not in self.org_data:
            self.org_data["applicants"] = []
            
        # --- MODIFIED: Added date to application to match 3-column model ---
        # Format: [Name, Position, Date Applied]
        self.org_data["applicants"].append([
            student_name, 
            "Member", 
            datetime.date.today().isoformat()
        ])
        # --- END MODIFIED ---
        
        # Save this specific org's data
        self.main_window.save_data_for_org(self.org_data)
        
        # --- ADDED: Set global 7-hour cooldown and reload all cards ---
        
        # 1. Set the 7-hour global cooldown for the student
        self.main_window.set_application_cooldown(hours=7)
        
        # 2. Show confirmation message
        QMessageBox.information(
            self, 
            "Application Submitted", 
            f"You have successfully applied to {self.org_data['name']}.\n"
            "You must wait 7 hours before applying to another organization."
        )
        
        # 3. Update this button's state immediately (it will now be "Pending")
        self._update_apply_button_status() 
        
        # 4. Reload all orgs/branches to update all OTHER "Apply" buttons
        # This will make them show the new 7-hour global cooldown
        if self.main_window.ui.comboBox.currentIndex() == 0:
            self.main_window.load_orgs()
        else:
            self.main_window.load_branches()
        # --- END ADDED ---

class OfficerCard(QtWidgets.QFrame):
    def __init__(self, officer_data, main_window):
        super().__init__()
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
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

        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignVCenter)
        top_spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        layout.addItem(top_spacer)

        image_label = QtWidgets.QLabel()
        image_label.setFixedSize(150, 150)
        image_label.setStyleSheet("border: none; ")
        image_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter | QtCore.Qt.AlignmentFlag.AlignVCenter)

        if "card_image_path" in officer_data and officer_data["card_image_path"] != "No Photo":
            resolved_image_path = resolve_image_path(officer_data["card_image_path"])
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
        btn_details.setStyleSheet("background-color: #FFD700; color: black; border-radius: 5px; font-weight: bold;")
        btn_details.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        btn_details.clicked.connect(lambda: main_window.show_officer_dialog(officer_data))

        layout.addWidget(image_label)
        layout.addWidget(name_label)
        layout.addWidget(position_label)
        layout.addWidget(btn_details)

        bottom_spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        layout.addItem(bottom_spacer)

class EventCard(QtWidgets.QFrame):
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
