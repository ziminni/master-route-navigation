# views/Showcase/ShowcaseAdminApproval.py
from __future__ import annotations
import os
from typing import List, Dict, Optional

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, QRectF, QSize, QUrl
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QPixmap, QIcon, QFont, QDesktopServices
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QTabWidget, QTableWidget,
    QTableWidgetItem, QPushButton, QTextBrowser, QSizePolicy, QMessageBox
)

# ---------- Theme ----------
GREEN = "#146c43"
TEXT = "#1f2937"
MUTED = "#6b7280"
MUTED_DARK = "#4b5563"
TAG_BLUE = "#0369a1"
CATEGORY_COLOR = "#4f46e5"   # indigo
CONTEXT_COLOR = "#0f766e"    # teal
IMAGES_COLOR = "#b45309"     # amber
BG = "#f3f4f6"
CARD_BG = "#ffffff"
BORDER = "#e5e7eb"

# ---------- DB wiring ----------
try:
    from .db.ShowcaseDBHelper import (
        list_showcase_cards,
        list_achievements,
        set_project_status,
        set_competition_status,
    )
    from .db.ShowcaseDBInitialize import ensure_bootstrap
except Exception:
    from db.ShowcaseDBHelper import (
        list_showcase_cards,
        list_achievements,
        set_project_status,
        set_competition_status,
    )
    from db.ShowcaseDBInitialize import ensure_bootstrap


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

def _placeholder(side: int, label: str = "image") -> QPixmap:
    side = max(side, 1)
    pm = QPixmap(side, side)
    pm.fill(QColor("#d1d5db"))
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(QColor("#9ca3af"))
    p.setBrush(QColor("#e5e7eb"))
    p.drawRoundedRect(0, 0, side, side, 18, 18)
    f = QFont()
    f.setPointSize(12)
    f.setBold(True)
    p.setFont(f)
    p.setPen(QColor("#6b7280"))
    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, label.upper())
    p.end()
    return pm

