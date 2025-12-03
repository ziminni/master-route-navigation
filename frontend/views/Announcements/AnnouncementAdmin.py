from __future__ import annotations

import os, sys, importlib.util
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from collections import OrderedDict

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QLineEdit,
    QHBoxLayout,
    QVBoxLayout,
    QScrollArea,
    QFrame,
    QGridLayout,
    QSizePolicy,
    QSpacerItem,
    QMessageBox,
    QStackedWidget,
    QMenu,
)

HERE = Path(__file__).resolve().parent

# ---- DB package shim ----
import types

DB_DIR = HERE / "db"
if DB_DIR.exists():
    if "db" not in sys.modules:
        pkg = types.ModuleType("db")
        pkg.__path__ = [str(DB_DIR)]
        sys.modules["db"] = pkg
    if str(DB_DIR) not in sys.path:
        sys.path.insert(0, str(DB_DIR))


def _ensure_local_mod(mod_name: str, file_name: str) -> None:
    if mod_name in sys.modules:
        return
    p = HERE / file_name
    if not p.exists():
        return
    spec = importlib.util.spec_from_file_location(mod_name, str(p))
    mod = importlib.util.module_from_spec(spec)  # type: ignore
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore
    sys.modules[mod_name] = mod


_ensure_local_mod("AnnouncementAdminApproval", "AnnouncementAdminApproval.py")

# ---- preview dialogs ----
try:
    from .AnnouncementPreviewC import AnnouncementPreviewCardDialog
except Exception:
    def _load_by_path(mod_name: str, file_path: Path):
        spec = importlib.util.spec_from_file_location(mod_name, str(file_path))
        mod = importlib.util.module_from_spec(spec)  # type: ignore
        assert spec and spec.loader
        spec.loader.exec_module(mod)  # type: ignore
        return mod

    C = _load_by_path("AnnouncementPreviewC", HERE / "AnnouncementPreviewC.py")
    AnnouncementPreviewCardDialog = C.AnnouncementPreviewCardDialog

# ---- DB helpers ----
try:
    from db.AnnouncementDBHelper import (
        init_db,
        list_announcements,
        # delete_announcement,  # keep/import later when you wire up delete UI
    )
except Exception:
    from AnnouncementDBHelper import (  # type: ignore
        init_db,
        list_announcements,
        # delete_announcement,
    )



try:
    from .AnnouncementAdminEditA import AnnouncementAdminEditAPage
except Exception:
    from AnnouncementAdminEditA import AnnouncementAdminEditAPage  # type: ignore

try:
    from .AnnouncementAdminAnnouncement import AnnouncementAdminAnnouncementPage
except Exception:
    from AnnouncementAdminAnnouncement import AnnouncementAdminAnnouncementPage  # type: ignore

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .AnnouncementAdminApproval import AnnouncementAdminApprovalPage  # type: ignore

# ----- theme -----
GREEN = "#146c43"
TEXT = "#1f2937"
MUTED = "#6b7280"
BG = "#f3f4f6"
BORDER = "#e5e7eb"

# ----- pixmap cache (avoid repeated disk reads) -----
_PIXMAP_CACHE: "OrderedDict[str, QPixmap]" = OrderedDict()
_MAX_PIXMAP_CACHE = 64


