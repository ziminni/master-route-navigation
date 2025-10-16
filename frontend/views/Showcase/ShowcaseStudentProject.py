# views/Showcase/ShowcaseStudentProject.py
from __future__ import annotations
import os, shutil, sqlite3, uuid
from datetime import datetime
from pathlib import Path
from typing import List

from PyQt6 import QtGui, QtCore, QtWidgets
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QComboBox,
    QPushButton, QFrame, QListWidget, QListWidgetItem, QFileDialog, QCheckBox,
    QSpinBox, QMessageBox
)

# DB helpers (package-safe)
try:
    from .db.ShowcaseDBHelper import create_project, set_project_tags, seed_images_if_missing
    from .db.ShowcaseDBInitialize import db_path, ensure_bootstrap
except Exception:
    from db.ShowcaseDBHelper import create_project, set_project_tags, seed_images_if_missing
    from db.ShowcaseDBInitialize import db_path, ensure_bootstrap


# Optional session bridge; safe fallback without static import warnings
import importlib
_session_mod = None
try:
    _session_mod = importlib.import_module("utils")
except Exception:
    _session_mod = None

session = getattr(_session_mod, "session", None)
if session is None:
    class _S:
        @staticmethod
        def get_username(): return "student"
        @staticmethod
        def get_user_id(): return None
    session = _S()

# ---------- helper shims for variable session signatures ----------
def _safe_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except TypeError:
        try:
            return fn()
        except Exception:
            return None

def _safe_username() -> str:
    fn = getattr(session, "get_username", None)
    if not callable(fn):
        return ""
    v = _safe_call(fn, "")
    return v or ""

def _safe_user_id() -> int | None:
    fn = getattr(session, "get_user_id", None)
    if not callable(fn):
        return None
    v = _safe_call(fn, None)
    try:
        return int(v) if v is not None else None
    except Exception:
        return None

# ---------- constants ----------
def _find_images_dir() -> Path:
    here = Path(__file__).resolve()
    # walk up until we find assets/images next to this file
    for up in range(0, 7):
        base = here.parents[up] if up else here.parent
        cand = base / "assets" / "images"
        if cand.is_dir():
            return cand
    # create locally if missing
    cand = here.parent / "assets" / "images"
    cand.mkdir(parents=True, exist_ok=True)
    return cand

IMAGES_DIR = _find_images_dir()                       # absolute path to assets/images
ASSETS_ROOT = IMAGES_DIR.parent                       # absolute path to assets/

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
FILE_EXTS  = IMAGE_EXTS | {".pdf", ".mp4", ".mov", ".avi", ".mp3", ".wav", ".txt", ".zip"}

# ---------- little DB utilities ----------
def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path()))
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sqlite3.Row
    return con

def _lookup_auth_user_id(preferred_user_id=None) -> int | None:
    """Try session user_id first, else map by username in auth_user."""
    if preferred_user_id is not None:
        try:
            return int(preferred_user_id)
        except Exception:
            pass
    uname = _safe_username()
    if not uname:
        return None
    with _conn() as con:
        row = con.execute("SELECT auth_user_id FROM auth_user WHERE username = ?", (uname,)).fetchone()
        return int(row["auth_user_id"]) if row else None

def _map_media_to_project(project_id: int, media_ids: List[int]) -> None:
    if not media_ids:
        return
    with _conn() as con:
        for idx, mid in enumerate(media_ids, start=1):
            con.execute(
                "INSERT OR IGNORE INTO project_media_map (media_id, project_id, sort_order, is_primary) VALUES (?,?,?,?)",
                (mid, project_id, idx, 1 if idx == 1 else 0),
            )
        con.commit()

