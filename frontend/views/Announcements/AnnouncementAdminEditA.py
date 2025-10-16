from __future__ import annotations
import os, shutil, sqlite3, time
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, QSize, QDateTime, pyqtSignal
from PyQt6.QtGui  import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QDialog, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame,
    QLineEdit, QTextEdit, QComboBox, QFileDialog, QMessageBox, QSizePolicy, QCheckBox, QDateTimeEdit
)

# ---------- theme ----------
GREEN="#146c43"; TEXT="#1f2937"; MUTED="#6b7280"; BG="#f3f4f6"; BORDER="#e5e7eb"

# ---------- assets ----------
def _find_dir(name: str) -> Path:
    here = Path(__file__).resolve()
    for up in range(0, 7):
        base = here.parents[up] if up else here.parent
        p = base / "assets" / name
        if p.is_dir(): return p
    p = Path(os.getcwd()) / "assets" / name
    p.mkdir(parents=True, exist_ok=True)
    return p

ICON_DIR=_find_dir("icons"); IMG_DIR=_find_dir("images")

def _icon(fname: str) -> QIcon:
    p = ICON_DIR / fname
    return QIcon(str(p)) if p.exists() else QIcon()

def _pm_or_placeholder(w: int, h: int, path: Optional[str]) -> QPixmap:
    def _resolve(pstr: str) -> Optional[Path]:
        p = Path(pstr)
        if p.is_absolute() and p.exists(): return p
        p2 = Path(os.getcwd()) / pstr
        if p2.exists(): return p2
        assets_dir = ICON_DIR.parent
        proj_root = assets_dir.parent
        p3 = proj_root / pstr
        if p3.exists(): return p3
        p4 = IMG_DIR / p.name
        if p4.exists(): return p4
        return None
    if path:
        rp = _resolve(path)
        if rp:
            pm = QPixmap(str(rp))
            if not pm.isNull():
                return pm.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio,
                                 Qt.TransformationMode.SmoothTransformation)
    pm = QPixmap(w, h); pm.fill(Qt.GlobalColor.lightGray)
    return pm

# ---------- DB ----------
try:
    from .db.AnnouncementDBInitialize import db_path
except Exception:
    from db.AnnouncementDBInitialize import db_path

try:
    from .db.AnnouncementDBHelper import (
        get_announcement, list_documents, add_document,
        update_announcement, delete_announcement, set_tags
    )
except Exception:
    from db.AnnouncementDBHelper import (
        get_announcement, list_documents, add_document,
        update_announcement, delete_announcement, set_tags
    )

def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path()))
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sqlite3.Row
    return con

