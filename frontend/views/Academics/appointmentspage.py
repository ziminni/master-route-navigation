from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont

class AppointmentsPage(QWidget):  # e.g., class Browse(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        title = QLabel("Appointment")  # e.g., "Browse"
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        content = QLabel("Custom [Page Name] content goes here.")
        layout.addWidget(title)
        layout.addWidget(content)
        layout.addStretch()
        self.setLayout(layout)