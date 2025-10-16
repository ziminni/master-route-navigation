# views/AnnouncementAdmin.py
from __future__ import annotations

import os, sys, importlib.util
from pathlib import Path
from datetime import datetime
from typing import List, Dict

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QLineEdit, QHBoxLayout, QVBoxLayout,
    QScrollArea, QFrame, QGridLayout, QSizePolicy, QSpacerItem, QMessageBox, QStackedWidget, QMenu
)

# ----- preview dialogs (works when run as script or package) -----
HERE = Path(__file__).resolve().parent

import types
DB_DIR = HERE / "db"
if DB_DIR.exists():
    # provide a namespace package "db"
    if "db" not in sys.modules:
        pkg = types.ModuleType("db")
        pkg.__path__ = [str(DB_DIR)]
        sys.modules["db"] = pkg
    # also allow plain "from AnnouncementDBHelper import ..."
    if str(DB_DIR) not in sys.path:
        sys.path.insert(0, str(DB_DIR))

# --- import shim for modules that import Approval absolutely ---
def _ensure_local_mod(mod_name: str, file_name: str) -> None:
    if mod_name in sys.modules:
        return
    p = HERE / file_name
    if p.exists():
        spec = importlib.util.spec_from_file_location(mod_name, str(p))
        mod = importlib.util.module_from_spec(spec)  # type: ignore
        assert spec and spec.loader
        spec.loader.exec_module(mod)  # type: ignore
        sys.modules[mod_name] = mod

_ensure_local_mod("AnnouncementAdminApproval", "AnnouncementAdminApproval.py")

# make "import AnnouncementAdminApproval" work even if callers use absolute import
_ensure_local_mod("AnnouncementAdminApproval", "AnnouncementAdminApproval.py")


try:
    from .AnnouncementPreviewC import AnnouncementPreviewCardDialog
    from .AnnouncementPreviewR import AnnouncementPreviewReminderDialog
except Exception:
    def _load_by_path(mod_name: str, file_path: Path):
        spec = importlib.util.spec_from_file_location(mod_name, str(file_path))
        mod = importlib.util.module_from_spec(spec)  # type: ignore
        assert spec and spec.loader
        spec.loader.exec_module(mod)  # type: ignore
        return mod
    C = _load_by_path("AnnouncementPreviewC", HERE / "AnnouncementPreviewC.py")
    R = _load_by_path("AnnouncementPreviewR", HERE / "AnnouncementPreviewR.py")
    AnnouncementPreviewCardDialog = C.AnnouncementPreviewCardDialog
    AnnouncementPreviewReminderDialog = R.AnnouncementPreviewReminderDialog

# ----- DB helpers (robust) -----
try:
    from db.AnnouncementDBHelper import init_db, get_announcements, get_reminders, delete_announcement
except Exception:
    DB_DIR = HERE / "db"
    sys.path.insert(0, str(DB_DIR))
    from AnnouncementDBHelper import init_db, get_announcements, get_reminders, delete_announcement  # type: ignore

try:
    from .AnnouncementAdminEditA import AnnouncementAdminEditAPage
except Exception:
    from AnnouncementAdminEditA import AnnouncementAdminEditAPage 
try:
    from .AnnouncementAdminEditR import AnnouncementAdminEditRPage, delete_reminder
except Exception:
    from AnnouncementAdminEditR import AnnouncementAdminEditRPage, delete_reminder  # type: ignore

try:
    from .AnnouncementAdminReminder import AnnouncementAdminReminderPage
except Exception:
    from AnnouncementAdminReminder import AnnouncementAdminReminderPage  # type: ignore
try:
    from .AnnouncementAdminAnnouncement import AnnouncementAdminAnnouncementPage
except Exception:
    from AnnouncementAdminAnnouncement import AnnouncementAdminAnnouncementPage  # type: ignore


# ----- subview (approval) -----
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .AnnouncementAdminApproval import AnnouncementAdminApprovalPage  # editor-only hint
  
# ----- theme -----
GREEN = "#146c43"; TEXT = "#1f2937"; BG = "#f3f4f6"; BORDER = "#e5e7eb"

