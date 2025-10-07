from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import QFileDialog

class BlurredDialog(QtWidgets.QDialog):
    _blur_count = 0
    _original_effect = None
    _blur_effect = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        self.main_window = None

        if parent:
            current = parent
            while current and isinstance(current, QtWidgets.QDialog):
                current = current.parent()
            if current:
                self.main_window = current.window()
            if self.main_window:
                BlurredDialog._blur_count += 1
                if BlurredDialog._blur_count == 1:
                    BlurredDialog._original_effect = self.main_window.graphicsEffect()
                    BlurredDialog._blur_effect = QtWidgets.QGraphicsBlurEffect()
                    BlurredDialog._blur_effect.setBlurRadius(5)
                    self.main_window.setGraphicsEffect(BlurredDialog._blur_effect)

        self.finished.connect(self.restore_blur)

    def restore_blur(self):
        if self.main_window:
            BlurredDialog._blur_count -= 1
            if BlurredDialog._blur_count <= 0:
                self.main_window.setGraphicsEffect(BlurredDialog._original_effect)
                BlurredDialog._blur_count = 0

    def closeEvent(self, event):
        QtWidgets.QDialog.closeEvent(self, event)
        QtCore.QTimer.singleShot(0, self.restore_blur)

class OfficerDialog(BlurredDialog):
    def __init__(self, officer_data, parent=None):
        super().__init__(parent)
        self.setFixedSize(400, 350)
        self.setWindowTitle("Officer Details")

        main_layout = QtWidgets.QVBoxLayout(self)

        hlayout = QtWidgets.QHBoxLayout()
        self.photo_label = QtWidgets.QLabel()
        parent.set_circular_logo(self.photo_label, officer_data.get("photo_path", "No Photo"), size=125, border_width=4)
        hlayout.addWidget(self.photo_label)

        vinfo = QtWidgets.QVBoxLayout()
        self.name_label = QtWidgets.QLabel(officer_data.get("name", "Unknown"))
        self.name_label.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Weight.Bold))
        self.name_label.setStyleSheet("margin-top: 10px")
        vinfo.addWidget(self.name_label)
        self.position_label = QtWidgets.QLabel(officer_data.get("position", "Unknown Position"))
        vinfo.addWidget(self.position_label)
        self.date_label = QtWidgets.QLabel(f"{officer_data.get('start_date', '07/08/2025')} - Present")
        self.date_label.setStyleSheet("margin-bottom: 10px")
        vinfo.addWidget(self.date_label)
        hlayout.addLayout(vinfo)

        main_layout.addLayout(hlayout)

        cv_btn = QtWidgets.QPushButton("Curriculum Vitae")
        cv_btn.setStyleSheet("background-color: #084924; color: white; border-radius: 5px; padding: 10px;")
        contact_btn = QtWidgets.QPushButton("Contact Me")
        contact_btn.setStyleSheet("background-color: white; border: 1px solid #ccc; border-radius: 5px; padding: 10px;")
        main_layout.addWidget(cv_btn)
        main_layout.addWidget(contact_btn)
        
        if (hasattr(parent, 'is_managing') and parent.is_managing) or parent.name == officer_data.get("name"):
            edit_btn = QtWidgets.QPushButton("Edit")
            edit_btn.setStyleSheet("background-color: #FFD700; color: black; border: 1px solid #ccc; border-radius: 5px; padding: 10px;")
            edit_btn.clicked.connect(lambda: self.open_edit_officer(officer_data))
            main_layout.addWidget(edit_btn)

    def open_edit_officer(self, officer_data):
        dialog = EditOfficerDialog(officer_data, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            updated_data = dialog.updated_data
            self.parent().update_officer_in_org(updated_data)
            self.update_dialog(updated_data)

    def update_dialog(self, officer_data):
        self.parent().set_circular_logo(self.photo_label, officer_data.get("photo_path", "No Photo"), size=150, border_width=4)
        self.position_label.setText(officer_data.get("position", "Unknown Position"))
        self.date_label.setText(f"{officer_data.get('start_date', '07/08/2025')} - Present")

class EditOrgDialog(BlurredDialog):
    def __init__(self, org_data: dict, parent: QtWidgets.QMainWindow):
        super().__init__(parent)
        self.org_data = org_data
        self.parent_window = parent
        self.setWindowTitle("Edit Organization/Branch Details")
        self.setFixedSize(600, 500)

        main_layout = QtWidgets.QVBoxLayout(self)

        content_layout = QtWidgets.QHBoxLayout()

        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_widget)
        self.preview_label = QtWidgets.QLabel()
        self.preview_label.setFixedSize(200, 200)
        self.preview_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.parent_window.set_circular_logo(self.preview_label, self.parent_window._get_logo_path(org_data["logo_path"]))
        left_layout.addWidget(self.preview_label)

        browse_btn = QtWidgets.QPushButton("Browse Image")
        browse_btn.setStyleSheet("""
            border: 2px solid #084924; 
            background-color: transparent;
            border-radius: 10px;
            padding: 5px;
            color: #084924;
        """)
        browse_btn.clicked.connect(self.browse_image)
        left_layout.addWidget(browse_btn)

        content_layout.addWidget(left_widget)

        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)

        brief_label = QtWidgets.QLabel("Brief Overview")
        brief_label.setStyleSheet("color: #084924; text-decoration: underline #084924;")

        right_layout.addWidget(brief_label)
        self.brief_edit = QtWidgets.QTextEdit(org_data.get("brief", ""))
        self.brief_edit.setStyleSheet("")
        right_layout.addWidget(self.brief_edit)

        obj_label = QtWidgets.QLabel("Objectives")
        obj_label.setStyleSheet("color: #084924; text-decoration: underline #084924;")

        right_layout.addWidget(obj_label)
        self.desc_edit = QtWidgets.QTextEdit(org_data.get("description", ""))
        right_layout.addWidget(self.desc_edit)

        content_layout.addWidget(right_widget)
        main_layout.addLayout(content_layout)

        btn_layout = QtWidgets.QHBoxLayout()
        confirm_btn = QtWidgets.QPushButton("Confirm")
        confirm_btn.setStyleSheet("""
            border: 2px solid #084924; 
            background-color: #084924;
            border-radius: 10px;
            padding: 5px;
            color: white;
        """)
        confirm_btn.clicked.connect(self.confirm)
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            border: 2px solid #EB5757; 
            background-color: #EB5757;
            border-radius: 10px;
            padding: 5px;
            color: white;
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(confirm_btn)
        btn_layout.addWidget(cancel_btn)
        main_layout.addLayout(btn_layout)

    def browse_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Logo Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.org_data["logo_path"] = file_path
            self.parent_window.set_circular_logo(self.preview_label, file_path)

    def confirm(self):
        self.org_data["brief"] = self.brief_edit.toPlainText()
        self.org_data["description"] = self.desc_edit.toPlainText()

        self.parent_window.ui.brief_label.setText(self.org_data["brief"])
        self.parent_window.ui.obj_label.setText(self.org_data["description"])
        self.parent_window.set_circular_logo(self.parent_window.ui.logo, self.org_data["logo_path"])

        self.parent_window.save_data()

        self.accept()

