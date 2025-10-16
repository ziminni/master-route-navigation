from dataclasses import dataclass
from typing import List, Dict, Any
from PyQt6.QtCore import Qt, QAbstractListModel, QModelIndex


@dataclass
class Service:
    category: str
    title: str
    blurb: str
    url: str
    email: str


class ServiceModel(QAbstractListModel):
    CategoryRole = Qt.ItemDataRole.UserRole + 1
    TitleRole    = Qt.ItemDataRole.UserRole + 2
    BlurbRole    = Qt.ItemDataRole.UserRole + 3
    UrlRole      = Qt.ItemDataRole.UserRole + 4
    EmailRole    = Qt.ItemDataRole.UserRole + 5

    def __init__(self, items: List[Service] | None = None, parent=None) -> None:
        super().__init__(parent)
        self._items: List[Service] = items or []

    # Required
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._items)

    # Data for both display roles and custom roles
    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        if index.row() < 0 or index.row() >= len(self._items):
            return None

        s = self._items[index.row()]

        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole):
            return f"{s.title} — {s.category}"
        if role == self.CategoryRole:
            return s.category
        if role == self.TitleRole:
            return s.title
        if role == self.BlurbRole:
            return s.blurb
        if role == self.UrlRole:
            return s.url
        if role == self.EmailRole:
            return s.email
        return None

    def roleNames(self) -> Dict[int, bytes]:
        return {
            self.CategoryRole: b"category",
            self.TitleRole:    b"title",
            self.BlurbRole:    b"blurb",
            self.UrlRole:      b"url",
            self.EmailRole:    b"email",
        }
