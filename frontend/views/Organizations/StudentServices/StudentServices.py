from __future__ import annotations
from pathlib import Path
import json

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QPixmap
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton,
    QListView, QStackedWidget, QFrame, QGridLayout, QSizePolicy, QSpacerItem
)

# uses your existing files in the same package
from .service_list_view import ServiceListView
from .card_delegate import CardDelegate
from .models import Service, ServiceModel


class StudentServices(QWidget):
    """Student Services: list page + organization detail page."""
    def __init__(self, **kwargs):
        super().__init__()

        self._stack = QStackedWidget(self)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.addWidget(self._stack)

        # -------------------- LIST PAGE --------------------
        self._page_list = QWidget()
        self._stack.addWidget(self._page_list)
        L = QVBoxLayout(self._page_list)
        L.setSpacing(10)

        # Title
        title = QLabel("STUDENT SERVICES")
        title.setStyleSheet("font-size:22px; font-weight:800; color:#144f2e;")
        subtitle = QLabel("Student Organizations and Offices")
        subtitle.setStyleSheet("color:#6d7a73;")
        L.addWidget(title)
        L.addWidget(subtitle)

        # Filters row
        filt = QHBoxLayout()
        self.search = QLineEdit(placeholderText="Search here…")
        self.search.setClearButtonEnabled(True)
        self.category = QComboBox()
        self.category.addItem("All")
        filt.addWidget(self.search, 1)
        filt.addSpacing(8)
        filt.addWidget(self.category)
        L.addLayout(filt)

        # Count + “Available services”
        meta = QHBoxLayout()
        self.count = QLabel("0 services found")
        self.count.setStyleSheet("color:#6d7a73;")
        meta.addWidget(self.count, 1)
        right = QLabel("Available services")
        right.setStyleSheet("color:#6d7a73;")
        meta.addWidget(right, 0)
        L.addLayout(meta)

        # Card list
        self.view = ServiceListView()
        self.view.setSelectionMode(QListView.SelectionMode.NoSelection)
        L.addWidget(self.view, 1)

        # model + delegate
        self._raw_items = self._load_items()
        dataclass_items = [Service(
            category=it.get("category",""),
            title=it.get("title",""),
            blurb=it.get("blurb",""),
            url=it.get("url",""),
            email=it.get("email",""),
        ) for it in self._raw_items]

        self.model = ServiceModel(dataclass_items)
        self.view.setModel(self.model)
        self.delegate = CardDelegate(self.view)
        self.view.setItemDelegate(self.delegate)

        # fill categories from data
        cats = ["All"] + sorted({(it.get("category") or "Uncategorized") for it in self._raw_items})
        self.category.clear()
        self.category.addItems(cats)

        # wiring
        self.search.textChanged.connect(self._apply_filter)
        self.category.currentTextChanged.connect(self._apply_filter)
        self.delegate.accessClicked.connect(self._open_detail)

        self._apply_filter()

        # -------------------- DETAIL PAGE --------------------
        self._page_detail = QWidget()
        self._stack.addWidget(self._page_detail)
        self._detail_ui = _OrgDetail(self._page_detail, on_back=lambda: self._stack.setCurrentWidget(self._page_list))

        # start on list
        self._stack.setCurrentWidget(self._page_list)

    # ---------- data ----------
    def _data_path(self) -> Path:
        return Path(__file__).resolve().parent / "services.json"

    def _load_items(self) -> list[dict]:
        p = self._data_path()
        if not p.exists():
            p.write_text(json.dumps({"items":[]}, indent=2), encoding="utf-8")
        try:
            return json.loads(p.read_text(encoding="utf-8")).get("items", [])
        except Exception:
            return []

    # ---------- behavior ----------
    def _apply_filter(self, *_):
        q = (self.search.text() or "").strip().lower()
        cat = self.category.currentText()

        keep_rows = []
        for row, it in enumerate(self._raw_items):
            if cat != "All" and (it.get("category") or "") != cat:
                continue
            txt = f"{it.get('title','')} {it.get('blurb','')}".lower()
            if q and q not in txt:
                continue
            keep_rows.append(row)

        # hide by moving unmatched rows to the end and setting a dynamic “height 0” via a proxy
        # simpler: rebuild the model with kept rows
        items = [Service(
            category=self._raw_items[i].get("category",""),
            title=self._raw_items[i].get("title",""),
            blurb=self._raw_items[i].get("blurb",""),
            url=self._raw_items[i].get("url",""),
            email=self._raw_items[i].get("email",""),
        ) for i in keep_rows]
        self.model.beginResetModel()
        self.model._items = items  # type: ignore[attr-defined]
        self.model.endResetModel()

        self.count.setText(f"{len(keep_rows)} services found")

    def _open_detail(self, proxy_index):
        # proxy_index is already from our model (no proxy in this version)
        row = proxy_index.row()
        if row < 0 or row >= self.model.rowCount():
            return
        # reconstruct the dict from the visible row
        s = self.model._items[row]  # type: ignore[attr-defined]
        # find the original dict with more fields (image, services, …)
        match = next((it for it in self._raw_items
                    if (it.get("title",""), it.get("category","")) == (s.title, s.category)), None)
        data = match or {
            "category": s.category, "title": s.title, "blurb": s.blurb,
            "url": s.url, "email": s.email, "services": []
        }
        self._detail_ui.set_data(data)
        self._stack.setCurrentWidget(self._page_detail)


