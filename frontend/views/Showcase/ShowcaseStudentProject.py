# views/Showcase/ShowcaseStudentProject.py
from __future__ import annotations
import shutil, uuid
from datetime import datetime
from pathlib import Path
from typing import List

from PyQt6 import QtGui, QtCore, QtWidgets
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QComboBox,
    QPushButton, QFrame, QListWidget, QListWidgetItem, QFileDialog, QCheckBox,
    QSpinBox, QMessageBox, QScrollArea, QToolButton
)

# DB helpers (package-safe)
try:
    from .db.ShowcaseDBHelper import (
        create_project,
        set_project_tags,
        seed_images_if_missing,
        add_member,
        attach_media_to_project,
        get_auth_user_id_by_username,
        ensure_auth_user,
    )
    from .db.ShowcaseDBInitialize import ensure_bootstrap
except Exception:
    from db.ShowcaseDBHelper import (
        create_project,
        set_project_tags,
        seed_images_if_missing,
        add_member,
        attach_media_to_project,
        get_auth_user_id_by_username,
        ensure_auth_user,
    )
    from db.ShowcaseDBInitialize import ensure_bootstrap


# Optional session bridge
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

# ---------- helper shims ----------
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

# ---------- paths / constants ----------
def _find_images_dir() -> Path:
    here = Path(__file__).resolve()
    for up in range(0, 7):
        base = here.parents[up] if up else here.parent
        cand = base / "assets" / "images"
        if cand.is_dir():
            return cand
    cand = here.parent / "assets" / "images"
    cand.mkdir(parents=True, exist_ok=True)
    return cand

IMAGES_DIR = _find_images_dir()

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
FILE_EXTS  = IMAGE_EXTS | {".pdf", ".mp4", ".mov", ".avi", ".mp3", ".wav", ".txt", ".zip"}

# ---------- DB helpers (no raw SQL here) ----------
def _lookup_auth_user_id(preferred_user_id=None) -> int | None:
    """
    Resolve the auth_user_id for the current session user.

    1) If preferred_user_id is an int-like value, use it.
    2) Otherwise, fall back to username -> auth_user lookup via DB helper.
    """
    if preferred_user_id is not None:
        try:
            return int(preferred_user_id)
        except Exception:
            pass

    uname = _safe_username()
    if not uname:
        return None
    return get_auth_user_id_by_username(uname)


def _ensure_auth_user(username: str) -> int | None:
    """
    Ensure an auth_user record exists for the given username.
    Delegates to ShowcaseDBHelper.ensure_auth_user.
    """
    return ensure_auth_user(username)


def _map_media_to_project(project_id: int, media_ids: List[int]) -> None:
    """
    Map media IDs to a project using the DB helper attach_media_to_project.
    First media is marked primary and sort_order is 1..N.
    """
    if not media_ids:
        return
    for idx, mid in enumerate(media_ids, start=1):
        try:
            attach_media_to_project(
                project_id=project_id,
                media_id=mid,
                is_primary=(idx == 1),
                sort_order=idx,
            )
        except Exception:
            # Let caller handle partial failures via warning.
            continue

