# admin_details_dialog.py
from PyQt6 import QtWidgets
from .admin.admin_details import Ui_Form as DetailsUI

class MessageDetailsDialog(QtWidgets.QDialog, DetailsUI):
    def __init__(self, message: dict, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        # Fill header + basic info
        self.admin_header.setText(message.get("title", "Message details"))
        self.line_name.setText(message.get("content", ""))

        # Top strip (date/from/to)
        self.label_body_4.setText(message.get("date", "")[:10] or "Unknown")
        self.label_body_3.setText(f"From: {message.get('sender', 'Unknown')}")
        self.label_body_2.setText(f"To: {message.get('recipient', 'admin@cmu.edu.ph')}")

        # Right-side labels (priority, status, department, category, date)
        # These are static text widgets; you can replace them with value labels later if needed.
        # For now, just use tooltips to show dynamic values:
        self.label_2.setToolTip(message.get("priority", "normal").title())
        self.label_3.setToolTip(message.get("status", "pending").title())
        self.label_7.setToolTip(message.get("department", "General"))
        self.label_8.setToolTip(message.get("category", "System"))
        self.label_9.setToolTip(message.get("date", "")[:19])

        # Hook action buttons
        self.btn_assign.clicked.connect(self._on_assign)
        self.btn_mark.clicked.connect(self._on_mark_resolved)
        self.btn_archive.clicked.connect(self._on_archive)
        self.toolButton.clicked.connect(self.reject)  # "x" close

        # Keep original dict if needed
        self.message = message

    def _on_assign(self):
        # Placeholder; you can open another dialog or call DataManager here via parent
        QtWidgets.QMessageBox.information(self, "Assign", "Assign action not implemented yet.")

    def _on_mark_resolved(self):
        self.accept()  # or call backend before closing

    def _on_archive(self):
        self.accept()  # or call backend before closing
