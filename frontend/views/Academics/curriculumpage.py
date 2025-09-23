from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont

class CurriculumPage(QWidget):  # e.g., class Browse(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        title = QLabel("Curriculum")  # e.g., "Browse"
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        content = QLabel("Custom hi poe content goes here.")
        layout.addWidget(title)
        layout.addWidget(content)
        layout.addStretch()
        self.setLayout(layout)