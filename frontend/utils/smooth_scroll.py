from PyQt6.QtWidgets import QScrollArea
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve


class SmoothScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._anim = None
        self.setWidgetResizable(True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta == 0:
            return
        sb = self.verticalScrollBar()
        start = sb.value()
        scroll_factor = 1.5
        end = start - int(delta * scroll_factor)
        end = max(sb.minimum(), min(sb.maximum(), end))
        if self._anim and self._anim.state() == QPropertyAnimation.State.Running:
            self._anim.stop()
        self._anim = QPropertyAnimation(sb, b"value")
        self._anim.setStartValue(start)
        self._anim.setEndValue(end)
        self._anim.setDuration(250)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()
        event.accept()
