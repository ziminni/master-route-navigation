from __future__ import annotations
import os, sqlite3
from pathlib import Path
from typing import List, Dict, Optional

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QPixmap, QIcon, QFont
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QTabWidget, QTableWidget,
    QTableWidgetItem, QPushButton, QTextBrowser, QSizePolicy, QMessageBox, QHeaderView
)


# ---------- Theme ----------
GREEN = "#146c43"
TEXT = "#1f2937"
MUTED = "#6b7280"
BG = "#f3f4f6"
CARD_BG = "#ffffff"
BORDER = "#e5e7eb"

# ---------- DB wiring ----------
try:
    from .db.AnnouncementDBInitialize import db_path, ensure_bootstrap
    from .db.AnnouncementDBHelper import list_documents
except Exception:
    from db.AnnouncementDBInitialize import db_path, ensure_bootstrap
    try:
        from db.AnnouncementDBHelper import list_documents  # type: ignore
    except Exception:
        def list_documents(_announcement_id: int) -> list[dict]:  # fallback
            return []

# ---------- Assets / paths ----------
def _find_dir(name: str) -> str:
    here = os.path.abspath(os.path.dirname(__file__))
    for up in range(0, 7):
        base = here if up == 0 else os.path.abspath(os.path.join(here, *(['..'] * up)))
        cand = os.path.join(base, 'assets', name)
        if os.path.isdir(cand):
            return cand
    return os.path.join(os.getcwd(), 'assets', name)

ICON_DIR = _find_dir('icons')

def _icon(name: str) -> QIcon:
    p = os.path.join(ICON_DIR, name)
    return QIcon(p) if os.path.isfile(p) else QIcon()

HERE = Path(__file__).resolve().parent
def _project_root() -> Path:
    for up in range(0, 7):
        base = HERE.parents[up] if up else HERE
        if (base / "assets").exists():
            return base
    return Path.cwd()

def _resolve_path(p: Optional[str]) -> Optional[Path]:
    if not p:
        return None
    pp = Path(p)
    if pp.is_file():
        return pp
    cand = _project_root() / p
    return cand if cand.is_file() else None

