from PyQt6 import QtCore, QtGui, QtWidgets
from .data_manager import DataManager  # Assumes this is implemented
import main_chat_widget_wrapper
dm =  main_chat_widget_wrapper()

class RecipientDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        
        self.setWindowFlags(
         QtCore.Qt.WindowType.Dialog |
    QtCore.Qt.WindowType.FramelessWindowHint
)
        self.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        self.selected_recipient = None

        # Connect button signals
        self.ui.buttonBox.accepted.connect(self.on_accept)
        self.ui.buttonBox.rejected.connect(self.reject)

        # Connect list selection
        self.ui.recipient_list.itemClicked.connect(self.on_item_selected)

    def on_item_selected(self, item):
        """Store selected recipient and update search bar"""
        self.selected_recipient = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if self.selected_recipient:
            self.ui.recipient_search.setText(self.selected_recipient['name'])

    def on_accept(self):
        """OK button clicked"""
        if self.selected_recipient:
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please select a recipient first.")
            

    def get_selected_recipient(self):
        return self.selected_recipient


class Ui_Form(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("RecipientDialog")
        Dialog.resize(403, 385)
        self.header_widget = QtWidgets.QWidget(parent=Dialog)
        self.header_widget.setGeometry(QtCore.QRect(10, 10, 371, 41))
        self.header_widget.setStyleSheet("""
            QWidget#header_widget {
                background-color: #transparent;
                color: black;
                padding: 10px;
                font-size: 16px;
                font-family: "Poppins";
            }
        """)
        self.header_widget.setObjectName("header_widget")

        self.recipient_label = QtWidgets.QLabel(parent=self.header_widget)
        self.recipient_label.setGeometry(QtCore.QRect(10, -10, 300, 61))

        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(14)
        self.recipient_label.setFont(font)
        self.recipient_label.setText("Select Recipient...")
        self.recipient_label.setObjectName("recipient_label")
        self.recipient_label.setStyleSheet("color: black;")

        self.recipient_search = QtWidgets.QLineEdit(parent=Dialog)
        self.recipient_search.setGeometry(QtCore.QRect(10, 50, 371, 31))
        self.recipient_search.setObjectName("recipient_search")
        self.recipient_search.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc;
                font-family: "Segoe UI", sans-serif;
                padding: 5px;
                background-color: transparent;
                color: black;
            }
        """)

        self.widget_selector = QtWidgets.QWidget(parent=Dialog)
        self.widget_selector.setGeometry(QtCore.QRect(10, 80, 371, 281))
        self.widget_selector.setObjectName("widget_selector")
        self.widget_selector.setStyleSheet("""
            QWidget#widget_selector {
                background-color: white;
                border: 1px solid #ccc;
                font-family: "Segoe UI", sans-serif;
            }
        """)

        self.recipient_list = QtWidgets.QListWidget(parent=self.widget_selector)
        self.recipient_list.setGeometry(QtCore.QRect(10, 10, 351, 230))
        self.recipient_list.setObjectName("recipient_list")
        self.recipient_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: white;
                font-family: "Segoe UI", sans-serif;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
                color: black;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
            QListWidget::item:selected {
                background-color: #084924;
                color: white;
            }
        """)

        self.buttonBox = QtWidgets.QDialogButtonBox(parent=self.widget_selector)
        self.buttonBox.setGeometry(QtCore.QRect(210, 250, 156, 24))
        self.buttonBox.setStandardButtons(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel |
            QtWidgets.QDialogButtonBox.StandardButton.Ok
        )
        self.buttonBox.setStyleSheet("color: black;")
        self.buttonBox.setObjectName("buttonBox")

        # Load and populate data

        self.data_manager = dm.getDataManager()
        self.all_recipients = self.load_faculty_and_officers()
        self.filtered_recipients = self.all_recipients.copy()
        self.populate_recipient_list()

        # Search filtering
        self.recipient_search.textChanged.connect(self.filter_recipients)

    def load_faculty_and_officers(self):
        recipients = []
        all_users = self.data_manager.get_all_users()
        for user in all_users:
            if user.get('role') in ['faculty', 'admin', 'officer', 'staff']:
                recipients.append({
                    'id': user.get('id'),
                    'name': user.get('name'),
                    'email': user.get('email'),
                    'role': user.get('role'),
                    'department': user.get('department', 'Unknown')
                })
        return recipients
    def populate_recipient_list(self):
        self.recipient_list.clear()
        for recipient in self.filtered_recipients:
            display_text = f"{recipient['name']} ({recipient['role'].title()})"
            item = QtWidgets.QListWidgetItem(display_text)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, recipient)
            self.recipient_list.addItem(item)

    def filter_recipients(self, text):
        if not text.strip():
            self.filtered_recipients = self.all_recipients.copy()
        else:
            text = text.lower()
            self.filtered_recipients = [
                r for r in self.all_recipients
                if r['name'].lower().startswith(text)
            ]
        self.populate_recipient_list()


# # --------------------------
# # MAIN ENTRY POINT
# # --------------------------
# if __name__ == "__main__":
#     import sys
#     app = QtWidgets.QApplication(sys.argv)

#     dialog = RecipientDialog()
#     if dialog.exec():  # Will be True if accept() is called
#         selected = dialog.get_selected_recipient()
#         print("✅ Recipient selected:", selected)
#     else:
#         print("❌ Dialog canceled")

#     sys.exit(0)
