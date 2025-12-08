from PyQt6 import QtWidgets, QtCore
from views.Organizations.BrowseView.Utils.image_utils import get_image_path

class AdviserAssignDialog(QtWidgets.QDialog):
    def __init__(self, org_data: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Assign Faculty Adviser")
        self.org_data = org_data
        self.selected_faculty = None

        layout = QtWidgets.QVBoxLayout(self)

        faculty_list = self._load_faculty_list()

        lbl = QtWidgets.QLabel(f"Select adviser for <b>{org_data['name']}</b>:")
        layout.addWidget(lbl)

        self.combo = QtWidgets.QComboBox()
        current = org_data.get("adviser")
        for fac in faculty_list:
            self.combo.addItem(fac, fac)
            if fac == current:
                self.combo.setCurrentText(fac)
        layout.addWidget(self.combo)

        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _load_faculty_list(self):
        try:
            import json, os
            path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "Data", "users.json")
            with open(path) as f:
                users = json.load(f)
            return [u["name"] for u in users if u.get("role") == "faculty"]
        except Exception:
            return ["Prof. Juan Dela Cruz", "Prof. Maria Santos"]   # fallback

    def get_selected_faculty(self):
        return self.combo.currentText() if self.combo.currentText() else None