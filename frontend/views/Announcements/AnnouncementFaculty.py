from __future__ import annotations

import sys, importlib.util
from pathlib import Path
from datetime import datetime
from typing import List, Dict

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
)

HERE = Path(__file__).resolve().parent

# --- DB package shim ---
import types

DB_DIR = HERE / "db"
if DB_DIR.exists():
    if "db" not in sys.modules:
        pkg = types.ModuleType("db")
        pkg.__path__ = [str(DB_DIR)]
        sys.modules["db"] = pkg
    if str(DB_DIR) not in sys.path:
        sys.path.insert(0, str(DB_DIR))

# ---- preview dialog (announcements only) ----
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
    from db.AnnouncementDBHelper import init_db, get_announcements
except Exception:
    DB_DIR = HERE / "db"
    sys.path.insert(0, str(DB_DIR))
    from AnnouncementDBHelper import init_db, get_announcements  # type: ignore

# ---- theme ----
GREEN = "#146c43"
TEXT = "#1f2937"
BG = "#f3f4f6"
BORDER = "#e5e7eb"
MUTED = "#6b7280"

# ---- path helpers ----
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


# ---- misc ----
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
        f"QLabel{{background:{BG};border:1px solid {BORDER};border-radius:10px;"
        f"padding:2px 8px;font:9pt;color:{TEXT};}}"
    )
    return w


def _pill(text: str, fg: str, bg: str) -> QLabel:
    w = QLabel(text)
    w.setStyleSheet(
        f"QLabel{{background:{bg};color:{fg};border-radius:999px;"
        f"padding:2px 10px;font:9pt;}}"
    )
    return w


# ---- image cache / helpers ----
_PIX_CACHE: dict[str, QPixmap] = {}


def _get_pixmap(path: str | None) -> QPixmap | None:
    if not path:
        return None
    if path in _PIX_CACHE:
        return _PIX_CACHE[path]
    pm = QPixmap(path)
    if pm.isNull():
        return None
    _PIX_CACHE[path] = pm
    return pm


