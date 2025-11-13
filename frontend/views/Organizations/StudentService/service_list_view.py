from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QListView

class ServiceListView(QListView):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWrapping(True)
        self.setFlow(QListView.Flow.LeftToRight)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setViewMode(QListView.ViewMode.IconMode)
        self.setSpacing(16)
        self.setMovement(QListView.Movement.Static)
        self.setSelectionRectVisible(False)
        # match CardDelegate.card_height
        self.setGridSize(QSize(380, 260))