def _is_image_name(name: str) -> bool:
    n = (name or "").lower()
    return any(n.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff"))

def _chip(text: str) -> QLabel:
    lab = QLabel(text)
    lab.setProperty("class", "chip")
    lab.setStyleSheet(
        f'QLabel[class="chip"]{{background:#ecfdf5;color:{GREEN};border:1px solid #c7f0df;'
        'border-radius:10px;padding:2px 8px;font-size:11px;}}'
    )
    return lab

# ---------- Small rounded image widget ----------
class RoundedImage(QWidget):
    def __init__(self, radius: int = 18, parent: QWidget | None = None):
        super().__init__(parent)
        self.radius = float(radius)
        self._pm = QPixmap()
        self.setMinimumHeight(260)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def setPixmap(self, pm: QPixmap):
        self._pm = pm; self.update()

    def paintEvent(self, _e):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath(); path.addRoundedRect(r, self.radius, self.radius)
        p.setClipPath(path)
        if not self._pm.isNull():
            p.drawPixmap(r, self._pm, QRectF(self._pm.rect()))
        else:
            p.fillRect(r, QColor("#d1d5db"))
        p.setClipping(False); p.setPen(QColor(BORDER))
        p.drawRoundedRect(r, self.radius, self.radius)
        p.end()

def _load_and_fill(p: Optional[Path], w: int, h: int) -> QPixmap:
    if p and p.exists():
        pm = QPixmap(str(p))
        if not pm.isNull():
            return pm.scaled(max(1, w), max(1, h),
                             Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                             Qt.TransformationMode.SmoothTransformation)
    ph = QPixmap(max(1, w), max(1, h))
    ph.fill(QColor("#e5e7eb"))
    painter = QPainter(ph)
    painter.setPen(QColor("#9ca3af"))
    f = QFont(); f.setBold(True); f.setPointSize(12)
    painter.setFont(f)
    painter.drawText(ph.rect(), Qt.AlignmentFlag.AlignCenter, "IMAGE")
    painter.end()
    return ph

# ---------- Preview pane ----------
class PreviewPane(QFrame):
    approved = QtCore.pyqtSignal()
    declined  = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.kind: str = "announcement"
        self.item: Dict | None = None
        self.imgs: List[Path] = []
        self.img_idx = 0

        self.setStyleSheet(f"""
            QFrame {{ background:{BG}; border-left:1px solid {BORDER}; }}
            QLabel.title {{ color:{GREEN}; font-size:18px; font-weight:700; }}
            QLabel.meta  {{ color:{MUTED}; font-size:12px; }}
            QPushButton[kind="pill"] {{
                background:{GREEN}; color:white; border:none; border-radius:14px; padding:8px 14px;
            }}
            QPushButton[kind="pill"]:disabled {{ background:#9ca3af; }}
        """)

        v = QVBoxLayout(self); v.setContentsMargins(12,12,12,12); v.setSpacing(8)

        # image + nav
        self.image = RoundedImage(18, self); self.image.setMinimumHeight(260)
        v.addWidget(self.image, 0)

        nav = QHBoxLayout(); nav.setSpacing(6)
        self.prev_btn = QPushButton("◀"); self.prev_btn.setProperty("kind","pill"); self.prev_btn.setFixedHeight(28)
        self.next_btn = QPushButton("▶"); self.next_btn.setProperty("kind","pill"); self.next_btn.setFixedHeight(28)
        self.prev_btn.clicked.connect(self._prev); self.next_btn.clicked.connect(self._next)
        nav.addWidget(self.prev_btn); nav.addStretch(1); nav.addWidget(self.next_btn)
        v.addLayout(nav)

        # text
        head = QHBoxLayout()
        self.title = QLabel("Select a row"); self.title.setProperty("class","title")
        self.status_chip = _chip(""); self.status_chip.setVisible(False)
        head.addWidget(self.title, 1); head.addWidget(self.status_chip, 0)
        v.addLayout(head)

        self.meta = QLabel(""); self.meta.setProperty("class","meta")
        v.addWidget(self.meta)

        # chips
        self.chip_wrap = QWidget()
        self.chips = QHBoxLayout(self.chip_wrap); self.chips.setContentsMargins(0,0,0,0); self.chips.setSpacing(6)
        v.addWidget(self.chip_wrap)

        self.body = QTextBrowser()
        self.body.setStyleSheet(f"QTextBrowser{{border:1px solid {BORDER}; background:white; border-radius:12px; padding:8px;}}")
        v.addWidget(self.body, 1)

        # actions
        act = QHBoxLayout(); act.setSpacing(8)
        self.btnApprove = QPushButton("Approve"); self.btnApprove.setProperty("kind","pill")
        self.btnDecline = QPushButton("Delete");  self.btnDecline.setProperty("kind","pill")
        self.btnApprove.clicked.connect(self.approved.emit)
        self.btnDecline.clicked.connect(self.declined.emit)
        act.addStretch(1); act.addWidget(self.btnDecline); act.addWidget(self.btnApprove)
        v.addLayout(act)

        self._refresh_ui()

    # images for an announcement
    @staticmethod
    def _images_for_announcement(it: Dict) -> List[Path]:
        imgs: List[Path] = []
        try:
            aid = int(it.get("id") or it.get("announcement_id") or 0)
            if aid:
                for d in list_documents(aid):
                    p = d.get("file_path") or ""
                    if d.get("mime_type","").startswith("image") or _is_image_name(p):
                        rp = _resolve_path(p)
                        if rp: imgs.append(rp)
        except Exception:
            pass
        if not imgs:
            rp = _resolve_path(it.get("file_path"))
            if rp: imgs = [rp]
        return imgs

    def set_item(self, kind: str, it: Dict):
        self.kind = kind; self.item = it or {}
        self.imgs = self._images_for_announcement(it) if kind == "announcement" else []
        self.img_idx = 0
        self._refresh_ui()

    def _refresh_ui(self):
        it = self.item or {}

        # title + status
        self.title.setText(it.get("title",""))
        st = it.get("status")
        if self.kind == "reminder" and not st:
            st = "inactive" if int(it.get("is_active") or 0) == 0 else "active"
        self.status_chip.setText(st or "")
        self.status_chip.setVisible(bool(st))

        # meta
        meta_parts = []
        if it.get("author_name"): meta_parts.append(f"by {it['author_name']}")
        if it.get("created_at"):  meta_parts.append(str(it["created_at"]))
        if self.kind == "announcement" and isinstance(it.get("images_count"), int):
            meta_parts.append(f"{it['images_count']} attachment(s)")
        self.meta.setText(" • ".join(meta_parts))

        # chips
        while self.chips.count():
            ci = self.chips.takeAt(0); w = ci.widget()
            if w: w.setParent(None)
        if self.kind == "announcement":
            if it.get("visibility"): self.chips.addWidget(_chip(str(it["visibility"])))
            if it.get("location"):   self.chips.addWidget(_chip(str(it["location"])))
            try:
                pr = int(it.get("priority", 0))
                if pr > 0: self.chips.addWidget(_chip(f"priority {pr}"))
            except Exception:
                pass
            try:
                pin = int(it.get("is_pinned", 0))
                if pin == 1: self.chips.addWidget(_chip("pinned"))
            except Exception:
                pass
        else:
            if it.get("visibility"):     self.chips.addWidget(_chip(str(it["visibility"])))
            if it.get("repeat_interval"): self.chips.addWidget(_chip(str(it["repeat_interval"])))
            try:
                pr = int(it.get("priority", 0))
                if pr > 0: self.chips.addWidget(_chip(f"priority {pr}"))
            except Exception:
                pass

        # body
        body = (it.get("body") or "").strip()
        self.body.setHtml(f"<p style='color:{TEXT};font-size:13px;line-height:1.5'>{body}</p>")

        # image
        if self.kind == "announcement" and self.imgs:
            pm = _load_and_fill(self.imgs[self.img_idx], self.image.width() or 800, self.image.height() or 260)
        else:
            pm = _load_and_fill(None, self.image.width() or 800, self.image.height() or 260)
        self.image.setPixmap(pm)
        multi = self.kind == "announcement" and len(self.imgs) > 1
        self.prev_btn.setVisible(multi); self.next_btn.setVisible(multi)

    def resizeEvent(self, e): super().resizeEvent(e); self._refresh_ui()
    def _prev(self):
        if not self.imgs: return
        self.img_idx = (self.img_idx - 1) % len(self.imgs); self._refresh_ui()
    def _next(self):
        if not self.imgs: return
        self.img_idx = (self.img_idx + 1) % len(self.imgs); self._refresh_ui()

# ---------- Approval page ----------
class AnnouncementAdminApprovalPage(QWidget):
    back_requested = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        ensure_bootstrap()

        self.setStyleSheet(f"""
            QWidget {{ background:{BG}; color:{TEXT}; }}
            QTableWidget {{ background:white; border:1px solid {BORDER}; border-radius:10px; }}
            QHeaderView::section {{ background:{CARD_BG}; padding:6px; border:1px solid {BORDER}; }}
            QLabel.hint {{ color:{MUTED}; font-size:12px; }}
            QPushButton#backBtn {{
                border:1px solid {GREEN}; color:{GREEN}; background:transparent;
                border-radius:15px; padding:6px 10px;
            }}
        """)

        vroot = QVBoxLayout(self)
        vroot.setContentsMargins(12, 12, 12, 12)
        vroot.setSpacing(8)

        hdr = QHBoxLayout()
        self.backBtn = QPushButton(); self.backBtn.setObjectName("backBtn")
        self.backBtn.setIcon(_icon("icon_chevron_left.png"))
        self.backBtn.setToolTip("Back")
        self.backBtn.clicked.connect(self._go_back)
        title = QLabel("Announcements")
        f = title.font(); f.setPointSize(16); f.setBold(True); title.setFont(f); title.setStyleSheet(f"color:{GREEN}")
        hdr.addWidget(self.backBtn, 0); hdr.addSpacing(6); hdr.addWidget(title, 0); hdr.addStretch(1)
        vroot.addLayout(hdr)

        row = QHBoxLayout(); row.setSpacing(12)
        vroot.addLayout(row, 1)

        self.tabs = QTabWidget(self); self.tabs.setDocumentMode(True)
        row.addWidget(self.tabs, 1)

        self.preview = PreviewPane(self)
        row.addWidget(self.preview, 1)

        self._ann_tab = self._make_tab(kind="announcement")
        self._rem_tab = self._make_tab(kind="reminder")
        self.tabs.addTab(self._ann_tab, "Announcements")
        self.tabs.addTab(self._rem_tab, "Reminders")

        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.preview.approved.connect(self._approve_current)
        self.preview.declined.connect(self._decline_current)

        self.items: dict[str, List[Dict]] = {"announcement": [], "reminder": []}
        self._current_row: int = -1

        self._reload()

    # ----- UI builders -----
    def _make_tab(self, kind: str) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w); v.setContentsMargins(0,0,0,0); v.setSpacing(6)

        hint = QLabel("Pending only"); hint.setProperty("class","hint"); v.addWidget(hint, 0)

        tbl = QTableWidget(); tbl.setObjectName(f"tbl_{kind}")
        if kind == "announcement":
            tbl.setColumnCount(5)
            tbl.setHorizontalHeaderLabels(["ID","Title","Author","Category","Date Submitted"])
            init_widths = [60, 280, 160, 120, 180]
        else:
            tbl.setColumnCount(4)
            tbl.setHorizontalHeaderLabels(["ID","Title","Author","Date Submitted"])
            init_widths = [60, 320, 200, 200]

        tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tbl.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        hdr = tbl.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)  # stop auto-resize jitter
        hdr.setStretchLastSection(False)
        for i, w0 in enumerate(init_widths):
            tbl.setColumnWidth(i, w0)
        tbl.verticalHeader().setVisible(False)

        # Update preview on both selection change and clicks on an already-selected row
        tbl.itemSelectionChanged.connect(lambda k=kind, t=tbl: self._on_row_selected(k, t))
        tbl.cellClicked.connect(lambda r, c, k=kind, t=tbl: self._on_row_clicked(k, t, r))

        v.addWidget(tbl, 1)
        return w



    def _table(self, kind: str) -> QTableWidget:
        return self._ann_tab.findChild(QTableWidget, "tbl_announcement") if kind == "announcement" \
            else self._rem_tab.findChild(QTableWidget, "tbl_reminder")

    # ----- data loading -----
    def _reload(self):
        self.items["announcement"] = self._list_pending_announcements()
        self.items["reminder"]     = self._list_pending_reminders()
        self._fill_table("announcement")
        self._fill_table("reminder")
        self._select_first_available()

    @staticmethod
    def _connect() -> sqlite3.Connection:
        con = sqlite3.connect(str(db_path()))
        con.execute("PRAGMA foreign_keys = ON")
        con.row_factory = sqlite3.Row
        return con

    @staticmethod
    def _list_pending_announcements() -> List[Dict]:
        sql = """
            SELECT
                a.announcement_id AS id,
                a.title, a.body, a.status, a.created_at, a.publish_at,
                a.visibility, a.location, a.priority, a.is_pinned,
                COALESCE(u.full_name, u.username, 'Unknown') AS author_name,
                MIN(d.file_path) AS file_path,
                COUNT(d.document_id) AS images_count
            FROM announcements a
            LEFT JOIN auth_user u ON u.user_id = a.author_id
            LEFT JOIN documents d ON d.announcement_id = a.announcement_id
            WHERE a.deleted_at IS NULL
              AND (a.status = 'pending' OR a.status = 'draft')
            GROUP BY a.announcement_id
            ORDER BY a.created_at DESC
        """
        with AnnouncementAdminApprovalPage._connect() as con:
            return [dict(r) for r in con.execute(sql).fetchall()]

    @staticmethod
    def _list_pending_reminders() -> List[Dict]:
        sql = """
            SELECT
                r.reminder_id AS id,
                r.title, r.body, r.is_active, r.created_at, r.remind_at,
                r.visibility, r.repeat_interval, r.priority,
                COALESCE(u.full_name, u.username, 'Unknown') AS author_name
            FROM reminders r
            LEFT JOIN auth_user u ON u.user_id = r.author_id
            WHERE IFNULL(r.is_active, 0) = 0
            ORDER BY r.created_at DESC
        """
        with AnnouncementAdminApprovalPage._connect() as con:
            return [dict(r) for r in con.execute(sql).fetchall()]

    def _fill_table(self, kind: str):
        tbl = self._table(kind)
        rows = self.items[kind]
        tbl.setRowCount(len(rows))
        for r, it in enumerate(rows):
            if kind == "announcement":
                vals = [
                    str(it.get("id","")),
                    it.get("title",""),
                    it.get("author_name",""),
                    it.get("visibility",""),
                    str(it.get("created_at","") or ""),
                ]
            else:
                vals = [
                    str(it.get("id","")),
                    it.get("title",""),
                    it.get("author_name",""),
                    str(it.get("created_at","") or ""),
                ]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setData(Qt.ItemDataRole.UserRole, it)
                if c == 0:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                tbl.setItem(r, c, item)

    # ----- selection + preview -----
    def _on_tab_changed(self, _idx: int):
        self._select_first_available()

    def _select_first_available(self):
        k = "announcement" if self.tabs.currentIndex() == 0 else "reminder"
        tbl = self._table(k)
        if tbl.rowCount():
            tbl.setFocus()
            tbl.selectRow(0)
            # Force-populate preview even if selection signal does not fire
            self._on_row_selected(k, tbl)
        else:
            self.preview.set_item(k, {})
            self._current_row = -1


    def _on_row_selected(self, kind: str, tbl: QTableWidget):
        sel = tbl.selectionModel().selectedRows()
        if not sel:
            self.preview.set_item(kind, {})
            self._current_row = -1
            return
        row = sel[0].row()
        it = tbl.item(row, 0).data(Qt.ItemDataRole.UserRole) or self.items[kind][row]
        self._current_row = row
        self.preview.set_item(kind, it)

    def _on_row_clicked(self, kind: str, tbl: QTableWidget, row: int):
        item = tbl.item(row, 0)
        if not item:
            return
        it = item.data(Qt.ItemDataRole.UserRole) or (self.items[kind][row] if row < len(self.items[kind]) else {})
        self._current_row = row
        self.preview.set_item(kind, it)


    # ----- approve/decline -----
    def _approve_current(self): self._update_current("approve")
    def _decline_current(self): self._update_current("decline")

    def _update_current(self, action: str):
        kind = "announcement" if self.tabs.currentIndex() == 0 else "reminder"
        tbl = self._table(kind)
        if self._current_row < 0 or self._current_row >= tbl.rowCount():
            return
        it = tbl.item(self._current_row, 0).data(Qt.ItemDataRole.UserRole) or self.items[kind][self._current_row]
        pk = it.get("id")
        if not pk:
            QMessageBox.warning(self, "Missing ID", "Cannot proceed without an ID.")
            return
        try:
            if kind == "announcement":
                self._apply_announcement_action(int(pk), action)
            else:
                self._apply_reminder_action(int(pk), action)
        except Exception as e:
            QMessageBox.critical(self, "DB Error", str(e))
            return
        self._reload()

    @staticmethod
    def _apply_announcement_action(pk: int, action: str):
        with AnnouncementAdminApprovalPage._connect() as con:
            if action == "approve":
                con.execute(
                    "UPDATE announcements "
                    "SET status='published', publish_at=COALESCE(publish_at, CURRENT_TIMESTAMP), "
                    "updated_at=CURRENT_TIMESTAMP "
                    "WHERE announcement_id=?",
                    (pk,),
                )
            else:
                con.execute(
                    "UPDATE announcements SET status='declined', updated_at=CURRENT_TIMESTAMP WHERE announcement_id=?",
                    (pk,),
                )

    @staticmethod
    def _apply_reminder_action(pk: int, action: str):
        with AnnouncementAdminApprovalPage._connect() as con:
            if action == "approve":
                con.execute(
                    "UPDATE reminders SET is_active=1, updated_at=CURRENT_TIMESTAMP WHERE reminder_id=?",
                    (pk,),
                )
            else:
                con.execute("DELETE FROM reminders WHERE reminder_id=?", (pk,))

    # ----- back -----
    def _go_back(self): self.back_requested.emit()

# ----- quick manual run -----
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = AnnouncementAdminApprovalPage()
    w.resize(1100, 680)
    w.show()
    sys.exit(app.exec())
