from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QScrollArea, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtWidgets import QDialog
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTableView, QHeaderView, QPushButton, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, QAbstractTableModel, QUrl, QTimer
from PyQt6.QtGui import QDesktopServices
import json
import os
import datetime

from views.Organizations.BrowseView.Utils.image_utils import copy_image_to_data, get_image_path, delete_image
from services.organization_api_service import OrganizationAPIService
from .styles import (
    CONFIRM_STYLE, CANCEL_STYLE, BROWSE_STYLE, 
    EDIT_STYLE, LABEL_STYLE, DIALOG_STYLE
)

class PhotoBrowseMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.temp_image_path = None
        self.preview_label = None
        self.circular_logo_setter = None
        self.image_preview_size = (150, 150)

    def browse_photo(self):
        """Browse and select a photo file with validation."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Photo", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            self.temp_image_path = file_path
            if self.preview_label and self.circular_logo_setter:
                self.circular_logo_setter(
                    self.preview_label,
                    file_path,
                    size=self.image_preview_size[0],
                    border_width=4
                )

    def _save_temp_image(self, folder_name):
        """
        Saves the temp image and returns the new filename.
        Returns filename on success.
        Returns "No Photo" if no temp image.
        Returns None on failure.
        """
        if not self.temp_image_path:
            return "No Photo"

        new_filename = copy_image_to_data(self.temp_image_path, folder_name)
        if new_filename:
            return new_filename
        else:
            QMessageBox.warning(
                self,
                "Image Error",
                "Failed to save the selected image. Please try again.",
                QMessageBox.StandardButton.Ok
            )
            return None

class BlurredDialog(QtWidgets.QDialog):
    _blur_count = 0
    _original_effect = None
    _blur_effect = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        self.main_window = None
        
        self.drag_start_position = None

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

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_start_position:
            self.move(event.globalPosition().toPoint() - self.drag_start_position)
            event.accept()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        self.drag_start_position = None
        event.accept()

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

class ArchiveConfirmDialog(BlurredDialog):
    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm Archive")
        self.setFixedSize(400, 200)
        
        layout = QVBoxLayout(self)
        label = QLabel(f"Are you sure you want to archive '{name}'?")
        label.setStyleSheet("color: #EB5757;")
        layout.addWidget(label)
        
        buttons_layout = QHBoxLayout()
        confirm_btn = QPushButton("Archive")
        confirm_btn.setStyleSheet(CANCEL_STYLE)
        confirm_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(BROWSE_STYLE)
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(confirm_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)

class PendingOfficerChangeModel(QAbstractTableModel):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self._data = data
        self.headers = ["Name", "From → To", "Proposed By", "Date", "Actions"]

    def rowCount(self, parent): return len(self._data)
    def columnCount(self, parent): return len(self.headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row = self._data[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return row.get("name")
            elif col == 1:
                old = row.get("old_position", "Member")
                new = row.get("position")
                return f"{old} → {new}"
            elif col == 2: return row.get("proposed_by", "Unknown")
            elif col == 3:
                try:
                    dt = datetime.datetime.fromisoformat(row["proposed_at"])
                    return dt.strftime("%b %d, %Y %I:%M %p")
                except:
                    return row.get("proposed_at", "N/A")
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.headers[section]
        return None

class PendingOfficerChangesDialog(QDialog):
    def __init__(self, org_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pending Officer Changes")
        self.setMinimumSize(800, 500)
        self.org_data = org_data
        self.parent = parent

        layout = QVBoxLayout(self)

        title = QLabel(f"<h2>Pending Officer Changes – {org_data['name']}</h2>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.table = QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("font-size: 14px;")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        self.load_data()

    def load_data(self):
        pending = self.org_data.get("pending_officers", [])
        model = PendingOfficerChangeModel(pending, self)
        self.table.setModel(model)

        # Clear any old index widgets first (important!)
        for row in range(self.table.model().rowCount()):
            self.table.setIndexWidget(self.table.model().index(row, 4), None)

        if not pending:
            # Clear table and show message
            self.table.setModel(None)
            no_label = QtWidgets.QLabel("No pending officer changes.")
            no_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            no_label.setStyleSheet("font-size: 18px; color: #666; padding: 40px;")
            self.layout().addWidget(no_label)
            return

        # Add Confirm/Decline buttons in last column
        for row in range(len(pending)):
            officer_data = pending[row]  # Capture current officer data

            widget = QtWidgets.QWidget()
            hbox = QtWidgets.QHBoxLayout(widget)
            hbox.setContentsMargins(8, 4, 8, 4)
            hbox.setSpacing(6)

            confirm_btn = QtWidgets.QPushButton("Confirm")
            confirm_btn.setStyleSheet("""
                QPushButton {
                    background:#084924; 
                    color:white; 
                    border-radius:6px; 
                    padding:6px 12px; 
                    font-weight: bold;
                }
                QPushButton:hover { background:#098f42; }
            """)

            decline_btn = QtWidgets.QPushButton("Decline")
            decline_btn.setStyleSheet("""
                QPushButton {
                    background:#EB5757; 
                    color:white; 
                    border-radius:6px; 
                    padding:6px 12px; 
                    font-weight: bold;
                }
                QPushButton:hover { background:#d64545; }
            """)

            confirm_btn.clicked.connect(lambda checked=False, data=officer_data: self.parent._approve_pending(data))
            decline_btn.clicked.connect(lambda checked=False, data=officer_data: self.parent._reject_pending(data))

            hbox.addWidget(confirm_btn)
            hbox.addWidget(decline_btn)
            widget.setLayout(hbox)

            self.table.setIndexWidget(model.index(row, 4), widget)

            self.table.horizontalHeader().setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeMode.Fixed)
            self.table.resizeColumnToContents(4)

class CVViewerDialog(BlurredDialog):
    """
    A modal, frameless dialog to view an officer's CV.
    Shows images and opens PDFs externally.
    """
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Curriculum Vitae Viewer")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("QDialog { border: 2px solid #084924; background-color: white; }")
        
        full_path = get_image_path(file_path)
        
        if full_path == "No Photo" or not os.path.exists(full_path):
            QMessageBox.warning(self, "No CV", f"No CV file found for: {file_path}")
            QTimer.singleShot(0, self.reject)
            return
            
        try:
            ext = os.path.splitext(full_path)[1].lower()
        except Exception:
            ext = ""
            
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        top_bar_layout = QtWidgets.QHBoxLayout()
        top_bar_layout.addStretch()
        close_btn = QtWidgets.QPushButton("X")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet(
            "QPushButton { background-color: #EB5757; color: white; border-radius: 15px; font-weight: bold; }"
            "QPushButton:hover { background-color: #cc0000; }"
        )
        close_btn.clicked.connect(self.reject)
        top_bar_layout.addWidget(close_btn)
        main_layout.addLayout(top_bar_layout)
        
        if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']:
            scroll_area = QScrollArea(self)
            scroll_area.setWidgetResizable(True)
            scroll_area.setStyleSheet("border: none;")
            
            img_label = QtWidgets.QLabel()
            pixmap = QtGui.QPixmap(full_path)
            img_label.setPixmap(pixmap)
            img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            scroll_area.setWidget(img_label)
            main_layout.addWidget(scroll_area)
            
            self.resize(
                min(pixmap.width() + 40, 1000), 
                min(pixmap.height() + 60, 800)
            )
            
        elif ext == '.pdf':
            label = QtWidgets.QLabel(
                f"This CV is a PDF document.\n({os.path.basename(full_path)})\n\nIt will be opened in your default PDF viewer."
            )
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setWordWrap(True)
            label.setStyleSheet("font-size: 14px; padding: 20px;")
            main_layout.addWidget(label)
            
            QDesktopServices.openUrl(QUrl.fromLocalFile(full_path))
            QTimer.singleShot(1500, self.reject) 
            
        else:
            label = QtWidgets.QLabel(f"Unsupported CV file format: {ext}")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-size: 14px; padding: 20px;")
            main_layout.addWidget(label)
    
class OfficerDialog(BlurredDialog):
    def __init__(self, officer_data, parent=None):
        super().__init__(parent)
        self.setFixedSize(400, 320)
        self.setWindowTitle("Officer Details")
        self.officer_data = officer_data

        main_layout = QtWidgets.QVBoxLayout(self)

        hlayout = QtWidgets.QHBoxLayout()
        self.photo_label = QtWidgets.QLabel()
        
        self._set_officer_photo(officer_data, size=125, border_width=4)

        hlayout.addWidget(self.photo_label)

        vinfo = QtWidgets.QVBoxLayout()
        
        vinfo.addStretch(1) 
        
        self.name_label = QtWidgets.QLabel(officer_data.get("name", "Unknown"))
        self.name_label.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Weight.Bold))
        self.name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter) 
        vinfo.addWidget(self.name_label)
        
        self.position_label = QtWidgets.QLabel(officer_data.get("position", "Unknown Position"))
        self.position_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        vinfo.addWidget(self.position_label)
        
        vinfo.addStretch(1) 

        hlayout.addStretch(1)
        hlayout.addLayout(vinfo)
        hlayout.addStretch(1)

        main_layout.addLayout(hlayout)

        self.cv_btn = QtWidgets.QPushButton("Curriculum Vitae")
        self.cv_path = officer_data.get("cv_path")
        
        if self.cv_path and self.cv_path != "No Photo":
            self.cv_btn.setEnabled(True)
            self.cv_btn.setStyleSheet("background-color: #084924; color: white; border-radius: 5px; padding: 10px;")
            self.cv_btn.clicked.connect(self.show_cv)
        else:
            self.cv_btn.setEnabled(False)
            self.cv_btn.setStyleSheet("background-color: #cccccc; color: #888888; border-radius: 5px; padding: 10px;")
            self.cv_btn.setToolTip("No CV has been uploaded for this officer.")
            
        contact_btn = QtWidgets.QPushButton("Contact Me")
        contact_btn.setStyleSheet("background-color: white; border: 1px solid #ccc; border-radius: 5px; padding: 10px;")
        
        main_layout.addWidget(self.cv_btn)
        main_layout.addWidget(contact_btn)
        
        self.is_manager = (hasattr(parent, 'is_managing') and parent.is_managing)
        self.is_self = parent.name == officer_data.get("name")
        can_edit = self.is_manager or self.is_self
        
        if can_edit:
            edit_btn = QtWidgets.QPushButton("Edit")
            edit_btn.setStyleSheet("background-color: #FFD700; color: black; border: 1px solid #ccc; border-radius: 5px; padding: 10px;")
            edit_btn.clicked.connect(lambda: self.open_edit_officer(officer_data))
            main_layout.addWidget(edit_btn)

    def show_cv(self):
        """Open the CV viewer dialog."""
        if self.cv_path:
            dialog = CVViewerDialog(self.cv_path, self)
            dialog.exec()

    def open_edit_officer(self, officer_data):
        is_self_edit_only = self.is_self and not self.is_manager
        dialog = EditOfficerDialog(officer_data, self, is_self_edit_only=is_self_edit_only)
        
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            updated_data = dialog.updated_data
            
            main_window = self.parent()
            
            if self.is_manager:
                main_window.update_officer_in_org(updated_data)
            elif self.is_self:
                main_window.update_own_officer_data(updated_data)
            
            self.update_dialog(updated_data)
            
            if main_window and hasattr(main_window, 'current_org') and main_window.current_org:
                current_index = main_window.ui.officer_history_dp.currentIndex()
                selected_semester = main_window.ui.officer_history_dp.itemText(current_index)
                officers = (
                    main_window.current_org.get("officer_history", {}).get(selected_semester, [])
                    if selected_semester != "Current Officers"
                    else main_window.current_org.get("officers", [])
                )
                main_window.load_officers(officers)

    def _set_officer_photo(self, officer_data, size=125, border_width=4):
        """Helper function to set the officer photo or 'No Photo' placeholder."""
        photo_path = get_image_path(officer_data.get("photo_path", "No Photo"))
        
        if photo_path == "No Photo":
            self.photo_label.setText("No Photo")
            self.photo_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.photo_label.setFixedSize(size, size)
            radius = size // 2
            self.photo_label.setStyleSheet(f"""
                QLabel {{
                    border: {border_width}px solid #084924; 
                    border-radius: {radius}px; 
                    color: #888888; 
                    background-color: white;
                }}
            """)
        else:
            self.parent().set_circular_logo(self.photo_label, photo_path, size=size, border_width=border_width)

    def update_dialog(self, officer_data):
        self.officer_data = officer_data
        self._set_officer_photo(officer_data, size=125, border_width=4)
        
        self.position_label.setText(officer_data.get("position", "Unknown Position"))
        
        self.cv_path = officer_data.get("cv_path")
        if self.cv_path and self.cv_path != "No Photo":
            self.cv_btn.setEnabled(True)
            self.cv_btn.setStyleSheet("background-color: #084924; color: white; border-radius: 5px; padding: 10px;")
            self.cv_btn.setToolTip("")
            try:
                self.cv_btn.clicked.disconnect()
            except TypeError:
                pass
            self.cv_btn.clicked.connect(self.show_cv)
        else:
            self.cv_btn.setEnabled(False)
            self.cv_btn.setStyleSheet("background-color: #cccccc; color: #888888; border-radius: 5px; padding: 10px;")
            self.cv_btn.setToolTip("No CV has been uploaded for this officer.")

class BaseEditDialog(PhotoBrowseMixin, BlurredDialog):
    def __init__(self, data, title, parent=None, fixed_size=(500, 400), has_photo=True):
        super().__init__(parent)
        self.data = data.copy() if isinstance(data, dict) else data
        self.setWindowTitle(title)
        self.setFixedSize(*fixed_size)
        self.setStyleSheet(DIALOG_STYLE)
        
        self.image_preview_size = (150, 150)
        if parent and hasattr(parent, 'parent') and callable(parent.parent):
             self.circular_logo_setter = self.parent().parent().set_circular_logo
        
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
        
        if self.circular_logo_setter:
            self.circular_logo_setter(self.preview_label, photo_path, size=150, border_width=4)
            
        photo_layout.addWidget(self.preview_label)
        browse_btn = QtWidgets.QPushButton("Browse Photo")
        browse_btn.setStyleSheet(BROWSE_STYLE)
        browse_btn.clicked.connect(self.browse_photo)
        photo_layout.addWidget(browse_btn)
        return photo_layout

    def _add_form_fields(self, layout):
        raise NotImplementedError("Subclasses must implement _add_form_fields")

    def confirm(self):
        raise NotImplementedError("Subclasses must implement confirm")

class EditOfficerDialog(BaseEditDialog):
    def __init__(self, officer_data, parent=None, is_self_edit_only=False):
        self.temp_cv_path = None
        cv_file = officer_data.get("cv_path", "No Photo")
        self.cv_filename = os.path.basename(cv_file) if cv_file and cv_file != "No Photo" else "No CV Uploaded"
        
        self.is_self_edit_only = is_self_edit_only
        
        super().__init__(officer_data, "Edit Officer Details", parent, (500, 450), has_photo=True)
        self.original_position = officer_data.get("position", "")

    def _add_form_fields(self, layout):
        layout.addWidget(QtWidgets.QLabel("Position:"))
        self.position_edit = QtWidgets.QComboBox()
        self.position_edit.setStyleSheet(EDIT_STYLE)
        possible_positions = ["Chairperson", "Vice - Internal Chairperson", "Vice - External Chairperson", "Secretary", "Treasurer", "Member"]
        self.position_edit.addItems(possible_positions)
        self.position_edit.setCurrentText(self.data.get("position", ""))
        self.position_edit.setEnabled(not self.is_self_edit_only)
        layout.addWidget(self.position_edit)
        
        if self.is_self_edit_only:
            helper_label = QtWidgets.QLabel("Position can only be changed by a manager.")
            helper_label.setStyleSheet("font-size: 10px; color: #888; font-style: italic;")
            layout.addWidget(helper_label)
        
        layout.addWidget(QtWidgets.QLabel("Curriculum Vitae (CV):"))
        cv_layout = QtWidgets.QHBoxLayout()
        self.cv_label = QtWidgets.QLabel(self.cv_filename) 
        self.cv_label.setStyleSheet("font-style: italic; color: #555; padding: 5px;")
        
        browse_cv_btn = QtWidgets.QPushButton("Browse CV")
        browse_cv_btn.setStyleSheet(BROWSE_STYLE)
        browse_cv_btn.clicked.connect(self.browse_cv)
        
        cv_layout.addWidget(self.cv_label)
        cv_layout.addStretch()
        cv_layout.addWidget(browse_cv_btn)
        layout.addLayout(cv_layout)

    def browse_cv(self):
        """Browse for a CV file (Image or PDF)."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select CV", "", "Files (*.png *.jpg *.jpeg *.pdf)"
        )
        if file_path:
            self.temp_cv_path = file_path
            self.cv_label.setText(os.path.basename(file_path))

    def confirm(self): # MODIFIED
        new_position = self.position_edit.currentText()
        main_window = self.parent().parent()
        
        if not self.is_self_edit_only:
            if BlurredDialog._check_position_conflict(main_window, new_position, self.data.get("name"), self.original_position):
                QtWidgets.QMessageBox.warning(
                    self,
                    "Position Already Taken",
                    f"The position '{new_position}' is already occupied by another officer.",
                    QtWidgets.QMessageBox.StandardButton.Ok
                )
                return

        org_name = main_window.current_org.get("name", "Unknown")

        old_cv_path = self.data.get("cv_path") 
        if self.temp_cv_path:
            new_cv_filename = copy_image_to_data(self.temp_cv_path, org_name)
            if new_cv_filename is None:
                return
            if new_cv_filename != "No Photo":
                self.data["cv_path"] = new_cv_filename
                delete_image(old_cv_path)

        old_photo_path = self.data.get("photo_path") 
        if self.temp_image_path:
            new_filename = self._save_temp_image(org_name)
            
            if new_filename is None:
                return
            if new_filename != "No Photo":
                self.data["photo_path"] = new_filename
                if "card_image_path" in self.data:
                    self.data["card_image_path"] = new_filename
                delete_image(old_photo_path)

        self.data["position"] = new_position
        
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

class BaseOrgDialog(PhotoBrowseMixin, BlurredDialog):
    def __init__(self, parent, title, fixed_size=(600, 500)):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowTitle(title)
        self.setFixedSize(*fixed_size)
        self.logo_path = "No Photo"
        
        self.image_preview_size = (200, 200)
        self.circular_logo_setter = self.parent_window.set_circular_logo
        
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)

        name_layout = QtWidgets.QHBoxLayout()
        name_layout.addWidget(QtWidgets.QLabel("Name:"))
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setStyleSheet(EDIT_STYLE)
        name_layout.addWidget(self.name_edit)
        main_layout.addLayout(name_layout)

        content_layout = self._create_content_layout()
        main_layout.addLayout(content_layout)

        btn_layout = self._create_button_layout(self.confirm, self.reject)
        main_layout.addLayout(btn_layout)

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
        browse_btn.clicked.connect(self.browse_photo)
        left_layout.addWidget(browse_btn)
        content_layout.addWidget(left_widget)

        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)

        # Organization Level dropdown
        org_level_layout = QtWidgets.QHBoxLayout()
        org_level_label = QtWidgets.QLabel("Organization Level:")
        org_level_label.setStyleSheet(LABEL_STYLE)
        org_level_layout.addWidget(org_level_label)
        
        self.org_level_combo = QtWidgets.QComboBox()
        self.org_level_combo.setStyleSheet(EDIT_STYLE)
        self.org_level_combo.addItem("College", "col")
        self.org_level_combo.addItem("Program", "prog")
        org_level_layout.addWidget(self.org_level_combo)
        right_layout.addLayout(org_level_layout)

        # Main Organization multi-select (using QListWidget with checkboxes)
        main_org_label = QtWidgets.QLabel("Main Organization(s) (optional):")
        main_org_label.setStyleSheet(LABEL_STYLE)
        right_layout.addWidget(main_org_label)
        
        self.main_org_list = QtWidgets.QListWidget()
        self.main_org_list.setStyleSheet(EDIT_STYLE)
        self.main_org_list.setMaximumHeight(100)
        self.main_org_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.MultiSelection)
        
        # Fetch organizations from API
        api_response = OrganizationAPIService.fetch_organizations()
        
        if api_response.get('success'):
            organizations_data = api_response.get('data', {}).get('data', [])
            for org in organizations_data:
                item = QtWidgets.QListWidgetItem(org["name"])
                item.setData(QtCore.Qt.ItemDataRole.UserRole, org["id"])
                self.main_org_list.addItem(item)
        else:
            # Fallback to JSON data if API fails
            print(f"API Error: {api_response.get('message')}, falling back to JSON")
            organizations = self.parent_window._load_data()
            for org in organizations:
                if not org.get("is_branch", False):  # Only show organizations, not branches
                    item = QtWidgets.QListWidgetItem(org["name"])
                    item.setData(QtCore.Qt.ItemDataRole.UserRole, org["id"])
                    self.main_org_list.addItem(item)
        
        right_layout.addWidget(self.main_org_list)

        # Description text edit
        self.desc_edit = BlurredDialog._add_text_edit(right_layout, "Description")

        content_layout.addWidget(right_widget)
        return content_layout

    def confirm(self):
        raise NotImplementedError("Subclasses must implement confirm")