def _get_pixmap(path: str | None) -> QPixmap | None:
    if not path:
        return None

    pm = _PIXMAP_CACHE.get(path)
    if pm is not None and not pm.isNull():
        _PIXMAP_CACHE.move_to_end(path)
        return pm

    pm = QPixmap(path)
    if pm.isNull():
        return None

    # clamp very large images once
    max_dim = 1920
    if pm.width() > max_dim or pm.height() > max_dim:
        pm = pm.scaled(
            max_dim,
            max_dim,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    _PIXMAP_CACHE[path] = pm
    if len(_PIXMAP_CACHE) > _MAX_PIXMAP_CACHE:
        _PIXMAP_CACHE.popitem(last=False)
    return pm


# ----- asset helpers -----
def _project_root() -> Path:
    for up in range(0, 7):
        base = HERE.parents[up] if up else HERE
        if (base / "assets").exists():
            return base
    return Path.cwd()


def _resolve_path(p: str | None) -> str | None:
    if not p:
        return None
    pp = Path(p)
    if pp.is_file():
        return str(pp)
    cand = _project_root() / p
    return str(cand) if cand.is_file() else None


# ----- misc -----
def _relative_time(ts: str | None) -> str:
    if not ts:
        return "now"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", ""))
        secs = max(0, int((datetime.utcnow() - dt).total_seconds()))
    except Exception:
        return ts
    if secs < 60:
        return f"{secs}s"
    mins = secs // 60
    if mins < 60:
        return f"{mins}m"
    hrs = mins // 60
    if hrs < 24:
        return f"{hrs}h"
    return f"{hrs // 24}d"


def _chip(text: str) -> QLabel:
    w = QLabel(text)
    w.setStyleSheet(
        f"QLabel{{background:{BG};border:1px solid {BORDER};border-radius:999px;"
        f"padding:3px 10px;font:9pt;color:{MUTED};}}"
    )
    return w


def _pill(text: str, fg: str, bg: str) -> QLabel:
    w = QLabel(text)
    w.setStyleSheet(
        f"QLabel{{background:{bg};border-radius:999px;padding:3px 10px;"
        f"font:9pt;font-weight:600;color:{fg};}}"
    )
    return w


def _icon_btn(text: str, tooltip: str, cb) -> QPushButton:
    b = QPushButton(text)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setToolTip(tooltip)
    b.setFixedSize(30, 30)
    b.setStyleSheet(
        f"QPushButton{{background:rgba(255,255,255,0.96);border:1px solid {BORDER};"
        f"border-radius:15px;font:12pt;color:{TEXT};}}"
        "QPushButton:hover{background:#ffffff;}"
    )
    b.clicked.connect(cb)
    return b


# ===== main widget =====
class AnnouncementAdmin(QWidget):
    def __init__(
        self,
        username: str | None = None,
        roles: List[str] | None = None,
        primary_role: str | None = None,
        token: str | None = None,
        parent=None,
    ):
        super().__init__(parent)

        self.username = username or ""
        self.roles = roles or []
        self.primary_role = primary_role or ""
        self.token = token or ""
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

        self.setWindowTitle("Announcements")
        self.setMinimumSize(1100, 680)

        # responsive layout state
        self._cols: int = 2
        self._min_card_width: int = 520
        self._ann_items: List[Dict] = []
        self._ann_cards: List[QWidget] = []

        self._build_ui()
        self.reload()

    # resize -> recompute grid layout
    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_grid_columns()

    # ----- UI build -----
    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self.stack = QStackedWidget(self)
        outer.addWidget(self.stack)

        self.pageMain = QWidget()
        rootV = QVBoxLayout(self.pageMain)
        rootV.setContentsMargins(12, 12, 12, 12)
        rootV.setSpacing(12)

        # top bar
        topbar = QHBoxLayout()
        topbar.setSpacing(10)

        self.btnMenu = QPushButton("☰")
        self.btnMenu.setFixedSize(36, 36)
        self.btnMenu.setStyleSheet(
            f"QPushButton{{background:#fff;border:1px solid {BORDER};border-radius:10px;}}"
        )

        title = QLabel("Announcements")
        title.setStyleSheet(f"color:{GREEN};font:700 22pt;")
        title.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        def _primary(btn: QPushButton) -> QPushButton:
            btn.setFixedHeight(36)
            btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            btn.setStyleSheet(
                f"QPushButton{{background:{GREEN};color:white;padding:0 18px;"""
                f"border-radius:10px;font:600 11pt;}}"
                "QPushButton:hover{opacity:0.96;}"
            )
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            return btn

        self.btnRequests = _primary(QPushButton("Requests"))
        self.btnRequests.clicked.connect(self._on_requests)

        self.btnAddAnnouncement = _primary(QPushButton("＋  Announcement"))
        self.btnAddAnnouncement.clicked.connect(self._on_add_announcement)

        self.searchBar = QLineEdit()
        self.searchBar.setPlaceholderText("Search announcements")
        self.searchBar.setClearButtonEnabled(True)
        self.searchBar.returnPressed.connect(self.reload)
        self.searchBar.setFixedHeight(36)
        self.searchBar.setFixedWidth(360)
        icon_path = _project_root() / "assets/icons/icon_search.png"
        if icon_path.is_file():
            self.searchBar.addAction(
                QIcon(str(icon_path)), QLineEdit.ActionPosition.LeadingPosition
            )
        self.searchBar.setStyleSheet(
            f"QLineEdit{{background:#fff;border:1px solid {BORDER};border-radius:18px;"
            f"padding-left:30px;padding-right:14px;font:10.5pt;color:{TEXT};}}"
        )

        topbar.addWidget(self.btnMenu, 0)
        topbar.addWidget(title, 0)
        topbar.addSpacing(10)
        topbar.addWidget(self.btnRequests, 0)
        topbar.addWidget(self.btnAddAnnouncement, 0)
        topbar.addStretch(1)
        topbar.addWidget(self.searchBar, 0)
        rootV.addLayout(topbar)

        # content row
        row = QHBoxLayout()
        row.setSpacing(12)

        # left: announcements (full width now)
        leftWrap = QWidget()
        leftWrap.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        leftV = QVBoxLayout(leftWrap)
        leftV.setContentsMargins(0, 0, 0, 0)
        leftV.setSpacing(0)

        self.gridHost = QWidget()
        self.gridHost.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.grid = QGridLayout(self.gridHost)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(14)
        self.grid.setVerticalSpacing(14)

        leftScroll = QScrollArea()
        self.leftScroll = leftScroll
        leftScroll.setWidget(self.gridHost)
        leftScroll.setWidgetResizable(True)
        leftScroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        leftScroll.setStyleSheet("QScrollArea{border:none;}")
        leftV.addWidget(leftScroll, 1)

        orig_resize = leftScroll.resizeEvent

        def _left_resize(ev):
            if orig_resize:
                orig_resize(ev)
            self._update_grid_columns()

        leftScroll.resizeEvent = _left_resize  # type: ignore[assignment]

        row.addWidget(leftWrap, 1)

        rootV.addLayout(row, 1)
        self.stack.addWidget(self.pageMain)

    # ----- navigation helpers -----
    def _open_add_announcement(self) -> None:
        page = AnnouncementAdminAnnouncementPage(parent=self)
        page.back_requested.connect(lambda: self._close_add_announcement(page))
        page.published.connect(lambda _aid: self.reload())
        page.request_close.connect(lambda: self._close_add_announcement(page))
        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)

    def _close_add_announcement(self, page: QWidget) -> None:
        self.stack.setCurrentWidget(self.pageMain)
        self.stack.removeWidget(page)
        page.deleteLater()

    def _open_edit_a(self, aid: int) -> None:
        page = AnnouncementAdminEditAPage(aid, parent=self)
        page.back_requested.connect(lambda: self._close_edit_a(page))
        page.saved.connect(self.reload)
        page.deleted.connect(self.reload)
        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)

    def _close_edit_a(self, page: QWidget) -> None:
        self.stack.setCurrentWidget(self.pageMain)
        self.stack.removeWidget(page)
        page.deleteLater()

    # ----- data -----
    def reload(self) -> None:
        q = self.searchBar.text().strip() or None
        self._ann_items = list_announcements(limit=30, search=q)
        self._paint_announcements(self._ann_items)
        self._update_grid_columns()

    # ----- responsive helpers -----
    def _effective_view_width(self) -> int:
        if hasattr(self, "leftScroll"):
            return self.leftScroll.viewport().width()
        return self.gridHost.width()

    def _update_grid_columns(self) -> None:
        avail = self._effective_view_width()
        if avail <= 0:
            avail = self.width()

        max_cols = 2
        cols = max(1, min(max_cols, avail // self._min_card_width))

        for i in range(max_cols):
            self.grid.setColumnStretch(i, 1 if i < cols else 0)

        if cols != self._cols:
            self._cols = cols
            self._paint_announcements(self._ann_items)
        else:
            self._apply_card_widths()

    def _apply_card_widths(self) -> None:
        if not self._ann_cards:
            return
        avail = self._effective_view_width()
        if avail <= 0:
            return

        cols = max(self._cols, 1)
        spacing = self.grid.horizontalSpacing() or 0
        total_spacing = spacing * (cols - 1)
        col_width = max(1, (avail - total_spacing) // cols)

        for card in self._ann_cards:
            card.setMinimumWidth(col_width)
            card.setMaximumWidth(col_width)

    def _update_card_image(self, label: QLabel) -> None:
        pix: QPixmap | None = getattr(label, "_orig_pixmap", None)
        if not pix or pix.isNull():
            return
        size = label.size()
        if size.width() <= 0 or size.height() <= 0:
            return
        scaled = pix.scaled(
            size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        label.setPixmap(scaled)

    # ----- painters -----
    def _paint_announcements(self, items: List[Dict]) -> None:
        while self.grid.count():
            it = self.grid.takeAt(0)
            w = it.widget()
            if w:
                w.setParent(None)

        self._ann_cards = []
        cols = max(self._cols, 1)

        for i, it in enumerate(items):
            r, c = divmod(i, cols)
            card = self._build_announcement_card(it, i)
            self._ann_cards.append(card)
            self.grid.addWidget(card, r, c)

        self.grid.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding),
            (len(items) + cols - 1) // cols + 1,
            0,
            1,
            cols,
        )

        self._apply_card_widths()

    # ----- redesigned announcement card -----
    def _build_announcement_card(self, item: Dict, idx: int) -> QWidget:
        """
        Large announcement card with:
        - hero image (zoom-to-fill)
        - author chip + relative time
        - status / audience pills
        - title + short description
        - schedule line (publish / expire / pinned-while-active)
        - tags, priority, attachments
        - top-right button that goes straight to Edit page
        """
        card = QFrame()
        card.setObjectName("annCard")
        card.setStyleSheet(
            f"#annCard{{background:#fff;border:1px solid {BORDER};border-radius:16px;}}"
        )
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        outer = QVBoxLayout(card)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # --- hero image ---
        img = QLabel(card)
        img.setFixedHeight(220)
        img.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img.setScaledContents(False)

        p = _resolve_path(item.get("file_path"))
        pix = _get_pixmap(p) if p else None
        if pix is not None:
            img._orig_pixmap = pix  # type: ignore[attr-defined]
            self._update_card_image(img)

        outer.addWidget(img)

        def _open_preview(_e=None, i=idx):
            dlg = AnnouncementPreviewCardDialog(self._ann_items, start_index=i, parent=self)
            dlg.exec()

        # whole card (and image) opens preview
        card.mouseReleaseEvent = _open_preview  # type: ignore[assignment]
        img.mouseReleaseEvent = _open_preview   # type: ignore[assignment]

        # author chip
        pill = QLabel(img)
        pill.setText(
            f"By {item.get('author_name','Unknown')} • "
            f"{_relative_time(item.get('publish_at') or item.get('created_at'))}"
        )
        pill.setStyleSheet(
            f"QLabel{{background:rgba(255,255,255,0.96);border-radius:999px;"
            f"padding:4px 12px;font:10pt;color:{TEXT};border:1px solid {BORDER};}}"
        )
        pill.adjustSize()
        pill.move(12, 12)
        pill.raise_()

        # top-right button: directly open Edit page (no menu)
        btnBar = QWidget(img)
        hb = QHBoxLayout(btnBar)
        hb.setContentsMargins(0, 0, 0, 0)
        hb.setSpacing(0)

        aid = int(item.get("announcement_id") or 0)
        edit_btn = _icon_btn("⋯", "Edit announcement", lambda _=None, a=aid: self._open_edit_a(a))
        hb.addWidget(edit_btn)

        btnBar.adjustSize()
        btnBar.move(img.width() - btnBar.sizeHint().width() - 12, 12)
        btnBar.raise_()

        def _on_img_resize(ev, w=img, bar=btnBar):
            self._update_card_image(w)
            bar.move(w.width() - bar.sizeHint().width() - 12, 12)

        img.resizeEvent = _on_img_resize  # type: ignore[assignment]

        # --- content section ---
        body = QWidget(card)
        bodyL = QVBoxLayout(body)
        bodyL.setContentsMargins(16, 14, 16, 14)
        bodyL.setSpacing(6)

        # pills row (status / visibility / pinned)
        pillRowW = QWidget(body)
        pillRow = QHBoxLayout(pillRowW)
        pillRow.setContentsMargins(0, 0, 0, 0)
        pillRow.setSpacing(6)

        status = (item.get("status") or "").lower()
        if status:
            if status == "published":
                pillRow.addWidget(_pill("Published", GREEN, "#dcfce7"))
            elif status == "draft":
                pillRow.addWidget(_pill("Draft", "#92400e", "#ffedd5"))
            else:
                pillRow.addWidget(_pill(status.capitalize(), TEXT, BG))

        visibility = item.get("visibility")
        if visibility:
            pillRow.addWidget(_pill(f"Visible: {visibility}", MUTED, "#eef2ff"))

        try:
            pinned_active = int(item.get("pinned_active", item.get("is_pinned", 0) or 0))
        except Exception:
            pinned_active = 0
        if pinned_active == 1:
            pillRow.addWidget(_pill("Pinned", "#b45309", "#fef3c7"))

        pillRow.addStretch(1)
        bodyL.addWidget(pillRowW)

        # title row
        titleRowW = QWidget(body)
        titleRow = QHBoxLayout(titleRowW)
        titleRow.setContentsMargins(0, 0, 0, 0)
        titleRow.setSpacing(8)

        lblTitle = QLabel(item.get("title", ""))
        lblTitle.setStyleSheet(f"font:700 16pt;color:{GREEN};")
        lblTitle.setWordWrap(True)
        titleRow.addWidget(lblTitle, 1)

        publish_ts = item.get("publish_at") or item.get("created_at")
        ts_text = _relative_time(publish_ts) if publish_ts else ""
        if ts_text:
            ts_lbl = QLabel(f"{ts_text} ago")
            ts_lbl.setStyleSheet(f"font:9pt;color:{MUTED};")
            titleRow.addWidget(ts_lbl, 0, Qt.AlignmentFlag.AlignTop)

        bodyL.addWidget(titleRowW)

        # body preview
        full_body = (item.get("body") or "").strip()
        preview_text = full_body
        max_chars = 220
        if len(preview_text) > max_chars:
            preview_text = preview_text[: max_chars - 1].rstrip() + "…"

        preview = QLabel(preview_text)
        preview.setWordWrap(True)
        preview.setStyleSheet(f"color:{TEXT};font:10.5pt;")
        bodyL.addWidget(preview)

        # schedule line
        schedule_parts: List[str] = []
        if publish_ts:
            schedule_parts.append(f"Published {publish_ts.split(' ')[0]}")
        exp = item.get("expire_at")
        if exp:
            schedule_parts.append(f"Expires {exp.split(' ')[0]}")
        pinned_until = item.get("pinned_until")
        if pinned_until and pinned_active == 1:
            schedule_parts.append(f"Pinned until {pinned_until.split(' ')[0]}")

        if schedule_parts:
            sched_lbl = QLabel(" • ".join(schedule_parts))
            sched_lbl.setStyleSheet(f"font:9pt;color:{MUTED};")
            bodyL.addWidget(sched_lbl)

        # chips row
        metaW = QWidget(body)
        meta = QHBoxLayout(metaW)
        meta.setContentsMargins(0, 4, 0, 0)
        meta.setSpacing(6)

        loc = item.get("location")
        if loc:
            meta.addWidget(_chip(loc))

        try:
            pr = int(item.get("priority", 0))
        except Exception:
            pr = 0
        if pr > 0:
            meta.addWidget(_chip(f"priority {pr}"))

        tags_csv = item.get("tags_csv") or ""
        tags = [t for t in tags_csv.split(",") if t]
        for t in tags[:3]:
            meta.addWidget(_chip(f"#{t}"))
        if len(tags) > 3:
            meta.addWidget(_chip(f"+{len(tags) - 3} more"))

        try:
            dc = int(item.get("doc_count", 0))
        except Exception:
            dc = 0
        if dc > 0:
            meta.addWidget(_chip(f"{dc} attachment(s)"))

        meta.addStretch(1)
        bodyL.addWidget(metaW)

        outer.addWidget(body)
        return card

    # ----- top-level stubs -----
    def _on_add_announcement(self) -> None:
        self._open_add_announcement()

    def _on_requests(self) -> None:
        try:
            from .AnnouncementAdminApproval import (  # type: ignore
                AnnouncementAdminApprovalPage,
            )
        except Exception:
            ap = HERE / "AnnouncementAdminApproval.py"
            if not ap.exists():
                QMessageBox.critical(self, "Missing file", f"Not found: {ap}")
                return
            spec = importlib.util.spec_from_file_location(
                "AnnouncementAdminApproval", str(ap)
            )
            mod = importlib.util.module_from_spec(spec)  # type: ignore
            assert spec and spec.loader
            spec.loader.exec_module(mod)  # type: ignore
            AnnouncementAdminApprovalPage = getattr(
                mod, "AnnouncementAdminApprovalPage"
            )

        if not hasattr(self, "pageApproval"):
            self.pageApproval = AnnouncementAdminApprovalPage(self)
            self.pageApproval.back_requested.connect(self._close_requests)
            self.stack.addWidget(self.pageApproval)

        self.stack.setCurrentWidget(self.pageApproval)

    def _close_requests(self) -> None:
        self.stack.setCurrentWidget(self.pageMain)
        if hasattr(self, "pageApproval"):
            w = self.pageApproval
            self.stack.removeWidget(w)
            w.deleteLater()
            delattr(self, "pageApproval")


if __name__ == "__main__":
    init_db(seed=True)
    app = QApplication(sys.argv)
    w = AnnouncementAdmin()
    w.show()
    sys.exit(app.exec())