class EditOfficerDialog(BlurredDialog):
    def __init__(self, officer_data, parent=None):
        super().__init__(parent)
        self.officer_data = officer_data.copy()
        self.original_position = officer_data.get("position", "")
        self.setWindowTitle("Edit Officer Details")
        self.setFixedSize(500, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 10px;
                padding: 10px;
            }
        """)

        main_layout = QtWidgets.QVBoxLayout(self)

        # Photo section
        photo_layout = QtWidgets.QHBoxLayout()
        self.preview_label = QtWidgets.QLabel()
        self.preview_label.setStyleSheet("text-align: center;")
        self.preview_label.setFixedSize(150, 150)
        self.preview_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        parent.parent().set_circular_logo(self.preview_label, self.officer_data.get("photo_path", "No Photo"), size=150, border_width=4)
        photo_layout.addWidget(self.preview_label)
        browse_btn = QtWidgets.QPushButton("Browse Photo")
        browse_btn.setStyleSheet("""
            border: 2px solid #084924; 
            background-color: transparent;
            border-radius: 10px;
            padding: 5px;
            color: #084924;
        """)
        browse_btn.clicked.connect(self.browse_photo)
        photo_layout.addWidget(browse_btn)
        main_layout.addLayout(photo_layout)

        # Position
        main_layout.addWidget(QtWidgets.QLabel("Position:"))
        self.position_edit = QtWidgets.QComboBox()
        self.position_edit.setStyleSheet("border-radius: 10px; padding: 10px; border: 1px solid #084924; color: #084924;")
        possible_positions = ["President", "Vice - Internal Chairperson", "Vice - External Chairperson", "Secretary", "Treasurer", "Member"]
        self.position_edit.addItems(possible_positions)
        self.position_edit.setCurrentText(self.officer_data.get("position", ""))
        main_layout.addWidget(self.position_edit)

        # Start Date
        main_layout.addWidget(QtWidgets.QLabel("Start Date (MM/DD/YYYY):"))
        self.date_edit = QtWidgets.QLineEdit(self.officer_data.get("start_date", ""))
        self.date_edit.setStyleSheet("border-radius: 10px; padding: 10px; border: 1px solid #084924; color: #084924;")
        main_layout.addWidget(self.date_edit)

        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        confirm_btn = QtWidgets.QPushButton("Confirm")
        confirm_btn.setStyleSheet("""
            border: 2px solid #084924; 
            background-color: #084924;
            border-radius: 10px;
            padding: 5px;
            color: white;
        """)
        confirm_btn.clicked.connect(self.confirm)
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            border: 2px solid #EB5757; 
            background-color: #EB5757;
            border-radius: 10px;
            padding: 5px;
            color: white;
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(confirm_btn)
        btn_layout.addWidget(cancel_btn)
        main_layout.addLayout(btn_layout)

    def browse_photo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Officer Photo", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.officer_data["photo_path"] = file_path
            self.officer_data["card_image_path"] = file_path
            self.parent().parent().set_circular_logo(self.preview_label, file_path, size=150, border_width=4)

    def confirm(self):
        new_position = self.position_edit.currentText()
        
        if new_position != self.original_position and new_position != "Member":
            main_window = self.parent().parent()
            if hasattr(main_window, 'current_org') and main_window.current_org:
                current_officers = main_window.current_org.get("officers", [])
                
                for officer in current_officers:
                    if officer.get("name") != self.officer_data.get("name") and officer.get("position") == new_position:
                        QtWidgets.QMessageBox.warning(
                            self,
                            "Position Already Taken",
                            f"The position '{new_position}' is already occupied by {officer.get('name')}.",
                            QtWidgets.QMessageBox.StandardButton.Ok
                        )
                        return
        
        self.officer_data["position"] = new_position
        self.officer_data["start_date"] = self.date_edit.text()
        self.updated_data = self.officer_data
        self.accept()

class EditMemberDialog(BlurredDialog):
    def __init__(self, member_data: list, parent=None):
        super().__init__(parent)
        self.member_data = member_data
        self.original_position = member_data[1]
        self.setWindowTitle("Edit Member Position")
        self.setFixedSize(300, 150)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 1px solid #ccc;
                padding: 10px;
            }
        """)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(QtWidgets.QLabel("Position:"))
        self.position_edit = QtWidgets.QComboBox()
        self.position_edit.setStyleSheet("border-radius: 10px; padding: 10px; border: 1px solid #084924; color: #084924;")
        possible_positions = ["President", "Vice - Internal Chairperson", "Vice - External Chairperson", "Secretary", "Treasurer", "Member"]
        self.position_edit.addItems(possible_positions)
        self.position_edit.setCurrentText(member_data[1])
        main_layout.addWidget(self.position_edit)

        btn_layout = QtWidgets.QHBoxLayout()
        confirm_btn = QtWidgets.QPushButton("Confirm")
        confirm_btn.setStyleSheet("""
            border: 2px solid #084924; 
            background-color: #084924;
            border-radius: 10px;
            padding: 5px;
            color: white;
        """)
        confirm_btn.clicked.connect(self.confirm)
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            border: 2px solid #EB5757; 
            background-color: #EB5757;
            border-radius: 10px;
            padding: 5px;
            color: white;
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(confirm_btn)
        btn_layout.addWidget(cancel_btn)
        main_layout.addLayout(btn_layout)

    def confirm(self):
        new_position = self.position_edit.currentText()
        
        if new_position != self.original_position and new_position != "Member":
            main_window = self.parent()
            if hasattr(main_window, 'current_org') and main_window.current_org:
                current_officers = main_window.current_org.get("officers", [])
                
                for officer in current_officers:
                    if officer.get("name") != self.member_data[0] and officer.get("position") == new_position:
                        QtWidgets.QMessageBox.warning(
                            self,
                            "Position Already Taken",
                            f"The position '{new_position}' is already occupied by {officer.get('name')}.",
                            QtWidgets.QMessageBox.StandardButton.Ok
                        )
                        return
        
        self.updated_position = new_position
        self.accept()