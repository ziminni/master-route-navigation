import sys
from typing import List, Dict, Any
from PyQt6 import QtCore, QtWidgets
from .data_manager import DataManager
from .organization.org_home import Ui_Form  # adjust the import path if needed


class OrgMainUI(QtWidgets.QWidget):
    """
    Wrapper for org_home.Ui_Form (Student Organization / Officer view).

    - Binds the generated Ui_Form to a QWidget.
    - Connects category buttons (All, Pending, Replied, New Messages).
    - Uses DataManager to load organization-related messages for the current officer.
    """

    def __init__(
            self,
            username: str | None = None,
            roles: list | None = None,
            primary_role: str | None = None,
            token: str | None = None,
            data_manager=None,
            parent=None,
            layout=None,
    ):
        super().__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.layout_manger = layout

        # Session + data manager

        self.username = username
        self.primary_role = primary_role or "officer"
        self.roles = roles or ["officer"]
        self.data_manager = data_manager

        # In‑memory items
        self.all_items: List[Dict[str, Any]] = []
        self.filtered_items: List[Dict[str, Any]] = []

        # Build internal content area
        self._init_items_area()
        self._connect_signals()

        # Load data
        self._load_org_counts()
        self._load_messages()
        # --- HEADER FROM LAYOUT MANAGER ---
        self.header = self.layout_manager.get_header() if self.layout_manager else None

        # only wire mail popup if header exists
        if self.header is not None and hasattr(self.header, "mail_menu"):
            self.header.mail_menu.messageActivated.connect(
                self._on_inbox_item_clicked
            )
            self._refresh_inbox_popup()

    # ---------------------------
    # UI setup
    # ---------------------------
    def _init_items_area(self):
        # Create a scrollable list inside widget_main
        self.scroll_area = QtWidgets.QScrollArea(self.ui.widget_main)
        self.scroll_area.setGeometry(QtCore.QRect(10, 60, 771, 521))
        self.scroll_area.setWidgetResizable(True)

        self.list_container = QtWidgets.QWidget()
        self.list_layout = QtWidgets.QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(6)
        self.list_layout.addStretch()

        self.scroll_area.setWidget(self.list_container)

    def _connect_signals(self):
        # Category buttons
        self.ui.btn_org.clicked.connect(self._filter_new_messages)
        self.ui.btn_all.clicked.connect(lambda: self._filter_status("all"))
        self.ui.btn_pend.clicked.connect(lambda: self._filter_status("pending"))
        self.ui.btn_reply.clicked.connect(lambda: self._filter_status("replied"))

        # Priority combo
        self.ui.combo_prio.currentTextChanged.connect(self.apply_filters)

    # ---------------------------
    # Data loading
    # ---------------------------
    def _load_org_counts(self):
        """
        Fill the small cards (TOTAL, PENDING, REPLIED).
        Later you can replace this with a dedicated stats endpoint.
        """
        try:
            # If you have a stats endpoint like /org/stats/, call it here.
            # For now, counts will be derived after _load_messages if needed.
            pass
        except Exception as e:
            print(f"[OrgMainUI] Error loading org counts: {e}")



    def _load_messages(self):
        """
        Load organization messages for this officer.
        Replace the API logic to match your backend schema (org, officer, etc.).
        """
        try:
            officer_id = None
            if self.username:
                user = self.data_manager.get_user_by_email(self.username)
                officer_id = user.get("id") if user else None

            raw_messages: List[Dict[str, Any]] = []
            if officer_id:
                # Example: use get_messages_by_user for now.
                raw_messages = self.data_manager.get_messages_by_user(officer_id)
            else:
                raw_messages = []

            items: List[Dict[str, Any]] = []
            for msg in raw_messages:
                items.append(
                    {
                        "id": msg.get("id"),
                        "title": msg.get("subject", "No Subject"),
                        "content": msg.get("content", ""),
                        "sender": msg.get("sender_name", "Unknown"),
                        "priority": msg.get("priority", "normal").lower(),
                        "status": msg.get("status", "pending").lower(),  # pending / replied / etc.
                        "created_at": msg.get("created_at", ""),
                        "is_new": msg.get("is_new", False),
                    }
                )

            self.all_items = items
            self.filtered_items = items.copy()
            self._update_counts_from_items()
            self._refresh_list()
        except Exception as e:
            print(f"[OrgMainUI] Error loading org messages: {e}")

    def _update_counts_from_items(self):
        try:
            total = len(self.all_items)
            pending = sum(1 for i in self.all_items if i.get("status") == "pending")
            replied = sum(1 for i in self.all_items if i.get("status") == "replied")

            self.ui.label_num_pend.setText(str(total))        # TOTAL MESSAGES
            self.ui.label_num_pend_2.setText(str(pending))    # PENDING
            self.ui.label_num_reply.setText(str(replied))     # REPLIED
        except Exception as e:
            print(f"[OrgMainUI] Error updating org counts: {e}")

    # ---------------------------
    # Display
    # ---------------------------
    def _clear_list(self):
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _refresh_list(self):
        self._clear_list()

        if not self.filtered_items:
            lbl = QtWidgets.QLabel("No messages found.")
            lbl.setStyleSheet("color: #888888; font-size: 14px;")
            self.list_layout.insertWidget(0, lbl)
            return

        for msg in self.filtered_items:
            try:
                card = self._create_message_card(msg)
                self.list_layout.insertWidget(self.list_layout.count() - 1, card)
            except Exception as e:
                print(f"[OrgMainUI] Error creating message card: {e}")

    def _create_message_card(self, item: Dict[str, Any]) -> QtWidgets.QFrame:
        card = QtWidgets.QFrame()
        card.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        card.setStyleSheet(
            """
            QFrame {
                background-color: #ffffff;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
            QFrame:hover {
                background-color: #f7f7f7;
            }
            """
        )
        card.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )

        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Header row: sender + status
        header_layout = QtWidgets.QHBoxLayout()
        sender_lbl = QtWidgets.QLabel(item.get("sender", "Unknown"))
        sender_lbl.setStyleSheet("font-weight: bold; color: #006420;")
        header_layout.addWidget(sender_lbl)

        header_layout.addStretch()

        status = item.get("status", "pending")
        status_color = {
            "pending": "#fbbf24",
            "replied": "#10b981",
        }.get(status, "#6b7280")

        status_lbl = QtWidgets.QLabel(status.upper())
        status_lbl.setStyleSheet(
            f"background-color: {status_color};"
            "color: white; padding: 2px 8px; border-radius: 10px; font-size: 10px;"
        )
        header_layout.addWidget(status_lbl)
        layout.addLayout(header_layout)

        # Title
        title_lbl = QtWidgets.QLabel(item.get("title", "No Subject"))
        title_lbl.setStyleSheet("font-size: 14px;")
        title_lbl.setWordWrap(True)
        layout.addWidget(title_lbl)

        # Content preview
        content = item.get("content", "")
        preview = content[:120] + "..." if len(content) > 120 else content
        content_lbl = QtWidgets.QLabel(preview)
        content_lbl.setWordWrap(True)
        layout.addWidget(content_lbl)

        # Footer
        footer_layout = QtWidgets.QHBoxLayout()
        created_at = item.get("created_at", "")[:10] if item.get("created_at") else ""
        footer_layout.addWidget(QtWidgets.QLabel(created_at or ""))
        footer_layout.addStretch()
        footer_layout.addWidget(QtWidgets.QLabel(item.get("priority", "normal").upper()))
        layout.addLayout(footer_layout)

        # Click handling
        card.mousePressEvent = lambda e, data=item: self._open_message_details(data)
        return card

    def _open_message_details(self, item: Dict[str, Any]):
        dlg = QtWidgets.QMessageBox(self)
        dlg.setWindowTitle(item.get("title", "Message Details"))
        dlg.setText(item.get("content", ""))
        dlg.exec()

    # ---------------------------
    # Filtering & search
    # ---------------------------
    def _filter_status(self, status: str):
        """
        Status buttons: all, pending, replied.
        """
        if status == "all":
            self.filtered_items = self.all_items.copy()
        else:
            self.filtered_items = [
                i for i in self.all_items if i.get("status") == status
            ]
        self.apply_filters()

    def _filter_new_messages(self):
        """
        'New Messages' button: you can define 'new' as status=pending or is_new==True.
        """
        self.filtered_items = [
            i for i in self.all_items if i.get("is_new") or i.get("status") == "pending"
        ]
        self.apply_filters()

    def apply_filters(self):
        try:
            items = self.filtered_items.copy()
            prio_text = self.ui.combo_prio.currentText()

            if prio_text and prio_text not in ("Priority", "Priorities"):
                # Customize mapping when you define real priority options
                p = prio_text.lower()
                items = [i for i in items if i.get("priority") == p]

            self.filtered_items = items
            self._refresh_list()
        except Exception as e:
            print(f"[OrgMainUI] Error applying filters: {e}")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = OrgMainUI(username="officer@cmu.edu.ph", roles=["officer"], primary_role="officer")
    win.resize(1285, 1105)
    win.show()
    sys.exit(app.exec())
