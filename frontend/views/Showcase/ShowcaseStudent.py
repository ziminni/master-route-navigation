# views/Showcase/ShowcaseStudent.py
from __future__ import annotations
import os, warnings
from pathlib import Path
from typing import List, Dict, Tuple

from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter, QFont, QCursor
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QLineEdit,
    QScrollArea, QFrame, QSizePolicy, QSpacerItem, QGraphicsDropShadowEffect,
    QStackedWidget, QGridLayout
)

# DB helper
try:
    from .db.ShowcaseDBHelper import list_showcase_cards
    from .db.ShowcaseDBInitialize import ensure_bootstrap
except Exception:
    from db.ShowcaseDBHelper import list_showcase_cards
    from db.ShowcaseDBInitialize import ensure_bootstrap

# Submit page is imported lazily inside _on_achievements

warnings.filterwarnings("ignore", message="sipPyTypeDict", category=DeprecationWarning)

# Preview dialog (reuse)
try:
    from .ShowcasePreview import ShowcasePreviewDialog
except Exception:
    from ShowcasePreview import ShowcasePreviewDialog

# ---------- Theme ----------
GREEN   = "#146c43"
TEXT    = "#1f2937"
MUTED   = "#6b7280"
BG      = "#f3f4f6"
CARD_BG = "#ffffff"
BORDER  = "#e5e7eb"
SIDECARD_VIEWPORT_H = 240

# ---------- Asset discovery ----------
def _find_dir(name: str) -> Path:
    here = Path(__file__).resolve()
    for up in range(0, 7):
        base = here.parents[up] if up else here.parent
        cand = base / "assets" / name
        if cand.is_dir():
            return cand
    cand = Path(os.getcwd()) / "assets" / name
    cand.mkdir(parents=True, exist_ok=True)
    return cand

ICON_DIR = _find_dir("icons")
IMG_DIR  = _find_dir("images")

def _icon(fname: str) -> QIcon:
    p = ICON_DIR / fname
    return QIcon(str(p)) if p.exists() else QIcon()

def _placeholder_pixmap(size: QSize, label: str = "image") -> QPixmap:
    pm = QPixmap(size)
    pm.fill(QColor("#d1d5db"))
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(QColor("#9ca3af"))
    p.setBrush(QColor("#e5e7eb"))
    p.drawRoundedRect(0, 0, size.width(), size.height(), 12, 12)
    f = QFont()
    f.setPointSize(14)
    f.setBold(True)
    p.setFont(f)
    p.setPen(QColor("#6b7280"))
    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, label.upper())
    p.end()
    return pm

# simple in-memory cache: (path, w, h) -> scaled pixmap
_IMAGE_CACHE: dict[Tuple[str, int, int], QPixmap] = {}

def _load_image(fname: str | None, w: int, h: int) -> QPixmap:
    if fname:
        p = (IMG_DIR / fname) if not Path(fname).exists() else Path(fname)
        if p.exists():
            key = (str(p), w, h)
            pm = _IMAGE_CACHE.get(key)
            if pm is not None and not pm.isNull():
                return pm
            base = QPixmap(str(p))
            if not base.isNull():
                pm = base.scaled(
                    w, h,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,  # zoom-to-fill
                    Qt.TransformationMode.FastTransformation,
                )
                _IMAGE_CACHE[key] = pm
                return pm
    return _placeholder_pixmap(QSize(w, h), "image")

def _add_shadow(w: QWidget, alpha: int = 24, blur: int = 18):
    eff = QGraphicsDropShadowEffect(w)
    c = QColor("#000")
    c.setAlpha(alpha)
    eff.setColor(c)
    eff.setBlurRadius(blur)
    eff.setOffset(0, 3)
    w.setGraphicsEffect(eff)