# ---------- detail view ----------
class _OrgDetail:
    def __init__(self, host: QWidget, on_back):
        wrap = QVBoxLayout(host)
        wrap.setContentsMargins(18, 18, 18, 18)
        wrap.setSpacing(10)

        # title row
        hdr = QHBoxLayout()
        back = QPushButton("←  Back")
        back.setCursor(Qt.CursorShape.PointingHandCursor)
        back.clicked.connect(on_back)
        back.setStyleSheet("QPushButton{padding:6px 10px;border:1px solid #cfd6d2;border-radius:8px;} QPushButton:hover{background:#f0f3f1;}")
        hdr.addWidget(back, 0)
        hdr.addItem(QSpacerItem(12, 12, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        wrap.addLayout(hdr)

        # banner
        banner = QHBoxLayout()
        self.logo = QLabel()
        self.logo.setFixedSize(96, 96)
        self.logo.setStyleSheet("background:#eef3ef;border:1px solid #d9e2dd;border-radius:8px;")
        self.logo.setScaledContents(True)
        banner.addWidget(self.logo, 0)

        info = QVBoxLayout()
        self.title = QLabel()
        self.title.setStyleSheet("font-size:18px; font-weight:800; color:#144f2e;")
        info.addWidget(self.title)

        meta = QHBoxLayout()
        self.chip = QLabel()
        self.chip.setStyleSheet("QLabel{background:#e7f1ea;color:#1c6d42;border-radius:10px;padding:2px 8px;}")
        meta.addWidget(self.chip, 0)

        self.email = QLabel()
        self.email.setTextFormat(Qt.TextFormat.RichText)
        self.email.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.email.setOpenExternalLinks(True)
        meta.addWidget(self.email, 0)

        self.url = QLabel()
        self.url.setTextFormat(Qt.TextFormat.RichText)
        self.url.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.url.setOpenExternalLinks(True)
        meta.addWidget(self.url, 0)

        meta.addStretch(1)
        info.addLayout(meta)

        self.blurb = QLabel()
        self.blurb.setWordWrap(True)
        self.blurb.setStyleSheet("color:#38443e;")
        info.addWidget(self.blurb)
        banner.addLayout(info, 1)
        wrap.addLayout(banner)

        # services grid
        self.grid_host = QFrame()
        self.grid_host.setStyleSheet("QFrame{border:0px;}")
        wrap.addWidget(self.grid_host, 1)
        self.grid = QGridLayout(self.grid_host)
        self.grid.setHorizontalSpacing(18)
        self.grid.setVerticalSpacing(18)
        self.grid.setContentsMargins(0, 10, 0, 0)

    def set_data(self, d: dict):
    # logo
        self._set_logo(d.get("image"))

    # header
        self.title.setText(d.get("title", ""))
        self.chip.setText(d.get("category", ""))
        em = d.get("email", "")
        self.email.setText(f'&nbsp;&nbsp;✉&nbsp;<a href="mailto:{em}">{em}</a>' if em else "")

    # normalize URL so clicks work even without http/https
        url = (d.get("url") or "").strip()
        if url and not url.startswith(("http://", "https://")):
            url = "http://" + url
        self.url.setText(f'&nbsp;&nbsp;🔗&nbsp;<a href="{url}">{url}</a>' if url else "")

        self.blurb.setText(d.get("blurb", ""))

    # tiles
        for i in reversed(range(self.grid.count())):
            w = self.grid.itemAt(i).widget()
            if w:
                w.deleteLater()

        services = d.get("services") or []
        if not services:
            services = [{"name": f"Service {i}"} for i in range(1, 7)]

        cols = 3
        for i, s in enumerate(services):
            r, c = divmod(i, cols)
            self.grid.addWidget(self._tile(s.get("name", "Service")), r, c)


    def _set_logo(self, image_path: str | None):
        # Try absolute, module-relative, and project-relative (frontend/...) paths
        if not image_path:
            self.logo.setPixmap(QPixmap())
            return

        img = Path(image_path)
        module_dir = Path(__file__).resolve().parent           # .../views/Organization/StudentServices
        project_frontend = Path(__file__).resolve().parents[3] # .../frontend

        candidates = [
            img,                              # absolute or cwd-relative
            module_dir / img,                 # module-relative
            project_frontend / img,           # project-relative, e.g. assets/uploads/_canon/...
        ]

        for p in candidates:
            if p.is_file():
                self.logo.setPixmap(QPixmap(str(p)))
                return

        self.logo.setPixmap(QPixmap())

    def _tile(self, text: str) -> QWidget:
        w = QFrame()
        w.setMinimumSize(220, 140)
        w.setStyleSheet(
            "QFrame{background:#0f4d2a;border:1px solid #0c3e22;border-radius:12px;} "
            "QFrame:hover{background:#165f35;} QLabel{color:white;font-size:14px;font-weight:600;}"
        )
        v = QVBoxLayout(w)
        v.addStretch(1)
        lab = QLabel(text)
        lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(lab)
        v.addStretch(1)
        return w
