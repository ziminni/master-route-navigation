from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import QFileDialog, QMessageBox
import json
import os

import sys
from views.Organizations.image_utils import copy_image_to_data, get_image_path

CONFIRM_STYLE = """
    border: 2px solid #084924; 
    background-color: #084924;
    border-radius: 10px;
    padding: 5px;
    color: white;
"""
CANCEL_STYLE = """
    border: 2px solid #EB5757; 
    background-color: #EB5757;
    border-radius: 10px;
    padding: 5px;
    color: white;
"""
BROWSE_STYLE = """
    border: 2px solid #084924; 
    background-color: transparent;
    border-radius: 10px;
    padding: 5px;
    color: #084924;
"""
EDIT_STYLE = "border-radius: 10px; padding: 10px; border: 1px solid #084924; color: #084924;"
LABEL_STYLE = "color: #084924; text-decoration: underline #084924;"
DIALOG_STYLE = """
    QDialog {
        background-color: white;
        border: 1px solid #ccc;
        border-radius: 10px;
        padding: 10px;
    }
"""

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

    @staticmethod
    def _create_button_layout(confirm_cb, cancel_cb=None):
        btn_layout = QtWidgets.QHBoxLayout()
        confirm_btn = QtWidgets.QPushButton("Confirm")
        confirm_btn.setStyleSheet(CONFIRM_STYLE)
        confirm_btn.clicked.connect(confirm_cb)
        btn_layout.addWidget(confirm_btn)
        if cancel_cb:
            cancel_btn = QtWidgets.QPushButton("Cancel")
            cancel_btn.setStyleSheet(CANCEL_STYLE)
            cancel_btn.clicked.connect(cancel_cb)
            btn_layout.addWidget(cancel_btn)
        return btn_layout

    @staticmethod
    def _add_text_edit(layout, label_text, initial_text="", is_brief=False):
        label = QtWidgets.QLabel(label_text)
        label.setStyleSheet(LABEL_STYLE)
        layout.addWidget(label)
        edit = QtWidgets.QTextEdit(initial_text)
        if not is_brief:
            edit.setStyleSheet("")
        layout.addWidget(edit)
        return edit

    @staticmethod
    def _check_position_conflict(main_window, new_position, current_name, original_position=""):
        if new_position == original_position or new_position == "Member":
            return False
        if hasattr(main_window, 'current_org') and main_window.current_org:
            current_officers = main_window.current_org.get("officers", [])
            for officer in current_officers:
                if officer.get("name") != current_name and officer.get("position") == new_position:
                    return True
        return False

class OfficerDialog(BlurredDialog):
    def __init__(self, officer_data, parent=None):
        super().__init__(parent)
        self.setFixedSize(400, 350)
        self.setWindowTitle("Officer Details")

        main_layout = QtWidgets.QVBoxLayout(self)

        hlayout = QtWidgets.QHBoxLayout()
        self.photo_label = QtWidgets.QLabel()
        photo_path = get_image_path(officer_data.get("photo_path", "No Photo"))
        parent.set_circular_logo(self.photo_label, photo_path, size=125, border_width=4)
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
        
        can_edit = (hasattr(parent, 'is_managing') and parent.is_managing) or parent.name == officer_data.get("name")
        if can_edit:
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
        photo_path = get_image_path(officer_data.get("photo_path", "No Photo"))
        self.parent().set_circular_logo(self.photo_label, photo_path, size=150, border_width=4)
        self.position_label.setText(officer_data.get("position", "Unknown Position"))
        self.date_label.setText(f"{officer_data.get('start_date', '07/08/2025')} - Present")

