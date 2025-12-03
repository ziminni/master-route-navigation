from PyQt6 import QtCore, QtWidgets
from .recipient_dialog import RecipientDialog


class InlineMessageDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, title="Message", text=""):
        super().__init__(parent)
        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint |
            QtCore.Qt.WindowType.Dialog
        )
        self.setModal(True)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        container = QtWidgets.QWidget(self)
        container.setObjectName("inline_msg_container")
        container.setStyleSheet("""
            QWidget#inline_msg_container {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #dddddd;
            }
            QLabel {
                color: black;
            }
            QPushButton {
                background-color: #f0f0f0;
                color: #333;
                border: none;
                border-radius: 5px;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        inner = QtWidgets.QVBoxLayout(container)
        inner.setContentsMargins(20, 20, 20, 15)
        inner.setSpacing(8)

        title_lbl = QtWidgets.QLabel(title, container)
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: black;")
        inner.addWidget(title_lbl)

        text_lbl = QtWidgets.QLabel(text, container)
        text_lbl.setWordWrap(True)
        inner.addWidget(text_lbl)

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch(1)
        ok_btn = QtWidgets.QPushButton("OK", container)
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)
        inner.addLayout(btn_row)

        layout.addWidget(container)


class Ui_InquiryDialog(object):
    # (UNCHANGED UI CODE — KEPT EXACTLY AS YOU PROVIDED)
    def setupUi(self, Dialog):
        Dialog.setObjectName("InquiryDialog")
        Dialog.resize(420, 500)

        self.main_layout = QtWidgets.QVBoxLayout(Dialog)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(10)

        self.inquiry_widget = QtWidgets.QWidget(parent=Dialog)
        self.inquiry_widget.setObjectName("inquiry_widget")
        self.inquiry_widget.setStyleSheet("""
            QWidget#inquiry_widget {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #dddddd;
            }
        """)

        self.form_layout = QtWidgets.QVBoxLayout(self.inquiry_widget)
        self.form_layout.setContentsMargins(20, 20, 20, 20)
        self.form_layout.setSpacing(12)

        self.inquiry_header = QtWidgets.QLabel("New Inquiry")
        self.inquiry_header.setStyleSheet("color: #084924; font-size: 20px; font-weight: bold;")
        self.form_layout.addWidget(self.inquiry_header)

        self.type_layout = QtWidgets.QGridLayout()
        self.push_acad = QtWidgets.QRadioButton("Academic")
        self.push_admin = QtWidgets.QRadioButton("Administrative")
        self.push_tech = QtWidgets.QRadioButton("Technical")
        self.push_gen = QtWidgets.QRadioButton("General")
        for rb in (self.push_acad, self.push_admin, self.push_tech, self.push_gen):
            rb.setStyleSheet("color: black")
        self.push_gen.setChecked(True)
        self.type_layout.addWidget(self.push_acad, 0, 0)
        self.type_layout.addWidget(self.push_tech, 0, 1)
        self.type_layout.addWidget(self.push_admin, 1, 0)
        self.type_layout.addWidget(self.push_gen, 1, 1)
        self.form_layout.addLayout(self.type_layout)

        self.label_to = QtWidgets.QLabel("Send to")
        self.label_to.setStyleSheet("color: black")
        self.form_layout.addWidget(self.label_to)

        self.recipient_layout = QtWidgets.QHBoxLayout()
        self.search_recipt = QtWidgets.QLineEdit()
        self.search_recipt.setPlaceholderText("Select recipient...")
        self.search_recipt.setStyleSheet("color: black")
        self.search_recipt.setReadOnly(True)

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
        self.recipient_layout.addWidget(self.btn_select_recipient)
        self.form_layout.addLayout(self.recipient_layout)

        self.label_priority = QtWidgets.QLabel("Priority Level")
        self.label_priority.setStyleSheet("color: black")
        self.form_layout.addWidget(self.label_priority)

        self.priority_layout = QtWidgets.QHBoxLayout()
        self.checkBox = QtWidgets.QRadioButton("Normal")
        self.checkBox_2 = QtWidgets.QRadioButton("High")
        self.checkBox_3 = QtWidgets.QRadioButton("Urgent")
        for rb in (self.checkBox, self.checkBox_2, self.checkBox_3):
            rb.setStyleSheet("color: black")
        self.checkBox.setChecked(True)
        self.priority_layout.addWidget(self.checkBox)
        self.priority_layout.addWidget(self.checkBox_2)
        self.priority_layout.addWidget(self.checkBox_3)
        self.form_layout.addLayout(self.priority_layout)

        self.label_sub = QtWidgets.QLabel("Subject")
        self.label_sub.setStyleSheet("color: black")
        self.search_sub = QtWidgets.QLineEdit()
        self.search_sub.setStyleSheet("color: black")
        self.form_layout.addWidget(self.label_sub)
        self.form_layout.addWidget(self.search_sub)

        self.label_msg = QtWidgets.QLabel("Detailed message")
        self.label_msg.setStyleSheet("color: black")
        self.search_msg = QtWidgets.QTextEdit()
        self.search_msg.setStyleSheet("color: black")
        self.form_layout.addWidget(self.label_msg)
        self.form_layout.addWidget(self.search_msg)

        self.label_note = QtWidgets.QLabel(
            "Be as specific as possible to help us provide the best assistance."
        )
        self.label_note.setWordWrap(True)
        self.label_note.setStyleSheet("font-size: 11px; color: gray;")
        self.form_layout.addWidget(self.label_note)

        self.label_opts = QtWidgets.QLabel("Additional Options")
        self.label_opts.setStyleSheet("color: black")
        self.form_layout.addWidget(self.label_opts)

        self.checkBox_4 = QtWidgets.QCheckBox("Request read receipt")
        self.checkBox_5 = QtWidgets.QCheckBox("Send copy to my email")
        self.checkBox_6 = QtWidgets.QCheckBox("Mark as confidential")
        for cb in (self.checkBox_4, self.checkBox_5, self.checkBox_6):
            cb.setStyleSheet("color: black")
            self.form_layout.addWidget(cb)

        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_cancel = QtWidgets.QPushButton("Cancel")
        self.button_create = QtWidgets.QPushButton("Create")
        for btn in (self.button_cancel, self.button_create):
            btn.setStyleSheet("""
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

        self.main_layout.addWidget(self.inquiry_widget)


class InquiryDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, current_user_id=None, data_manager=None):
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

        self.data_manager = data_manager
        self.current_user_id = int(current_user_id) if current_user_id else None

        self.inquiry_data = None
        self.recipient = None

        self.ui.button_cancel.clicked.connect(self.reject)
        self.ui.button_create.clicked.connect(self.create_inquiry)
        self.ui.btn_select_recipient.clicked.connect(self.open_recipient_dialog)

    def _show_inline_message(self, title: str, text: str):
        dlg = InlineMessageDialog(self, title=title, text=text)
        dlg.exec()

    def set_recipient(self, recipient: dict):
        self.recipient = recipient
        self.ui.search_recipt.setText(recipient["name"])
        print("✅ Recipient set:", recipient["name"])

    def open_recipient_dialog(self):
        dialog = RecipientDialog(self, data_manager=self.data_manager)
        if dialog.exec():
            selected = dialog.get_selected_recipient()
            if selected:
                self.set_recipient(selected)
            else:
                self._show_inline_message("No Selection", "Please select a recipient.")

    # FIXED VERSION
    def _get_or_create_conversation(self, faculty_id: int):

        if not self.data_manager or not self.current_user_id:
            print("[Inquiry] Missing data_manager or current_user_id")
            return None

        try:
            faculty_id = int(faculty_id)
            uid = int(self.current_user_id)

            print(f"[Inquiry] current_user_id={uid} faculty_id={faculty_id}")

            convs = self.data_manager.get_conversations_by_user(uid)
            print("[Inquiry] Loaded", len(convs), "conversations")

            for conv in convs:
                raw_participants = conv.get("participants", [])
                participants = [int(p) for p in raw_participants]

                print(" - conv:", conv.get("id"), "participants:", participants)

                if (
                        uid in participants
                        and faculty_id in participants
                        and not conv.get("is_group", False)
                ):
                    print("[Inquiry] Using existing conversation", conv.get("id"))
                    return conv.get("id")

            # IMPORTANT: include creator
            payload = {
                "title": "",
                "participants": [uid, faculty_id],
                "creator": uid,
            }

            print("[Inquiry] Creating conversation:", payload)

            created = self.data_manager.create_conversation(payload)
            print("[Inquiry] API returned:", created)

            if not created:
                print("[Inquiry] ERROR: create_conversation returned None/False")
                return None

            conv_id = created.get("id")
            print("[Inquiry] New conversation ID:", conv_id)

            return conv_id

        except Exception as e:
            print("[Inquiry] Error in conversation:", e)

        return None


    def create_inquiry(self):
        if not self.recipient:
            self._show_inline_message("Validation Error", "Please select a recipient.")
            return

        subject = self.ui.search_sub.text().strip()
        message = self.ui.search_msg.toPlainText().strip()

        if not subject or not message:
            self._show_inline_message(
                "Validation Error",
                "Please fill in all required fields (Subject, Message)",
            )
            return

        priority = self.get_selected_priority()
        inquiry_type = self.get_selected_inquiry_type()
        department = self.recipient.get("department", "General")

        # FIX: use self.recipient, not undefined variable
        faculty_id = int(self.recipient.get("id"))

        print("👉 Selected recipient:", self.recipient)
        print("👉 Passing faculty_id:", faculty_id)

        conv_id = self._get_or_create_conversation(faculty_id)
        if conv_id is None:
            self._show_inline_message(
                "Conversation Error",
                "Could not create or retrieve a conversation.",
            )
            return

        body = f"[{inquiry_type.capitalize()} Inquiry]\n\n{message}"

        self.inquiry_data = {
            "conversation": conv_id,
            "content": body,
            "subject": subject,
            "priority": priority,
            "status": "pending",
            "department": department,
            "message_type": "inquiry",
            "is_broadcast": False,
            "receiver": faculty_id,
        }

        self.accept()

    def get_inquiry_data(self):
        return self.inquiry_data

    def get_selected_inquiry_type(self):
        if self.ui.push_acad.isChecked():
            return "academic"
        if self.ui.push_admin.isChecked():
            return "administrative"
        if self.ui.push_tech.isChecked():
            return "technical"
        return "general"

    def get_selected_priority(self):
        if self.ui.checkBox_3.isChecked():
            return "urgent"
        if self.ui.checkBox_2.isChecked():
            return "high"
        return "normal"
