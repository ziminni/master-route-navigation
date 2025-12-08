from __future__ import annotations

import os, shutil, uuid, importlib
from pathlib import Path
from typing import List, Optional

from PyQt6 import QtGui, QtCore, QtWidgets
from PyQt6.QtCore import Qt, QDateTime, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QPushButton,
    QFrame,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QMessageBox,
    QScrollArea,
    QDateTimeEdit,
    QCheckBox,
    QSpinBox,
    QGraphicsDropShadowEffect,
)

HERE = Path(__file__).resolve().parent

# ---- DB bootstrap (works as package or script) ----
try:
    from db.AnnouncementDBInitialize import db_path, ensure_bootstrap
except Exception:
    DB_DIR = HERE / "db"
    DB_DIR.mkdir(parents=True, exist_ok=True)
    import sys

    sys.path.insert(0, str(DB_DIR))
    from AnnouncementDBInitialize import db_path, ensure_bootstrap  # type: ignore

# ---- DB helper facade ----
try:
    from db.AnnouncementDBHelper import (
        add_announcement,
        add_document,
        set_tags,
        add_audience_scope,
        get_user_id_by_username,
    )
except Exception:
    import sys

    DB_DIR = HERE / "db"
    DB_DIR.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(DB_DIR))
    from AnnouncementDBHelper import (  # type: ignore
        add_announcement,
        add_document,
        set_tags,
        add_audience_scope,
        get_user_id_by_username,
    )

# ---- optional session bridge ----
_session_mod = None
try:
    _session_mod = importlib.import_module("utils")
except Exception:
    _session_mod = None

session = getattr(_session_mod, "session", None)
if session is None:

    class _S:
        @staticmethod
        def get_username():
            return "org_officer"

        @staticmethod
        def get_user_id():
            return None

    session = _S()


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


# ---- assets / paths ----
def _project_root() -> Path:
    for up in range(0, 7):
        base = HERE.parents[up] if up else HERE
        if (base / "assets").exists():
            return base
    return Path.cwd()


ASSETS = _project_root() / "assets"
IMAGES_DIR = ASSETS / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def _icon(name: str) -> Optional[QtGui.QIcon]:
    p = ASSETS / "icons" / name
    return QtGui.QIcon(str(p)) if p.is_file() else None