# ---------- dialog ----------
# ---------- page ----------
class AnnouncementAdminEditAPage(QWidget):
    """
    Edit/Delete an announcement and manage its images (documents) inside the same window.
    Emits back_requested when user wants to go back.
    Emits saved/deleted on successful operations so parent can reload.
    """
    back_requested = pyqtSignal()
    saved = pyqtSignal()
    deleted = pyqtSignal()

    def __init__(self, announcement_id: int, parent: QWidget | None = None):
        super().__init__(parent)
        self.announcement_id = int(announcement_id)
        self.docs: List[Dict[str, Any]] = []
        self.doc_index = 0

        self.setObjectName("AnnEdit")
        self.setStyleSheet(f"""
            QWidget#AnnEdit      {{ background:white; border:1px solid {GREEN}; border-radius:12px; }}
            QLabel#title         {{ color:white; font-size:20px; font-weight:700; }}
            QFrame#hdr           {{ background:{GREEN}; border-top-left-radius:12px; border-top-right-radius:12px; }}
            QLabel[role="label"] {{ color:{MUTED}; font-size:12px; }}
            QLineEdit, QTextEdit, QComboBox, QDateTimeEdit {{
                background:white; color:{TEXT}; border:1px solid {BORDER}; border-radius:8px; padding:6px;
            }}
            QCheckBox {{ color:{TEXT}; }}
            QPushButton[kind="pri"]    {{ background:{GREEN}; color:white; border:none; border-radius:8px; padding:8px 14px; }}
            QPushButton[kind="ghost"]  {{ background:transparent; color:{GREEN}; border:1px solid {GREEN}; border-radius:18px; padding:6px 10px; }}
            QPushButton[kind="danger"] {{ background:#dc3545; color:white; border:none; border-radius:8px; padding:8px 14px; }}
            QPushButton#closeBtn {{
                background: transparent; color: white; border: 1px solid white;
                border-radius: 16px; font-size: 18px; font-weight: 700;
                min-width:32px; min-height:32px;
            }}
            QPushButton#closeBtn:hover {{ background: rgba(255,255,255,0.12); }}
        """)

        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        # header
        hdr = QFrame(); hdr.setObjectName("hdr")
        h = QHBoxLayout(hdr); h.setContentsMargins(14,10,10,10)
        title = QLabel("Edit Announcement"); title.setObjectName("title")
        self.closeBtn = QPushButton("←"); self.closeBtn.setObjectName("closeBtn")
        self.closeBtn.setToolTip("Back")
        self.closeBtn.clicked.connect(self.back_requested.emit)
        h.addWidget(title, 0); h.addStretch(1); h.addWidget(self.closeBtn, 0)
        root.addWidget(hdr)

        # content
        row = QHBoxLayout(); row.setContentsMargins(12,12,12,12); row.setSpacing(14)
        root.addLayout(row, 1)

        # left form
        left = QVBoxLayout(); left.setSpacing(8)
        left.addWidget(self._lbl("Title"))
        self.in_title = QLineEdit(); left.addWidget(self.in_title)

        left.addWidget(self._lbl("Body"))
        self.in_body = QTextEdit(); self.in_body.setMinimumHeight(160); left.addWidget(self.in_body)

        # meta row 1
        meta1 = QHBoxLayout()
        col1 = QVBoxLayout()
        col1.addWidget(self._lbl("Location"))
        self.in_location = QLineEdit(); col1.addWidget(self.in_location)
        meta1.addLayout(col1, 1)

        col2 = QVBoxLayout()
        col2.addWidget(self._lbl("Visibility"))
        self.in_visibility = QComboBox(); self.in_visibility.setEditable(True)
        for v in ["public","organization","faculty","students","private"]:
            self.in_visibility.addItem(v)
        col2.addWidget(self.in_visibility)
        meta1.addLayout(col2, 1)

        col3 = QVBoxLayout()
        col3.addWidget(self._lbl("Status"))
        self.in_status = QComboBox(); self.in_status.setEditable(True)
        for s in ["draft","published","archived"]:
            self.in_status.addItem(s)
        col3.addWidget(self.in_status)
        meta1.addLayout(col3, 1)

        left.addLayout(meta1)

        # meta row 2
        meta2 = QHBoxLayout()
        col4 = QVBoxLayout()
        col4.addWidget(self._lbl("Priority"))
        self.in_priority = QLineEdit(); self.in_priority.setPlaceholderText("0, 1, 2 …"); col4.addWidget(self.in_priority)
        meta2.addLayout(col4, 1)

        col5 = QVBoxLayout()
        col5.addWidget(self._lbl("Pinned"))
        self.in_pinned = QCheckBox("Pinned"); col5.addWidget(self.in_pinned)
        meta2.addLayout(col5, 1)

        col6 = QVBoxLayout()
        col6.addWidget(self._lbl("Tags (comma-separated)"))
        self.in_tags = QLineEdit(); col6.addWidget(self.in_tags)
        meta2.addLayout(col6, 2)

        left.addLayout(meta2)

        # dates
        dates = QHBoxLayout()
        d1 = QVBoxLayout()
        d1.addWidget(self._lbl("Publish at"))
        self.dt_publish = QDateTimeEdit(); self.dt_publish.setCalendarPopup(True); d1.addWidget(self.dt_publish)
        dates.addLayout(d1, 1)

        d2 = QVBoxLayout()
        d2.addWidget(self._lbl("Expire at"))
        self.dt_expire = QDateTimeEdit(); self.dt_expire.setCalendarPopup(True); d2.addWidget(self.dt_expire)
        dates.addLayout(d2, 1)

        left.addLayout(dates)

        # actions
        btn_row = QHBoxLayout()
        self.btn_save = QPushButton("Save"); self.btn_save.setProperty("kind","pri")
        self.btn_save.clicked.connect(self._save)
        self.btn_delete = QPushButton("Delete Announcement"); self.btn_delete.setProperty("kind","danger")
        self.btn_delete.clicked.connect(self._delete_announcement)
        btn_row.addWidget(self.btn_save); btn_row.addSpacing(8); btn_row.addWidget(self.btn_delete); btn_row.addStretch(1)

        left_wrap = QWidget(); left_wrap.setLayout(left)
        left.addLayout(btn_row)
        row.addWidget(left_wrap, 1)

        # right media pane
        right = QVBoxLayout(); right.setSpacing(10)
        right.addWidget(self._lbl("Images"))
        top = QHBoxLayout()
        self.path_line = QLineEdit(); self.path_line.setPlaceholderText("No file selected"); self.path_line.setReadOnly(True)
        self.btn_browse = QPushButton("Browse"); self.btn_browse.setProperty("kind","ghost"); self.btn_browse.clicked.connect(self._browse)
        top.addWidget(self.path_line, 1); top.addWidget(self.btn_browse, 0)
        right.addLayout(top)

        nav = QHBoxLayout()
        self.btn_prev = QPushButton(); self.btn_prev.setIcon(_icon("icon_chevron_left.png")); self.btn_prev.setProperty("kind","ghost")
        self.btn_next = QPushButton(); self.btn_next.setIcon(_icon("icon_chevron_right.png")); self.btn_next.setProperty("kind","ghost")
        self.btn_prev.clicked.connect(lambda: self._shift(-1))
        self.btn_next.clicked.connect(lambda: self._shift(+1))
        nav.addWidget(self.btn_prev, 0)

        self.preview = QLabel(); self.preview.setMinimumSize(QSize(420, 240))
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav.addWidget(self.preview, 1)

        nav.addWidget(self.btn_next, 0)
        right.addLayout(nav, 1)

        self.btn_del_photo = QPushButton("Delete Photo"); self.btn_del_photo.setProperty("kind","ghost")
        self.btn_del_photo.clicked.connect(self._delete_current_media)
        right.addWidget(self.btn_del_photo, 0, Qt.AlignmentFlag.AlignHCenter)

        right_wrap = QWidget(); right_wrap.setLayout(right)
        right_wrap.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        row.addWidget(right_wrap, 1)

        # load
        self._load_record()
        self._load_docs()
        self._render_media()

    # ---- helpers ----
    def _lbl(self, text: str) -> QLabel:
        l = QLabel(text); l.setProperty("role","label"); return l

    def _parse_dt(self, s: Optional[str]) -> QDateTime:
        if not s: return QDateTime.currentDateTime()
        try:
            dt = QDateTime.fromString(s.replace("T"," "), "yyyy-MM-dd HH:mm:ss")
            if not dt.isValid():
                dt = QDateTime.fromString(s, Qt.DateFormat.ISODate)
            return dt if dt.isValid() else QDateTime.currentDateTime()
        except Exception:
            return QDateTime.currentDateTime()

    def _fmt_dt(self, dt: QDateTime) -> Optional[str]:
        if not dt or not dt.isValid(): return None
        return dt.toString("yyyy-MM-dd HH:mm:ss")

    def _load_record(self):
        rec = get_announcement(self.announcement_id, include_tags=True)
        if not rec:
            QMessageBox.critical(self, "Error", "Announcement not found.")
            self.back_requested.emit()
            return
        self.in_title.setText(rec.get("title") or "")
        self.in_body.setPlainText(rec.get("body") or "")
        self.in_location.setText(rec.get("location") or "")
        self.in_visibility.setCurrentText(rec.get("visibility") or "public")
        self.in_status.setCurrentText(rec.get("status") or "draft")
        self.in_priority.setText(str(rec.get("priority") or 0))
        self.in_pinned.setChecked(int(rec.get("is_pinned") or 0) == 1)
        self.in_tags.setText(", ".join(rec.get("tags") or []))

        self.dt_publish.setDateTime(self._parse_dt(rec.get("publish_at")))
        self.dt_expire.setDateTime(self._parse_dt(rec.get("expire_at")))

    def _load_docs(self):
        self.docs = list_documents(self.announcement_id)
        self.doc_index = 0 if self.docs else -1

    def _current_doc(self) -> Optional[Dict[str, Any]]:
        if self.doc_index < 0 or self.doc_index >= len(self.docs): return None
        return self.docs[self.doc_index]

    def _render_media(self):
        cur = self._current_doc()
        path = cur["file_path"] if cur else None
        self.preview.setPixmap(_pm_or_placeholder(self.preview.width() or 420, self.preview.height() or 240, path))

    def resizeEvent(self, e): super().resizeEvent(e); self._render_media()

    # ---- actions: media ----
    def _shift(self, d: int):
        if not self.docs: return
        self.doc_index = (self.doc_index + d) % len(self.docs)
        self._render_media()

    def _browse(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Select image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if not fn: return
        self.path_line.setText(fn)
        try:
            new_name = f"ann_{int(time.time())}_{Path(fn).name}"
            dst = IMG_DIR / new_name
            shutil.copy2(fn, dst)
            rel_path = f"assets/images/{new_name}"
            add_document(self.announcement_id,
                         file_name=new_name,
                         file_path=rel_path,
                         mime_type="image/unknown")
            self._load_docs(); self.doc_index = len(self.docs)-1; self._render_media()
        except Exception as e:
            QMessageBox.critical(self, "Add image failed", str(e))

    def _delete_current_media(self):
        cur = self._current_doc()
        if not cur: return
        did = int(cur["document_id"])
        try:
            with _conn() as con:
                con.execute("DELETE FROM documents WHERE document_id=?", (did,))
            self._load_docs(); self._render_media()
        except Exception as e:
            QMessageBox.critical(self, "Delete failed", str(e))

    # ---- actions: record ----
    def _save(self):
        title = self.in_title.text().strip()
        if not title:
            QMessageBox.warning(self, "Missing", "Title is required.")
            return
        body = self.in_body.toPlainText().strip()
        location = self.in_location.text().strip() or None
        visibility = self.in_visibility.currentText().strip() or "public"
        status = self.in_status.currentText().strip() or "draft"
        try:
            priority = int(self.in_priority.text().strip() or "0")
        except Exception:
            priority = 0
        is_pinned = 1 if self.in_pinned.isChecked() else 0
        publish_at = self._fmt_dt(self.dt_publish.dateTime())
        expire_at  = self._fmt_dt(self.dt_expire.dateTime())

        try:
            update_announcement(
                self.announcement_id,
                title=title, body=body, location=location, visibility=visibility,
                status=status, priority=priority, is_pinned=is_pinned,
                publish_at=publish_at, expire_at=expire_at
            )
            tags = [t.strip() for t in self.in_tags.text().split(",") if t.strip()]
            set_tags(self.announcement_id, tags)
            self.saved.emit()
            self.back_requested.emit()
        except Exception as e:
            QMessageBox.critical(self, "Save failed", str(e))

    def _delete_announcement(self):
        if QMessageBox.question(
            self, "Confirm delete", "Delete this announcement permanently?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        try:
            delete_announcement(self.announcement_id)
            self.deleted.emit()
            self.back_requested.emit()
        except Exception as e:
            QMessageBox.critical(self, "Delete failed", str(e))
