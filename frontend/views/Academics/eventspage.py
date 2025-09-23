from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont

class EventsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        title = QLabel("This is Events page")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        content = QLabel("Custom content: View Overview details, lists, etc.")
        layout.addWidget(title)
        layout.addWidget(content)
        layout.addStretch()
        self.setLayout(layout)