def _update_card_image(label: QLabel) -> None:
    pix = getattr(label, "_orig_pixmap", None)
    if not isinstance(pix, QPixmap) or pix.isNull():
        return
    w = label.width()
    h = label.height()
    if w <= 0 or h <= 0:
        return
    scaled = pix.scaled(
        w,
        h,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation,
    )
    x = max(0, (scaled.width() - w) // 2)
    y = max(0, (scaled.height() - h) // 2)
    label.setPixmap(
        scaled.copy(
            x,
            y,
            min(w, scaled.width() - x),
            min(h, scaled.height() - y),
        )
    )


# ===== main widget =====
class AnnouncementFaculty(QWidget):
    def __init__(
        self,
        username: str | None = None,
        roles: List[str] | None = None,
        primary_role: str | None = None,
        token: str | None = None,
        parent=None,
    ):
        super().__init__(parent)

        # session context
        self.username = username or ""
        self.roles = roles or []
        self.primary_role = primary_role or ""
        self.token = token or ""
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

        self._ann_items: List[Dict] = []
        self._grid_cols: int = 1

        self.setWindowTitle("Announcements")
        self.setMinimumSize(1100, 680)
        self._build_ui()
        self.reload()

    # ---------- UI ----------
    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

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

        self.searchBar = QLineEdit()
        self.searchBar.setPlaceholderText("Search announcements")
        self.searchBar.setClearButtonEnabled(True)
        self.searchBar.returnPressed.connect(self.reload)
        self.searchBar.setFixedHeight(36)
        self.searchBar.setFixedWidth(360)
        icon_path = _project_root() / "assets/icons/icon_search.png"
        if icon_path.is_file():
            self.searchBar.addAction(
                QIcon(str(icon_path)),
                QLineEdit.ActionPosition.LeadingPosition,
            )
        self.searchBar.setStyleSheet(
            f"QLineEdit{{background:#fff;border:1px solid {BORDER};border-radius:18px;"
            f"padding-left:30px;padding-right:14px;font:10.5pt;color:{TEXT};}}"
        )

        topbar.addWidget(self.btnMenu, 0)
        topbar.addWidget(title, 0)
        topbar.addStretch(1)
        topbar.addWidget(self.searchBar, 0)
        rootV.addLayout(topbar)

        # content row (announcements only, full width)
        row = QHBoxLayout()
        row.setSpacing(12)

        leftWrap = QWidget()
        leftWrap.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.leftWrap = leftWrap

        leftV = QVBoxLayout(leftWrap)
        leftV.setContentsMargins(0, 0, 0, 0)
        leftV.setSpacing(0)

        self.gridHost = QWidget()
        self.grid = QGridLayout(self.gridHost)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(14)
        self.grid.setVerticalSpacing(14)
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 1)

        leftScroll = QScrollArea()
        leftScroll.setWidget(self.gridHost)
        leftScroll.setWidgetResizable(True)
        leftScroll.setStyleSheet("QScrollArea{border:none;}")
        leftScroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        leftV.addWidget(leftScroll, 1)

        row.addWidget(leftWrap, 1)
        rootV.addLayout(row, 1)

        outer.addWidget(self.pageMain)

    # ---------- data ----------
    def reload(self) -> None:
        q = self.searchBar.text().strip()
        # faculty sees General + Faculty announcements
        scopes = ["general", "faculty"]
        self._ann_items = get_announcements(
            limit=30,
            q=q,
            audience_scopes=scopes,
        )
        self._paint_announcements(self._ann_items)

    # decide columns based on available width (no right sidebar anymore)
    def _compute_cols(self) -> int:
        total = self.pageMain.width() or self.width()
        if total <= 0:
            return 1
        # two columns only when there is enough space for two ~520px cards
        return 2 if total >= 1150 else 1

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        new_cols = self._compute_cols()
        if new_cols != self._grid_cols:
            self._grid_cols = new_cols
            self._paint_announcements(self._ann_items)

    # ---------- painters ----------
    def _paint_announcements(self, items: List[Dict]) -> None:
        while self.grid.count():
            it = self.grid.takeAt(0)
            w = it.widget()
            if w:
                w.setParent(None)

        cols = self._compute_cols()
        self._grid_cols = cols

        for i, it in enumerate(items):
            r, c = divmod(i, cols)
            self.grid.addWidget(self._build_announcement_card(it, i), r, c)

        # stretch columns evenly
        for c in range(cols):
            self.grid.setColumnStretch(c, 1)

        # bottom spacer so cards hug the top
        self.grid.addItem(
            QSpacerItem(
                0,
                0,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding,
            ),
            (len(items) + cols - 1) // cols + 1,
            0,
            1,
            cols,
        )

    # ---------- builders ----------
    def _build_announcement_card(self, item: Dict, idx: int) -> QWidget:
        """
        Read-only faculty card:
        - responsive width (1 or 2 columns)
        - hero image zoom-to-fill
        - author + relative time
        - status / audience / pinned pills
        - schedule line
        - location, priority, tags, attachment count
        """
        card = QFrame()
        card.setObjectName("annCard")
        card.setStyleSheet(
            f"#annCard{{background:#fff;border:1px solid {BORDER};border-radius:16px;}}"
        )
        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        outer = QVBoxLayout(card)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # --- hero image ---
        img = QLabel(card)
        img.setFixedHeight(220)
        img.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img.setScaledContents(False)

        p = _resolve_path(item.get("file_path"))
        pix = _get_pixmap(p) if p else None
        if pix is not None:
            img._orig_pixmap = pix  # type: ignore[attr-defined]
            _update_card_image(img)

        outer.addWidget(img)

        def _open(_e=None, i=idx):
            dlg = AnnouncementPreviewCardDialog(
                self._ann_items,
                start_index=i,
                parent=self,
            )
            dlg.exec()

        # whole card (and image) opens preview
        card.mouseReleaseEvent = _open  # type: ignore[assignment]
        img.mouseReleaseEvent = _open   # type: ignore[assignment]

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

        def _on_img_resize(ev, w=img):
            _update_card_image(w)

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
            pinned_active = int(
                item.get("pinned_active", item.get("is_pinned", 0) or 0)
            )
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

        # body preview (trim long text)
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

        # chips row: location / priority / tags / attachments
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


if __name__ == "__main__":
    init_db(seed=True)
    app = QApplication(sys.argv)
    w = AnnouncementFaculty()
    w.show()
    sys.exit(app.exec())
