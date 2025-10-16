from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout

class OrganizationMain(QWidget):
    def __init__(self, navigate=None, **kwargs):
        super().__init__()
        self._navigate = navigate
        self._main_id = 40
        root = QVBoxLayout(self)
        root.addWidget(QLabel("Organization"))
        row = QHBoxLayout(); root.addLayout(row)
        btn_student = QPushButton("Student Services")
        btn_admin   = QPushButton("Admin Dashboard")
        row.addWidget(btn_student); row.addWidget(btn_admin)
        btn_student.clicked.connect(lambda: self._go(401))
        btn_admin.clicked.connect(lambda: self._go(402))
    def _go(self, child_id: int):
        if callable(self._navigate):
            self._navigate(page_id=child_id, is_modular=True, parent_main_id=self._main_id)