# ----- asset helpers -----
def _project_root() -> Path:
    for up in range(0, 7):
        base = HERE.parents[up] if up else HERE
        if (base / "assets").exists(): return base
    return Path.cwd()

def _resolve_path(p: str | None) -> str | None:
    if not p: return None
    pp = Path(p)
    if pp.is_file(): return str(pp)
    cand = _project_root() / p
    return str(cand) if cand.is_file() else None

# ----- misc -----
def _relative_time(ts: str | None) -> str:
    if not ts: return "now"
    try:
        dt = datetime.fromisoformat(ts.replace("Z",""))
        secs = max(0, int((datetime.utcnow() - dt).total_seconds()))
    except Exception:
        return ts
    if secs < 60: return f"{secs}s"
    mins = secs // 60
    if mins < 60: return f"{mins}m"
    hrs = mins // 60
    if hrs < 24: return f"{hrs}h"
    return f"{hrs//24}d"

def _chip(text: str) -> QLabel:
    w = QLabel(text)
    w.setStyleSheet(f"QLabel{{background:{BG};border:1px solid {BORDER};border-radius:10px;padding:2px 8px;font:9pt;color:{TEXT};}}")
    return w

def _icon_btn(text: str, tooltip: str, cb) -> QPushButton:
    b = QPushButton(text); b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setToolTip(tooltip); b.setFixedSize(28, 28)
    b.setStyleSheet(f"QPushButton{{background:rgba(255,255,255,0.95);border:1px solid {BORDER};border-radius:14px;font:12pt;color:{TEXT};}}"
                    "QPushButton:hover{background:#ffffff;}")
    b.clicked.connect(cb); return b

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

        # session context
        self.username = username or ""
        self.roles = roles or []
        self.primary_role = primary_role or ""
        self.token = token or ""
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

        self.setWindowTitle("Announcements")
        self.setMinimumSize(1100, 680)
        self._build_ui()
        self.reload()

    def _build_ui(self) -> None:
        # Outer holds a stack so we can navigate without new windows
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)
        self.stack = QStackedWidget(self)
        outer.addWidget(self.stack)

        # ---- pageMain (existing admin list UI) ----
        self.pageMain = QWidget()
        rootV = QVBoxLayout(self.pageMain)
        rootV.setContentsMargins(12, 12, 12, 12)
        rootV.setSpacing(12)

        # ---------- Global top bar ----------
        topbar = QHBoxLayout()
        topbar.setSpacing(10)

        self.btnMenu = QPushButton("☰")
        self.btnMenu.setFixedSize(36, 36)
        self.btnMenu.setStyleSheet(f"QPushButton{{background:#fff;border:1px solid {BORDER};border-radius:10px;}}")

        title = QLabel("Announcements")
        title.setStyleSheet(f"color:{GREEN};font:700 22pt;")
        title.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        def _pill(btn: QPushButton) -> QPushButton:
            btn.setFixedHeight(36)
            btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            btn.setStyleSheet(f"QPushButton{{background:{GREEN};color:white;padding:0 18px;border-radius:10px;font:600 11pt;}}"
                              "QPushButton:hover{opacity:0.96;}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            return btn

        self.btnRequests = _pill(QPushButton("Requests"))
        self.btnRequests.clicked.connect(self._on_requests)

        self.btnAddAnnouncement = _pill(QPushButton("＋  Announcement"))
        self.btnAddAnnouncement.clicked.connect(self._on_add_announcement)

        self.btnAddReminder = _pill(QPushButton("＋  Reminders"))
        self.btnAddReminder.clicked.connect(self._on_add_reminder)

        self.searchBar = QLineEdit()
        self.searchBar.setPlaceholderText("Search")
        self.searchBar.setClearButtonEnabled(True)
        self.searchBar.returnPressed.connect(self.reload)
        self.searchBar.setFixedHeight(36)
        self.searchBar.setFixedWidth(360)
        icon_path = _project_root() / "assets/icons/icon_search.png"
        if icon_path.is_file():
            self.searchBar.addAction(QIcon(str(icon_path)), QLineEdit.ActionPosition.LeadingPosition)
        self.searchBar.setStyleSheet(
            f"QLineEdit{{background:#fff;border:1px solid {BORDER};border-radius:18px;"
            f"padding-left:30px;padding-right:14px;font:10.5pt;color:{TEXT};}}"
        )

        topbar.addWidget(self.btnMenu, 0)
        topbar.addWidget(title, 0)
        topbar.addSpacing(10)
        topbar.addWidget(self.btnRequests, 0)
        topbar.addWidget(self.btnAddAnnouncement, 0)
        topbar.addWidget(self.btnAddReminder, 0)
        topbar.addStretch(1)
        topbar.addWidget(self.searchBar, 0)
        rootV.addLayout(topbar)

        # ---------- Content row: announcements grid + reminders list ----------
        row = QHBoxLayout()
        row.setSpacing(12)

        leftWrap = QWidget()
        leftWrap.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
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
        leftV.addWidget(leftScroll, 1)

        rightPane = QWidget()
        rightPane.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        rightPane.setFixedWidth(380)
        rightCol = QVBoxLayout(rightPane)
        rightCol.setSpacing(0)
        rightCol.setContentsMargins(0, 0, 0, 0)

        self.reminderHost = QWidget()
        self.reminderList = QVBoxLayout(self.reminderHost)
        self.reminderList.setContentsMargins(0, 0, 0, 0)
        self.reminderList.setSpacing(10)
        self.reminderList.addStretch(1)

        rightScroll = QScrollArea()
        rightScroll.setWidget(self.reminderHost)
        rightScroll.setWidgetResizable(True)
        rightScroll.setFixedWidth(360)
        rightScroll.setStyleSheet("QScrollArea{border:none;}")

        rightCol.addWidget(rightScroll, 1)

        row.addWidget(leftWrap, 1)
        row.addWidget(rightPane, 0)

        rootV.addLayout(row, 1)

        # add pageMain to stack
        self.stack.addWidget(self.pageMain)

    def _open_add_reminder(self) -> None:
        page = AnnouncementAdminReminderPage(parent=self)
        page.back_requested.connect(lambda: self._close_add_reminder(page))
        page.published.connect(lambda _rid: self.reload())
        page.request_close.connect(lambda: self._close_add_reminder(page))  # legacy
        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)

    def _close_add_reminder(self, page: QWidget) -> None:
        self.stack.setCurrentWidget(self.pageMain)
        self.stack.removeWidget(page)
        page.deleteLater()

    def _open_add_announcement(self) -> None:
        page = AnnouncementAdminAnnouncementPage(parent=self)
        page.back_requested.connect(lambda: self._close_add_announcement(page))
        page.published.connect(lambda _aid: self.reload())
        # legacy signal support
        page.request_close.connect(lambda: self._close_add_announcement(page))
        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)

    def _close_add_announcement(self, page: QWidget) -> None:
        self.stack.setCurrentWidget(self.pageMain)
        self.stack.removeWidget(page)
        page.deleteLater()


    def _open_edit_r(self, rid: int) -> None:
        page = AnnouncementAdminEditRPage(rid, parent=self)
        page.back_requested.connect(lambda: self._close_edit_r(page))
        page.saved.connect(self.reload)
        page.deleted.connect(self.reload)
        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)

    def _close_edit_r(self, page: QWidget) -> None:
        self.stack.setCurrentWidget(self.pageMain)
        self.stack.removeWidget(page)
        page.deleteLater()


    def _open_edit_a(self, aid: int) -> None:
        # create page, wire signals, push to stack
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


    # data
    def reload(self) -> None:
        q = self.searchBar.text().strip()
        self._ann_items = get_announcements(limit=30, q=q)
        self._rem_items = get_reminders(limit=30, q=q)
        self._paint_announcements(self._ann_items)
        self._paint_reminders(self._rem_items)

    # painters
    def _paint_announcements(self, items: List[Dict]) -> None:
        while self.grid.count():
            it = self.grid.takeAt(0); w = it.widget()
            if w: w.setParent(None)
        cols = 2
        for i, it in enumerate(items):
            r, c = divmod(i, cols)
            self.grid.addWidget(self._build_announcement_card(it, i), r, c)
        self.grid.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding),
                          (len(items)+cols-1)//cols + 1, 0, 1, cols)

    def _paint_reminders(self, items: List[Dict]) -> None:
        while self.reminderList.count() > 1:
            it = self.reminderList.takeAt(0); w = it.widget()
            if w: w.setParent(None)
        for i, it in enumerate(items):
            self.reminderList.insertWidget(self.reminderList.count()-1, self._build_reminder_card(it, i))

    # builders
    def _build_announcement_card(self, item: Dict, idx: int) -> QWidget:
        card = QFrame(); card.setObjectName("annCard")
        card.setStyleSheet(f"#annCard{{background:#fff;border:1px solid {BORDER};border-radius:14px;}}")
        card.setMaximumWidth(540); card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        v = QVBoxLayout(card); v.setContentsMargins(0,0,0,0); v.setSpacing(0)

        img = QLabel(card)
        img.setFixedHeight(220); img.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        img.setAlignment(Qt.AlignmentFlag.AlignCenter); img.setScaledContents(True)
        p = _resolve_path(item.get("file_path"))
        if p: img.setPixmap(QPixmap(p))
        v.addWidget(img)

        def _open(_e=None, i=idx):
            dlg = AnnouncementPreviewCardDialog(self._ann_items, start_index=i, parent=self)
            dlg.exec()
        card.mouseReleaseEvent = _open; img.mouseReleaseEvent = _open

        pill = QLabel(img)
        pill.setText(f"By {item.get('author_name','Unknown')} • {_relative_time(item.get('publish_at') or item.get('created_at'))}")
        pill.setStyleSheet(f"QLabel{{background:rgba(255,255,255,0.92);border-radius:12px;padding:4px 10px;font:10pt;color:{TEXT};border:1px solid {BORDER};}}")
        pill.adjustSize(); pill.move(10,10); pill.raise_()

        btnBar = QWidget(img); hb = QHBoxLayout(btnBar); hb.setContentsMargins(0,0,0,0); hb.setSpacing(6)

        def _show_menu():
            aid = int(item.get("announcement_id"))
            btn = _icon_btn("⋯", "More", lambda: None)
            menu = QMenu(btn)
            act_edit = menu.addAction("Edit")
            act_del  = menu.addAction("Delete")
            def _on_triggered(a):
                if a == act_edit:
                    self._open_edit_a(aid)
                elif a == act_del:
                    if QMessageBox.question(
                        self, "Confirm delete", f"Delete announcement #{aid}?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    ) == QMessageBox.StandardButton.Yes:
                        try:
                            delete_announcement(aid)
                            self.reload()
                        except Exception as e:
                            QMessageBox.critical(self, "Delete failed", str(e))
            menu.triggered.connect(_on_triggered)
            btn.clicked.disconnect()
            btn.clicked.connect(lambda: menu.exec(btn.mapToGlobal(btn.rect().bottomRight())))
            hb.addWidget(btn)

        _show_menu()
        btnBar.adjustSize(); btnBar.move(img.width()-btnBar.sizeHint().width()-10, 10); btnBar.raise_()
        img.resizeEvent = lambda ev, w=img, bar=btnBar: bar.move(w.width()-bar.sizeHint().width()-10, 10)

        body = QWidget(card); b = QVBoxLayout(body); b.setContentsMargins(14,16,14,14); b.setSpacing(8)
        title = QLabel(item.get("title","")); title.setStyleSheet(f"font:700 16pt;color:{GREEN};"); b.addWidget(title)
        preview = QLabel((item.get("body") or "").strip()); preview.setWordWrap(True)
        preview.setStyleSheet(f"color:{TEXT};font:10.5pt;"); b.addWidget(preview)

        metaW = QWidget(body); meta = QHBoxLayout(metaW); meta.setContentsMargins(0,0,0,0); meta.setSpacing(6)
        loc = item.get("location");  vis = item.get("visibility")
        if loc: meta.addWidget(_chip(loc))
        if vis: meta.addWidget(_chip(vis))
        try: pr = int(item.get("priority",0))
        except Exception: pr = 0
        if pr>0: meta.addWidget(_chip(f"priority {pr}"))
        try: pinned = int(item.get("is_pinned",0))
        except Exception: pinned = 0
        if pinned==1: meta.addWidget(_chip("pinned"))
        for t in [t for t in (item.get("tags_csv") or "").split(",") if t][:3]:
            meta.addWidget(_chip(f"#{t}"))
        try: dc = int(item.get("doc_count",0))
        except Exception: dc = 0
        if dc>0: meta.addWidget(_chip(f"{dc} attachment(s)"))
        meta.addStretch(1); b.addWidget(metaW)

        v.addWidget(body); return card

    def _build_reminder_card(self, item: Dict, idx: int) -> QWidget:
        card = QFrame(); card.setObjectName("remCard")
        card.setStyleSheet(f"#remCard{{background:#fff;border:1px solid {BORDER};border-radius:12px;}}")
        v = QVBoxLayout(card); v.setContentsMargins(12,10,12,12); v.setSpacing(6)

        header = QHBoxLayout(); header.setSpacing(6)
        header.addWidget(_chip(f"By {item.get('author_name','Unknown')} • {_relative_time(item.get('created_at'))}"))
        header.addStretch(1)
        btn_more = _icon_btn("⋯", "More", lambda: None)
        menu = QMenu(btn_more)
        act_edit = menu.addAction("Edit")
        act_del  = menu.addAction("Delete")

        def _trigger(a, rid=int(item.get("reminder_id","0") or 0)):
            if a == act_edit:
                self._open_edit_r(rid)
            elif a == act_del:
                if QMessageBox.question(
                    self, "Confirm delete", f"Delete reminder #{rid}?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                ) == QMessageBox.StandardButton.Yes:
                    try:
                        delete_reminder(rid)
                        self.reload()
                    except Exception as e:
                        QMessageBox.critical(self, "Delete failed", str(e))

        menu.triggered.connect(_trigger)
        btn_more.clicked.disconnect()
        btn_more.clicked.connect(lambda: menu.exec(btn_more.mapToGlobal(btn_more.rect().bottomRight())))
        header.addWidget(btn_more)
        v.addLayout(header)

        title = QLabel(item.get("title","")); title.setStyleSheet(f"font:700 12.5pt;color:{TEXT};"); v.addWidget(title)
        body  = QLabel((item.get("body") or "").strip()); body.setWordWrap(True); body.setStyleSheet(f"color:{TEXT};")
        v.addWidget(body)

        def _open(_e=None, i=idx):
            dlg = AnnouncementPreviewReminderDialog(self._rem_items[i], parent=self)
            dlg.exec()
        card.mouseReleaseEvent = _open

        return card

    # stubs
    def _on_add_announcement(self) -> None:
        self._open_add_announcement()
            
    def _on_add_reminder(self) -> None:
        self._open_add_reminder()

    def _on_requests(self) -> None:
        # lazy import to avoid package import errors
        try:
            from .AnnouncementAdminApproval import AnnouncementAdminApprovalPage  # type: ignore
        except Exception:
            ap = HERE / "AnnouncementAdminApproval.py"
            if not ap.exists():
                QMessageBox.critical(self, "Missing file", f"Not found: {ap}")
                return
            spec = importlib.util.spec_from_file_location("AnnouncementAdminApproval", str(ap))
            mod = importlib.util.module_from_spec(spec)  # type: ignore
            assert spec and spec.loader
            spec.loader.exec_module(mod)  # type: ignore
            AnnouncementAdminApprovalPage = getattr(mod, "AnnouncementAdminApprovalPage")

        if not hasattr(self, "pageApproval"):
            self.pageApproval = AnnouncementAdminApprovalPage(self)
            self.pageApproval.back_requested.connect(self._close_requests)
            self.stack.addWidget(self.pageApproval)

        self.stack.setCurrentWidget(self.pageApproval)


    def _close_requests(self) -> None:
        # Return to main page and remove the approval page from the stack
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