class BaseEditDialog(BlurredDialog):
    def __init__(self, data, title, parent=None, fixed_size=(500, 400), has_photo=True):
        super().__init__(parent)
        self.data = data.copy() if isinstance(data, dict) else data
        self.setWindowTitle(title)
        self.setFixedSize(*fixed_size)
        if hasattr(DIALOG_STYLE, 'setStyleSheet'):
            self.setStyleSheet(DIALOG_STYLE)
        self.preview_label = None
        self.temp_image_path = None
        self._setup_ui(has_photo)

    def _setup_ui(self, has_photo):
        main_layout = QtWidgets.QVBoxLayout(self)
        if has_photo:
            photo_layout = self._create_photo_layout()
            main_layout.addLayout(photo_layout)
        self._add_form_fields(main_layout)
        btn_layout = self._create_button_layout(self.confirm, self.reject)
        main_layout.addLayout(btn_layout)

    def _create_photo_layout(self):
        photo_layout = QtWidgets.QHBoxLayout()
        self.preview_label = QtWidgets.QLabel()
        self.preview_label.setStyleSheet("text-align: center;")
        self.preview_label.setFixedSize(150, 150)
        self.preview_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        photo_filename = self.data.get("photo_path") if isinstance(self.data, dict) else "No Photo"
        photo_path = get_image_path(photo_filename)
        self.parent().parent().set_circular_logo(self.preview_label, photo_path, size=150, border_width=4)
        photo_layout.addWidget(self.preview_label)
        browse_btn = QtWidgets.QPushButton("Browse Photo")
        browse_btn.setStyleSheet(BROWSE_STYLE)
        browse_btn.clicked.connect(self.browse_photo)
        photo_layout.addWidget(browse_btn)
        return photo_layout

    def browse_photo(self):
        """Browse and select a photo file with validation."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Photo", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            self.temp_image_path = file_path
            # Show preview immediately
            self.parent().parent().set_circular_logo(self.preview_label, file_path, size=150, border_width=4)

    def _add_form_fields(self, layout):
        raise NotImplementedError("Subclasses must implement _add_form_fields")

    def confirm(self):
        raise NotImplementedError("Subclasses must implement confirm")

class EditOfficerDialog(BaseEditDialog):
    def __init__(self, officer_data, parent=None):
        super().__init__(officer_data, "Edit Officer Details", parent, (500, 400), has_photo=True)
        self.original_position = officer_data.get("position", "")

    def _add_form_fields(self, layout):
        layout.addWidget(QtWidgets.QLabel("Position:"))
        self.position_edit = QtWidgets.QComboBox()
        self.position_edit.setStyleSheet(EDIT_STYLE)
        possible_positions = ["Chairperson", "Vice - Internal Chairperson", "Vice - External Chairperson", "Secretary", "Treasurer", "Member"]
        self.position_edit.addItems(possible_positions)
        self.position_edit.setCurrentText(self.data.get("position", ""))
        layout.addWidget(self.position_edit)

        layout.addWidget(QtWidgets.QLabel("Start Date (MM/DD/YYYY):"))
        self.date_edit = QtWidgets.QLineEdit(self.data.get("start_date", ""))
        self.date_edit.setStyleSheet(EDIT_STYLE)
        layout.addWidget(self.date_edit)

    def confirm(self):
        new_position = self.position_edit.currentText()
        main_window = self.parent().parent()
        if BlurredDialog._check_position_conflict(main_window, new_position, self.data.get("name"), self.original_position):
            QtWidgets.QMessageBox.warning(
                self,
                "Position Already Taken",
                f"The position '{new_position}' is already occupied by another officer.",
                QtWidgets.QMessageBox.StandardButton.Ok
            )
            return

        if self.temp_image_path:
            org_name = main_window.current_org.get("name", "Unknown")
            new_filename = copy_image_to_data(self.temp_image_path, org_name)
            if new_filename:
                self.data["photo_path"] = new_filename
                if "card_image_path" in self.data:
                    self.data["card_image_path"] = new_filename
            else:
                QMessageBox.warning(
                    self,
                    "Image Error",
                    "Failed to save the selected image. Please try again with a different image.",
                    QMessageBox.StandardButton.Ok
                )
                return

        self.data["position"] = new_position
        self.data["start_date"] = self.date_edit.text()
        self.updated_data = self.data
        self.accept()

class EditMemberDialog(BlurredDialog):
    def __init__(self, member_data: list, parent=None):
        super().__init__(parent)
        self.member_data = member_data
        self.original_position = member_data[1]
        self.setWindowTitle("Edit Member Position")
        self.setFixedSize(300, 150)
        self.setStyleSheet(DIALOG_STYLE)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(QtWidgets.QLabel("Position:"))
        self.position_edit = QtWidgets.QComboBox()
        self.position_edit.setStyleSheet(EDIT_STYLE)
        possible_positions = ["Chairperson", "Vice - Internal Chairperson", "Vice - External Chairperson", "Secretary", "Treasurer", "Member"]
        self.position_edit.addItems(possible_positions)
        self.position_edit.setCurrentText(member_data[1])
        main_layout.addWidget(self.position_edit)

        btn_layout = BlurredDialog._create_button_layout(self.confirm, self.reject)
        main_layout.addLayout(btn_layout)

    def confirm(self):
        new_position = self.position_edit.currentText()
        main_window = self.parent()
        if BlurredDialog._check_position_conflict(main_window, new_position, self.member_data[0], self.original_position):
            QtWidgets.QMessageBox.warning(
                self,
                "Position Already Taken",
                f"The position '{new_position}' is already occupied by another officer.",
                QtWidgets.QMessageBox.StandardButton.Ok
            )
            return

        self.updated_position = new_position
        self.accept()

class BaseOrgDialog(BlurredDialog):
    def __init__(self, parent, title, fixed_size=(600, 500), is_branch=False):
        super().__init__(parent)
        self.parent_window = parent
        self.is_branch = is_branch
        self.setWindowTitle(title)
        self.setFixedSize(*fixed_size)
        self.logo_path = "No Photo"
        self.temp_logo_path = None
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)

        if self.is_branch:
            parent_layout = self._create_parent_layout()
            main_layout.addLayout(parent_layout)

        name_layout = QtWidgets.QHBoxLayout()
        name_layout.addWidget(QtWidgets.QLabel("Name:"))
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setStyleSheet(EDIT_STYLE)
        name_layout.addWidget(self.name_edit)
        main_layout.addLayout(name_layout)

        content_layout = self._create_content_layout()
        main_layout.addLayout(content_layout)

        btn_layout = BlurredDialog._create_button_layout(self.confirm, self.reject)
        main_layout.addLayout(btn_layout)

    def _create_parent_layout(self):
        parent_layout = QtWidgets.QHBoxLayout()
        parent_label = QtWidgets.QLabel("Parent Organization:")
        parent_label.setStyleSheet("font-weight: bold; color: #084924;")
        parent_layout.addWidget(parent_label)
        self.parent_combo = QtWidgets.QComboBox()
        self.parent_combo.setStyleSheet(EDIT_STYLE)

        organizations = self.parent_window._load_data()
        parent_orgs = [org for org in organizations if not org.get("is_branch", False)]

        if not parent_orgs:
            QtWidgets.QMessageBox.warning(
                self,
                "No Organizations",
                "No parent organizations available. Please create an organization first.",
                QtWidgets.QMessageBox.StandardButton.Ok
            )
            self.reject()
            return None

        for org in parent_orgs:
            self.parent_combo.addItem(org["name"], org)

        parent_layout.addWidget(self.parent_combo)
        return parent_layout

    def _create_content_layout(self):
        content_layout = QtWidgets.QHBoxLayout()

        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_widget)
        self.preview_label = QtWidgets.QLabel()
        self.preview_label.setFixedSize(200, 200)
        self.preview_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.parent_window.set_circular_logo(self.preview_label, "No Photo")
        left_layout.addWidget(self.preview_label)

        browse_btn = QtWidgets.QPushButton("Browse Image")
        browse_btn.setStyleSheet(BROWSE_STYLE)
        browse_btn.clicked.connect(self.browse_image)
        left_layout.addWidget(browse_btn)
        content_layout.addWidget(left_widget)

        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)

        self.brief_edit = BlurredDialog._add_text_edit(right_layout, "Brief Overview", is_brief=True)
        self.desc_edit = BlurredDialog._add_text_edit(right_layout, "Description")

        content_layout.addWidget(right_widget)
        return content_layout

    def browse_image(self):
        """Browse and select a logo image with validation."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Logo Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            self.temp_logo_path = file_path
            # Show preview immediately
            self.parent_window.set_circular_logo(self.preview_label, file_path)

    def confirm(self):
        raise NotImplementedError("Subclasses must implement confirm")