# ---------- Card widgets (no 3-dots) ----------
class LargeCard(QFrame):
    clicked = pyqtSignal()

    THUMB_ONE_COL = 260   # thumb height when card is wide (1 column)
    THUMB_TWO_COL = 210   # thumb height when card is narrow (2 columns)

    def __init__(self, payload: Dict, parent: QWidget | None = None):
        super().__init__(parent)
        self.payload = payload
        self._src = payload.get("image")
        self._thumb_h = self.THUMB_ONE_COL

        self.setObjectName("LargeCard")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self.setStyleSheet(f"""
            QFrame#LargeCard {{
                background:{CARD_BG};
                border:1px solid {BORDER};
                border-radius:12px;
            }}
            QLabel[role="title"] {{
                color:{GREEN};
                font-size:18px;
                font-weight:700;
            }}
            QLabel[role="blurb"] {{
                color:{MUTED};
                font-size:13px;
            }}
            QLabel[role="meta"] {{
                color:{MUTED};
                font-size:12px;
            }}
            QLabel[role="by"] {{
                color:{MUTED};
                font-size:12px;
            }}
            QLabel[role="chip"] {{
                background:#ecfdf5;
                color:{GREEN};
                border:1px solid #c7f0df;
                border-radius:10px;
                padding:2px 8px;
                font-size:11px;
            }}
            QLabel[role="pill-cat"] {{
                background:#eff6ff;
                color:{GREEN};
                padding:4px 10px;
                border-radius:8px;
                font-size:11px;
            }}
            QLabel[role="pill-ctx"] {{
                background:#f5f3ff;
                color:{GREEN};
                padding:4px 10px;
                border-radius:8px;
                font-size:11px;
            }}
            QLabel[role="pill-img"] {{
                background:#ecfdf5;
                color:{GREEN};
                padding:4px 10px;
                border-radius:8px;
                font-size:11px;
            }}
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # thumbnail
        self.img = QLabel(self)
        self.img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.img.setScaledContents(False)  # keep aspect, let pixmap be cropped
        self.img.setMinimumHeight(self._thumb_h)
        self.img.setMaximumHeight(self._thumb_h)
        outer.addWidget(self.img)

        # body
        body = QFrame(self)
        body.setObjectName("CardBody")
        body.setStyleSheet(
            "QFrame#CardBody { background:white; "
            "border-bottom-left-radius:12px; border-bottom-right-radius:12px; }"
        )
        v2 = QVBoxLayout(body)
        v2.setContentsMargins(16, 12, 16, 12)
        v2.setSpacing(6)

        # title + status chip
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        self.title_lbl = QLabel(payload.get("title", ""))
        self.title_lbl.setProperty("role", "title")
        self.title_lbl.setWordWrap(True)
        title_row.addWidget(self.title_lbl, 1)

        self.status_chip = QLabel(payload.get("status") or "")
        self.status_chip.setProperty("role", "chip")
        self.status_chip.setVisible(bool(self.status_chip.text()))
        title_row.addWidget(self.status_chip, 0, Qt.AlignmentFlag.AlignRight)
        v2.addLayout(title_row)

        # meta row
        meta_row = QHBoxLayout()
        meta_row.setSpacing(8)
        by = payload.get("author_display")
        self.by_lbl = QLabel(f"by {by}" if by else "")
        self.by_lbl.setProperty("role", "by")
        self.by_lbl.setVisible(bool(by))
        if by:
            meta_row.addWidget(self.by_lbl, 0)

        posted = payload.get("posted_ago") or ""
        if posted:
            if by:
                dot = QLabel("•")
                dot.setProperty("role", "meta")
                meta_row.addWidget(dot, 0)
            self.posted_lbl = QLabel(posted)
            self.posted_lbl.setProperty("role", "meta")
            meta_row.addWidget(self.posted_lbl, 0)

        meta_row.addStretch(1)
        v2.addLayout(meta_row)

        # blurb
        self.blurb_lbl = QLabel(payload.get("blurb", ""))
        self.blurb_lbl.setWordWrap(True)
        self.blurb_lbl.setProperty("role", "blurb")
        self.blurb_lbl.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum
        )
        v2.addWidget(self.blurb_lbl)

        # chips row
        chips_row = QHBoxLayout()
        chips_row.setSpacing(6)

        cat = payload.get("category")
        ctx = payload.get("context")
        nimg = payload.get("images_count", 0)

        if cat:
            cat_lbl = QLabel(str(cat))
            cat_lbl.setProperty("role", "pill-cat")
            chips_row.addWidget(cat_lbl, 0)

        if ctx:
            ctx_lbl = QLabel(str(ctx))
            ctx_lbl.setProperty("role", "pill-ctx")
            chips_row.addWidget(ctx_lbl, 0)

        img_lbl = QLabel(f"{nimg} image{'s' if nimg != 1 else ''}")
        img_lbl.setProperty("role", "pill-img")
        chips_row.addWidget(img_lbl, 0)

        chips_row.addStretch(1)
        v2.addLayout(chips_row)

        outer.addWidget(body)
        _add_shadow(self, alpha=30, blur=22)

        self.adjustSize()
        self.setFixedHeight(self.sizeHint().height())

        self._update_thumb_height()
        self._update_pixmap()

    def _update_thumb_height(self):
        w = max(1, self.width())
        target = self.THUMB_TWO_COL if w < 620 else self.THUMB_ONE_COL
        if target != self._thumb_h:
            self._thumb_h = target
            self.img.setMinimumHeight(target)
            self.img.setMaximumHeight(target)

    def _update_pixmap(self):
        w = max(1, self.img.width() or self.width() or 600)
        h = max(1, self.img.height() or self._thumb_h)
        self.img.setPixmap(_load_image(self._src, w, h))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._update_thumb_height()
        self._update_pixmap()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(e)


class SmallCard(QFrame):
    clicked = pyqtSignal()

    SIDE_THUMB_HEIGHT = 180  # more room for sidebar thumbnails

    def __init__(self, payload: Dict, parent: QWidget | None = None):
        super().__init__(parent)
        self.payload = payload
        self._src = payload.get("image")
        self.setObjectName("SmallCard")
        self.setStyleSheet(f"""
            QFrame#SmallCard {{
                background:{CARD_BG};
                border:1px solid {BORDER};
                border-radius:12px;
            }}
            QLabel[role="title"] {{
                color:{GREEN};
                font-size:15px;
                font-weight:600;
            }}
            QLabel[role="blurb"] {{
                color:{MUTED};
                font-size:12px;
            }}
            QLabel[role="meta"] {{
                color:{MUTED};
                font-size:11px;
            }}
        """)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        self.img = QLabel(self)
        self.img.setFixedHeight(self.SIDE_THUMB_HEIGHT)
        self.img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.img.setScaledContents(False)
        v.addWidget(self.img)

        body = QFrame(self)
        body.setObjectName("CardBody")
        body.setStyleSheet(
            "QFrame#CardBody{background:white; "
            "border-bottom-left-radius:12px; border-bottom-right-radius:12px;}"
        )
        hb = QVBoxLayout(body)
        hb.setContentsMargins(14, 10, 10, 10)
        hb.setSpacing(6)

        self.title_lbl = QLabel(payload.get("title", ""))
        self.title_lbl.setProperty("role", "title")
        self.blurb_lbl = QLabel(payload.get("blurb", ""))
        self.blurb_lbl.setWordWrap(True)
        self.blurb_lbl.setProperty("role", "blurb")
        self.meta_lbl = QLabel(payload.get("posted_ago", ""))
        self.meta_lbl.setProperty("role", "meta")

        hb.addWidget(self.title_lbl)
        hb.addWidget(self.blurb_lbl)
        hb.addWidget(self.meta_lbl)
        v.addWidget(body)

        self.update_image()
        _add_shadow(self, alpha=20, blur=14)

    def update_image(self):
        w = max(1, self.img.width() or self.width() or 1)
        h = max(1, self.img.height() or self.SIDE_THUMB_HEIGHT)
        self.img.setPixmap(_load_image(self._src, w, h))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.update_image()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(e)

# ---------- Sidebar scroller ----------
class SidebarScroller(QFrame):
    def __init__(
        self,
        title: str,
        parent: QWidget | None = None,
        on_open=None,
        fixed_height: int | None = SIDECARD_VIEWPORT_H,
    ):
        super().__init__(parent)
        self.on_open = on_open
        self.items_all: List[Dict] = []
        self.setObjectName("SidebarScroller")
        self.setStyleSheet(f"""
            QFrame#SidebarScroller {{
                background:transparent;
                border:1px solid {GREEN};
                border-radius:8px;
            }}
            QLabel[role="section"] {{
                color:{MUTED};
                font-size:12px;
                padding:10px 10px 0 10px;
            }}
        """)
        v = QVBoxLayout(self)
        v.setContentsMargins(10, 6, 10, 10)
        v.setSpacing(10)
        cap = QLabel(f"{title}:")
        cap.setProperty("role", "section")
        v.addWidget(cap)

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        if fixed_height is not None:
            self.scroll.setFixedHeight(fixed_height)

        v.addWidget(self.scroll)

        self.container = QWidget()
        self.scroll.setWidget(self.container)
        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(10)
        self.list_layout.addStretch(1)

    def set_items(self, items: List[Dict], all_items: List[Dict] | None = None):
        self.items_all = all_items or items
        while self.list_layout.count() > 1:
            it = self.list_layout.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        for it in items[:3]:
            card = SmallCard(it)
            idx = self.items_all.index(it) if it in self.items_all else 0
            if callable(self.on_open):
                card.clicked.connect(
                    lambda i=idx, arr=self.items_all: self.on_open(arr, i)
                )
            self.list_layout.insertWidget(self.list_layout.count() - 1, card)

# ---------- Top bar (no Requests; add Achievements) ----------
class TopBar(QFrame):
    search_requested = pyqtSignal(str)
    achievements_clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("TopBar")
        self.setStyleSheet(f"""
            QFrame#TopBar {{ background:{BG}; }}
            QLabel[role="title"] {{
                color:{TEXT};
                font-size:26px;
                font-weight:600;
            }}
            QLineEdit[role="search"] {{
                background:white;
                border:1px solid {BORDER};
                border-radius:18px;
                padding:8px 36px 8px 12px;
                color:{TEXT};
                selection-background-color:{GREEN};
            }}
            QPushButton[role="nav"], QPushButton[role="searchbtn"] {{
                background:transparent;
                border:none;
                padding:6px;
                border-radius:8px;
            }}
            QPushButton[role="nav"]:hover, QPushButton[role="searchbtn"]:hover {{
                background:#e9ecef;
            }}
            QPushButton[role="ach"] {{
                background:{GREEN};
                color:white;
                border:none;
                padding:6px 14px;
                border-radius:8px;
            }}
        """)
        h = QHBoxLayout(self)
        h.setContentsMargins(12, 8, 12, 4)
        h.setSpacing(10)

        self.menu_btn = QPushButton()
        self.menu_btn.setIcon(_icon("icon_menu.png"))
        self.menu_btn.setProperty("role", "nav")
        self.menu_btn.setFixedSize(32, 32)
        h.addWidget(self.menu_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        title = QLabel("Project and Competition Showcase")
        title.setProperty("role", "title")
        h.addWidget(title, 0, Qt.AlignmentFlag.AlignVCenter)

        h.addStretch(1)

        search_holder = QWidget()
        shl = QHBoxLayout(search_holder)
        shl.setContentsMargins(0, 0, 0, 0)
        shl.setSpacing(0)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search")
        self.search.setProperty("role", "search")
        self.search.setFixedWidth(280)
        self.search.returnPressed.connect(
            lambda: self.search_requested.emit(self.search.text().strip())
        )

        self.search_btn = QPushButton()
        self.search_btn.setIcon(_icon("icon_search.png"))
        self.search_btn.setProperty("role", "searchbtn")
        self.search_btn.setFixedSize(32, 32)
        self.search_btn.clicked.connect(
            lambda: self.search_requested.emit(self.search.text().strip())
        )

        shl.addWidget(self.search)
        shl.addWidget(self.search_btn)
        h.addWidget(search_holder, 0, Qt.AlignmentFlag.AlignVCenter)

        self.ach_btn = QPushButton("Your Achievements")
        self.ach_btn.setProperty("role", "ach")
        plus = _icon("Plus 24px.png")
        if not plus.isNull():
            self.ach_btn.setIcon(plus)
        self.ach_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.ach_btn.clicked.connect(self.achievements_clicked.emit)
        h.addWidget(self.ach_btn, 0, Qt.AlignmentFlag.AlignRight)

# ---------- Segmented tabs ----------
class TabsBar(QFrame):
    changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.cur = "project"
        self.setObjectName("TabsBar")
        self.setStyleSheet(f"""
            QFrame#TabsBar {{ background:{BG}; }}
            QPushButton[role="seg"] {{
                border:1px solid {BORDER};
                background:white;
                color:{TEXT};
                padding:6px 14px;
                border-radius:18px;
                min-width:100px;
            }}
        """)
        h = QHBoxLayout(self)
        h.setContentsMargins(12, 0, 12, 8)
        h.setSpacing(10)

        seg_wrap = QWidget()
        seg = QHBoxLayout(seg_wrap)
        seg.setContentsMargins(0, 0, 0, 0)
        seg.setSpacing(0)

        self.btn_project = QPushButton("Project")
        self.btn_project.setProperty("role", "seg")
        self.btn_comp = QPushButton("Competition")
        self.btn_comp.setProperty("role", "seg")
        self.btn_project.clicked.connect(lambda: self._set_tab("project"))
        self.btn_comp.clicked.connect(lambda: self._set_tab("competition"))

        seg.addWidget(self.btn_project)
        seg.addWidget(self.btn_comp)
        h.addWidget(seg_wrap, 0, Qt.AlignmentFlag.AlignLeft)
        h.addStretch(1)
        self._refresh()

    def _set_tab(self, name: str):
        if name == self.cur:
            return
        self.cur = name
        self._refresh()
        self.changed.emit(self.cur)

    def _refresh(self):
        def style(active: bool):
            return (
                "QPushButton{border:1px solid "
                f"{'#146c43' if active else BORDER}; "
                f"background:{'#146c43' if active else 'white'}; "
                f"color:{'white' if active else TEXT}; "
                "padding:6px 14px; border-radius:18px;}"
            )
        self.btn_project.setStyleSheet(style(self.cur == "project"))
        self.btn_comp.setStyleSheet(style(self.cur == "competition"))

# ---------- Page ----------
class ShowcaseStudentPage(QWidget):
    """Student view: no admin actions; has Achievements button."""
    def __init__(
        self,
        username: str | None = None,
        roles: List[str] | None = None,
        primary_role: str | None = None,
        token: str | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.username = username or ""
        self.roles = roles or []
        self.primary_role = primary_role or ""
        self.token = token or ""
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        ensure_bootstrap()

        self.setObjectName("ShowcaseStudentPage")
        self.setStyleSheet(f"QWidget#ShowcaseStudentPage {{ background:{BG}; }}")

        # outer layout → full-window stack
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self._stack = QStackedWidget(self)
        outer.addWidget(self._stack)

        # main page (index 0)
        main = QWidget(self)
        root = QVBoxLayout(main)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)
        self._stack.addWidget(main)  # index 0

        self.top = TopBar(main)
        self.top.search_requested.connect(self._on_search)
        self.top.achievements_clicked.connect(self._on_achievements)
        root.addWidget(self.top)

        self.tabs = TabsBar(main)
        self.tabs.changed.connect(self._on_tab_changed)
        root.addWidget(self.tabs)

        central = QFrame(main)
        ch = QHBoxLayout(central)
        ch.setContentsMargins(10, 2, 10, 10)
        ch.setSpacing(14)
        root.addWidget(central, 1)

        self.left_scroll = QScrollArea(central)
        self.left_scroll.setWidgetResizable(True)
        self.left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # keep cards pinned to top-left
        self.left_scroll.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        ch.addWidget(self.left_scroll, 1)

        self.left_container = QWidget()
        self.left_scroll.setWidget(self.left_container)
        self.left_col = QGridLayout(self.left_container)
        self.left_col.setSpacing(16)
        self.left_col.setContentsMargins(0, 0, 0, 0)
        self.card_columns = 1

        right_wrap = QWidget()
        right_wrap.setFixedWidth(320)
        rv = QVBoxLayout(right_wrap)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(14)
        ch.addWidget(right_wrap, 0)

        self.featured = SidebarScroller(
            "Featured", right_wrap, on_open=self._open_preview,
            fixed_height=SIDECARD_VIEWPORT_H,
        )
        self.popular = SidebarScroller(
            "Popular", right_wrap, on_open=self._open_preview,
            fixed_height=None,   # stretch with window
        )
        rv.addWidget(self.featured)
        rv.addWidget(self.popular, 1)

        self.cur_kind = "project"
        self.cur_query: str | None = None
        self.data: Dict[str, List[Dict]] = {"project": [], "competition": []}
        self.sidebar_source: Dict[str, List[Dict]] = {"project": [], "competition": []}

        self._reload()

    # ----- layout helpers -----
    def _compute_columns(self) -> int:
        avail = max(1, self.left_scroll.viewport().width())
        min_card_width = 520
        cols = max(1, min(2, avail // min_card_width))
        return cols

    def _maybe_reflow_cards(self):
        new_cols = self._compute_columns()
        if new_cols != getattr(self, "card_columns", 1):
            self.card_columns = new_cols
            self._populate_lists(self.cur_kind)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._maybe_reflow_cards()

    # ----- navigation back from achievements -----
    def _close_submit_page(self):
        w = self._stack.currentWidget()
        if w is not None and self._stack.indexOf(w) != 0:
            try:
                if hasattr(w, "btnClose"):
                    w.btnClose.clicked.disconnect()
            except Exception:
                pass
            w.setParent(None)
        self._stack.setCurrentIndex(0)

    # ----- data -----
    def _reload(self):
        # Student view: only approved items are visible
        status_filter = "approved"

        self.sidebar_source[self.cur_kind] = list_showcase_cards(
            kind=self.cur_kind,
            q=None,
            status=status_filter,
            limit=100,
        )
        self.data[self.cur_kind] = list_showcase_cards(
            kind=self.cur_kind,
            q=self.cur_query,
            status=status_filter,
            limit=100,
        )
        self._populate_lists(self.cur_kind)


    # ----- UI population -----
    def _populate_lists(self, kind: str):
        while self.left_col.count():
            it = self.left_col.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

        items = self.data.get(kind, [])
        cols = getattr(self, "card_columns", 1) or 1
        row = 0
        col = 0

        for idx, it in enumerate(items):
            card = LargeCard(it)
            card.clicked.connect(lambda i=idx, arr=items: self._open_preview(arr, i))
            self.left_col.addWidget(card, row, col)
            col += 1
            if col >= cols:
                col = 0
                row += 1

        src = self.sidebar_source.get(kind, items)
        self.featured.set_items(src[:3], all_items=src)
        self.popular.set_items(
            src[2:5] if len(src) >= 5 else src[:3], all_items=src
        )

    # ----- interactions -----
    def _open_preview(self, items: List[Dict], start_index: int):
        dlg = ShowcasePreviewDialog(items, start_index=start_index, parent=self)
        dlg.exec()

    def _on_tab_changed(self, name: str):
        self.cur_kind = name
        self._reload()
        self._maybe_reflow_cards()

    def _on_search(self, text: str):
        self.cur_query = text or None
        self._reload()
        self._maybe_reflow_cards()

    def _on_achievements(self):
        try:
            from .ShowcaseStudentProject import ShowcaseStudentProjectPage
        except Exception:
            from ShowcaseStudentProject import ShowcaseStudentProjectPage
        page = ShowcaseStudentProjectPage(self)
        if hasattr(page, "request_close"):
            page.request_close.connect(self._close_submit_page)
        self._stack.addWidget(page)
        self._stack.setCurrentWidget(page)

# ---------- Demo ----------
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    stacked = QStackedWidget()
    page = ShowcaseStudentPage()
    stacked.addWidget(page)
    stacked.resize(980, 680)
    stacked.show()
    sys.exit(app.exec())
