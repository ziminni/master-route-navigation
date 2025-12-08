from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import Qt
from functools import partial
import datetime


class PendingOfficerDialog(QtWidgets.QDialog):
    def __init__(self, org_data, dean_instance, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Pending Officer Changes – {org_data.get('name', 'Organization')}")
        self.setMinimumSize(1100, 700)
        self.org_data = org_data
        self.dean = dean_instance

        # Main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)

        # Title
        title = QtWidgets.QLabel("<h2 style='color:#084924;'>Pending Officer Changes</h2>")
        subtitle = QtWidgets.QLabel(f"<b style='font-size:18px; color:#084924;'>{org_data.get('name')}</b>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        # === STACKED WIDGET TO SWITCH BETWEEN TABLE AND EMPTY STATE ===
        self.stacked_widget = QtWidgets.QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # Page 1: Table
        self.table = QtWidgets.QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.setStyleSheet("""
            QTableView {
                background: white;
                gridline-color: #ddd;
                font-size: 14px;
                border: none;
            }
            QHeaderView::section {
                background: #084924;
                color: white;
                padding: 15px;
                font-weight: bold;
                border: none;
            }
        """)
        self.stacked_widget.addWidget(self.table)

        # Page 2: Empty state
        self.empty_label = QtWidgets.QLabel("No pending officer changes pending approval.")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("font-size: 20px; color: #999; padding: 100px;")
        self.stacked_widget.addWidget(self.empty_label)

        # Initial load
        self.load_data()

    def load_data(self):
        # Always refresh from current org (in case changed externally)
        if hasattr(self.dean, 'current_org'):
            self.org_data = self.dean.current_org
        pending = self.org_data.get("pending_officers", [])

        if not pending:
            self.stacked_widget.setCurrentWidget(self.empty_label)
            return

        # Switch to table
        self.stacked_widget.setCurrentWidget(self.table)

        # Build model
        model = QtGui.QStandardItemModel()
        model.setHorizontalHeaderLabels(["Officer", "From to To", "Proposed By", "Date", "Actions"])

        for item in pending:
            name = QtGui.QStandardItem(item.get("name", "Unknown"))
            old = item.get("old_position", "Member")
            new = item.get("position", "Unknown")
            change = QtGui.QStandardItem(f"{old} to {new}")
            by = QtGui.QStandardItem(item.get("proposed_by", "Unknown"))

            try:
                dt = datetime.datetime.fromisoformat(item["proposed_at"])
                date = dt.strftime("%b %d, %Y • %I:%M %p")
            except:
                date = "Unknown"
            date_item = QtGui.QStandardItem(date)
            action_item = QtGui.QStandardItem("")

            model.appendRow([name, change, by, date_item, action_item])

        self.table.setModel(model)

        # Add buttons
        for row, item in enumerate(pending):
            widget = QtWidgets.QWidget()
            hbox = QtWidgets.QHBoxLayout(widget)
            hbox.setContentsMargins(20, 10, 20, 10)
            hbox.setSpacing(15)

            confirm = QtWidgets.QPushButton("Confirm")
            confirm.setFixedSize(110, 45)
            confirm.setStyleSheet("background:#084924;color:white;border-radius:12px;font-weight:bold;")

            decline = QtWidgets.QPushButton("Decline")
            decline.setFixedSize(110, 45)
            decline.setStyleSheet("background:#EB5757;color:white;border-radius:12px;font-weight:bold;")

            confirm.clicked.connect(partial(self.dean._approve_pending_officer, item, self))
            decline.clicked.connect(partial(self.dean._reject_pending_officer, item, self))

            hbox.addWidget(confirm)
            hbox.addWidget(decline)
            hbox.addStretch()

            self.table.setIndexWidget(model.index(row, 4), widget)
            self.table.setRowHeight(row, 80)

        # Resize columns
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 300)