class EditOrgDialog(BaseOrgDialog):
    def __init__(self, org_data: dict, parent: QtWidgets.QMainWindow):
        self.org_data = org_data
        super().__init__(parent, "Edit Organization/Branch Details", (600, 500), org_data.get("is_branch", False))
        self.name_edit.setText(org_data.get("name", ""))
        self.brief_edit.setPlainText(org_data.get("brief", ""))
        self.desc_edit.setPlainText(org_data.get("description", ""))
        logo_path = get_image_path(org_data["logo_path"])
        self.parent_window.set_circular_logo(self.preview_label, logo_path)

    def _create_parent_layout(self):
        return None  # No parent selection for edit

    def confirm(self):
        old_name = self.org_data.get("name", "")
        new_name = self.name_edit.text().strip()
        
        if not new_name:
            QtWidgets.QMessageBox.warning(self, "Invalid Input", "Name is required.")
            return

        if self.temp_logo_path:
            # Use the new name for the folder
            new_filename = copy_image_to_data(self.temp_logo_path, new_name)
            if new_filename:
                self.org_data["logo_path"] = new_filename
            else:
                QMessageBox.warning(
                    self,
                    "Image Error",
                    "Failed to save the selected image. Please try again with a different image.",
                    QMessageBox.StandardButton.Ok
                )
                return

        self.org_data["name"] = new_name
        self.org_data["brief"] = self.brief_edit.toPlainText().strip()
        self.org_data["description"] = self.desc_edit.toPlainText().strip()

        self.parent_window.ui.org_name.setText(self.org_data["name"])
        self.parent_window.ui.brief_label.setText(self.org_data["brief"])
        self.parent_window.ui.obj_label.setText(self.org_data["description"])
        logo_path = get_image_path(self.org_data["logo_path"])
        self.parent_window.set_circular_logo(self.parent_window.ui.logo, logo_path)

        self.parent_window.save_data()
        self.accept()

