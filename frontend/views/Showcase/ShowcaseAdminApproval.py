# views/Showcase/ShowcaseAdminApproval.py
from __future__ import annotations
import os, sqlite3
from typing import List, Dict, Optional

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QPixmap, QIcon, QFont
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QTabWidget, QTableWidget,
    QTableWidgetItem, QPushButton, QTextBrowser, QSizePolicy, QMessageBox
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
    from .db.ShowcaseDBHelper import list_showcase_cards
    from .db.ShowcaseDBInitialize import db_path, ensure_bootstrap
except Exception:
    from db.ShowcaseDBHelper import list_showcase_cards
    from db.ShowcaseDBInitialize import db_path, ensure_bootstrap


# ---------- Assets ----------
def _find_dir(name: str) -> str:
    here = os.path.abspath(os.path.dirname(__file__))
    for up in range(0, 7):
        base = here if up == 0 else os.path.abspath(os.path.join(here, *(['..'] * up)))
        cand = os.path.join(base, 'assets', name)
        if os.path.isdir(cand):
            return cand
    return os.path.join(os.getcwd(), 'assets', name)

ICON_DIR = _find_dir('icons')
IMG_DIR  = _find_dir('images')

def _icon(name: str) -> QIcon:
    p = os.path.join(ICON_DIR, name)
    return QIcon(p) if os.path.isfile(p) else QIcon()

def _placeholder(w: int, h: int, label: str = "image") -> QPixmap:
    pm = QPixmap(w, h); pm.fill(QColor("#d1d5db"))
    p = QPainter(pm); p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(QColor("#9ca3af")); p.setBrush(QColor("#e5e7eb"))
    p.drawRoundedRect(0, 0, w, h, 18, 18)
    f = QFont(); f.setPointSize(12); f.setBold(True)
    p.setFont(f); p.setPen(QColor("#6b7280"))
    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, label.upper())
    p.end()
    return pm

def _load_image(fname: Optional[str], w: int, h: int) -> QPixmap:
    if fname:
        p = fname if os.path.isabs(fname) else os.path.join(IMG_DIR, fname)
        if os.path.isfile(p):
            pm = QPixmap(p)
            if not pm.isNull():
                return pm.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                 Qt.TransformationMode.SmoothTransformation)
    return _placeholder(w, h)


# ---------- Small rounded image widget (inline version) ----------
class RoundedImage(QWidget):
    def __init__(self, radius: int = 18, parent: QWidget | None = None):
        super().__init__(parent)
        self.radius = float(radius)
        self._pm = QPixmap()
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


