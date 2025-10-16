import requests
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt

class AdminDashboard(QWidget):
    def __init__(self, username, roles, primary_role, token, parent=None):
        super().__init__(parent)
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token

        # ---- config your API base + endpoints here ----
        self.api_base = "http://127.0.0.1:8000/api/"
        self.users_url = self.api_base + "users/"
        self.promote_url_tmpl = self.api_base +"users/" + "roles/org-officer/{user_id}/promote/"
        self.demote_url_tmpl  = self.api_base +"users/" + "roles/org-officer/{user_id}/demote/"
        self.promote_registrar = self.api_base +"users/" + "roles/registrar/{user_id}/promote/"
        self.demote_registrar = self.api_base +"users/" + "roles/registrar/{user_id}/demote/"

        self.headers = {"Authorization": f"Bearer {self.token}"}

        self.setWindowTitle("Dashboard")
        self.resize(900, 600)

        # Header
        hdr = QVBoxLayout()
        hdr.addWidget(QLabel(f"Welcome, {self.username}"))
        hdr.addWidget(QLabel(f"Primary role: {self.primary_role}"))
        hdr.addWidget(QLabel(f"All roles: [{', '.join(self.roles)}]"))

        # Table
        self.table = QTableWidget(0, 6, self)
        self.table.setHorizontalHeaderLabels(["ID", "Username", "Email", "First Name", "Last Name", "Groups"])
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(self.table.SelectionMode.SingleSelection)
        self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)

        # Buttons
        btns = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh")
        self.add_registrar=QPushButton("Promote to Registrar")
        self.remove_registrar=QPushButton("Retire from Registrar")
        self.promote_btn = QPushButton("Promote to org_officer")
        self.demote_btn  = QPushButton("Remove org_officer")
        btns.addWidget(self.refresh_btn)
        btns.addStretch()
        btns.addWidget(self.add_registrar)
        btns.addWidget(self.remove_registrar)
        btns.addWidget(self.promote_btn)
        btns.addWidget(self.demote_btn)

        # Layout
        root = QVBoxLayout(self)
        root.addLayout(hdr)
        root.addWidget(self.table)
        root.addLayout(btns)

        # Signals
        self.refresh_btn.clicked.connect(self.load_users)
        self.add_registrar.clicked.connect(lambda: self.change_Registrar(True))
        self.remove_registrar.clicked.connect(lambda: self.change_Registrar(False))
        self.promote_btn.clicked.connect(lambda: self.change_officer(True))
        self.demote_btn.clicked.connect(lambda: self.change_officer(False))

        # Initial data
        self.load_users()

    # -------- API helpers --------
    # def load_users(self):
    #     try:
    #         r = requests.get(self.users_url, headers=self.headers, timeout=10)
    #         if r.status_code != 200:
    #             return self._error(f"Load users failed: HTTP {r.status_code} {r.text[:200]}")
    #         data = r.json()
    #         users = data.get("results", data if isinstance(data, list) else [])
    #         self._populate_table(users)
    #     except requests.RequestException as e:
    #         self._error(f"Cannot reach backend: {e}")

    def load_users(self):
        try:
            r = requests.get(self.users_url, headers=self.headers, timeout=10)
            if r.status_code != 200:
                return self._error(f"Load users failed: HTTP {r.status_code} {r.text[:200]}")

            data = r.json()

            # Handle both paginated (dict) and non-paginated (list)
            if isinstance(data, dict):
                users = data.get("results", [])
            elif isinstance(data, list):
                users = data
            else:
                users = []

            self.populate_table(users)

        except requests.RequestException as e:
            self._error(f"Cannot reach backend: {e}")


    def populate_table(self, users):
        self.table.setRowCount(0)
        for u in users:
            # expected fields: id, username, email, first_name, last_name, groups (list of names)
            row = self.table.rowCount()
            self.table.insertRow(row)
            groups = u.get("groups", [])
            # allow backends that return groups as list of names OR list of objects
            if groups and isinstance(groups[0], dict):
                groups = [g.get("name", "") for g in groups]
            cells = [
                str(u.get("id", "")),
                u.get("username", ""),
                u.get("email", ""),
                u.get("first_name", ""),
                u.get("last_name", ""),
                ", ".join(groups),
            ]
            for col, val in enumerate(cells):
                item = QTableWidgetItem(val)
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, u.get("id"))  # store selected user id
                self.table.setItem(row, col, item)
        self.table.resizeColumnsToContents()

    def selected_user_id(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            self._info("Select a user first.")
            return None
        row = rows[0].row()
        item = self.table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole)
    def change_Registrar(self, promote):
        user_id = self.selected_user_id()
        if user_id is None:
            return
        url = (self.promote_registrar if promote else self.demote_registrar).format(user_id=user_id)
        try:
            r = requests.post(url, headers=self.headers, timeout=10)
            if r.status_code not in (200, 201):
                return self._error(f"Role change failed: HTTP {r.status_code} {r.text[:200]}")
            self._info(r.json().get("message", "Success"))
            self.load_users()
        except requests.RequestException as e:
            self._error(f"Cannot reach backend: {e}")
    # def removeRegistrar(self, promote):
    #     user_id = self.selected_user_id()
    #     if user_id is None:
    #         return
    #     url = (self.promote_registrar if promote else self.demote_registrar).format(user_id=user_id)
    #     try:
    #         r = requests.post(url, headers=self.headers, timeout=10)
    #         if r.status_code not in (200, 201):
    #             return self._error(f"Role change failed: HTTP {r.status_code} {r.text[:200]}")
    #         self._info(r.json().get("message", "Success"))
    #         self.load_users()
    #     except requests.RequestException as e:
    #         self._error(f"Cannot reach backend: {e}")

    def change_officer(self, promote: bool):
        user_id = self.selected_user_id()
        if user_id is None:
            return
        url = (self.promote_url_tmpl if promote else self.demote_url_tmpl).format(user_id=user_id)
        try:
            r = requests.post(url, headers=self.headers, timeout=10)
            if r.status_code not in (200, 201):
                return self._error(f"Role change failed: HTTP {r.status_code} {r.text[:200]}")
            self._info(r.json().get("message", "Success"))
            self.load_users()
        except requests.RequestException as e:
            self._error(f"Cannot reach backend: {e}")

    # -------- UI helpers --------
    def _info(self, msg):
        QMessageBox.information(self, "Info", str(msg))

    def _error(self, msg):
        QMessageBox.critical(self, "Error", str(msg))