# ---------- UI widgets ----------
class DropListWidget(QListWidget):
    """Icon-mode list with drag/drop of files and Delete/Clear actions."""
    filesChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setIconSize(QtCore.QSize(96, 96))
        self.setSpacing(12)
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self._paths: List[str] = []

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._open_menu)

    def dragEnterEvent(self, e: QtGui.QDragEnterEvent) -> None:
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dragMoveEvent(self, e: QtGui.QDragMoveEvent) -> None:
        e.acceptProposedAction()

    def dropEvent(self, e: QtGui.QDropEvent) -> None:
        added = False
        for url in e.mimeData().urls():
            p = url.toLocalFile()
            if not p:
                continue
            ext = Path(p).suffix.lower()
            if ext in FILE_EXTS:
                self._add_path(p)
                added = True
        if added:
            self.filesChanged.emit()

    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        if e.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.remove_selected()
            return
        super().keyPressEvent(e)

    def _add_path(self, path: str) -> None:
        if path in self._paths:
            return
        self._paths.append(path)
        item = QListWidgetItem()
        item.setText(Path(path).name)
        item.setToolTip(path)
        item.setData(Qt.ItemDataRole.UserRole, path)
        item.setIcon(self._icon_for(path))
        self.addItem(item)

    def _icon_for(self, path: str) -> QtGui.QIcon:
        ext = Path(path).suffix.lower()
        if ext in IMAGE_EXTS:
            pm = QtGui.QPixmap(path)
            if not pm.isNull():
                return QtGui.QIcon(pm.scaled(self.iconSize(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        return self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileIcon)

    def _open_menu(self, pos: QtCore.QPoint) -> None:
        menu = QtWidgets.QMenu(self)
        act_remove = menu.addAction("Remove selected")
        act_clear  = menu.addAction("Clear all")
        act = menu.exec(self.mapToGlobal(pos))
        if act == act_remove:
            self.remove_selected()
        elif act == act_clear:
            self.clear_all()

    def remove_selected(self) -> None:
        for item in list(self.selectedItems()):
            path = item.data(Qt.ItemDataRole.UserRole)
            if path in self._paths:
                self._paths.remove(path)
            self.takeItem(self.row(item))
        self.filesChanged.emit()

    def clear_all(self) -> None:
        self._paths.clear()
        self.clear()
        self.filesChanged.emit()

    def paths(self) -> List[str]:
        return list(self._paths)

# ---------- main page ----------
class ShowcaseStudentProjectPage(QWidget):
    request_close = QtCore.pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        ensure_bootstrap(seed=True)
        self.setObjectName("ShowcaseStudentProjectPage")
        self._build_ui()
        self._wire()

    # ----- UI -----
    def _build_ui(self) -> None:
        root = QVBoxLayout(self); root.setContentsMargins(12, 12, 12, 12); root.setSpacing(12)

        # Header
        hdr = QHBoxLayout(); hdr.setSpacing(8)
        title = QLabel("Submit Your Project"); title.setStyleSheet("font-size:22px;font-weight:600;color:#0b4d2a;")
        hdr.addWidget(title); hdr.addStretch(1)
        self.btnClose = QPushButton("✕"); self.btnClose.setFixedSize(32, 28)
        hdr.addWidget(self.btnClose)
        root.addLayout(hdr)

        # Two-column body
        body = QHBoxLayout(); body.setSpacing(12)

        # Left: Project Information
        left = QFrame(); left.setFrameShape(QFrame.Shape.StyledPanel); left.setStyleSheet("QFrame{border:1px solid #cbd5e1;border-radius:8px;}")
        leftL = QVBoxLayout(left); leftL.setContentsMargins(14, 14, 14, 14); leftL.setSpacing(10)
        leftL.addWidget(self._section_label("Project Information"))

        grid = QtWidgets.QGridLayout(); grid.setHorizontalSpacing(12); grid.setVerticalSpacing(10)

        self.txtTitle = QLineEdit(); self.txtTitle.setPlaceholderText("Input text")
        self.cmbCategory = QComboBox(); self.cmbCategory.setEditable(True)
        self.cmbCategory.addItems(["capstone", "software", "hardware", "research", "other"])

        self.cmbContext = QComboBox(); self.cmbContext.setEditable(True)
        self.cmbContext.addItems(["mobile", "web", "hardware", "data", "ai", "research", "other"])

        self.txtAuthor = QLineEdit(); self.txtAuthor.setPlaceholderText("Input text")
        self.txtAuthor.setText(_safe_username())

        self.spnCourseId = QSpinBox(); self.spnCourseId.setRange(0, 10_000); self.spnCourseId.setSpecialValueText("None")
        self.spnOrgId = QSpinBox(); self.spnOrgId.setRange(0, 10_000); self.spnOrgId.setSpecialValueText("None")

        self.chkPublic = QCheckBox("Public"); self.chkPublic.setChecked(False)

        self.txtDesc = QTextEdit(); self.txtDesc.setPlaceholderText("Enter Text Here")
        self.txtTags = QLineEdit(); self.txtTags.setPlaceholderText("Tags, comma-separated (optional)")

        r = 0
        grid.addWidget(self._label("Project Title"), r, 0); grid.addWidget(self.txtTitle, r, 1)
        grid.addWidget(self._label("Category"),     r, 2); grid.addWidget(self.cmbCategory, r, 3); r += 1
        grid.addWidget(self._label("Context"),      r, 0); grid.addWidget(self.cmbContext, r, 1)
        grid.addWidget(self._label("Author"),       r, 2); grid.addWidget(self.txtAuthor, r, 3); r += 1
        grid.addWidget(self._label("Course ID"),    r, 0); grid.addWidget(self.spnCourseId, r, 1)
        grid.addWidget(self._label("Organization ID"), r, 2); grid.addWidget(self.spnOrgId, r, 3); r += 1
        grid.addWidget(self.chkPublic, r, 0, 1, 1); r += 1
        grid.addWidget(self._label("Enter Description"), r, 0, 1, 4); r += 1
        grid.addWidget(self.txtDesc, r, 0, 1, 4); r += 1
        grid.addWidget(self._label("Tags"), r, 0, 1, 1); grid.addWidget(self.txtTags, r, 1, 1, 3); r += 1

        leftL.addLayout(grid)
        body.addWidget(left, 2)

        # Right: Uploads
        right = QFrame(); right.setFrameShape(QFrame.Shape.StyledPanel); right.setStyleSheet("QFrame{border:1px solid #cbd5e1;border-radius:8px;}")
        rightL = QVBoxLayout(right); rightL.setContentsMargins(14, 14, 14, 14); rightL.setSpacing(10)
        rightL.addWidget(self._section_label("Supporting Materials (Optional)"))

        self.dropList = DropListWidget()
        self.dropList.setMinimumHeight(260)
        self.dropList.setStyleSheet("QListWidget{border:2px dashed #2b7a4b;border-radius:10px;background:#f8fafc;}")

        hint = QLabel("Drag & drop here or use Browse"); hint.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        hint.setStyleSheet("color:#0b4d2a;")
        rightL.addWidget(self.dropList)
        rightL.addWidget(hint)

        actRow = QHBoxLayout()
        self.btnBrowse = QPushButton("Browse")
        self.btnRemove = QPushButton("Remove selected")
        self.btnClear = QPushButton("Clear all")
        actRow.addWidget(self.btnBrowse); actRow.addWidget(self.btnRemove); actRow.addWidget(self.btnClear); actRow.addStretch(1)
        rightL.addLayout(actRow)

        self.txtLink = QLineEdit(); self.txtLink.setPlaceholderText("e.g. Github repo, website link")
        rightL.addWidget(self._label("Link to Project"))
        rightL.addWidget(self.txtLink)

        body.addWidget(right, 1)
        root.addLayout(body)

        self.btnSubmit = QPushButton("Submit for Review")
        self.btnSubmit.setFixedHeight(36)
        root.addWidget(self.btnSubmit, alignment=Qt.AlignmentFlag.AlignHCenter)

    def _label(self, text: str) -> QLabel:
        l = QLabel(text); l.setStyleSheet("color:#1f2937;")
        return l

    def _section_label(self, text: str) -> QLabel:
        l = QLabel(text); l.setStyleSheet("font-weight:600;color:#1f2937;")
        return l

    # ----- wiring -----
    def _wire(self) -> None:
        self.btnBrowse.clicked.connect(self._browse_files)
        self.btnRemove.clicked.connect(self.dropList.remove_selected)
        self.btnClear.clicked.connect(self.dropList.clear_all)
        self.btnSubmit.clicked.connect(self._submit)
        self.btnClose.clicked.connect(self.request_close.emit)

    def _browse_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self, "Select files", str(Path.home()), "All files (*)")
        for p in files:
            if Path(p).suffix.lower() in FILE_EXTS:
                self.dropList._add_path(p)
        self.dropList.filesChanged.emit()

    def _close_parent(self) -> None:
        w = self.window()
        if hasattr(w, "close"):
            w.close()

    # ----- submit path -----
    def _submit(self) -> None:
        title = self.txtTitle.text().strip()
        if not title:
            QMessageBox.warning(self, "Missing title", "Project Title is required.")
            return

        submitted_by = _lookup_auth_user_id(_safe_user_id())
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        data = {
            "title": title,
            "description": self.txtDesc.toPlainText().strip() or None,
            "submitted_by": submitted_by,
            "course_id": self.spnCourseId.value() or None,
            "organization_id": self.spnOrgId.value() or None,
            "status": "pending",
            "is_public": 1 if self.chkPublic.isChecked() else 0,
            "publish_at": None,
            "created_at": now,
            "updated_at": now,
            "category": self.cmbCategory.currentText().strip() or None,
            "context": self.cmbContext.currentText().strip() or None,
            "external_url": self.txtLink.text().strip() or None,
            "author_display": self.txtAuthor.text().strip() or None,
        }

        try:
            pid = create_project(data)
        except Exception as ex:
            QMessageBox.critical(self, "DB error", f"Failed to create project:\n{ex}")
            return

        # copy files to assets/uploads and map images as media
        rel_paths: List[str] = []
        for src in self.dropList.paths():
            try:
                if Path(src).suffix.lower() in IMAGE_EXTS:  # only images become media rows
                    rp = self._copy_into_images(src)
                    rel_paths.append(rp)
            except Exception as ex:
                print("copy error:", ex)

        if rel_paths:
            try:
                media_ids = seed_images_if_missing(rel_paths, uploaded_by=submitted_by or 1)
                _map_media_to_project(pid, media_ids)
            except Exception as ex:
                QMessageBox.warning(self, "Media warning", f"Saved project but failed to map some media:\n{ex}")

        # tags
        tags_txt = self.txtTags.text().strip()
        if tags_txt:
            try:
                tags = [t.strip() for t in tags_txt.split(",") if t.strip()]
                set_project_tags(pid, tags)
            except Exception as ex:
                QMessageBox.warning(self, "Tags warning", f"Saved project but failed to set tags:\n{ex}")

        QMessageBox.information(self, "Submitted", "Project submitted for review.")
        self._reset_form()

    def _copy_into_images(self, src: str) -> str:
        """Copy to assets/images and return 'assets/images/<file>'."""
        src_path = Path(src)
        dest_name = f"{src_path.stem}_{uuid.uuid4().hex[:8]}{src_path.suffix.lower()}"
        dest = IMAGES_DIR / dest_name
        shutil.copy2(src_path, dest)
        # Always store DB path relative to the repo, matching seed data
        return f"assets/images/{dest_name}"

    def _reset_form(self) -> None:
        self.txtTitle.clear()
        self.cmbCategory.setCurrentIndex(0)
        self.cmbContext.setCurrentIndex(0)
        self.txtAuthor.setText(_safe_username())
        self.spnCourseId.setValue(0)
        self.spnOrgId.setValue(0)
        self.chkPublic.setChecked(False)
        self.txtDesc.clear()
        self.txtTags.clear()
        self.txtLink.clear()
        self.dropList.clear_all()

# quick launcher for standalone test
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = ShowcaseStudentProjectPage()
    w.resize(1080, 720)
    w.show()
    sys.exit(app.exec())