class EditOrgDialog(BaseOrgDialog):
    def __init__(self, org_data: dict, parent: QtWidgets.QMainWindow):
        self.org_data = org_data
        super().__init__(parent, "Edit Organization/Branch Details", (600, 500))
        self.name_edit.setText(org_data.get("name", ""))
        
        # Set org level if available
        org_level = org_data.get("org_level", "col")
        index = self.org_level_combo.findData(org_level)
        if index >= 0:
            self.org_level_combo.setCurrentIndex(index)
        
        self.desc_edit.setPlainText(org_data.get("description", ""))
        logo_path = get_image_path(org_data.get("logo_path", "No Photo"))
        self.parent_window.set_circular_logo(self.preview_label, logo_path)
        
        # Pre-select main organizations if any
        main_orgs = org_data.get("main_org", [])
        for i in range(self.main_org_list.count()):
            item = self.main_org_list.item(i)
            org_id = item.data(QtCore.Qt.ItemDataRole.UserRole)
            if org_id in main_orgs:
                item.setSelected(True)

    def _create_parent_layout(self):
        return None

    def confirm(self):
        new_name = self.name_edit.text().strip()
        
        if not new_name:
            QtWidgets.QMessageBox.warning(self, "Invalid Input", "Name is required.")
            return

        # Get organization ID
        org_id = self.org_data.get("id")
        if not org_id:
            QtWidgets.QMessageBox.critical(self, "Error", "Organization ID not found.")
            return

        # Handle logo upload if changed
        logo_full_path = None
        if self.temp_image_path:
            new_filename = self._save_temp_image(new_name)
            if new_filename is None:
                return
            if new_filename != "No Photo":
                logo_full_path = get_image_path(new_filename)
                # Delete old logo
                old_logo_path = self.org_data.get("logo_path")
                if old_logo_path:
                    delete_image(old_logo_path)

        # Get updated values
        new_description = self.desc_edit.toPlainText().strip()
        new_org_level = self.org_level_combo.currentData()
        
        # Get selected main organizations
        selected_main_orgs = []
        for i in range(self.main_org_list.count()):
            item = self.main_org_list.item(i)
            if item.isSelected():
                item_org_id = item.data(QtCore.Qt.ItemDataRole.UserRole)
                selected_main_orgs.append(item_org_id)
        
        # Call API to update organization
        api_response = OrganizationAPIService.update_organization(
            org_id=org_id,
            name=new_name,
            description=new_description,
            org_level=new_org_level,
            logo_path=logo_full_path,
            status="active",
            main_org_ids=selected_main_orgs if selected_main_orgs else None
        )
        
        # Handle API response
        if api_response.get('success'):
            print(f"Updated organization '{new_name}' (ID: {org_id})")
            
            # Refresh the UI to load updated data from database
            if hasattr(self.parent_window, 'load_orgs'):
                self.parent_window.load_orgs()
            
            QtWidgets.QMessageBox.information(
                self,
                "Success",
                f"Organization '{new_name}' updated successfully!",
                QtWidgets.QMessageBox.StandardButton.Ok
            )
            
            self.accept()
        else:
            # API call failed
            error_msg = api_response.get('message', 'Unknown error occurred')
            error_details = api_response.get('error', '')
            
            QtWidgets.QMessageBox.critical(
                self,
                "Update Failed",
                f"{error_msg}\n\nDetails: {error_details}",
                QtWidgets.QMessageBox.StandardButton.Ok
            )