# ---------- Preview pane ----------
class PreviewPane(QFrame):
    approved = QtCore.pyqtSignal()
    declined = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.item: Dict | None = None
        self.kind: str = "project"
        self.imgs: List[str] = []
        self.img_idx = 0

        self.setStyleSheet(f"""
            QFrame {{ background:{BG}; border-left:1px solid {BORDER}; }}
            QLabel.title {{ color:{GREEN}; font-size:18px; font-weight:700; }}
            QLabel.meta  {{ color:{MUTED}; font-size:12px; }}
            QLabel.chip  {{ background:#ecfdf5; color:{GREEN}; border:1px solid #c7f0df;
                            border-radius:10px; padding:2px 8px; font-size:11px; }}
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
        self.prev_btn = QPushButton(); self.prev_btn.setIcon(_icon("icon_chevron_left.png"))
        self.next_btn = QPushButton(); self.next_btn.setIcon(_icon("icon_chevron_right.png"))
        for b in (self.prev_btn, self.next_btn):
            b.setProperty("kind", "pill"); b.setFixedHeight(28)
        self.prev_btn.clicked.connect(self._prev); self.next_btn.clicked.connect(self._next)
        nav.addWidget(self.prev_btn); nav.addStretch(1); nav.addWidget(self.next_btn)
        v.addLayout(nav)

        # text
        self.title = QLabel("Select a row"); self.title.setProperty("class","title")
        self.status_chip = QLabel(""); self.status_chip.setProperty("class","chip")
        head = QHBoxLayout(); head.addWidget(self.title, 1); head.addWidget(self.status_chip, 0)
        v.addLayout(head)

        self.meta = QLabel(""); self.meta.setProperty("class","meta")
        v.addWidget(self.meta)

        self.body = QTextBrowser()
        self.body.setStyleSheet(f"QTextBrowser{{border:1px solid {BORDER}; background:white; border-radius:12px; padding:8px;}}")
        v.addWidget(self.body, 1)

        # actions
        act = QHBoxLayout(); act.setSpacing(8)
        self.btnApprove = QPushButton("Approve"); self.btnApprove.setProperty("kind","pill")
        self.btnDecline = QPushButton("Decline"); self.btnDecline.setProperty("kind","pill")
        self.btnApprove.clicked.connect(self.approved.emit)
        self.btnDecline.clicked.connect(self.declined.emit)
        act.addStretch(1); act.addWidget(self.btnDecline); act.addWidget(self.btnApprove)
        v.addLayout(act)

        self._refresh_ui()

    def set_item(self, kind: str, it: Dict):
        self.kind = kind; self.item = it
        imgs = it.get("images") or ([it.get("image")] if it.get("image") else [])
        self.imgs = imgs if imgs else ["1.jpg"]
        self.img_idx = 0
        self._refresh_ui()

    def _refresh_ui(self):
        it = self.item or {}
        self.title.setText(it.get("title",""))
        st = it.get("status") or "pending"
        self.status_chip.setText(st); self.status_chip.setVisible(bool(st))
        meta_parts = []
        if it.get("author_display"): meta_parts.append(f"by {it['author_display']}")
        if it.get("posted_ago"):     meta_parts.append(it["posted_ago"])
        if it.get("category"):       meta_parts.append(it["category"])
        if it.get("context"):        meta_parts.append(it["context"])
        nimg = it.get("images_count")
        if isinstance(nimg, int):    meta_parts.append(f"{nimg} image{'s' if nimg != 1 else ''}")
        self.meta.setText(" • ".join(meta_parts))

        body = (it.get("long_text") or it.get("blurb") or "").strip()
        self.body.setHtml(f"<p style='color:{TEXT};font-size:13px;line-height:1.5'>{body}</p>")

        pm = _load_image(self.imgs[self.img_idx] if self.imgs else None,
                         self.image.width() or 800, self.image.height() or 260)
        self.image.setPixmap(pm)

    def resizeEvent(self, e): super().resizeEvent(e); self._refresh_ui()
    def _prev(self): 
        if not self.imgs: return
        self.img_idx = (self.img_idx - 1) % len(self.imgs); self._refresh_ui()
    def _next(self):
        if not self.imgs: return
        self.img_idx = (self.img_idx + 1) % len(self.imgs); self._refresh_ui()


# ---------- Approval page ----------
class ShowcaseAdminApprovalPage(QWidget):
    """
    Two tabs: Projects and Competitions.
    Left: table of pending items.
    Right: preview pane with Approve/Decline.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        ensure_bootstrap(seed=False)

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

        # root = header + content
        vroot = QVBoxLayout(self)
        vroot.setContentsMargins(12, 12, 12, 12)
        vroot.setSpacing(8)

        # header with back button
        hdr = QHBoxLayout()
        self.backBtn = QPushButton()
        self.backBtn.setObjectName("backBtn")
        self.backBtn.setIcon(_icon("icon_chevron_left.png"))
        self.backBtn.setToolTip("Back")
        self.backBtn.clicked.connect(self._go_back)
        title = QLabel("Project and Competition Showcase")
        f = title.font(); f.setPointSize(16); f.setBold(True); title.setFont(f); title.setStyleSheet(f"color:{GREEN}")
        hdr.addWidget(self.backBtn, 0)
        hdr.addSpacing(6)
        hdr.addWidget(title, 0)
        hdr.addStretch(1)
        vroot.addLayout(hdr)

        # content row: tabs + preview
        row = QHBoxLayout()
        row.setSpacing(12)
        vroot.addLayout(row, 1)

        self.tabs = QTabWidget(self)
        self.tabs.setDocumentMode(True)
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        row.addWidget(self.tabs, 1)

        self.preview = PreviewPane(self)
        row.addWidget(self.preview, 1)

        # build tabs
        self._proj_tab = self._make_tab(kind="project")
        self._comp_tab = self._make_tab(kind="competition")
        self.tabs.addTab(self._proj_tab, "Projects")
        self.tabs.addTab(self._comp_tab, "Competitions")

        # signals
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.preview.approved.connect(self._approve_current)
        self.preview.declined.connect(self._decline_current)

        # data holders
        self.items: dict[str, List[Dict]] = {"project": [], "competition": []}
        self._current_row: int = -1

        self._reload()

    # ----- UI builders -----
    def _make_tab(self, kind: str) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w); v.setContentsMargins(0,0,0,0); v.setSpacing(6)

        hint = QLabel("Pending only"); hint.setProperty("class","hint"); v.addWidget(hint, 0)

        tbl = QTableWidget(); tbl.setObjectName(f"tbl_{kind}")
        if kind == "project":
            tbl.setColumnCount(8)
            tbl.setHorizontalHeaderLabels([
                "ID","Title","Author","Category","Context","Images","Status","Posted"
            ])
        else:
            tbl.setColumnCount(6)
            tbl.setHorizontalHeaderLabels([
                "ID","Title","Event Type","Images","Status","Posted"
            ])
        tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tbl.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.horizontalHeader().setStretchLastSection(True)
        tbl.verticalHeader().setVisible(False)
        tbl.itemSelectionChanged.connect(lambda k=kind, t=tbl: self._on_row_selected(k, t))
        v.addWidget(tbl, 1)
        return w

    def _go_back(self):
        # clear preview before leaving
        k = "project" if self.tabs.currentIndex() == 0 else "competition"
        self.preview.set_item(k, {})
        # close if hosted in a dialog
        from PyQt6.QtWidgets import QDialog
        host = self.window()
        if isinstance(host, QDialog):
            host.close()
        else:
            self.hide()

    def _table(self, kind: str) -> QTableWidget:
        return self._proj_tab.findChild(QTableWidget, "tbl_project") if kind == "project" \
            else self._comp_tab.findChild(QTableWidget, "tbl_competition")

    # ----- data loading -----
    def _reload(self):
        for kind in ("project", "competition"):
            self.items[kind] = list_showcase_cards(kind=kind, q=None, status="pending", limit=200, offset=0)
            self._fill_table(kind)
        # choose a row or clear the preview if none
        self._select_first_available()

    def _fill_table(self, kind: str):
        tbl = self._table(kind)
        rows = self.items[kind]
        tbl.setRowCount(len(rows))
        for r, it in enumerate(rows):
            if kind == "project":
                vals = [
                    str(it.get("id","")),
                    it.get("title",""),
                    it.get("author_display",""),
                    it.get("category",""),
                    it.get("context","") or "",
                    str(it.get("images_count") or 0),
                    it.get("status",""),
                    it.get("posted_ago",""),
                ]
            else:
                vals = [
                    str(it.get("id","")),
                    it.get("title",""),
                    it.get("category","") or "",   # event type
                    str(it.get("images_count") or 0),
                    it.get("status",""),
                    it.get("posted_ago",""),
                ]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setData(Qt.ItemDataRole.UserRole, it)
                if c == 0:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                tbl.setItem(r, c, item)
        tbl.resizeColumnsToContents()


    def _select_first_available(self):
        k = "project" if self.tabs.currentIndex() == 0 else "competition"
        tbl = self._table(k)
        if tbl.rowCount():
            tbl.selectRow(0)
        else:
            # nothing pending, clear preview
            self.preview.set_item(k, {})
            self._current_row = -1

    # ----- selection + preview -----
    def _on_tab_changed(self, _idx: int):
        self._select_first_available()

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

    # ----- approve/decline actions -----
    def _approve_current(self): self._update_current_status("approved")
    def _decline_current(self): self._update_current_status("declined")

    def _update_current_status(self, new_status: str):
        kind = "project" if self.tabs.currentIndex() == 0 else "competition"
        tbl = self._table(kind)
        if self._current_row < 0 or self._current_row >= tbl.rowCount():
            return
        it = tbl.item(self._current_row, 0).data(Qt.ItemDataRole.UserRole) or self.items[kind][self._current_row]
        pk = it.get("projects_id") or it.get("competition_id") or it.get("id")
        if not pk:
            QMessageBox.warning(self, "Missing ID", "Cannot update without an ID.")
            return
        try:
            self._apply_status(kind, int(pk), new_status)
        except Exception as e:
            QMessageBox.critical(self, "DB Error", str(e))
            return
        # reload list and clear preview if nothing left
        self._reload()
        tbl = self._table(kind)
        if tbl.rowCount() == 0:
            self.preview.set_item(kind, {})

    @staticmethod
    def _apply_status(kind: str, pk: int, status: str):
        # direct, minimal SQL to avoid touching helpers
        path = str(db_path())
        con = sqlite3.connect(path)
        con.execute("PRAGMA foreign_keys = ON")
        cur = con.cursor()
        if kind == "project":
            cur.execute("UPDATE projects SET status=? WHERE projects_id=?", (status, pk))
        else:
            cur.execute("UPDATE competitions SET status=? WHERE competition_id=?", (status, pk))
        con.commit()
        con.close()


# ----- quick manual run -----
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = ShowcaseAdminApprovalPage()
    w.resize(1100, 680)
    w.show()
    sys.exit(app.exec())