# ---- upload widget ----
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}


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
            if Path(p).suffix.lower() in IMAGE_EXTS:
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
        item = QListWidgetItem(Path(path).name)
        item.setToolTip(path)
        item.setData(Qt.ItemDataRole.UserRole, path)
        pm = QtGui.QPixmap(path)
        if not pm.isNull():
            item.setIcon(
                QtGui.QIcon(
                    pm.scaled(
                        self.iconSize(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
            )
        else:
            item.setIcon(
                self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileIcon)
            )
        self.addItem(item)

    def _open_menu(self, pos: QtCore.QPoint) -> None:
        menu = QtWidgets.QMenu(self)
        a1 = menu.addAction("Remove selected")
        a2 = menu.addAction("Clear all")
        act = menu.exec(self.mapToGlobal(pos))
        if act == a1:
            self.remove_selected()
        elif act == a2:
            self.clear_all()

    def remove_selected(self) -> None:
        for it in list(self.selectedItems()):
            p = it.data(Qt.ItemDataRole.UserRole)
            if p in self._paths:
                self._paths.remove(p)
            self.takeItem(self.row(it))
        self.filesChanged.emit()

    def clear_all(self) -> None:
        self._paths.clear()
        self.clear()
        self.filesChanged.emit()

    def paths(self) -> List[str]:
        return list(self._paths)


# ---- UI theme ----
GREEN = "#146c43"
TEXT = "#1f2937"
BG = "#f3f4f6"
BORDER = "#e5e7eb"
WHITE = "#ffffff"


class AnnouncementOrganizationAnnouncementPage(QWidget):
    request_close = QtCore.pyqtSignal()  # legacy
    back_requested = QtCore.pyqtSignal()
    submitted = QtCore.pyqtSignal(int)  # emits announcement_id

    def __init__(self, parent=None):
        super().__init__(parent)
        ensure_bootstrap()
        self.setMinimumSize(1100, 680)
        self._apply_theme()
        self._build_ui()
        self._wire()

    # ---------- theme ----------
    def _apply_theme(self) -> None:
        self.setStyleSheet(
            f"""
            QWidget {{
                background: #f3f4f6;
                color: {TEXT};
                font-family: "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont;
                font-size: 10pt;
            }}
            QFrame#HeaderBar {{
                background: {GREEN};
                border-radius: 10px;
            }}
            QFrame#Card {{
                background: {WHITE};
                border-radius: 12px;
                border: 1px solid {BORDER};
            }}
            QLineEdit,
            QComboBox,
            QTextEdit,
            QDateTimeEdit,
            QSpinBox {{
                background: {WHITE};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 6px 10px;
            }}
            QLineEdit:focus,
            QComboBox:focus,
            QTextEdit:focus,
            QDateTimeEdit:focus,
            QSpinBox:focus {{
                border: 1px solid {GREEN};
            }}
            QScrollArea {{
                border: none;
            }}
            QListWidget {{
                border: 2px dashed #2b7a4b;
                border-radius: 10px;
                background: #f9fafb;
            }}
            QPushButton#primaryButton {{
                background: {GREEN};
                color: white;
                border: none;
                border-radius: 999px;
                padding: 8px 28px;
                font-weight: 600;
            }}
            QPushButton#primaryButton:hover {{
                background: #0f5132;
            }}
            QPushButton#primaryButton:disabled {{
                background: #9ca3af;
            }}
            QPushButton#menuButton,
            QPushButton#closeButton {{
                background: {WHITE};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
            QPushButton#menuButton:hover,
            QPushButton#closeButton:hover {{
                background: transparent;
                border: none;
            }}
            """
        )

    def _add_shadow(self, widget: QWidget, radius: int = 18, y_offset: int = 8) -> None:
        eff = QGraphicsDropShadowEffect(widget)
        eff.setBlurRadius(radius)
        eff.setXOffset(0)
        eff.setYOffset(y_offset)
        eff.setColor(QtGui.QColor(15, 23, 42, 50))
        widget.setGraphicsEffect(eff)

    # ---------- UI build ----------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # Header row
        hdr = QHBoxLayout()
        hdr.setSpacing(8)

        btnMenu = QPushButton()
        btnMenu.setObjectName("menuButton")
        btnMenu.setFixedSize(36, 36)
        btnMenu.setCursor(Qt.CursorShape.PointingHandCursor)
        ico = _icon("icon_menu.png")
        if ico:
            btnMenu.setIcon(ico)

        title = QLabel("Announcements")
        title.setStyleSheet(
            f"color:{GREEN};font-size:22px;font-weight:700;letter-spacing:0.5px;"
        )

        hdr.addWidget(btnMenu, 0)
        hdr.addWidget(title, 0)
        hdr.addStretch(1)
        root.addLayout(hdr)

        # Green header bar
        cap = QFrame()
        cap.setObjectName("HeaderBar")
        capL = QHBoxLayout(cap)
        capL.setContentsMargins(16, 10, 12, 10)
        capL.setSpacing(8)

        t = QLabel("Submit Announcement")
        t.setStyleSheet(
            "background: transparent;"
            "color:white;"
            "font-size:18px;"
            "font-weight:600;"
        )
        capL.addWidget(t)
        capL.addStretch(1)

        btnClose = QPushButton()
        btnClose.setObjectName("closeButton")
        btnClose.setCursor(Qt.CursorShape.PointingHandCursor)
        btnClose.setFixedSize(28, 28)
        xico = _icon("icon_close2.png") or _icon("icon_close.png")
        if xico:
            btnClose.setIcon(xico)
        else:
            btnClose.setText("×")
        btnClose.clicked.connect(
            lambda: (self.request_close.emit(), self.back_requested.emit())
        )
        capL.addWidget(btnClose)

        self._add_shadow(cap, radius=18, y_offset=6)
        root.addWidget(cap)

        # Scrollable form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        host = QWidget()
        scroll.setWidget(host)
        form = QVBoxLayout(host)
        form.setContentsMargins(4, 16, 4, 16)
        form.setSpacing(16)

        # Main card
        panel = QFrame()
        panel.setObjectName("Card")
        panelL = QVBoxLayout(panel)
        panelL.setContentsMargins(16, 16, 16, 16)
        panelL.setSpacing(18)
        self._add_shadow(panel, radius=22, y_offset=10)

        # Row 0: Post To + Visibility
        r0 = QHBoxLayout()
        r0.setSpacing(16)

        self.cboPost = QComboBox()
        self.cboPost.addItems(["General", "Students", "Faculty", "Organization"])
        self.cboPost.setMinimumWidth(200)
        self._label_wrap(r0, "Post To", self.cboPost)

        self.cboVisibility = QComboBox()
        self.cboVisibility.addItems(["public", "private"])
        self.cboVisibility.setMinimumWidth(160)
        self._label_wrap(r0, "Visibility", self.cboVisibility)

        r0.addStretch(1)
        panelL.addLayout(r0)

        # Row 1: Title + Location
        r1 = QHBoxLayout()
        r1.setSpacing(16)

        self.txtTitle = QLineEdit()
        self.txtTitle.setPlaceholderText("Enter announcement title")
        self.txtTitle.setMinimumWidth(420)
        self._label_wrap(r1, "Title", self.txtTitle, stretch=2)

        self.txtLocation = QLineEdit()
        self.txtLocation.setPlaceholderText("Optional location")
        self._label_wrap(r1, "Location", self.txtLocation, stretch=1)
        panelL.addLayout(r1)

        # Row 2: Dates
        r2 = QHBoxLayout()
        r2.setSpacing(16)

        self.dtPublish = QDateTimeEdit(QDateTime.currentDateTime())
        self.dtPublish.setCalendarPopup(True)
        self.dtPublish.setDisplayFormat("yyyy-MM-dd HH:mm")
        self._label_wrap(r2, "Publish at", self.dtPublish)

        self.dtExpire = QDateTimeEdit()
        self.dtExpire.setCalendarPopup(True)
        self.dtExpire.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.dtExpire.setSpecialValueText("None")
        self.dtExpire.setDateTimeRange(
            QDateTime.fromString("1900-01-01 00:00", "yyyy-MM-dd HH:mm"),
            QDateTime.fromString("2999-12-31 23:59", "yyyy-MM-dd HH:mm"),
        )
        self.dtExpire.setDateTime(self.dtPublish.dateTime().addDays(7))
        self._label_wrap(r2, "Expire at", self.dtExpire)
        r2.addStretch(1)
        panelL.addLayout(r2)

        # Row 3: Priority + Pinned + Pinned until
        r3 = QHBoxLayout()
        r3.setSpacing(16)

        self.spnPriority = QSpinBox()
        self.spnPriority.setRange(0, 9)
        self.spnPriority.setValue(0)
        self._label_wrap(r3, "Priority", self.spnPriority)

        pinnedCol = QVBoxLayout()
        pinnedCol.setSpacing(4)

        self.chkPinned = QCheckBox("Pinned")
        self.chkPinned.stateChanged.connect(self._toggle_pinned_until)
        self.chkPinned.setStyleSheet("font-weight:500;color:#374151;")
        pinnedCol.addWidget(self.chkPinned)

        lblPinnedUntil = QLabel("Pinned until")
        lblPinnedUntil.setStyleSheet(
            "color:#4b5563;font-weight:600;font-size:10pt;margin-bottom:2px;"
        )
        pinnedCol.addWidget(lblPinnedUntil)

        self.dtPinnedUntil = QDateTimeEdit()
        self.dtPinnedUntil.setCalendarPopup(True)
        self.dtPinnedUntil.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.dtPinnedUntil.setEnabled(False)
        pinnedCol.addWidget(self.dtPinnedUntil)

        r3.addLayout(pinnedCol)
        r3.addStretch(1)
        panelL.addLayout(r3)

        # Row 4: Two-column body + uploads
        bodyRow = QHBoxLayout()
        bodyRow.setSpacing(18)

        # left column: message + note
        left = QVBoxLayout()
        left.setSpacing(12)

        lblMsg = QLabel("Message")
        lblMsg.setStyleSheet(
            "color:#4b5563;font-weight:600;font-size:10pt;margin-bottom:2px;"
        )
        self.txtBody = QTextEdit()
        self.txtBody.setPlaceholderText("Write the announcement message here.")
        self.txtBody.setFixedHeight(220)

        left.addWidget(lblMsg)
        left.addWidget(self.txtBody)

        lblNote = QLabel("Note to admin (optional)")
        lblNote.setStyleSheet(
            "color:#6b7280;font-weight:500;font-size:9.5pt;margin-top:4px;"
        )
        self.txtNote = QTextEdit()
        self.txtNote.setPlaceholderText(
            "Internal note to admin. Not visible to students."
        )
        self.txtNote.setFixedHeight(120)

        left.addWidget(lblNote)
        left.addWidget(self.txtNote)

        bodyRow.addLayout(left, 1)

        # right column: uploads + tags
        right = QVBoxLayout()
        right.setSpacing(10)

        lblUp = QLabel("Photos / screenshots")
        lblUp.setStyleSheet(
            "color:#4b5563;font-weight:600;font-size:10pt;margin-bottom:2px;"
        )
        self.dropList = DropListWidget()
        self.dropList.setMinimumHeight(260)

        hint = QLabel("Drag and drop images here, or use Browse.")
        hint.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        hint.setStyleSheet("color:#059669;font-size:9.5pt;")

        acts = QHBoxLayout()
        acts.setSpacing(8)
        self.btnBrowse = QPushButton("Browse")
        self.btnRemove = QPushButton("Remove selected")
        self.btnClear = QPushButton("Clear all")
        for b in (self.btnBrowse, self.btnRemove, self.btnClear):
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(
                f"QPushButton{{background:#f9fafb;border:1px solid {BORDER};"
                "border-radius:6px;padding:4px 10px;font-weight:500;}}"
                "QPushButton:hover{background:#e5e7eb;}"
            )
        acts.addWidget(self.btnBrowse)
        acts.addWidget(self.btnRemove)
        acts.addWidget(self.btnClear)
        acts.addStretch(1)

        lblTags = QLabel("Tags")
        lblTags.setStyleSheet(
            "color:#4b5563;font-weight:600;font-size:10pt;margin-top:4px;"
        )
        self.txtTags = QLineEdit()
        self.txtTags.setPlaceholderText(
            "Tags, comma-separated (optional), e.g. schedule, faculty, freshmen"
        )

        right.addWidget(lblUp)
        right.addWidget(self.dropList)
        right.addWidget(hint)
        right.addLayout(acts)
        right.addWidget(lblTags)
        right.addWidget(self.txtTags)

        bodyRow.addLayout(right, 1)
        panelL.addLayout(bodyRow)

        form.addWidget(panel)
        root.addWidget(scroll, 1)

        # Submit button row
        self.btnSubmit = QPushButton("Post for approval")
        self.btnSubmit.setObjectName("primaryButton")
        self.btnSubmit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnSubmit.setFixedHeight(38)
        self.btnSubmit.setFixedWidth(220)

        bb = QHBoxLayout()
        bb.addStretch(1)
        bb.addWidget(self.btnSubmit, 0)
        bb.addStretch(1)
        root.addLayout(bb)

    # ---------- helpers ----------
    def _label_wrap(
        self,
        layout: QHBoxLayout,
        label: str,
        widget: QtWidgets.QWidget,
        stretch: int = 0,
    ) -> None:
        col = QVBoxLayout()
        col.setSpacing(4)
        lbl = QLabel(label)
        lbl.setStyleSheet(
            "color:#4b5563;font-weight:600;font-size:10pt;margin-bottom:2px;"
        )
        col.addWidget(lbl)
        col.addWidget(widget)
        if stretch:
            layout.addLayout(col, stretch)
        else:
            layout.addLayout(col)

    def _toggle_pinned_until(self) -> None:
        self.dtPinnedUntil.setEnabled(self.chkPinned.isChecked())
        if self.chkPinned.isChecked() and not self.dtPinnedUntil.dateTime().isValid():
            self.dtPinnedUntil.setDateTime(self.dtPublish.dateTime().addDays(1))

    def _wire(self) -> None:
        self.btnBrowse.clicked.connect(self._browse_files)
        self.btnRemove.clicked.connect(self.dropList.remove_selected)
        self.btnClear.clicked.connect(self.dropList.clear_all)
        self.btnSubmit.clicked.connect(self._submit)

    # ---- actions ----
    def _browse_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select images",
            str(Path.home()),
            "Images (*.png *.jpg *.jpeg *.gif *.bmp *.webp);;All files (*)",
        )
        for p in files:
            if Path(p).suffix.lower() in IMAGE_EXTS:
                self.dropList._add_path(p)
        self.dropList.filesChanged.emit()

    def _submit(self) -> None:
        title = self.txtTitle.text().strip()
        body = self.txtBody.toPlainText().strip()
        if not title:
            QMessageBox.warning(self, "Missing title", "Title is required.")
            return
        if not body:
            QMessageBox.warning(self, "Missing message", "Message is required.")
            return

        # resolve user_id: prefer session user_id, fall back to username lookup, then 1
        preferred_id = _safe_user_id()
        if preferred_id is not None:
            user_id = preferred_id
        else:
            uname = _safe_username()
            user_id = get_user_id_by_username(uname) or 1

        def _fmt_utc(dt: QDateTime) -> str:
            return dt.toUTC().toString("yyyy-MM-dd HH:mm:ss")

        publish_at = _fmt_utc(self.dtPublish.dateTime())
        expire_at = (
            _fmt_utc(self.dtExpire.dateTime())
            if self.dtExpire.dateTime().isValid()
            else None
        )
        pinned_until = (
            _fmt_utc(self.dtPinnedUntil.dateTime())
            if (self.chkPinned.isChecked() and self.dtPinnedUntil.isEnabled())
            else None
        )

        scope_map = {
            "General": "general",
            "Students": "students",
            "Faculty": "faculty",
            "Organization": "organization",
        }
        scope_type = scope_map.get(self.cboPost.currentText(), "general")
        visibility = self.cboVisibility.currentText()

        try:
            # create pending announcement via DB helper
            ann_id = add_announcement(
                title=title,
                body=body,
                author_id=user_id,
                publish_at=publish_at,
                expire_at=expire_at,
                location=(self.txtLocation.text().strip() or None),
                status="pending",
                visibility=visibility,
                priority=int(self.spnPriority.value()),
                is_pinned=1 if self.chkPinned.isChecked() else 0,
                pinned_until=pinned_until,
                note=(self.txtNote.toPlainText().strip() or None),
                created_by=user_id,
            )

            # audience scope record
            add_audience_scope(ann_id, scope_type)

            # documents
            for src in self.dropList.paths():
                rel = self._copy_into_images(src)
                full = IMAGES_DIR / Path(rel).name
                try:
                    size = os.path.getsize(full)
                except OSError:
                    size = 0
                add_document(
                    ann_id,
                    file_name=Path(rel).name,
                    file_path=rel,
                    mime_type=_mime_for(rel),
                    file_size_bytes=int(size),
                    uploaded_by=user_id,
                )

            # tags
            tags_txt = self.txtTags.text().strip()
            if tags_txt:
                tags = [t.strip() for t in tags_txt.split(",") if t.strip()]
                if tags:
                    set_tags(ann_id, tags)

        except Exception as ex:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to submit announcement:\n{ex}",
            )
            return

        QMessageBox.information(
            self,
            "Submitted",
            f"Announcement #{ann_id} submitted for review.",
        )
        self.submitted.emit(ann_id)
        self.back_requested.emit()
        self.request_close.emit()
        self._reset_form()

    # ---- helpers ----
    def _copy_into_images(self, src: str) -> str:
        src_path = Path(src)
        dest_name = (
            f"{src_path.stem}_{uuid.uuid4().hex[:8]}{src_path.suffix.lower()}"
        )
        dest = IMAGES_DIR / dest_name
        shutil.copy2(src_path, dest)
        return f"assets/images/{dest_name}"

    def _reset_form(self) -> None:
        self.cboPost.setCurrentIndex(0)
        self.cboVisibility.setCurrentIndex(0)
        self.txtTitle.clear()
        self.txtLocation.clear()
        self.dtPublish.setDateTime(QDateTime.currentDateTime())
        self.dtExpire.setDateTime(self.dtPublish.dateTime().addDays(7))
        self.spnPriority.setValue(0)
        self.chkPinned.setChecked(False)
        self.dtPinnedUntil.setEnabled(False)
        self.txtBody.clear()
        self.txtNote.clear()
        self.txtTags.clear()
        self.dropList.clear_all()


def _mime_for(rel_path: str) -> str:
    ext = Path(rel_path).suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
        ".webp": "image/webp",
    }.get(ext, "application/octet-stream")


# Back-compat alias
AnnouncementOrganizationAnnouncement = AnnouncementOrganizationAnnouncementPage

# ---- run ----
if __name__ == "__main__":
    ensure_bootstrap()
    app = QApplication([])
    w = AnnouncementOrganizationAnnouncementPage()
    w.resize(1120, 720)
    w.show()
    app.exec()