# ---------- UI widgets ----------
class DropListWidget(QListWidget):
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
                return QtGui.QIcon(
                    pm.scaled(
                        self.iconSize(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
        return self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileIcon)

    def _open_menu(self, pos: QtCore.QPoint) -> None:
        menu = QtWidgets.QMenu(self)
        act_remove = menu.addAction("Remove selected")
        act_clear = menu.addAction("Clear all")
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
        self.member_rows: list[tuple[QWidget, QLineEdit, QLineEdit, QLineEdit]] = []
        self._build_ui()
        self._wire()

    # ----- helpers -----
    def _label(self, text: str) -> QLabel:
        l = QLabel(text)
        l.setStyleSheet("color:#374151;font-size:12px;")
        return l

    def _section_label(self, text: str) -> QLabel:
        l = QLabel(text)
        l.setStyleSheet("font-weight:600;color:#0b4d2a;")
        return l

    def _card(self) -> QFrame:
        f = QFrame()
        # subtle card: light border + rounded corners
        f.setStyleSheet(
            "QFrame{border:1px solid #e5e7eb;"
            "border-radius:10px;"
            "background:#ffffff;}"
        )
        return f

    # ----- UI -----
    def _build_ui(self) -> None:
        self.setStyleSheet(
            """
            #ShowcaseStudentProjectPage{
                background:#f3f4f6;
            }
            QPushButton{
                background:#15803d;
                color:white;
                border-radius:6px;
                padding:6px 14px;
                border:none;
            }
            QPushButton:hover{
                background:#166534;
            }
            QPushButton#closeButton{
                background:transparent;
                color:#111827;
                border:none;
                padding:0;
                font-size:16px;
            }
            QLineEdit, QTextEdit, QComboBox, QSpinBox{
                background:#f9fafb;
                border:1px solid #e5e7eb;
                border-radius:6px;
                padding:4px 8px;
                font-size:12px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus{
                border-color:#22c55e;
            }
            QCheckBox{
                color:#374151;
                font-size:12px;
            }
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        # Header
        hdr = QHBoxLayout()
        hdr.setSpacing(8)
        title = QLabel("Submit Your Project")
        title.setStyleSheet("font-size:22px;font-weight:600;color:#0b4d2a;")
        hdr.addWidget(title)
        subtitle = QLabel("Share your capstone or project with the showcase committee.")
        subtitle.setStyleSheet("color:#6b7280;font-size:12px;")
        hdr.addWidget(subtitle)
        hdr.addStretch(1)
        self.btnClose = QPushButton("✕")
        self.btnClose.setObjectName("closeButton")
        self.btnClose.setFixedSize(24, 24)
        hdr.addWidget(self.btnClose)
        root.addLayout(hdr)

        # Scrollable body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        root.addWidget(scroll, 1)

        container = QWidget()
        scroll.setWidget(container)
        body = QHBoxLayout(container)
        body.setSpacing(12)

        # Left column ---------------------------------------------------
        leftCol = QVBoxLayout()
        leftCol.setSpacing(10)
        body.addLayout(leftCol, 2)

        # Project details card
        projectCard = self._card()
        projL = QVBoxLayout(projectCard)
        projL.setContentsMargins(14, 12, 14, 12)
        projL.setSpacing(8)
        projL.addWidget(self._section_label("Project Information"))

        grid = QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(6)

        self.txtTitle = QLineEdit()
        self.txtTitle.setPlaceholderText("Project title")
        self.cmbCategory = QComboBox()
        self.cmbCategory.setEditable(True)
        self.cmbCategory.addItems(["capstone", "software", "hardware", "research", "other"])

        self.cmbContext = QComboBox()
        self.cmbContext.setEditable(True)
        self.cmbContext.addItems(["mobile", "web", "hardware", "data", "ai", "research", "other"])

        self.spnCourseId = QSpinBox()
        self.spnCourseId.setRange(0, 10_000)
        self.spnCourseId.setSpecialValueText("None")

        self.spnOrgId = QSpinBox()
        self.spnOrgId.setRange(0, 10_000)
        self.spnOrgId.setSpecialValueText("None")

        self.chkPublic = QCheckBox("Make project public")

        r = 0
        grid.addWidget(self._label("Project Title"), r, 0)
        grid.addWidget(self.txtTitle, r, 1, 1, 3)
        r += 1

        grid.addWidget(self._label("Category"), r, 0)
        grid.addWidget(self.cmbCategory, r, 1)
        grid.addWidget(self._label("Context"), r, 2)
        grid.addWidget(self.cmbContext, r, 3)
        r += 1

        grid.addWidget(self._label("Course ID"), r, 0)
        grid.addWidget(self.spnCourseId, r, 1)
        grid.addWidget(self._label("Organization ID"), r, 2)
        grid.addWidget(self.spnOrgId, r, 3)
        r += 1

        grid.addWidget(self.chkPublic, r, 0, 1, 4)
        r += 1

        projL.addLayout(grid)
        leftCol.addWidget(projectCard)

        # Team / group members card
        teamCard = self._card()
        teamL = QVBoxLayout(teamCard)
        teamL.setContentsMargins(14, 12, 14, 12)
        teamL.setSpacing(8)
        teamL.addWidget(self._section_label("Team & Group Members"))

        authorGrid = QtWidgets.QGridLayout()
        authorGrid.setHorizontalSpacing(10)
        authorGrid.setVerticalSpacing(6)

        self.txtAuthor = QLineEdit()
        self.txtAuthor.setPlaceholderText("Lead author / leader")
        self.txtAuthor.setText(_safe_username())

        authorGrid.addWidget(self._label("Leader / Main Author"), 0, 0)
        authorGrid.addWidget(self.txtAuthor, 0, 1)
        teamL.addLayout(authorGrid)

        membersHeader = QHBoxLayout()
        membersHeader.addWidget(self._label("Group Members"))
        membersHeader.addStretch(1)
        self.btnAddMember = QPushButton("+ Add member")
        self.btnAddMember.setFixedHeight(26)
        self.btnAddMember.setStyleSheet(
            "QPushButton{background:#e5f3ec;color:#166534;border-radius:6px;"
            "padding:4px 10px;border:none;font-size:11px;}"
            "QPushButton:hover{background:#d1fae5;}"
        )
        membersHeader.addWidget(self.btnAddMember)
        teamL.addLayout(membersHeader)

        self.membersContainer = QVBoxLayout()
        self.membersContainer.setSpacing(6)
        teamL.addLayout(self.membersContainer)
        self._add_member_row()

        tip = QLabel("Optional: add your group mates, their roles, and main contributions.")
        tip.setStyleSheet("color:#6b7280;font-size:11px;")
        teamL.addWidget(tip)

        leftCol.addWidget(teamCard)

        # Description / tags card
        descCard = self._card()
        descL = QVBoxLayout(descCard)
        descL.setContentsMargins(14, 12, 14, 12)
        descL.setSpacing(8)

        descL.addWidget(self._section_label("Project Description"))

        self.txtDesc = QTextEdit()
        self.txtDesc.setPlaceholderText(
            "Describe what your project does, key features, and technologies used."
        )
        self.txtDesc.setMinimumHeight(140)
        descL.addWidget(self.txtDesc)

        tagsRow = QHBoxLayout()
        tagsRow.addWidget(self._label("Tags"))
        tagsRow.addStretch(1)
        descL.addLayout(tagsRow)

        self.txtTags = QLineEdit()
        self.txtTags.setPlaceholderText(
            "Tags, comma-separated (e.g. IoT, Android, Agriculture)"
        )
        descL.addWidget(self.txtTags)

        leftCol.addWidget(descCard)
        leftCol.addStretch(1)

        # Right column --------------------------------------------------
        rightCol = QVBoxLayout()
        rightCol.setSpacing(10)
        body.addLayout(rightCol, 1)

        # Supporting materials
        rightCard = self._card()
        rightL = QVBoxLayout(rightCard)
        rightL.setContentsMargins(14, 12, 14, 12)
        rightL.setSpacing(8)
        rightL.addWidget(self._section_label("Supporting Materials (Optional)"))

        self.dropList = DropListWidget()
        self.dropList.setMinimumHeight(260)
        self.dropList.setStyleSheet(
            "QListWidget{border:2px dashed #22c55e;"
            "border-radius:10px;background:#f8fafc;}"
        )
        rightL.addWidget(self.dropList)

        hint = QLabel("Drag & drop files here or use Browse.")
        hint.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        hint.setStyleSheet("color:#0b4d2a;font-size:11px;")
        rightL.addWidget(hint)

        actRow = QHBoxLayout()
        self.btnBrowse = QPushButton("Browse")
        self.btnRemove = QPushButton("Remove selected")
        self.btnClear = QPushButton("Clear all")
        for b in (self.btnBrowse, self.btnRemove, self.btnClear):
            b.setFixedHeight(28)
            b.setStyleSheet(
                "QPushButton{background:#15803d;color:white;border-radius:6px;"
                "padding:4px 10px;font-size:11px;}"
                "QPushButton:hover{background:#166534;}"
            )
        actRow.addWidget(self.btnBrowse)
        actRow.addWidget(self.btnRemove)
        actRow.addWidget(self.btnClear)
        actRow.addStretch(1)
        rightL.addLayout(actRow)

        rightCol.addWidget(rightCard)

        # Link card
        linkCard = self._card()
        linkL = QVBoxLayout(linkCard)
        linkL.setContentsMargins(14, 12, 14, 12)
        linkL.setSpacing(6)
        linkL.addWidget(self._section_label("Online Link"))

        self.txtLink = QLineEdit()
        self.txtLink.setPlaceholderText(
            "e.g. GitHub repository, project website, demo video link"
        )
        linkL.addWidget(self.txtLink)

        small = QLabel("Optional but recommended if you host your code or demo online.")
        small.setStyleSheet("color:#6b7280;font-size:11px;")
        linkL.addWidget(small)

        rightCol.addWidget(linkCard)
        rightCol.addStretch(1)

        # Footer buttons
        footer = QHBoxLayout()
        footer.setContentsMargins(0, 4, 0, 0)
        footer.addStretch(1)
        self.btnSubmit = QPushButton("Submit for Review")
        self.btnSubmit.setFixedHeight(36)
        footer.addWidget(self.btnSubmit)
        root.addLayout(footer)

    # ----- member rows -----
    def _add_member_row(self, name: str = "", role: str = "", contrib: str = "") -> None:
        rowWidget = QWidget()
        rowLayout = QHBoxLayout(rowWidget)
        rowLayout.setContentsMargins(0, 0, 0, 0)
        rowLayout.setSpacing(6)

        nameEdit = QLineEdit()
        nameEdit.setPlaceholderText("Full name")
        nameEdit.setText(name)

        roleEdit = QLineEdit()
        roleEdit.setPlaceholderText("Role (e.g. Developer)")
        roleEdit.setText(role)

        contribEdit = QLineEdit()
        contribEdit.setPlaceholderText("Main contribution")
        contribEdit.setText(contrib)

        removeBtn = QToolButton()
        removeBtn.setText("✕")
        removeBtn.setToolTip("Remove member")
        removeBtn.setStyleSheet(
            "QToolButton{border:none;background:transparent;color:#9ca3af;font-size:12px;}"
            "QToolButton:hover{color:#b91c1c;}"
        )
        removeBtn.clicked.connect(lambda _=False, w=rowWidget: self._remove_member_row(w))

        rowLayout.addWidget(nameEdit, 2)
        rowLayout.addWidget(roleEdit, 1)
        rowLayout.addWidget(contribEdit, 2)
        rowLayout.addWidget(removeBtn)

        self.membersContainer.addWidget(rowWidget)
        self.member_rows.append((rowWidget, nameEdit, roleEdit, contribEdit))

    def _remove_member_row(self, rowWidget: QWidget) -> None:
        for idx, (w, _, _, _) in enumerate(self.member_rows):
            if w is rowWidget:
                self.member_rows.pop(idx)
                break
        rowWidget.setParent(None)

    def _collect_members(self) -> list[tuple[str, str, str]]:
        collected: list[tuple[str, str, str]] = []
        for _, nameEdit, roleEdit, contribEdit in self.member_rows:
            name = nameEdit.text().strip()
            role = roleEdit.text().strip()
            contrib = contribEdit.text().strip()
            if name:
                collected.append((name, role, contrib))
        return collected

    def _reset_members(self) -> None:
        for w, _, _, _ in self.member_rows:
            w.setParent(None)
        self.member_rows.clear()
        self._add_member_row()

    # ----- wiring -----
    def _wire(self) -> None:
        self.btnBrowse.clicked.connect(self._browse_files)
        self.btnRemove.clicked.connect(self.dropList.remove_selected)
        self.btnClear.clicked.connect(self.dropList.clear_all)
        self.btnSubmit.clicked.connect(self._submit)
        self.btnClose.clicked.connect(self.request_close.emit)
        self.btnAddMember.clicked.connect(lambda: self._add_member_row())

    def _browse_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select files", str(Path.home()), "All files (*)"
        )
        for p in files:
            if Path(p).suffix.lower() in FILE_EXTS:
                self.dropList._add_path(p)
        self.dropList.filesChanged.emit()

    # ----- submit -----
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

        # media
        rel_paths: List[str] = []
        for src in self.dropList.paths():
            try:
                if Path(src).suffix.lower() in IMAGE_EXTS:
                    rp = self._copy_into_images(src)
                    rel_paths.append(rp)
            except Exception as ex:
                print("copy error:", ex)

        if rel_paths:
            try:
                media_ids = seed_images_if_missing(rel_paths, uploaded_by=submitted_by or 1)
                _map_media_to_project(pid, media_ids)
            except Exception as ex:
                QMessageBox.warning(
                    self,
                    "Media warning",
                    f"Saved project but failed to map some media:\n{ex}",
                )

        # tags
        tags_txt = self.txtTags.text().strip()
        if tags_txt:
            try:
                tags = [t.strip() for t in tags_txt.split(",") if t.strip()]
                set_project_tags(pid, tags)
            except Exception as ex:
                QMessageBox.warning(
                    self,
                    "Tags warning",
                    f"Saved project but failed to set tags:\n{ex}",
                )

        # group members -> project_members
        members = self._collect_members()
        if members:
            try:
                for name, role, contrib in members:
                    user_id = _ensure_auth_user(name)
                    add_member(pid, user_id, role or None, contrib or None)
            except Exception as ex:
                QMessageBox.warning(
                    self,
                    "Members warning",
                    f"Saved project but failed to record some group members:\n{ex}",
                )

        QMessageBox.information(self, "Submitted", "Project submitted for review.")
        self._reset_form()

    def _copy_into_images(self, src: str) -> str:
        src_path = Path(src)
        dest_name = f"{src_path.stem}_{uuid.uuid4().hex[:8]}{src_path.suffix.lower()}"
        dest = IMAGES_DIR / dest_name
        shutil.copy2(src_path, dest)
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
        self._reset_members()


# quick launcher
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = ShowcaseStudentProjectPage()
    w.resize(1080, 720)
    w.show()
    sys.exit(app.exec())