def _load_image(fname: Optional[str], w: int, h: int) -> QPixmap:
    """
    Load an image and return a square pixmap (1:1) cropped and zoomed to fill.
    """
    side = max(1, min(w, h))
    if fname:
        p = fname if os.path.isabs(fname) else os.path.join(IMG_DIR, fname)
        if os.path.isfile(p):
            pm = QPixmap(p)
            if not pm.isNull():
                pm = pm.scaled(
                    side,
                    side,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
                if pm.width() != side or pm.height() != side:
                    x = max((pm.width() - side) // 2, 0)
                    y = max((pm.height() - side) // 2, 0)
                    pm = pm.copy(x, y, side, side)
                return pm
    return _placeholder(side)


# ---------- Small rounded image widget (square) ----------
class RoundedImage(QWidget):
    def __init__(self, radius: int = 18, parent: QWidget | None = None):
        super().__init__(parent)
        self.radius = float(radius)
        self._pm = QPixmap()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(260)

    def setPixmap(self, pm: QPixmap):
        self._pm = pm
        self.update()

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # square drawing area centred inside widget
        w = self.width()
        h = self.height()
        side = max(1, min(w, h))
        x = (w - side) / 2.0
        y = (h - side) / 2.0
        r = QRectF(x + 0.5, y + 0.5, side - 1.0, side - 1.0)

        path = QPainterPath()
        path.addRoundedRect(r, self.radius, self.radius)
        p.setClipPath(path)

        if not self._pm.isNull():
            src = QRectF(self._pm.rect())
            p.drawPixmap(r, self._pm, src)
        else:
            p.fillRect(r, QColor("#d1d5db"))

        p.setClipping(False)
        p.setPen(QColor(BORDER))
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
            QLabel.metaStrong {{ color:{MUTED_DARK}; font-size:12px; }}
            QLabel.chip  {{ background:#ecfdf5; color:{GREEN}; border:1px solid #c7f0df;
                            border-radius:10px; padding:2px 8px; font-size:11px; }}
            QPushButton[kind="pill"] {{
                background:{GREEN}; color:white; border:none; border-radius:14px; padding:8px 14px;
            }}
            QPushButton[kind="pill"]:disabled {{ background:#9ca3af; }}
            QPushButton[kind="nav"] {{
                background:white;
                color:{TEXT};
                border:1px solid #d1d5db;
                border-radius:14px;
                padding:4px 10px;
            }}
            QPushButton[kind="nav"]:hover {{
                background:#f3f4f6;
            }}
        """)

        v = QVBoxLayout(self)
        v.setContentsMargins(12, 12, 12, 12)
        v.setSpacing(8)

        # --- image (square) ---
        self.image = RoundedImage(18, self)
        v.addWidget(self.image, 0)

        # --- image nav row (always visible) ---
        nav = QHBoxLayout()
        nav.setSpacing(6)

        self.prev_btn = QPushButton()
        self.prev_btn.setProperty("kind", "nav")
        self.prev_btn.setIcon(_icon("icon_chevron_left.png"))
        self.prev_btn.setIconSize(QSize(18, 18))

        self.img_counter = QLabel("1 / 1")
        self.img_counter.setStyleSheet("color:#4b5563; font-size:11px;")

        self.next_btn = QPushButton()
        self.next_btn.setProperty("kind", "nav")
        self.next_btn.setIcon(_icon("icon_chevron_right.png"))
        self.next_btn.setIconSize(QSize(18, 18))

        self.prev_btn.clicked.connect(self._prev)
        self.next_btn.clicked.connect(self._next)

        nav.addWidget(self.prev_btn)
        nav.addStretch(1)
        nav.addWidget(self.img_counter)
        nav.addStretch(1)
        nav.addWidget(self.next_btn)
        v.addLayout(nav)

        # --- title + status chip ---
        self.title = QLabel("Select a row")
        self.title.setProperty("class", "title")
        self.status_chip = QLabel("")
        self.status_chip.setProperty("class", "chip")
        head = QHBoxLayout()
        head.addWidget(self.title, 1)
        head.addWidget(self.status_chip, 0)
        v.addLayout(head)

        # meta line 1: author + time (rich text)
        self.meta_line1 = QLabel("")
        self.meta_line1.setProperty("class", "metaStrong")
        self.meta_line1.setTextFormat(Qt.TextFormat.RichText)
        v.addWidget(self.meta_line1)

        # meta line 2: category + context + images (rich text, vertical layout)
        self.meta_line2 = QLabel("")
        self.meta_line2.setProperty("class", "meta")
        self.meta_line2.setTextFormat(Qt.TextFormat.RichText)
        v.addWidget(self.meta_line2)

        # tags + external link button
        tags_row = QHBoxLayout()
        tags_row.setSpacing(6)

        self.tags_label = QLabel("")
        self.tags_label.setStyleSheet(f"color:{TAG_BLUE}; font-size:12px;")

        self.link_btn = QPushButton("Open link")
        self.link_btn.setProperty("kind", "pill")
        self.link_btn.setVisible(False)
        self.link_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.link_btn.clicked.connect(self._open_link)

        tags_row.addWidget(self.tags_label, 1)
        tags_row.addWidget(self.link_btn, 0)
        v.addLayout(tags_row)

        # body + achievements
        self.body = QTextBrowser()
        self.body.setOpenExternalLinks(True)
        self.body.setStyleSheet(
            f"QTextBrowser{{border:1px solid {BORDER}; background:white; "
            f"border-radius:12px; padding:10px;}}"
        )
        v.addWidget(self.body, 1)

        # actions
        act = QHBoxLayout()
        act.setSpacing(8)
        self.btnApprove = QPushButton("Approve")
        self.btnApprove.setProperty("kind", "pill")
        self.btnDecline = QPushButton("Decline")
        self.btnDecline.setProperty("kind", "pill")
        self.btnApprove.clicked.connect(self.approved.emit)
        self.btnDecline.clicked.connect(self.declined.emit)
        act.addStretch(1)
        act.addWidget(self.btnDecline)
        act.addWidget(self.btnApprove)
        v.addLayout(act)

        self._refresh_ui()

    # --- public API ---
    def set_item(self, kind: str, it: Dict):
        self.kind = kind
        self.item = it or {}
        imgs = self.item.get("images") or ([self.item.get("image")] if self.item.get("image") else [])
        self.imgs = imgs if imgs else ["1.jpg"]
        self.img_idx = 0
        self._refresh_ui()

    # --- internal UI refresh ---
    def _refresh_ui(self):
        it = self.item or {}

        # title + status
        self.title.setText(it.get("title", "") or "Select a row")
        st = it.get("status") or "pending"
        self.status_chip.setText(st)
        self.status_chip.setVisible(bool(st))

        # meta line 1: author + time (with emphasis)
        author = it.get("author_display")
        ago = it.get("posted_ago")
        if author or ago:
            pieces: List[str] = []
            if author:
                pieces.append(
                    f"<span style='color:{MUTED};'>by </span>"
                    f"<span style='color:{GREEN}; font-weight:600;'>{author}</span>"
                )
            if ago:
                if pieces:
                    pieces.append(f"<span style='color:{MUTED};'> • </span>")
                pieces.append(
                    f"<span style='color:{MUTED_DARK}; font-style:italic;'>{ago}</span>"
                )
            self.meta_line1.setText("".join(pieces))
        else:
            self.meta_line1.clear()

        # meta line 2: vertical lines
        category = it.get("category")
        context = it.get("context")
        nimg = it.get("images_count") if isinstance(it.get("images_count"), int) else None
        segs: List[str] = []
        if category:
            segs.append(
                f"<span style='color:{MUTED}; font-weight:600;'>Category:</span> "
                f"<span style='color:{CATEGORY_COLOR}; font-weight:600;'>{category}</span>"
            )
        if context:
            segs.append(
                f"<span style='color:{MUTED}; font-weight:600;'>Context:</span> "
                f"<span style='color:{CONTEXT_COLOR}; font-weight:600;'>{context}</span>"
            )
        if nimg is not None:
            segs.append(
                f"<span style='color:{MUTED}; font-weight:600;'>Images:</span> "
                f"<span style='color:{IMAGES_COLOR}; font-weight:600;'>{nimg}</span>"
            )
        self.meta_line2.setText("<br>".join(segs))

        # tags (blue)
        tags = it.get("tags") or []
        if tags:
            self.tags_label.setText("Tags: " + ", ".join(tags))
        else:
            self.tags_label.setText("Tags: —")

        # external link button
        ext = it.get("external_url")
        self.link_btn.setVisible(bool(ext))

        # description + optional achievements for competitions
        body_text = (it.get("long_text") or it.get("blurb") or "").strip()
        if not body_text:
            body_text = "No description provided."

        desc_html = (
            f"<p style='color:{MUTED}; font-weight:bold; margin-bottom:4px;'>Description</p>"
            f"<p style='color:{TEXT}; margin-top:0px;'>{body_text}</p>"
        )

        ach_html = ""
        if self.kind == "competition":
            achievements = it.get("achievements") or []
            if achievements:
                ach_html = (
                    "<hr style='margin:12px 0; border:0; border-top:1px solid #e5e7eb;'>"
                    f"<p style='color:{MUTED}; font-weight:bold; margin-bottom:6px;'>"
                    "Featured Achievements</p>"
                )
                for idx, a in enumerate(achievements, start=1):
                    title = a.get("achievement_title") or "Untitled"
                    recog = a.get("result_recognition") or "—"
                    awards = a.get("specific_awards") or "—"
                    notes = a.get("notes") or ""
                    awarded = a.get("awarded_at") or "—"
                    ach_html += (
                        "<div style='margin-bottom:10px; padding:8px 10px; "
                        "border-radius:8px; background:#f9fafb;'>"
                        f"<div style='font-weight:600; color:{MUTED_DARK};'>"
                        f"Achievement #{idx}: {title}</div>"
                        f"<div style='font-size:12px; color:{MUTED};'>"
                        f"Result: <span style='color:{GREEN}; font-weight:600;'>{recog}</span></div>"
                    )
                    if awards and awards != "—":
                        ach_html += (
                            f"<div style='font-size:12px; color:{MUTED};'>"
                            f"Specific awards: <span style='color:{CATEGORY_COLOR};'>{awards}</span></div>"
                        )
                    if notes:
                        ach_html +=(
                            f"<div style='font-size:12px; color:{MUTED};'>"
                            f"Notes: <span style='color:{TEXT};'>{notes}</span></div>"
                        )
                    ach_html += (
                        f"<div style='font-size:12px; color:{MUTED};'>"
                        f"Awarded: <span style='font-style:italic;'>{awarded}</span></div>"
                        "</div>"
                    )

        html = f"<div style='font-size:13px; line-height:1.5'>{desc_html}{ach_html}</div>"
        self.body.setHtml(html)

        # image + counter, nav always visible (disabled when single)
        count = max(len(self.imgs), 1)
        self.img_counter.setText(f"{min(self.img_idx + 1, count)} / {count}")
        disable = count <= 1
        self.prev_btn.setDisabled(disable)
        self.next_btn.setDisabled(disable)

        pm = _load_image(
            self.imgs[self.img_idx] if self.imgs else None,
            self.image.width() or 400,
            self.image.height() or 400,
        )
        self.image.setPixmap(pm)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._refresh_ui()

    # --- image nav handlers ---
    def _prev(self):
        if len(self.imgs) <= 1:
            return
        self.img_idx = (self.img_idx - 1) % len(self.imgs)
        self._refresh_ui()

    def _next(self):
        if len(self.imgs) <= 1:
            return
        self.img_idx = (self.img_idx + 1) % len(self.imgs)
        self._refresh_ui()

    # --- external link handler ---
    def _open_link(self):
        if not self.item:
            return
        url = self.item.get("external_url")
        if not url:
            return
        QDesktopServices.openUrl(QUrl(url))


# ---------- Approval page ----------
class ShowcaseAdminApprovalPage(QWidget):
    """
    Two tabs: Projects and Competitions.
    Left: table of pending items.
    Right: preview pane with Approve/Decline.

    When embedded inside a parent stack, use `back_requested` to go back.
    """
    back_requested = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # only schema + seed, no raw SQL here
        ensure_bootstrap(seed=False)

        self.setStyleSheet(f"""
            QWidget {{ background:{BG}; color:{TEXT}; }}
            QTableWidget {{
                background:white;
                border:1px solid {BORDER};
                border-radius:10px;
                gridline-color:{BORDER};
                selection-background-color:#ecfdf5;
                selection-color:{GREEN};
                alternate-background-color:#f9fafb;
            }}
            QHeaderView::section {{
                background:{CARD_BG};
                padding:6px;
                border:1px solid {BORDER};
            }}
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
        f = title.font()
        f.setPointSize(16)
        f.setBold(True)
        title.setFont(f)
        title.setStyleSheet(f"color:{GREEN}")
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
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)

        hint = QLabel("Pending only")
        hint.setProperty("class", "hint")
        v.addWidget(hint, 0)

        tbl = QTableWidget()
        tbl.setObjectName(f"tbl_{kind}")
        if kind == "project":
            tbl.setColumnCount(7)
            tbl.setHorizontalHeaderLabels([
                "Title", "Author", "Category", "Context", "Images", "Status", "Posted"
            ])
        else:
            tbl.setColumnCount(5)
            tbl.setHorizontalHeaderLabels([
                "Title", "Event Type", "Images", "Status", "Posted"
            ])
        tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tbl.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.horizontalHeader().setStretchLastSection(True)
        tbl.verticalHeader().setVisible(False)
        tbl.setAlternatingRowColors(True)

        tbl.itemSelectionChanged.connect(lambda k=kind, t=tbl: self._on_row_selected(k, t))
        tbl.cellClicked.connect(lambda _r, _c, k=kind, t=tbl: self._on_row_selected(k, t))

        v.addWidget(tbl, 1)
        return w

    def _go_back(self):
        # reset preview then tell parent to go back in its stack
        k = "project" if self.tabs.currentIndex() == 0 else "competition"
        self.preview.set_item(k, {})
        self.back_requested.emit()

        # if running standalone inside a modal QDialog, also close that dialog
        from PyQt6.QtWidgets import QDialog
        host = self.window()
        if isinstance(host, QDialog):
            host.close()

    def _table(self, kind: str) -> QTableWidget:
        return self._proj_tab.findChild(QTableWidget, "tbl_project") if kind == "project" \
            else self._comp_tab.findChild(QTableWidget, "tbl_competition")

    # ----- data loading -----
    def _reload(self):
        for kind in ("project", "competition"):
            self.items[kind] = list_showcase_cards(
                kind=kind,
                q=None,
                status="pending",
                limit=200,
                offset=0,
            )
            self._fill_table(kind)
        self._select_first_available()

    def _fill_table(self, kind: str):
        tbl = self._table(kind)
        rows = self.items[kind]
        tbl.setRowCount(len(rows))
        for r, it in enumerate(rows):
            if kind == "project":
                vals = [
                    it.get("title", ""),
                    it.get("author_display", ""),
                    it.get("category", ""),
                    it.get("context", "") or "",
                    str(it.get("images_count") or 0),
                    (it.get("status") or "").lower(),
                    it.get("posted_ago", ""),
                ]
                status_col = 5
                center_cols = {4}
            else:
                vals = [
                    it.get("title", ""),
                    it.get("category", "") or "",
                    str(it.get("images_count") or 0),
                    (it.get("status") or "").lower(),
                    it.get("posted_ago", ""),
                ]
                status_col = 3
                center_cols = {2}

            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setData(Qt.ItemDataRole.UserRole, it)

                if c == 0:
                    f = item.font()
                    f.setBold(True)
                    item.setFont(f)

                if c in center_cols:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if c == status_col:
                    text = v.upper()
                    item.setText(text)
                    if v == "pending":
                        item.setForeground(QColor(GREEN))
                    elif v == "approved":
                        item.setForeground(QColor("#166534"))
                    elif v == "declined":
                        item.setForeground(QColor("#b91c1c"))

                tbl.setItem(r, c, item)

        tbl.resizeColumnsToContents()

    def _augment_item(self, kind: str, it: Dict) -> Dict:
        """
        Attach extra data for preview (e.g., achievements for competitions).
        """
        if kind == "competition":
            try:
                cid = it.get("id") or it.get("competition_id")
                if cid:
                    extra = list_achievements(competition_id=int(cid))
                    it = dict(it)
                    it["achievements"] = extra
            except Exception:
                pass
        return it

    def _select_first_available(self):
        k = "project" if self.tabs.currentIndex() == 0 else "competition"
        tbl = self._table(k)
        if tbl.rowCount():
            self._current_row = 0
            tbl.selectRow(0)
            raw = tbl.item(0, 0).data(Qt.ItemDataRole.UserRole) or self.items[k][0]
            it = self._augment_item(k, raw)
            self.preview.set_item(k, it)
        else:
            self.preview.set_item(k, {})
            self._current_row = -1

    # ----- selection + preview -----
    def _on_tab_changed(self, _idx: int):
        self._select_first_available()

    def _on_row_selected(self, kind: str, tbl: QTableWidget):
        row = tbl.currentRow()
        if row < 0 or row >= tbl.rowCount():
            self.preview.set_item(kind, {})
            self._current_row = -1
            return
        raw = tbl.item(row, 0).data(Qt.ItemDataRole.UserRole) or self.items[kind][row]
        it = self._augment_item(kind, raw)
        self._current_row = row
        self.preview.set_item(kind, it)

    # ----- approve/decline actions -----
    def _approve_current(self):
        self._update_current_status("approved")

    def _decline_current(self):
        self._update_current_status("declined")

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
        self._reload()
        tbl = self._table(kind)
        if tbl.rowCount() == 0:
            self.preview.set_item(kind, {})

    @staticmethod
    def _apply_status(kind: str, pk: int, status: str):
        # delegate status updates to DBHelper (no raw SQL here)
        if kind == "project":
            set_project_status(pk, status)
        else:
            set_competition_status(pk, status)


# ----- quick manual run -----
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = ShowcaseAdminApprovalPage()
    w.resize(1100, 680)
    w.show()
    sys.exit(app.exec())