class CreateOrgDialog(BaseOrgDialog):
    def __init__(self, parent):
        super().__init__(parent, "Create Organization", (600, 500))

    def confirm(self):
        name = self.name_edit.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, "Invalid Input", "Name is required.")
            return

        description = self.desc_edit.toPlainText().strip()
        
        logo_filename = self._save_temp_image(name)
        if logo_filename is None:
            return

        # Get organization level from dropdown
        org_level = self.org_level_combo.currentData()
        
        # Get selected main organizations
        selected_main_orgs = []
        for i in range(self.main_org_list.count()):
            item = self.main_org_list.item(i)
            if item.isSelected():
                org_id = item.data(QtCore.Qt.ItemDataRole.UserRole)
                selected_main_orgs.append(org_id)
        
        # Get the full path to the logo file for API upload
        logo_full_path = None
        if logo_filename != "No Photo":
            logo_full_path = get_image_path(logo_filename)
        
        # Call the API to create the organization
        api_response = OrganizationAPIService.create_organization(
            name=name,
            description=description,
            org_level=org_level,
            logo_path=logo_full_path,
            status="active",
            main_org_ids=selected_main_orgs if selected_main_orgs else None
        )
        
        # Handle API response
        if api_response.get('success'):
            org_data = api_response.get('data', {}).get('data', {})
            
            print(f"Created organization '{name}' with ID {org_data.get('id')}")
            if selected_main_orgs:
                print(f"  -> Part of main organization(s): {selected_main_orgs}")

            # Refresh the UI to load from database
            self.parent_window.load_orgs()

            QtWidgets.QMessageBox.information(
                self,
                "Success",
                f"Organization '{name}' created successfully!",
                QtWidgets.QMessageBox.StandardButton.Ok
            )

            self.accept()
        else:
            # API call failed
            error_msg = api_response.get('message', 'Unknown error occurred')
            error_details = api_response.get('error', '')
            
            QtWidgets.QMessageBox.critical(
                self,
                "Creation Failed",
                f"{error_msg}\n\nDetails: {error_details}",
                QtWidgets.QMessageBox.StandardButton.Ok
            )