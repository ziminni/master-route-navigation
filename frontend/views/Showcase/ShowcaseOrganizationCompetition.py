# views/Showcase/ShowcaseOrganizationCompetition.py
from __future__ import annotations
import os
from pathlib import Path
from typing import List, Dict

from PyQt6.QtCore import Qt, QSize, QMimeData, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QImageReader, QIntValidator
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QLineEdit,
    QTextEdit, QComboBox, QDateEdit, QDateTimeEdit, QCheckBox, QPushButton, QFileDialog,
    QFrame, QScrollArea, QListWidget, QListWidgetItem, QMessageBox, QToolButton, QSizePolicy
)

# --- DB helpers ---
try:
    # re-exported ensure_bootstrap; seed_images_if_missing is in DBHelper
    from .db.ShowcaseDBHelper import ensure_bootstrap, seed_images_if_missing  # type: ignore
    from .db.ShowcaseDBInitialize import db_path  # source of truth
except Exception:
    from db.ShowcaseDBHelper import ensure_bootstrap, seed_images_if_missing  # type: ignore
    from db.ShowcaseDBInitialize import db_path

import sqlite3
from datetime import datetime

import importlib
_session_mod = None
try:
    _session_mod = importlib.import_module("utils")
except Exception:
    _session_mod = None

# optional session bridge; safe default
session = getattr(_session_mod, "session", None)
try:
    from utils import session  # expected to expose get_user_id()
except Exception:
    class _S:
        def get_user_id(self, default=1):
            return default
    session = _S()

# ---------- Theme ----------
GREEN   = "#146c43"
TEXT    = "#1f2937"
MUTED   = "#6b7280"
BG      = "#f3f4f6"
CARD_BG = "#ffffff"
BORDER  = "#e5e7eb"

def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path()))
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sqlite3.Row
    return con

def _now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ---------- assets ----------
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

