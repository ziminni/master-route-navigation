# admin_broadcast_dialog.py
from PyQt6 import QtWidgets
from .admin.admin_broadcast import Ui_MainWindow as BroadcastUI

class BroadcastDialog(QtWidgets.QDialog, BroadcastUI):
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent)
        # Use QDialog as the base, but reuse Ui_MainWindow layout
        self.setWindowTitle("System Broadcast")
        self.setupUi(self)     # pass self instead of a QMainWindow

        self.data_manager = data_manager

        # Wire buttons
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_broadcast.clicked.connect(self._on_submit)

    def _on_submit(self):
        if self.data_manager is None:
            QtWidgets.QMessageBox.warning(self, "Error", "DataManager is not available.")
            return

        subject = self.text_edit_subject.toPlainText().strip()
        message = self.text_edit_message.toPlainText().strip()
        message_type = self.line_role.currentText()

        # Simple recipient selection from checkboxes
        recipients = []
        if self.checkBox.isChecked():
            recipients.append("all")
        if self.checkBox_2.isChecked():
            recipients.append("faculty")
        if self.checkBox_3.isChecked():
            recipients.append("students")
        if self.checkBox_7.isChecked():
            recipients.append("staff")

        if not subject or not message:
            QtWidgets.QMessageBox.warning(self, "Error", "Subject and message cannot be empty.")
            return

        # Call your backend
        try:
            ok = self.data_manager.send_system_broadcast(
                title=subject,
                content=message,
                message_type=message_type,
                recipients=recipients,
                schedule=self.checkBox_6.isChecked(),
            )
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Broadcast failed: {e}")
            return

        if ok:
            QtWidgets.QMessageBox.information(self, "Success", "Broadcast sent successfully.")
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Failed to send broadcast.")
