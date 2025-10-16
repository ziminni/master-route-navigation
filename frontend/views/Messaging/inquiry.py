from PyQt6 import QtCore, QtWidgets
from .recipient_dialog import RecipientDialog  # generated from recipient_dialog.ui


# ============================
# Inquiry Dialog UI Class
# ============================
class Ui_InquiryDialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("InquiryDialog")
        Dialog.resize(420, 500)

        # Main layout
        self.main_layout = QtWidgets.QVBoxLayout(Dialog)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(10)

        # White container (styled card)
        self.inquiry_widget = QtWidgets.QWidget(parent=Dialog)
        self.inquiry_widget.setObjectName("inquiry_widget")
        self.inquiry_widget.setStyleSheet("""
            QWidget#inquiry_widget {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #dddddd;
            }
        """)

        # Form layout
        self.form_layout = QtWidgets.QVBoxLayout(self.inquiry_widget)
        self.form_layout.setContentsMargins(20, 20, 20, 20)
        self.form_layout.setSpacing(12)

        # Title
        self.inquiry_header = QtWidgets.QLabel("New Inquiry")
        self.inquiry_header.setStyleSheet("color: #084924; font-size: 20px; font-weight: bold;")
        self.form_layout.addWidget(self.inquiry_header)

        # Inquiry Type Radio Buttons
        self.type_layout = QtWidgets.QGridLayout()
        self.push_acad = QtWidgets.QRadioButton("Academic")
        self.push_admin = QtWidgets.QRadioButton("Administrative")
        self.push_tech = QtWidgets.QRadioButton("Technical")
        self.push_gen = QtWidgets.QRadioButton("General")
        self.push_acad.setStyleSheet("color: black")
        self.push_admin.setStyleSheet("color: black")
        self.push_gen.setStyleSheet("color: black")
        self.push_tech.setStyleSheet("color: black")
        self.push_gen.setChecked(True)
        self.type_layout.addWidget(self.push_acad, 0, 0)
        self.type_layout.addWidget(self.push_tech, 0, 1)
        self.type_layout.addWidget(self.push_admin, 1, 0)
        self.type_layout.addWidget(self.push_gen, 1, 1)
        self.form_layout.addLayout(self.type_layout)

        # Recipient
        self.label_to = QtWidgets.QLabel("Send to")
        self.label_to.setStyleSheet("color: black")
        self.form_layout.addWidget(self.label_to)

        self.recipient_layout = QtWidgets.QHBoxLayout()
        self.search_recipt = QtWidgets.QLineEdit()
        self.search_recipt.setPlaceholderText("Enter recipient...")
        self.search_recipt.setStyleSheet("color: black")
        self.search_recipt.setReadOnly(True)

        # self.recipient_label = QtWidgets.QLabel("No recipient selected")
        # self.recipient_label.setStyleSheet("font-weight: bold; color: #084924;")

        self.btn_select_recipient = QtWidgets.QPushButton("△")
        self.btn_select_recipient.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #003d1f;
                border: none;
                font-size: 20px;
            }
            QPushButton:hover { color: #005a2e; }
            QPushButton:pressed { color: #002d17; }
        """)
        self.btn_select_recipient.setToolTip("Select Recipient")

        self.recipient_layout.addWidget(self.search_recipt)
        # self.recipient_layout.addWidget(self.recipient_label)
        self.recipient_layout.addWidget(self.btn_select_recipient)
        self.form_layout.addLayout(self.recipient_layout)

        # Priority
        self.label_priority = QtWidgets.QLabel("Priority Level")
        self.priority_layout = QtWidgets.QHBoxLayout()
        self.checkBox = QtWidgets.QRadioButton("Normal")
        self.checkBox_2 = QtWidgets.QRadioButton("High")
        self.checkBox_3 = QtWidgets.QRadioButton("Urgent")
        self.checkBox.setStyleSheet("color: black")
        self.checkBox_2.setStyleSheet("color: black")
        self.checkBox_3.setStyleSheet("color: black")
        self.label_priority.setStyleSheet("color: black")
        self.checkBox.setChecked(True)
        self.priority_layout.addWidget(self.checkBox)
        self.priority_layout.addWidget(self.checkBox_2)
        self.priority_layout.addWidget(self.checkBox_3)
        self.form_layout.addWidget(self.label_priority)
        self.form_layout.addLayout(self.priority_layout)

        # Subject
        self.label_sub = QtWidgets.QLabel("Subject")
        self.label_sub.setStyleSheet("color: black")
        self.search_sub = QtWidgets.QLineEdit()
        self.search_sub.setStyleSheet("color: black")
        self.form_layout.addWidget(self.label_sub)
        self.form_layout.addWidget(self.search_sub)

        # Message
        self.label_msg = QtWidgets.QLabel("Detailed message")
        self.label_msg.setStyleSheet("color: black")
        self.search_msg = QtWidgets.QTextEdit()
        self.search_msg.setStyleSheet("color: black")
        self.form_layout.addWidget(self.label_msg)
        self.form_layout.addWidget(self.search_msg)

        # Info Note
        self.label_note = QtWidgets.QLabel(
            "Be as specific as possible to help us provide the best assistance."
        )
        self.label_note.setWordWrap(True)
        self.label_note.setStyleSheet("font-size: 11px; color: gray;")
        self.form_layout.addWidget(self.label_note)

        # Additional Options
        self.label_opts = QtWidgets.QLabel("Additional Options")
        self.checkBox_4 = QtWidgets.QCheckBox("Request read receipt")
        self.checkBox_5 = QtWidgets.QCheckBox("Send copy to my email")
        self.checkBox_6 = QtWidgets.QCheckBox("Mark as confidential")
        self.label_opts.setStyleSheet("color: black")
        self.checkBox_4.setStyleSheet("color: black")
        self.checkBox_5.setStyleSheet("color: black")
        self.checkBox_6.setStyleSheet("color: black")
        self.form_layout.addWidget(self.label_opts)
        self.form_layout.addWidget(self.checkBox_4)
        self.form_layout.addWidget(self.checkBox_5)
        self.form_layout.addWidget(self.checkBox_6)

        # Bottom Buttons
        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_cancel = QtWidgets.QPushButton("Cancel")
        self.button_create = QtWidgets.QPushButton("Create")
        self.button_cancel.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #333;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px 15px;
                                         }
        """)
        self.button_create.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #333;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px 15px;
                                         }
        """)
        self.button_layout.addStretch(1)
        self.button_layout.addWidget(self.button_cancel)
        self.button_layout.addWidget(self.button_create)
        self.form_layout.addLayout(self.button_layout)

        # Add the card to main layout
        self.main_layout.addWidget(self.inquiry_widget)


# ============================
# Inquiry Dialog Wrapper
# ============================
class InquiryDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, current_user_id=2):
        super().__init__(parent)
        self.ui = Ui_InquiryDialog()
        self.ui.setupUi(self)

        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(420, 500)
        self.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint |
            QtCore.Qt.WindowType.Dialog
        )

        # Connect buttons
        self.ui.button_cancel.clicked.connect(self.reject)
        self.ui.button_create.clicked.connect(self.create_inquiry)
        self.ui.btn_select_recipient.clicked.connect(self.open_recipient_dialog)

        # Initialize data
        self.inquiry_data = None
        self.recipient = None
        self.current_user_id = current_user_id  # Placeholder for actual user context

    # ----------------------------
    # # Recipient Methods
    # # ----------------------------
    def set_recipient(self, recipient: dict):
        """Set the recipient for this inquiry"""
        self.recipient = recipient
        self.ui.search_recipt.setText(recipient['name'])  # Fill the input field
        print("✅ Recipient set in input:", recipient['name'])

    def open_recipient_dialog(self):
        """Open recipient selection dialog"""
        dialog = RecipientDialog(self)
        if dialog.exec():  # OK clicked
            selected = dialog.get_selected_recipient()
            if selected:
                self.set_recipient(selected)
                print("✅ Recipient selected:", selected)
            else:
                QtWidgets.QMessageBox.warning(self, "No Selection", "Please select a recipient.")
        else:
            print("❌ Recipient dialog canceled")

    # ----------------------------
    # Inquiry Data Methods
    # ----------------------------
    def create_inquiry(self):
        """Create inquiry with data from the form"""
        if not self.recipient:
            QtWidgets.QMessageBox.warning(self, "Validation Error", "Please select a recipient.")
            return

        subject = self.ui.search_sub.text().strip()
        message = self.ui.search_msg.toPlainText().strip()
        if not subject or not message:
            QtWidgets.QMessageBox.warning(self, "Validation Error",
                                        "Please fill in all required fields (Subject, Message)")
            return

       # Determine correct role-based key
        recipient_role = self.recipient.get('role')
        recipient_id = self.recipient.get('id')

        # Dynamically assign recipient based on role
        recipient_field = None
        if recipient_role == 'faculty':
            recipient_field = 'faculty_id'
        elif recipient_role == 'staff':
            recipient_field = 'staff_id'
        elif recipient_role == 'admin':
            recipient_field = 'admin_id'
        else:
            QtWidgets.QMessageBox.warning(self, "Invalid Recipient", "Selected recipient has an unsupported role.")
            return

        # Create the inquiry data
        self.inquiry_data = {
            'student_id': self.current_user_id,
            recipient_field: recipient_id,  # ✅ dynamically set key here
            'inquiry_type': self.get_selected_inquiry_type(),
            'subject': subject,
            'description': message,
            'priority': self.get_selected_priority(),
            'status': 'pending'
        }

        self.accept()


    def get_inquiry_data(self):
        return self.inquiry_data

    def get_selected_inquiry_type(self):
        if self.ui.push_acad.isChecked():
            return 'academic'
        elif self.ui.push_admin.isChecked():
            return 'administrative'
        elif self.ui.push_tech.isChecked():
            return 'technical'
        else:
            return 'general'

    def get_selected_priority(self):
        if self.ui.checkBox_3.isChecked():
            return 'urgent'
        elif self.ui.checkBox_2.isChecked():
            return 'high'
        else:
            return 'normal'