# ---------- Upload widget (drag, browse, preview, delete) ----------
class ImagesUploadPane(QFrame):
    files_changed = pyqtSignal(list)  # emits list[str] absolute or relative paths

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("ImagesUploadPane")
        self.setAcceptDrops(True)
        self.paths: List[str] = []

        self.setStyleSheet(f"""
            QFrame#ImagesUploadPane {{
                background:white; border:1px dashed {GREEN}; border-radius:8px;
            }}
            QListWidget#Thumbs {{
                background:transparent; border:none;
            }}
            QPushButton[role="browse"] {{
                background:transparent; color:{GREEN}; border:1px solid {BORDER};
                padding:6px 10px; border-radius:8px;
            }}
            QPushButton[role="danger"] {{
                background:transparent; color:#b91c1c; border:1px solid {BORDER};
                padding:6px 10px; border-radius:8px;
            }}
        """)

        v = QVBoxLayout(self); v.setContentsMargins(10,10,10,10); v.setSpacing(8)
        self.hint = QLabel("Drag n Drop here\nor")
        self.hint.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.hint.setStyleSheet(f"color:{MUTED};")
        v.addWidget(self.hint)

        self.browse_btn = QPushButton("Browse"); self.browse_btn.setProperty("role","browse")
        self.browse_btn.clicked.connect(self._browse)
        self.browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        v.addWidget(self.browse_btn, 0, Qt.AlignmentFlag.AlignHCenter)

        self.list = QListWidget(self); self.list.setObjectName("Thumbs")
        self.list.setViewMode(QListWidget.ViewMode.IconMode)
        self.list.setIconSize(QSize(120, 120))
        self.list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list.setMovement(QListWidget.Movement.Static)
        self.list.setSpacing(8)
        v.addWidget(self.list)

        btns = QHBoxLayout(); btns.setSpacing(8)
        self.remove_btn = QPushButton("Remove Selected"); self.remove_btn.setProperty("role","danger")
        self.clear_btn  = QPushButton("Clear All");        self.clear_btn.setProperty("role","danger")
        self.remove_btn.clicked.connect(self._remove_selected)
        self.clear_btn.clicked.connect(self._clear_all)
        btns.addWidget(self.remove_btn); btns.addWidget(self.clear_btn); v.addLayout(btns)

    # drag & drop
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            e.ignore()

    def dropEvent(self, e):
        md: QMimeData = e.mimeData()
        if not md.hasUrls():
            return
        paths = []
        for u in md.urls():
            fp = u.toLocalFile()
            if fp and self._is_image(fp):
                paths.append(fp)
        if paths:
            self._add_files(paths)

    def _is_image(self, path: str) -> bool:
        exts = {'.png','.jpg','.jpeg','.gif','.bmp','.webp'}
        if Path(path).suffix.lower() in exts:
            return True
        # try via Qt loaders
        fmts = {bytes(f).decode().lower() for f in QImageReader.supportedImageFormats()}
        return Path(path).suffix.lower().lstrip(".") in fmts

    def _browse(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select images", str(IMG_DIR),
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        if files:
            self._add_files(files)

    def _add_files(self, files: List[str]):
        for fp in files:
            if fp in self.paths:
                continue
            if not self._is_image(fp):
                continue
            self.paths.append(fp)
            pm = QPixmap(fp)
            if pm.isNull():
                continue
            it = QListWidgetItem(QIcon(pm.scaled(120,120, Qt.AspectRatioMode.KeepAspectRatio,
                                                 Qt.TransformationMode.SmoothTransformation)),
                                 Path(fp).name)
            it.setToolTip(fp)
            self.list.addItem(it)
        self.files_changed.emit(self.paths)

    def _remove_selected(self):
        for it in self.list.selectedItems():
            idx = self.list.row(it)
            self.list.takeItem(idx)
            try:
                del self.paths[idx]
            except Exception:
                pass
        self.files_changed.emit(self.paths)

    def _clear_all(self):
        self.list.clear()
        self.paths.clear()
        self.files_changed.emit(self.paths)

# ---------- Achievement entry ----------
class AchievementEntry(QFrame):
    removed = pyqtSignal("PyQt_PyObject")  # emits self

    def __init__(self, index: int, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("AchievementEntry")
        self.setStyleSheet(f"""
            QFrame#AchievementEntry {{ background:{CARD_BG}; border:1px solid {BORDER}; border-radius:8px; }}
            QLabel[role="cap"] {{ color:{MUTED}; font-size:12px; }}
        """)
        v = QVBoxLayout(self); v.setContentsMargins(12,10,12,12); v.setSpacing(8)

        top = QHBoxLayout(); top.setSpacing(8)
        cap = QLabel(f"Achievement Entry #{index}")
        cap.setProperty("role","cap")
        top.addWidget(cap)
        top.addStretch(1)
        self.close_btn = QToolButton(); self.close_btn.setText("✕")
        self.close_btn.setToolTip("Remove this achievement")
        self.close_btn.clicked.connect(lambda: self.removed.emit(self))
        top.addWidget(self.close_btn, 0, Qt.AlignmentFlag.AlignRight)
        v.addLayout(top)

        g = QGridLayout(); g.setHorizontalSpacing(12); g.setVerticalSpacing(10)

        self.title = QLineEdit();      self._label(g, "Achievement Title", 0, 0); g.addWidget(self.title, 1, 0)
        self.result = QComboBox();     self._label(g, "Result Recognition", 0, 1); g.addWidget(self.result, 1, 1)
        self.result.addItems(["", "Champion", "1st Place", "2nd Place", "3rd Place", "Finalist", "Honorable Mention"])
        self.specific = QLineEdit();   self._label(g, "Specific Awards", 2, 0); g.addWidget(self.specific, 3, 0)
        self.participants = QTextEdit(); self.participants.setPlaceholderText("Enter participant names or notes")
        self._label(g, "Participants / Notes", 2, 1); g.addWidget(self.participants, 3, 1)
        self.awarded_at = QDateEdit(); self.awarded_at.setCalendarPopup(True)
        self._label(g, "Awarded Date", 4, 0); g.addWidget(self.awarded_at, 5, 0)

        v.addLayout(g)

    def _label(self, grid: QGridLayout, text: str, r: int, c: int):
        lbl = QLabel(text); lbl.setProperty("role","cap"); grid.addWidget(lbl, r, c)

    def to_dict(self) -> Dict:
        return {
            "achievement_title": self.title.text().strip(),
            "result_recognition": self.result.currentText().strip() or None,
            "specific_awards": self.specific.text().strip() or None,
            "notes": self.participants.toPlainText().strip() or None,
            "awarded_at": self.awarded_at.date().toString("yyyy-MM-dd") if self.awarded_at.date().isValid() else None,
        }

# ---------- Page ----------
class ShowcaseOrganizationCompetition(QWidget):
    back_requested = pyqtSignal()

    """
    Submit Organizational Event Result.
    Renders all competition fields + media uploads + repeatable achievements.
    """
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        ensure_bootstrap()

        self.setObjectName("ShowcaseOrganizationCompetition")
        self.setStyleSheet(f"""
            QWidget#ShowcaseOrganizationCompetition {{ background:{BG}; }}
            QGroupBox {{ border:1px solid {BORDER}; border-radius:10px; margin-top:10px; }}
            QLabel[role="title"] {{ color:{TEXT}; font-size:24px; font-weight:600; }}
            QLabel[role="section"] {{ color:{TEXT}; font-size:16px; font-weight:600; }}
            QLabel[role="cap"] {{ color:{MUTED}; font-size:12px; }}
            QLineEdit, QTextEdit, QComboBox, QDateEdit, QDateTimeEdit {{
                background:white; border:1px solid {BORDER}; border-radius:6px; padding:8px;
                color:{TEXT};
            }}
            QCheckBox {{ color:{TEXT}; }}
            QPushButton[role="primary"] {{
                background:{GREEN}; color:white; border:none; border-radius:8px; padding:10px 16px;
            }}
            QPushButton[role="primary"]:disabled {{ background:#9ca3af; }}
            QFrame#Card {{ background:{CARD_BG}; border:1px solid {BORDER}; border-radius:12px; }}
        """)

        root = QVBoxLayout(self); root.setContentsMargins(10,10,10,10); root.setSpacing(8)

        # Header with close/back
        header = QFrame(); hv = QHBoxLayout(header); hv.setContentsMargins(12,8,12,8)
        title = QLabel("Submit Organizational Event Result"); title.setProperty("role","title")
        hv.addWidget(title)
        hv.addStretch(1)
        close_btn = QToolButton(); close_btn.setText("✕"); close_btn.setToolTip("Back")
        close_btn.clicked.connect(self.back_requested.emit)
        hv.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignRight)
        root.addWidget(header)

        # Scrollable content
        scroll = QScrollArea(self); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        root.addWidget(scroll, 1)

        content = QWidget(); scroll.setWidget(content)
        cv = QVBoxLayout(content); cv.setContentsMargins(2,2,2,80); cv.setSpacing(12)

        # Top section: form + uploads
        top = QFrame(); top.setObjectName("Card")
        cv.addWidget(top)
        th = QHBoxLayout(top); th.setContentsMargins(12,12,12,12); th.setSpacing(12)

        # left form
        lf = QFrame(); lf.setObjectName("Card"); lf.setStyleSheet("QFrame#Card{border-color:%s}" % GREEN)
        th.addWidget(lf, 2)
        lg = QGridLayout(lf); lg.setContentsMargins(12,12,12,12); lg.setHorizontalSpacing(12); lg.setVerticalSpacing(10)

        row = 0
        self.organizer = QLineEdit(); self._cap(lg, "Organization Name", row, 0); lg.addWidget(self.organizer, row+1, 0)
        self.end_date = QDateEdit(); self.end_date.setCalendarPopup(True); self._cap(lg, "Event End Date", row, 1); lg.addWidget(self.end_date, row+1, 1)

        row += 2
        self.name = QLineEdit(); self._cap(lg, "Event Name", row, 0); lg.addWidget(self.name, row+1, 0)
        self.event_type = QComboBox(); self.event_type.addItems(["Competition","Expo","Seminar","Hackathon","Workshop","Sports","Other"])
        self._cap(lg, "Event Type", row, 1); lg.addWidget(self.event_type, row+1, 1)

        row += 2
        self.start_date = QDateEdit(); self.start_date.setCalendarPopup(True); self._cap(lg, "Event Start Date", row, 0); lg.addWidget(self.start_date, row+1, 0)
        self.description = QTextEdit(); self.description.setPlaceholderText("Enter Text Here")
        self._cap(lg, "Enter Description", row, 1); lg.addWidget(self.description, row+1, 1)

        row += 2
        self.related_event_id = QLineEdit(); self.related_event_id.setValidator(QIntValidator(0, 2_000_000))
        self._cap(lg, "Related Event ID (optional)", row, 0); lg.addWidget(self.related_event_id, row+1, 0)
        self.is_public = QCheckBox("Make Public when approved"); lg.addWidget(self.is_public, row+1, 1, 1, 1)

        row += 2
        self.publish_at = QDateTimeEdit(); self.publish_at.setCalendarPopup(True)
        self._cap(lg, "Publish At (optional)", row, 0); lg.addWidget(self.publish_at, row+1, 0)

        # right uploads + external link
        rf = QFrame(); rf.setObjectName("Card"); th.addWidget(rf, 1)
        rv = QVBoxLayout(rf); rv.setContentsMargins(12,12,12,12); rv.setSpacing(10)

        cap = QLabel("Supporting Materials (Optional)"); cap.setProperty("role","section"); rv.addWidget(cap)
        sub = QLabel("Photos/Screenshots"); sub.setProperty("role","cap"); rv.addWidget(sub)

        self.upload = ImagesUploadPane(rf); rv.addWidget(self.upload, 1)

        self.external_url = QLineEdit(); self.external_url.setPlaceholderText("e.g. Github Repo, Website Link")
        self._rowcap(rv, "Link to Project", self.external_url)

        # Achievements section
        ach_card = QFrame(); ach_card.setObjectName("Card"); cv.addWidget(ach_card)
        av = QVBoxLayout(ach_card); av.setContentsMargins(12,12,12,12); av.setSpacing(10)
        head = QLabel("Featured Achievements"); head.setProperty("role","section"); av.addWidget(head)

        self.ach_wrap = QVBoxLayout(); self.ach_wrap.setSpacing(10)
        av.addLayout(self.ach_wrap)

        self.add_ach_btn = QPushButton("＋  Add Another Achievement")
        self.add_ach_btn.clicked.connect(self._add_achievement)
        av.addWidget(self.add_ach_btn, 0, Qt.AlignmentFlag.AlignLeft)

        # submit
        self.submit_btn = QPushButton("Submit for Review"); self.submit_btn.setProperty("role","primary")
        self.submit_btn.clicked.connect(self._on_submit)
        cv.addWidget(self.submit_btn, 0, Qt.AlignmentFlag.AlignHCenter)

        # state
        self.entries: List[AchievementEntry] = []
        self._add_achievement()  # start with one

    def _cap(self, grid: QGridLayout, text: str, r: int, c: int):
        lbl = QLabel(text); lbl.setProperty("role","cap"); grid.addWidget(lbl, r, c)

    def _rowcap(self, layout: QVBoxLayout, label: str, w: QWidget):
        t = QLabel(label); t.setProperty("role","cap"); layout.addWidget(t); layout.addWidget(w)

    # --- dynamic achievements ---
    def _add_achievement(self):
        entry = AchievementEntry(len(self.entries) + 1, self)
        entry.removed.connect(self._remove_entry)
        self.entries.append(entry)
        self.ach_wrap.addWidget(entry)

    def _remove_entry(self, entry: AchievementEntry):
        if entry in self.entries:
            self.entries.remove(entry)
            entry.setParent(None)
            entry.deleteLater()
        # renumber
        for i, e in enumerate(self.entries, start=1):
            # update caption text
            cap = e.findChild(QLabel)
            if cap:
                cap.setText(f"Achievement Entry #{i}")

    # --- submit ---
    def _on_submit(self):
        data = {
            "name": self.name.text().strip(),
            "organizer": self.organizer.text().strip(),
            "start_date": self.start_date.date().toString("yyyy-MM-dd") if self.start_date.date().isValid() else None,
            "end_date": self.end_date.date().toString("yyyy-MM-dd") if self.end_date.date().isValid() else None,
            "related_event_id": int(self.related_event_id.text()) if self.related_event_id.text() else None,
            "description": self.description.toPlainText().strip() or None,
            "event_type": self.event_type.currentText().strip() or None,
            "external_url": self.external_url.text().strip() or None,
            "submitted_by": session.get_user_id(1),
            "status": "pending",
            "is_public": 1 if self.is_public.isChecked() else 0,
            "publish_at": self.publish_at.dateTime().toString("yyyy-MM-dd HH:mm:ss") if self.publish_at.dateTime() else None,
            "created_at": _now_ts(),
            "updated_at": _now_ts(),
        }
        # basic validation
        if not data["name"]:
            QMessageBox.warning(self, "Missing", "Event Name is required.")
            return

        try:
            comp_id = self._create_competition(data)
            # images
            if self.upload.paths:
                user_id = data["submitted_by"] or 1
                media_ids = seed_images_if_missing(self.upload.paths, uploaded_by=user_id)
                with _conn() as con:
                    for i, mid in enumerate(media_ids, start=1):
                        con.execute(
                            "INSERT OR IGNORE INTO competition_media_map (media_id, competition_id, sort_order, is_primary) VALUES (?,?,?,?)",
                            (mid, comp_id, i, 1 if i == 1 else 0),
                        )
            # achievements
            achs = [e.to_dict() for e in self.entries if e.to_dict().get("achievement_title")]
            if achs:
                with _conn() as con:
                    for a in achs:
                        con.execute(
                            "INSERT INTO competition_achievements "
                            "(competition_id, achievement_title, result_recognition, specific_awards, notes, awarded_at) "
                            "VALUES (?,?,?,?,?,?)",
                            (comp_id, a["achievement_title"], a["result_recognition"], a["specific_awards"], a["notes"], a["awarded_at"]),
                        )

            QMessageBox.information(self, "Submitted", "Competition submitted for review.")
            self._reset_form()

        except Exception as ex:
            QMessageBox.critical(self, "Error", f"Failed to submit.\n{ex}")

    def _create_competition(self, data: Dict) -> int:
        cols = [
            "name","organizer","start_date","end_date","related_event_id","description",
            "event_type","external_url","submitted_by","status","is_public","publish_at",
            "created_at","updated_at"
        ]
        vals = [data.get(c) for c in cols]
        with _conn() as con:
            cur = con.execute(
                f"INSERT INTO competitions ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})",
                vals
            )
            return int(cur.lastrowid)

    def _reset_form(self):
        self.name.clear(); self.organizer.clear()
        self.start_date.clear(); self.end_date.clear(); self.related_event_id.clear()
        self.description.clear(); self.external_url.clear()
        self.is_public.setChecked(False); self.publish_at.clear()
        self.upload._clear_all()
        for e in list(self.entries):
            e.setParent(None); e.deleteLater()
        self.entries.clear()
        self._add_achievement()

# ---------- Demo ----------
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    w = ShowcaseOrganizationCompetition()
    w.resize(1100, 780)
    w.show()
    sys.exit(app.exec())
