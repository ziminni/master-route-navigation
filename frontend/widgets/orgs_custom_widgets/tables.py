from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal, QAbstractTableModel
from PyQt6.QtGui import QPainter, QBrush, QPen, QColor, QFont
from PyQt6.QtWidgets import QStyledItemDelegate, QAbstractItemView


class ActionDelegate(QStyledItemDelegate):
    """Beautiful, permanent Edit/Kick buttons – no crash, perfect size & spacing"""
    edit_clicked = pyqtSignal(int)
    kick_clicked = pyqtSignal(int)

    def __init__(self, parent: QAbstractItemView = None):
        super().__init__(parent)
        self.parent_view = parent  # Save reference to table view
        self.button_width = 68
        self.button_height = 28
        self.spacing = 8
        self.hover_edit = False
        self.hover_kick = False

    def paint(self, painter: QPainter, option, index):
        if index.column() != index.model().columnCount(None) - 1:
            super().paint(painter, option, index)
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Cell rectangle with padding
        cell_rect = option.rect
        available_width = cell_rect.width() - 20
        total_buttons_width = 2 * self.button_width + self.spacing
        start_x = cell_rect.left() + (available_width - total_buttons_width) // 2
        y = cell_rect.center().y() - self.button_height // 2

        edit_rect = QRect(start_x, y, self.button_width, self.button_height)
        kick_rect = QRect(start_x + self.button_width + self.spacing, y, self.button_width, self.button_height)

        # === Edit Button (Green) ===
        painter.setBrush(QBrush(QColor("#084924") if not self.hover_edit else QColor("#0a6b30")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(edit_rect, 8, 8)
        painter.setPen(QPen(QColor("white")))
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.drawText(edit_rect, Qt.AlignmentFlag.AlignCenter, "Edit")

        # === Kick Button (Red) ===
        painter.setBrush(QBrush(QColor("#EB5757") if not self.hover_kick else QColor("#c44646")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(kick_rect, 8, 8)
        painter.setPen(QPen(QColor("white")))
        painter.drawText(kick_rect, Qt.AlignmentFlag.AlignCenter, "Kick")

        painter.restore()

    def editorEvent(self, event, model, option, index):
        if not index.isValid() or index.column() != index.model().columnCount(None) - 1:
            return False

        cell_rect = option.rect
        available_width = cell_rect.width() - 20
        total_buttons_width = 2 * self.button_width + self.spacing
        start_x = cell_rect.left() + (available_width - total_buttons_width) // 2
        y = cell_rect.center().y() - self.button_height // 2

        edit_rect = QRect(start_x, y, self.button_width, self.button_height)
        kick_rect = QRect(start_x + self.button_width + self.spacing, y, self.button_width, self.button_height)

        pos = event.position().toPoint() if hasattr(event, "position") else event.pos()

        # Hover handling
        old_edit = self.hover_edit
        old_kick = self.hover_kick
        self.hover_edit = edit_rect.contains(pos)
        self.hover_kick = kick_rect.contains(pos)

        if old_edit != self.hover_edit or old_kick != self.hover_kick:
            if self.parent_view:
                self.parent_view.update(index)

        # Click handling
        if event.type() == event.Type.MouseButtonRelease:
            if edit_rect.contains(pos):
                self.edit_clicked.emit(index.row())
                return True
            if kick_rect.contains(pos):
                self.kick_clicked.emit(index.row())
                return True

        return True  # We handled the event


class ApplicantActionDelegate(QStyledItemDelegate):
    """Accept/Reject buttons for applicant management"""
    accept_clicked = pyqtSignal(int)  # Emits row index
    reject_clicked = pyqtSignal(int)  # Emits row index

    def __init__(self, parent: QAbstractItemView = None):
        super().__init__(parent)
        self.parent_view = parent
        self.button_width = 68
        self.button_height = 28
        self.spacing = 8
        self.hover_accept = False
        self.hover_reject = False

    def paint(self, painter: QPainter, option, index):
        if index.column() != index.model().columnCount(None) - 1:
            super().paint(painter, option, index)
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Cell rectangle with padding
        cell_rect = option.rect
        available_width = cell_rect.width() - 20
        total_buttons_width = 2 * self.button_width + self.spacing
        start_x = cell_rect.left() + (available_width - total_buttons_width) // 2
        y = cell_rect.center().y() - self.button_height // 2

        accept_rect = QRect(start_x, y, self.button_width, self.button_height)
        reject_rect = QRect(start_x + self.button_width + self.spacing, y, self.button_width, self.button_height)

        # === Accept Button (Green) ===
        painter.setBrush(QBrush(QColor("#084924") if not self.hover_accept else QColor("#0a6b30")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(accept_rect, 8, 8)
        painter.setPen(QPen(QColor("white")))
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.drawText(accept_rect, Qt.AlignmentFlag.AlignCenter, "Accept")

        # === Reject Button (Red) ===
        painter.setBrush(QBrush(QColor("#EB5757") if not self.hover_reject else QColor("#c44646")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(reject_rect, 8, 8)
        painter.setPen(QPen(QColor("white")))
        painter.drawText(reject_rect, Qt.AlignmentFlag.AlignCenter, "Reject")

        painter.restore()

    def editorEvent(self, event, model, option, index):
        if not index.isValid() or index.column() != index.model().columnCount(None) - 1:
            return False

        cell_rect = option.rect
        available_width = cell_rect.width() - 20
        total_buttons_width = 2 * self.button_width + self.spacing
        start_x = cell_rect.left() + (available_width - total_buttons_width) // 2
        y = cell_rect.center().y() - self.button_height // 2

        accept_rect = QRect(start_x, y, self.button_width, self.button_height)
        reject_rect = QRect(start_x + self.button_width + self.spacing, y, self.button_width, self.button_height)

        pos = event.position().toPoint() if hasattr(event, "position") else event.pos()

        # Hover handling
        old_accept = self.hover_accept
        old_reject = self.hover_reject
        self.hover_accept = accept_rect.contains(pos)
        self.hover_reject = reject_rect.contains(pos)

        if old_accept != self.hover_accept or old_reject != self.hover_reject:
            if self.parent_view:
                self.parent_view.update(index)

        # Click handling
        if event.type() == event.Type.MouseButtonRelease:
            if accept_rect.contains(pos):
                self.accept_clicked.emit(index.row())
                return True
            if reject_rect.contains(pos):
                self.reject_clicked.emit(index.row())
                return True

        return True


# Keep your other models unchanged
class BaseTableModel(QAbstractTableModel):
    def __init__(self, data, headers):
        super().__init__()
        self._data = data
        self._headers = headers

    def rowCount(self, parent=None): return len(self._data)
    def columnCount(self, parent=None): return len(self._headers)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and index.column() == 0:
            return str(index.row() + 1)
        return None
        
    def update_data(self, new_data):
        """Method to update the model's underlying data."""
        self.beginResetModel()
        self._data = new_data
        self.endResetModel()


class ViewMembers(BaseTableModel):
    def __init__(self, data, is_managing: bool = False):
        self.is_managing = is_managing
        headers = ["No.", "Name", "Position", "Status", "Join Date"] + (["Actions"] if is_managing else [])
        super().__init__(data, headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole: return None
        col = index.column()
        if col == 0: return super().data(index, role)
        data_col = col - 1
        if col < len(self._headers) - 1 or not self.is_managing:
            row = self._data[index.row()]
            return row[data_col] if data_col < len(row) else ""
        return None

    def flags(self, index):
        flags = super().flags(index)
        if self.is_managing and index.column() == len(self._headers) - 1:
            flags |= Qt.ItemFlag.ItemIsEnabled
        else:
            flags &= ~Qt.ItemFlag.ItemIsEditable
        return flags


class ViewApplicants(BaseTableModel):
    def __init__(self, data):
        headers = ["No.", "Name", "Email", "Program", "Year Level", "Actions"]
        super().__init__(data, headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole: 
            return None
        
        col = index.column()
        row_data = self._data[index.row()]
        
        if col == 0:  # No.
            return super().data(index, role)
        elif col == 1:  # Name
            return row_data.get("student_name", "")
        elif col == 2:  # Email
            return row_data.get("student_email", "")
        elif col == 3:  # Program
            return row_data.get("program", "")
        elif col == 4:  # Year Level
            return row_data.get("year_level", "")
        # Actions column handled by delegate
        return None

    def flags(self, index):
        return super().flags(index) | Qt.ItemFlag.ItemIsEnabled