# views/Showcase/ShowcaseAdminEdit.py
from __future__ import annotations
import os, shutil, sqlite3, time
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui  import QIcon, QPixmap, QFont
from PyQt6.QtWidgets import (
    QDialog, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame,
    QLineEdit, QTextEdit, QComboBox, QFileDialog, QMessageBox, QSizePolicy
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
        if p.is_absolute() and p.exists():
            return p
        # try relative like "assets/images/1.jpg"
        p2 = Path(os.getcwd()) / pstr
        if p2.exists():
            return p2
        # project/assets + given path
        assets_dir = ICON_DIR.parent
        proj_root = assets_dir.parent
        p3 = proj_root / pstr
        if p3.exists():
            return p3
        # fallback: filename inside assets/images
        p4 = IMG_DIR / p.name
        if p4.exists():
            return p4
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
    from .db.ShowcaseDBInitialize import db_path
    from .db.ShowcaseDBHelper import (
        list_project_media, list_competition_media, update_project, delete_project
    )
except Exception:
    from db.ShowcaseDBInitialize import db_path
    from db.ShowcaseDBHelper import (
        list_project_media, list_competition_media, update_project, delete_project
    )


def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path()))
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sqlite3.Row
    return con

# ---------- dialog ----------
class ShowcaseAdminEditDialog(QDialog):
    """
    kind: 'project' or 'competition'
    item_id: projects_id or competition_id
    """
    def __init__(self, kind: str, item_id: int, parent: QWidget | None = None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        assert kind in ("project","competition")
        self.kind = kind
        self.item_id = int(item_id)
        self.media: List[Dict[str, Any]] = []
        self.media_index = 0

        self.setObjectName("EditDlg")
        self.setStyleSheet(f"""
            QDialog#EditDlg      {{ background:white; border:1px solid {GREEN}; border-radius:12px; }}
            QLabel#title         {{ color:white; font-size:22px; font-weight:700; }}
            QFrame#hdr           {{ background:{GREEN}; border-top-left-radius:12px; border-top-right-radius:12px; }}
            QLabel[role="label"] {{ color:{MUTED}; font-size:12px; }}
            QLineEdit, QTextEdit, QComboBox {{
                background:white; color:{TEXT}; border:1px solid {BORDER}; border-radius:8px; padding:6px;
            }}
            QPushButton[kind="pri"] {{
                background:{GREEN}; color:white; border:none; border-radius:8px; padding:8px 14px;
            }}
            QPushButton[kind="ghost"] {{
                background:transparent; color:{GREEN}; border:1px solid {GREEN}; border-radius:18px; padding:6px 10px;
            }}
            QPushButton[kind="danger"] {{
                background:#dc3545; color:white; border:none; border-radius:8px; padding:8px 14px;
            }}
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
        title = QLabel("Edit Showcase"); title.setObjectName("title")
        self.closeBtn = QPushButton("×"); self.closeBtn.setObjectName("closeBtn")
        self.closeBtn.clicked.connect(lambda: self._close_host(False))
        h.addWidget(title, 0); h.addStretch(1); h.addWidget(self.closeBtn, 0)
        root.addWidget(hdr)


        # content
        row = QHBoxLayout(); row.setContentsMargins(12,12,12,12); row.setSpacing(14)
        root.addLayout(row, 1)

        # left form
        left = QVBoxLayout(); left.setSpacing(10)
        # title
        left.addWidget(self._lbl("Title"))
        self.in_title = QLineEdit(); left.addWidget(self.in_title)
        # post to / category or event type
        left.addWidget(self._lbl("Post To"))
        self.in_category = QComboBox(); self.in_category.setEditable(True); left.addWidget(self.in_category)
        # context
        left.addWidget(self._lbl("Context"))
        self.in_context = QLineEdit(); left.addWidget(self.in_context)
        # description
        left.addWidget(self._lbl("Enter Message"))
        self.in_desc = QTextEdit(); self.in_desc.setMinimumHeight(180); left.addWidget(self.in_desc, 1)
        # save + delete
        btn_row = QHBoxLayout()
        self.btn_save = QPushButton("Save current state"); self.btn_save.setProperty("kind","pri")
        self.btn_save.clicked.connect(self._save)
        self.btn_delete_show = QPushButton("Delete Showcase"); self.btn_delete_show.setProperty("kind","danger")
        self.btn_delete_show.clicked.connect(self._delete_showcase)
        btn_row.addWidget(self.btn_save)
        btn_row.addSpacing(8)
        btn_row.addWidget(self.btn_delete_show)
        btn_row.addStretch(1)
        left.addLayout(btn_row)
        left_wrap = QWidget(); left_wrap.setLayout(left)
        row.addWidget(left_wrap, 1)

        # right media pane
        right = QVBoxLayout(); right.setSpacing(10)
        right.addWidget(self._lbl("Photos/Screenshots"))
        top = QHBoxLayout()
        self.path_line = QLineEdit(); self.path_line.setPlaceholderText("No file selected"); self.path_line.setReadOnly(True)
        self.btn_browse = QPushButton("Browse"); self.btn_browse.setProperty("kind","ghost"); self.btn_browse.clicked.connect(self._browse)
        top.addWidget(self.path_line, 1); top.addWidget(self.btn_browse, 0)
        right.addLayout(top)

        # image viewer with prev/next
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

        self.btn_delete = QPushButton("Delete Photo"); self.btn_delete.setProperty("kind","ghost")
        self.btn_delete.clicked.connect(self._delete_current_media)
        right.addWidget(self.btn_delete, 0, Qt.AlignmentFlag.AlignHCenter)

        right_wrap = QWidget(); right_wrap.setLayout(right)
        right_wrap.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        row.addWidget(right_wrap, 1)

        # load data
        self._load_record()
        self._load_categories()
        self._load_media()
        self._render_media()
    
    def _close_host(self, accepted: bool):
        # close the overlay dialog that hosts this editor (or self if standalone)
        from PyQt6.QtWidgets import QDialog
        host = self.window()
        if isinstance(host, QDialog) and host is not self:
            host.accept() if accepted else host.reject()
        else:
            super().accept() if accepted else super().reject()

    def accept(self):
        # ensure Save closes the overlay too
        self._close_host(True)

    def reject(self):
        # ensure Close/X closes the overlay too
        self._close_host(False)

    # ---- helpers ----
    def _lbl(self, text: str) -> QLabel:
        l = QLabel(text); l.setProperty("role","label"); return l

    def _load_record(self):
        with _conn() as con:
            if self.kind == "project":
                r = con.execute("SELECT * FROM projects WHERE projects_id = ?", (self.item_id,)).fetchone()
                if not r: raise RuntimeError("Project not found")
                self.in_title.setText(r["title"] or "")
                self.in_desc.setPlainText(r["description"] or "")
                self.in_context.setText(r["context"] or "")
                self._cur_category = r["category"] or ""
            else:
                r = con.execute("SELECT * FROM competitions WHERE competition_id = ?", (self.item_id,)).fetchone()
                if not r: raise RuntimeError("Competition not found")
                self.in_title.setText(r["name"] or "")
                self.in_desc.setPlainText(r["description"] or "")
                self.in_context.setText("")  # no context column in competitions
                self._cur_category = r["event_type"] or ""

    def _delete_showcase(self):
        if QMessageBox.question(
            self, "Confirm delete", "Delete this showcase permanently?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        try:
            with _conn() as con:
                if self.kind == "project":
                    try:
                        delete_project(self.item_id)  # uses helper
                    except Exception:
                        con.execute("DELETE FROM project_tag_map WHERE project_id=?", (self.item_id,))
                        con.execute("DELETE FROM project_members WHERE project_id=?", (self.item_id,))
                        con.execute("DELETE FROM project_media_map WHERE project_id=?", (self.item_id,))
                        con.execute("DELETE FROM projects WHERE projects_id=?", (self.item_id,))
                else:
                    # remove linked achievements and maps, then competition
                    ach_ids = [r["achievement_id"] for r in con.execute(
                        "SELECT achievement_id FROM competition_achievements WHERE competition_id=?",
                        (self.item_id,)
                    )]
                    if ach_ids:
                        con.executemany(
                            "DELETE FROM competition_achievement_users WHERE achievement_id=?",
                            [(i,) for i in ach_ids]
                        )
                        con.executemany(
                            "DELETE FROM competition_achievement_projects WHERE achievement_id=?",
                            [(i,) for i in ach_ids]
                        )
                        con.execute("DELETE FROM competition_achievements WHERE competition_id=?", (self.item_id,))
                    con.execute("DELETE FROM competition_media_map WHERE competition_id=?", (self.item_id,))
                    con.execute("DELETE FROM competitions WHERE competition_id=?", (self.item_id,))
            # close overlay and refresh parent list
            self._close_host(True)
        except Exception as e:
            QMessageBox.critical(self, "Delete failed", str(e))


    def _load_categories(self):
        opts = set()
        with _conn() as con:
            for row in con.execute("SELECT DISTINCT category FROM projects WHERE category IS NOT NULL AND category<>''"):
                opts.add(row["category"])
            for row in con.execute("SELECT DISTINCT event_type AS category FROM competitions WHERE event_type IS NOT NULL AND event_type<>''"):
                opts.add(row["category"])
        base = ["General","Software","Hardware","Mobile"]
        for x in base + sorted(opts - set(base)): self.in_category.addItem(x)
        # set current
        i = self.in_category.findText(self._cur_category) if self._cur_category else -1
        if i >= 0: self.in_category.setCurrentIndex(i)
        else:
            if self._cur_category: self.in_category.insertItem(0, self._cur_category); self.in_category.setCurrentIndex(0)

    def _load_media(self):
        self.media = list_project_media(self.item_id) if self.kind == "project" else list_competition_media(self.item_id)
        self.media_index = 0 if self.media else -1

    def _current_media(self) -> Optional[Dict[str, Any]]:
        if self.media_index < 0 or self.media_index >= len(self.media): return None
        return self.media[self.media_index]

    def _render_media(self):
        cur = self._current_media()
        path = cur["path_or_url"] if cur else None
        self.preview.setPixmap(_pm_or_placeholder(self.preview.width() or 420, self.preview.height() or 240, path))

    def resizeEvent(self, e): super().resizeEvent(e); self._render_media()

    # ---- actions ----
    def _shift(self, d: int):
        if not self.media: return
        self.media_index = (self.media_index + d) % len(self.media)
        self._render_media()

    def _browse(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Select image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if not fn: return
        self.path_line.setText(fn)
        try:
            new_name = f"sc_{int(time.time())}_{Path(fn).name}"
            dst = IMG_DIR / new_name
            shutil.copy2(fn, dst)
            with _conn() as con:
                cur = con.execute(
                    "INSERT INTO media (media_type, path_or_url, mime_type, caption, alt_text) VALUES ('image', ?, ?, ?, ?)",
                    (str(dst), "image/unknown", Path(new_name).stem, Path(new_name).stem),
                )
                mid = int(cur.lastrowid)
                if self.kind == "project":
                    con.execute(
                        "INSERT OR IGNORE INTO project_media_map (media_id, project_id, sort_order, is_primary) VALUES (?,?,?,0)",
                        (mid, self.item_id, (len(self.media) + 1)),
                    )
                else:
                    con.execute(
                        "INSERT OR IGNORE INTO competition_media_map (media_id, competition_id, sort_order, is_primary) VALUES (?,?,?,0)",
                        (mid, self.item_id, (len(self.media) + 1)),
                    )
            self._load_media(); self.media_index = len(self.media)-1; self._render_media()
        except Exception as e:
            QMessageBox.critical(self, "Add image failed", str(e))

    def _delete_current_media(self):
        cur = self._current_media()
        if not cur: return
        mid = int(cur["media_id"])
        try:
            with _conn() as con:
                if self.kind == "project":
                    con.execute("DELETE FROM project_media_map WHERE media_id=? AND project_id=?", (mid, self.item_id))
                else:
                    con.execute("DELETE FROM competition_media_map WHERE media_id=? AND competition_id=?", (mid, self.item_id))
            self._load_media(); self._render_media()
        except Exception as e:
            QMessageBox.critical(self, "Delete failed", str(e))

    def _save(self):
        title = self.in_title.text().strip()
        cat   = self.in_category.currentText().strip()
        desc  = self.in_desc.toPlainText().strip()
        ctx   = self.in_context.text().strip()
        if not title:
            QMessageBox.warning(self, "Missing", "Title is required.")
            return
        try:
            with _conn() as con:
                if self.kind == "project":
                    # prefer helper
                    try:
                        update_project(self.item_id, {"title": title, "category": cat, "description": desc, "context": ctx})
                    except Exception:
                        con.execute(
                            "UPDATE projects SET title=?, category=?, description=?, context=? WHERE projects_id=?",
                            (title, cat, desc, ctx, self.item_id),
                        )
                else:
                    con.execute(
                        "UPDATE competitions SET name=?, event_type=?, description=? WHERE competition_id=?",
                        (title, cat, desc, self.item_id),
                    )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Save failed", str(e))
