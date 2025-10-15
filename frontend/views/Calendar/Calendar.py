from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont

class CalendarPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        title = QLabel("Classes")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        content = QLabel("Custom content: View class details, lists, etc.")
        layout.addWidget(title)
        layout.addWidget(content)
        layout.addStretch()
        self.setLayout(layout)