from PyQt6.QtCore import QAbstractTableModel, Qt
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QStyledItemDelegate, QHBoxLayout, QPushButton

class ActionDelegate(QStyledItemDelegate):
    edit_clicked = QtCore.pyqtSignal(int)
    kick_clicked = QtCore.pyqtSignal(int)

    def createEditor(self, parent, option, index):
        editor = QtWidgets.QWidget(parent)
        layout = QHBoxLayout(editor)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(8)

        edit_btn = QPushButton("Edit", editor)
        edit_btn.setStyleSheet("background-color: #0c5; color: white; padding: 3px; border-radius: 3px;")
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(index.row()))
        layout.addWidget(edit_btn)

        kick_btn = QPushButton("Kick", editor)
        kick_btn.setStyleSheet("background-color: #e55; color: white; padding: 3px; border-radius: 3px;")
        kick_btn.clicked.connect(lambda: self.kick_clicked.emit(index.row()))
        layout.addWidget(kick_btn)

        layout.addStretch()  # pushes buttons to the left
        return editor

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class ViewMembers(QAbstractTableModel):
    def __init__(self, data, is_managing: bool = False):
        super().__init__()
        self._data = data
        self.is_managing = is_managing
        self._headers = ["No.", "Name", "Position", "Status", "Join Date"] + (["Actions"] if is_managing else [])

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers)
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            col = index.column()
            if col == 0:
                return str(index.row() + 1)
            elif col < len(self._headers) - 1 or not self.is_managing:
                return self._data[index.row()][col - 1]
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._headers[section]
        return None
    
    def flags(self, index, parent=None):
        flags = super().flags(index)
        if self.is_managing and index.column() == len(self._headers) - 1:
            flags |= Qt.ItemFlag.ItemIsEditable
        return flags
    
class ViewApplicants(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data
        self._headers = ["No.", "Name", "Position", "Actions"]

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            col = index.column()
            if col == 0:
                return str(index.row() + 1)
            elif col < len(self._headers) - 1:
                return self._data[index.row()][col - 1]
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return None

    def flags(self, index):
        flags = super().flags(index)
        if index.column() == len(self._headers) - 1: 
            flags |= Qt.ItemFlag.ItemIsEditable
        return flags