class CreateOrgDialog(BaseOrgDialog):
    def __init__(self, parent, is_branch: bool = False):
        super().__init__(parent, f"Create {'Branch' if is_branch else 'Organization'}", (600, 500), is_branch)

    def confirm(self):
        name = self.name_edit.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, "Invalid Input", "Name is required.")
            return

        brief = self.brief_edit.toPlainText().strip()
        description = self.desc_edit.toPlainText().strip()
        
        logo_filename = "No Photo"
        if self.temp_logo_path:
            logo_filename = copy_image_to_data(self.temp_logo_path, name)
            if not logo_filename:
                QMessageBox.warning(
                    self,
                    "Image Error",
                    "Failed to save the selected image. Please try again with a different image.",
                    QMessageBox.StandardButton.Ok
                )
                return

        new_org = {
            "id": None,
            "name": name,
            "is_joined": False,
            "is_branch": self.is_branch,
            "logo_path": logo_filename,
            "brief": brief,
            "description": description,
            "events": [],
            "officers": [],
            "members": [],
            "applicants": [],
            "officer_history": {}
        }

        if not self.is_branch:
            new_org["branches"] = []

        organizations = self.parent_window._load_data()

        if self.is_branch:
            if not hasattr(self, 'parent_combo') or self.parent_combo.count() == 0:
                QtWidgets.QMessageBox.warning(self, "Invalid Input", "No parent organizations available.")
                return

            parent_org = self.parent_combo.currentData()
            if not parent_org:
                QtWidgets.QMessageBox.warning(self, "Invalid Input", "Please select a parent organization.")
                return

            branch_count = len(parent_org.get("branches", []))
            new_org["id"] = parent_org["id"] * 100 + branch_count + 1
            new_org["parent_id"] = parent_org["id"]

            if "branches" not in parent_org:
                parent_org["branches"] = []
            parent_org["branches"].append(new_org)

            for i, org in enumerate(organizations):
                if org["id"] == parent_org["id"]:
                    organizations[i] = parent_org
                    break

            print(f"Created branch '{name}' under parent org '{parent_org['name']}' with ID {new_org['id']}")
        else:
            max_id = max([org.get("id", 0) for org in organizations], default=0)
            new_org["id"] = max_id + 1
            organizations.append(new_org)
            print(f"Created organization '{name}' with ID {new_org['id']}")

        try:
            with open(self.parent_window.data_file, 'w') as file:
                json.dump({"organizations": organizations}, file, indent=4)
            print(f"Successfully saved new {'branch' if self.is_branch else 'organization'} to {self.parent_window.data_file}")
        except Exception as e:
            print(f"Error saving {self.parent_window.data_file}: {str(e)}")
            QtWidgets.QMessageBox.critical(self, "Save Error", f"Failed to save data: {str(e)}")
            return

        if self.is_branch:
            if hasattr(self.parent_window.ui, 'comboBox') and self.parent_window.ui.comboBox.currentIndex() == 1:
                self.parent_window.load_branches()
            else:
                if hasattr(self.parent_window.ui, 'comboBox'):
                    self.parent_window.ui.comboBox.setCurrentIndex(1)
                self.parent_window.load_branches()
        else:
            if hasattr(self.parent_window.ui, 'comboBox'):
                self.parent_window.ui.comboBox.setCurrentIndex(0)
            self.parent_window.load_orgs()

        QtWidgets.QMessageBox.information(
            self,
            "Success",
            f"{'Branch' if self.is_branch else 'Organization'} '{name}' created successfully!",
            QtWidgets.QMessageBox.StandardButton.Ok
        )

        self.accept()
