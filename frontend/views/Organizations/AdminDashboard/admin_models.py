from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any
from pathlib import Path
import json
from PyQt6.QtCore import Qt, QAbstractListModel, QModelIndex, pyqtSignal

@dataclass
class Service:
    category: str
    title: str
    blurb: str
    url: str
    email: str
    location: str = ""
    contact: str = ""
    image: str = ""
    services: list = field(default_factory=list)
    draft: bool = False

class ServiceStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.items: List[Service] = []
        self.load()

    def load(self):
        data = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {"items": []}
        self.items = []
        for it in data.get("items", []):
            self.items.append(Service(
                category=it.get("category", ""),
                title=it.get("title", ""),
                blurb=it.get("blurb", ""),
                url=it.get("url", ""),
                email=it.get("email", ""),
                location=it.get("location", ""),
                contact=it.get("contact", ""),
                image=it.get("image", ""),
                services=it.get("services", []),
                draft=it.get("draft", False),
            ))
        return self  # allow chaining

    def save(self) -> None:
        self.path.write_text(json.dumps({"items": [asdict(x) for x in self.items]}, indent=2), encoding="utf-8")

class AdminServiceModel(QAbstractListModel):
    CategoryRole = Qt.ItemDataRole.UserRole + 1
    TitleRole    = Qt.ItemDataRole.UserRole + 2
    BlurbRole    = Qt.ItemDataRole.UserRole + 3
    UrlRole      = Qt.ItemDataRole.UserRole + 4
    EmailRole    = Qt.ItemDataRole.UserRole + 5
    DraftRole    = Qt.ItemDataRole.UserRole + 6
    LocationRole = Qt.ItemDataRole.UserRole + 7
    ContactRole  = Qt.ItemDataRole.UserRole + 8

    changed = pyqtSignal()

    def __init__(self, store: ServiceStore) -> None:
        super().__init__()
        self.store = store

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.store.items)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        s = self.store.items[index.row()]
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole):
            return f"{s.title} — {s.category}"
        if role == self.CategoryRole: return s.category
        if role == self.TitleRole:    return s.title
        if role == self.BlurbRole:    return s.blurb
        if role == self.UrlRole:      return s.url
        if role == self.EmailRole:    return s.email or s.contact
        if role == self.DraftRole:    return s.draft
        if role == self.LocationRole: return s.location
        if role == self.ContactRole:  return s.contact
        return None

    def roleNames(self) -> Dict[int, bytes]:
        return {
            self.CategoryRole: b"category",
            self.TitleRole:    b"title",
            self.BlurbRole:    b"blurb",
            self.UrlRole:      b"url",
            self.EmailRole:    b"email",
            self.DraftRole:    b"draft",
            self.LocationRole: b"location",
            self.ContactRole:  b"contact",
        }

    def item(self, row: int) -> Service:
        return self.store.items[row]

    def add(self, s: Service) -> None:
        row = len(self.store.items)
        self.beginInsertRows(QModelIndex(), row, row)
        self.store.items.append(s)
        self.endInsertRows()
        self.store.save()
        self.changed.emit()

    def update(self, row: int, s: Service) -> None:
        if 0 <= row < len(self.store.items):
            self.store.items[row] = s
            idx = self.index(row, 0)
            self.dataChanged.emit(idx, idx, [])
            self.store.save()
            self.changed.emit()

    def remove(self, row: int) -> None:
        if 0 <= row < len(self.store.items):
            self.beginRemoveRows(QModelIndex(), row, row)
            self.store.items.pop(row)
            self.endRemoveRows()
            self.store.save()
            self.changed.emit()
