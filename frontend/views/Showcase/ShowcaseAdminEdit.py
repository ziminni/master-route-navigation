from __future__ import annotations
import os, shutil, time
from pathlib import Path
from typing import Any, Dict, List, Optional

from datetime import datetime

from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QFileDialog,
    QMessageBox,
    QSizePolicy,
    QCheckBox,
    QScrollArea,
)

# ---------- theme ----------
GREEN = "#146c43"
TEXT = "#1f2937"
MUTED = "#6b7280"
BG = "#f3f4f6"
BORDER = "#e5e7eb"


# ---------- assets ----------
def _find_dir(name: str) -> Path:
    here = Path(__file__).resolve()
    for up in range(0, 7):
        base = here.parents[up] if up else here.parent
        p = base / "assets" / name
        if p.is_dir():
            return p
    p = Path(os.getcwd()) / "assets" / name
    p.mkdir(parents=True, exist_ok=True)
    return p


ICON_DIR = _find_dir("icons")
IMG_DIR = _find_dir("images")


def _icon(fname: str) -> QIcon:
    p = ICON_DIR / fname
    return QIcon(str(p)) if p.exists() else QIcon()


def _pm_or_placeholder(w: int, h: int, path: Optional[str]) -> QPixmap:
    def _resolve(pstr: str) -> Optional[Path]:
        p = Path(pstr)
        if p.is_absolute() and p.exists():
            return p
        p2 = Path(os.getcwd()) / pstr
        if p2.exists():
            return p2
        assets_dir = ICON_DIR.parent
        proj_root = assets_dir.parent
        p3 = proj_root / pstr
        if p3.exists():
            return p3
        p4 = IMG_DIR / p.name
        if p4.exists():
            return p4
        return None

    if path:
        rp = _resolve(path)
        if rp:
            pm = QPixmap(str(rp))
            if not pm.isNull():
                return pm.scaled(
                    w,
                    h,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
    pm = QPixmap(w, h)
    pm.fill(Qt.GlobalColor.lightGray)
    return pm


def _now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------- DB (all DB work via helpers only) ----------
try:
    from .db.ShowcaseDBHelper import (
        list_project_media,
        list_competition_media,
        update_project,
        delete_project,
        get_project,
        get_competition,
        update_competition,
        delete_competition,
        remove_project_media_link,
        remove_competition_media_link,
        seed_images_if_missing,
        attach_media_to_project,
        attach_media_to_competition,
        list_showcase_categories,
        list_achievements,
        create_achievement,
        update_achievement,
        delete_achievement,
    )
except Exception:
    from db.ShowcaseDBHelper import (
        list_project_media,
        list_competition_media,
        update_project,
        delete_project,
        get_project,
        get_competition,
        update_competition,
        delete_competition,
        remove_project_media_link,
        remove_competition_media_link,
        seed_images_if_missing,
        attach_media_to_project,
        attach_media_to_competition,
        list_showcase_categories,
        list_achievements,
        create_achievement,
        update_achievement,
        delete_achievement,
    )


# ---------- page ----------
class ShowcaseAdminEditDialog(QWidget):
    """
    Stack page for editing a showcase entry.

    kind: 'project' or 'competition'
    item_id: projects_id or competition_id
    """

    back_requested = pyqtSignal()
    saved = pyqtSignal()
    deleted = pyqtSignal()

    def __init__(self, kind: str, item_id: int, parent: QWidget | None = None):
        super().__init__(parent)
        assert kind in ("project", "competition")
        self.kind = kind
        self.item_id = int(item_id)

        self.media: List[Dict[str, Any]] = []
        self.media_index = 0

        self.achievements: List[Dict[str, Any]] = []
        self.current_ach_id: Optional[int] = None

        self.setObjectName("EditDlg")
        self.setMinimumSize(1000, 620)
        self.setStyleSheet(
            f"""
            QWidget#EditDlg {{
                background: transparent;
                border: none;
            }}
            QFrame#card {{
                background: white;
                border: 1px solid {GREEN};
                border-radius: 12px;
            }}
            QLabel#title {{
                background: transparent;
                color:white;
                font-size:22px;
                font-weight:700;
                border:none;
                padding:0px;
                margin:0px;
            }}
            QFrame#hdr {{
                background:{GREEN};
                border-top-left-radius:12px;
                border-top-right-radius:12px;
            }}
            QLabel[role="label"] {{
                color:{MUTED};
                font-size:12px;
            }}
            QLabel[role="section"] {{
                color:{TEXT};
                font-size:13px;
                font-weight:600;
                margin-top:4px;
            }}
            QLineEdit, QTextEdit, QComboBox {{
                background:white;
                color:{TEXT};
                border:1px solid {BORDER};
                border-radius:8px;
                padding:6px;
            }}
            QCheckBox {{
                color:{TEXT};
            }}
            QPushButton[kind="pri"] {{
                background:{GREEN};
                color:white;
                border:none;
                border-radius:8px;
                padding:8px 14px;
            }}
            QPushButton[kind="ghost"] {{
                background:transparent;
                color:{GREEN};
                border:1px solid {GREEN};
                border-radius:18px;
                padding:6px 10px;
            }}
            QPushButton[kind="danger"] {{
                background:#dc3545;
                color:white;
                border:none;
                border-radius:8px;
                padding:8px 14px;
            }}
            QPushButton#closeBtn {{
                background-color: transparent;
                color: white;
                border: none;
                font-size: 18px;
                font-weight: 700;
                min-width: 32px;
                min-height: 32px;
            }}
            """
        )

        # outer layout
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # card frame (white rounded rectangle)
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)
        root.addWidget(card)

        # ----- header -----
        hdr = QFrame()
        hdr.setObjectName("hdr")
        h = QHBoxLayout(hdr)
        h.setContentsMargins(14, 10, 10, 10)
        title = QLabel(
            "Edit Project" if self.kind == "project" else "Edit Competition"
        )
        title.setObjectName("title")
        self.closeBtn = QPushButton("×")
        self.closeBtn.setObjectName("closeBtn")
        self.closeBtn.clicked.connect(self.back_requested.emit)
        h.addWidget(title, 0)
        h.addStretch(1)
        h.addWidget(self.closeBtn, 0)
        card_layout.addWidget(hdr)

        # ----- scrollable body -----
        body_scroll = QScrollArea()
        body_scroll.setWidgetResizable(True)
        body_scroll.setFrameShape(QFrame.Shape.NoFrame)

        body = QWidget()
        body_scroll.setWidget(body)
        card_layout.addWidget(body_scroll, 1)

        row = QHBoxLayout(body)
        row.setContentsMargins(16, 12, 16, 16)
        row.setSpacing(16)

        # ===== LEFT: meta fields =====
        left_wrap = QWidget()
        left = QVBoxLayout(left_wrap)
        left.setSpacing(8)

        left.addWidget(self._section_header("Basic information"))

        left.addWidget(self._lbl("Title"))
        self.in_title = QLineEdit()
        left.addWidget(self.in_title)

        post_label = (
            "Post to (Category)" if self.kind == "project" else "Event type"
        )
        left.addWidget(self._lbl(post_label))
        self.in_category = QComboBox()
        self.in_category.setEditable(True)
        left.addWidget(self.in_category)

        left.addWidget(self._section_header("Details"))

        # project-specific
        self.lbl_context = self._lbl("Context (e.g. web, mobile)")
        self.in_context = QLineEdit()
        left.addWidget(self.lbl_context)
        left.addWidget(self.in_context)

        self.lbl_author = self._lbl("Author display (for cards)")
        self.in_author_display = QLineEdit()
        left.addWidget(self.lbl_author)
        left.addWidget(self.in_author_display)

        # competition-specific
        self.lbl_organizer = self._lbl("Organizer")
        self.in_organizer = QLineEdit()
        left.addWidget(self.lbl_organizer)
        left.addWidget(self.in_organizer)

        self.lbl_start = self._lbl("Start date (YYYY-MM-DD)")
        self.in_start_date = QLineEdit()
        left.addWidget(self.lbl_start)
        left.addWidget(self.in_start_date)

        self.lbl_end = self._lbl("End date (YYYY-MM-DD)")
        self.in_end_date = QLineEdit()
        left.addWidget(self.lbl_end)
        left.addWidget(self.in_end_date)

        self.lbl_external = self._lbl("External link")
        self.in_external_url = QLineEdit()
        self.in_external_url.setPlaceholderText("https://…")
        left.addWidget(self.lbl_external)
        left.addWidget(self.in_external_url)

        left.addWidget(self._section_header("Description / notes"))
        self.in_desc = QTextEdit()
        self.in_desc.setMinimumHeight(100)
        left.addWidget(self.in_desc)

        left.addWidget(self._section_header("Publishing"))

        pub_row = QHBoxLayout()
        col_status = QVBoxLayout()
        col_status.addWidget(self._lbl("Status"))
        self.in_status = QComboBox()
        self.in_status.setEditable(True)
        self.in_status.addItems(
            ["", "draft", "pending", "approved", "published", "archived"]
        )
        col_status.addWidget(self.in_status)
        pub_row.addLayout(col_status, 1)

        col_pub = QVBoxLayout()
        col_pub.addWidget(self._lbl("Publish at (YYYY-MM-DD HH:MM:SS)"))
        self.in_publish_at = QLineEdit()
        col_pub.addWidget(self.in_publish_at)
        pub_row.addLayout(col_pub, 1)

        left.addLayout(pub_row)

        self.chk_public = QCheckBox(
            "Visible in showcase (uncheck to hide)"
        )
        left.addWidget(self.chk_public)

        left.addStretch(1)

        btn_row = QHBoxLayout()
        self.btn_save = QPushButton("Save changes")
        self.btn_save.setProperty("kind", "pri")
        self.btn_save.clicked.connect(self._save)

        self.btn_toggle_visibility = QPushButton()
        self.btn_toggle_visibility.setProperty("kind", "ghost")
        self.btn_toggle_visibility.clicked.connect(self._toggle_visibility)

        self.btn_delete_show = QPushButton("Delete showcase")
        self.btn_delete_show.setProperty("kind", "danger")
        self.btn_delete_show.clicked.connect(self._delete_showcase)

        btn_row.addWidget(self.btn_save)
        btn_row.addSpacing(6)
        btn_row.addWidget(self.btn_toggle_visibility)
        btn_row.addSpacing(6)
        btn_row.addWidget(self.btn_delete_show)
        btn_row.addStretch(1)
        left.addLayout(btn_row)

        left_wrap.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        row.addWidget(left_wrap, 2)

        # ===== RIGHT: media + achievements =====
        right_wrap = QWidget()
        right = QVBoxLayout(right_wrap)
        right.setSpacing(8)

        right.addWidget(self._section_header("Photos / screenshots"))

        top = QHBoxLayout()
        self.path_line = QLineEdit()
        self.path_line.setPlaceholderText("No file selected")
        self.path_line.setReadOnly(True)
        self.btn_browse = QPushButton("Browse")
        self.btn_browse.setProperty("kind", "ghost")
        self.btn_browse.clicked.connect(self._browse)
        top.addWidget(self.path_line, 1)
        top.addWidget(self.btn_browse, 0)
        right.addLayout(top)

        nav = QHBoxLayout()
        self.btn_prev = QPushButton()
        self.btn_prev.setIcon(_icon("icon_chevron_left.png"))
        self.btn_prev.setProperty("kind", "ghost")
        self.btn_prev.clicked.connect(lambda: self._shift(-1))

        self.btn_next = QPushButton()
        self.btn_next.setIcon(_icon("icon_chevron_right.png"))
        self.btn_next.setProperty("kind", "ghost")
        self.btn_next.clicked.connect(lambda: self._shift(+1))

        nav.addWidget(self.btn_prev, 0)

        self.preview = QLabel()
        self.preview.setMinimumSize(QSize(420, 260))
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav.addWidget(self.preview, 1)

        nav.addWidget(self.btn_next, 0)
        right.addLayout(nav, 1)

        self.btn_delete = QPushButton("Delete photo")
        self.btn_delete.setProperty("kind", "ghost")
        self.btn_delete.clicked.connect(self._delete_current_media)
        right.addWidget(self.btn_delete, 0, Qt.AlignmentFlag.AlignHCenter)

        if self.kind == "competition":
            right.addSpacing(10)
            self._build_achievements_ui(right)

        right.addStretch(1)

        right_wrap.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        row.addWidget(right_wrap, 2)

        # kind-specific visibility and data
        self._update_kind_specific_visibility()
        self._load_record()
        self._load_categories()
        self._load_media()
        self._render_media()
        if self.kind == "competition":
            self._load_achievements()

    # ---------- helpers ----------
    def _lbl(self, text: str) -> QLabel:
        l = QLabel(text)
        l.setProperty("role", "label")
        return l

    def _section_header(self, text: str) -> QLabel:
        l = QLabel(text)
        l.setProperty("role", "section")
        return l

    def _update_kind_specific_visibility(self) -> None:
        if self.kind == "project":
            self.lbl_context.show()
            self.in_context.show()
            self.lbl_author.show()
            self.in_author_display.show()

            self.lbl_organizer.hide()
            self.in_organizer.hide()
            self.lbl_start.hide()
            self.in_start_date.hide()
            self.lbl_end.hide()
            self.in_end_date.hide()
        else:
            self.lbl_context.hide()
            self.in_context.hide()
            self.lbl_author.hide()
            self.in_author_display.hide()

            self.lbl_organizer.show()
            self.in_organizer.show()
            self.lbl_start.show()
            self.in_start_date.show()
            self.lbl_end.show()
            self.in_end_date.show()

    # ---------- record load/save ----------
    def _load_record(self) -> None:
        if self.kind == "project":
            r = get_project(self.item_id)
            if not r:
                raise RuntimeError("Project not found")

            self.in_title.setText(r.get("title") or "")
            self.in_desc.setPlainText(r.get("description") or "")
            self.in_context.setText(r.get("context") or "")
            self.in_author_display.setText(r.get("author_display") or "")
            self.in_external_url.setText(r.get("external_url") or "")
            self.in_status.setCurrentText(r.get("status") or "")
            self.chk_public.setChecked(bool(r.get("is_public") or 0))
            self.in_publish_at.setText(r.get("publish_at") or "")
            self._cur_category = r.get("category") or ""
        else:
            r = get_competition(self.item_id)
            if not r:
                raise RuntimeError("Competition not found")

            self.in_title.setText(r.get("name") or "")
            self.in_desc.setPlainText(r.get("description") or "")
            self.in_organizer.setText(r.get("organizer") or "")
            self.in_start_date.setText(r.get("start_date") or "")
            self.in_end_date.setText(r.get("end_date") or "")
            self.in_external_url.setText(r.get("external_url") or "")
            self.in_status.setCurrentText(r.get("status") or "")
            self.chk_public.setChecked(bool(r.get("is_public") or 0))
            self.in_publish_at.setText(r.get("publish_at") or "")
            self._cur_category = r.get("event_type") or ""

        self._update_visibility_ui()

    def _update_visibility_ui(self) -> None:
        if self.chk_public.isChecked():
            self.btn_toggle_visibility.setText("Hide from showcase")
        else:
            self.btn_toggle_visibility.setText("Unhide / make visible")

    def _delete_showcase(self) -> None:
        if (
            QMessageBox.question(
                self,
                "Confirm delete",
                "Delete this showcase permanently?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        try:
            if self.kind == "project":
                delete_project(self.item_id)
            else:
                delete_competition(self.item_id)
            self.deleted.emit()
            self.back_requested.emit()
        except Exception as e:
            QMessageBox.critical(self, "Delete failed", str(e))

    def _toggle_visibility(self) -> None:
        new_public = 0 if self.chk_public.isChecked() else 1
        try:
            if self.kind == "project":
                update_project(
                    self.item_id,
                    {"is_public": new_public, "updated_at": _now_ts()},
                )
            else:
                update_competition(
                    self.item_id,
                    {"is_public": new_public, "updated_at": _now_ts()},
                )

            self.chk_public.setChecked(bool(new_public))
            self._update_visibility_ui()
            self.saved.emit()
        except Exception as e:
            QMessageBox.critical(
                self, "Visibility change failed", str(e)
            )

    def _load_categories(self) -> None:
        opts = set(list_showcase_categories())
        base = ["General", "Software", "Hardware", "Mobile"]
        for x in base + sorted(opts - set(base)):
            self.in_category.addItem(x)
        i = (
            self.in_category.findText(self._cur_category)
            if getattr(self, "_cur_category", "")
            else -1
        )
        if i >= 0:
            self.in_category.setCurrentIndex(i)
        elif getattr(self, "_cur_category", ""):
            self.in_category.insertItem(0, self._cur_category)
            self.in_category.setCurrentIndex(0)

    # ---------- media ----------
    def _load_media(self) -> None:
        self.media = (
            list_project_media(self.item_id)
            if self.kind == "project"
            else list_competition_media(self.item_id)
        )
        self.media_index = 0 if self.media else -1

    def _current_media(self) -> Optional[Dict[str, Any]]:
        if self.media_index < 0 or self.media_index >= len(self.media):
            return None
        return self.media[self.media_index]

    def _render_media(self) -> None:
        cur = self._current_media()
        path = cur["path_or_url"] if cur else None
        self.preview.setPixmap(
            _pm_or_placeholder(
                self.preview.width() or 420,
                self.preview.height() or 260,
                path,
            )
        )

    def resizeEvent(self, e) -> None:  # type: ignore[override]
        super().resizeEvent(e)
        self._render_media()

    def _shift(self, d: int) -> None:
        if not self.media:
            return
        self.media_index = (self.media_index + d) % len(self.media)
        self._render_media()

    def _browse(self) -> None:
        fn, _ = QFileDialog.getOpenFileName(
            self,
            "Select image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)",
        )
        if not fn:
            return
        self.path_line.setText(fn)
        try:
            new_name = f"sc_{int(time.time())}_{Path(fn).name}"
            dst = IMG_DIR / new_name
            shutil.copy2(fn, dst)

            # create media row (or reuse if already present) then attach mapping
            ids = seed_images_if_missing([str(dst)])
            if not ids:
                raise RuntimeError("Failed to create media record.")
            mid = ids[0]

            if self.kind == "project":
                attach_media_to_project(
                    self.item_id,
                    mid,
                    is_primary=False,
                    sort_order=len(self.media) + 1,
                )
            else:
                attach_media_to_competition(
                    self.item_id,
                    mid,
                    is_primary=False,
                    sort_order=len(self.media) + 1,
                )

            self._load_media()
            self.media_index = len(self.media) - 1
            self._render_media()
        except Exception as e:
            QMessageBox.critical(self, "Add image failed", str(e))

    def _delete_current_media(self) -> None:
        cur = self._current_media()
        if not cur:
            return
        mid = int(cur["media_id"])
        try:
            if self.kind == "project":
                remove_project_media_link(self.item_id, mid)
            else:
                remove_competition_media_link(self.item_id, mid)
            self._load_media()
            self._render_media()
        except Exception as e:
            QMessageBox.critical(self, "Delete failed", str(e))

    # ---------- save main record ----------
    def _save(self) -> None:
        title = self.in_title.text().strip()
        cat = self.in_category.currentText().strip()
        desc = self.in_desc.toPlainText().strip()
        url = self.in_external_url.text().strip()
        status = self.in_status.currentText().strip()
        publish_at = self.in_publish_at.text().strip()
        is_public = 1 if self.chk_public.isChecked() else 0

        ctx = self.in_context.text().strip()
        author = self.in_author_display.text().strip()
        organizer = self.in_organizer.text().strip()
        start_date = self.in_start_date.text().strip()
        end_date = self.in_end_date.text().strip()

        if not title:
            QMessageBox.warning(self, "Missing", "Title is required.")
            return

        try:
            if self.kind == "project":
                data = {
                    "title": title,
                    "category": cat or None,
                    "description": desc or None,
                    "context": ctx or None,
                    "external_url": url or None,
                    "author_display": author or None,
                    "status": status or None,
                    "is_public": is_public,
                    "publish_at": publish_at or None,
                    "updated_at": _now_ts(),
                }
                update_project(self.item_id, data)
            else:
                data = {
                    "name": title,
                    "organizer": organizer or None,
                    "start_date": start_date or None,
                    "end_date": end_date or None,
                    "description": desc or None,
                    "event_type": cat or None,
                    "external_url": url or None,
                    "status": status or None,
                    "is_public": is_public,
                    "publish_at": publish_at or None,
                    "updated_at": _now_ts(),
                }
                update_competition(self.item_id, data)

            self._update_visibility_ui()
            self.saved.emit()
            self.back_requested.emit()
        except Exception as e:
            QMessageBox.critical(self, "Save failed", str(e))

    # ---------- achievements (competition only) ----------
    def _build_achievements_ui(self, parent_layout: QVBoxLayout) -> None:
        parent_layout.addWidget(self._section_header("Achievements"))

        # Scrollable container so this section does not clutter/overlap
        self.ach_scroll = QScrollArea()
        self.ach_scroll.setWidgetResizable(True)
        self.ach_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.ach_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.ach_scroll.setFixedHeight(260)  # adjust if needed

        ach_inner = QWidget()
        self.ach_scroll.setWidget(ach_inner)
        layout = QVBoxLayout(ach_inner)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        self.ach_select = QComboBox()
        self.ach_select.currentIndexChanged.connect(self._on_ach_select)
        self.btn_ach_new = QPushButton("New")
        self.btn_ach_new.setProperty("kind", "ghost")
        self.btn_ach_new.clicked.connect(self._ach_new)
        self.btn_ach_delete = QPushButton("Delete")
        self.btn_ach_delete.setProperty("kind", "danger")
        self.btn_ach_delete.clicked.connect(self._delete_achievement)
        top_row.addWidget(self.ach_select, 1)
        top_row.addWidget(self.btn_ach_new, 0)
        top_row.addWidget(self.btn_ach_delete, 0)
        layout.addLayout(top_row)

        layout.addWidget(self._lbl("Title"))
        self.ach_title = QLineEdit()
        layout.addWidget(self.ach_title)

        layout.addWidget(self._lbl("Result / recognition"))
        self.ach_result = QLineEdit()
        layout.addWidget(self.ach_result)

        layout.addWidget(self._lbl("Specific awards"))
        self.ach_awards = QLineEdit()
        layout.addWidget(self.ach_awards)

        layout.addWidget(self._lbl("Notes"))
        self.ach_notes = QTextEdit()
        self.ach_notes.setFixedHeight(80)
        layout.addWidget(self.ach_notes)

        layout.addWidget(self._lbl("Awarded at (YYYY-MM-DD)"))
        self.ach_date = QLineEdit()
        layout.addWidget(self.ach_date)

        self.btn_ach_save = QPushButton("Save achievement")
        self.btn_ach_save.setProperty("kind", "pri")
        self.btn_ach_save.clicked.connect(self._save_achievement)
        layout.addWidget(self.btn_ach_save, 0, Qt.AlignmentFlag.AlignRight)

        parent_layout.addWidget(self.ach_scroll)

    def _load_achievements(self) -> None:
        self.achievements = list_achievements(competition_id=self.item_id)
        self._refresh_ach_combo()

    def _refresh_ach_combo(self) -> None:
        self.ach_select.blockSignals(True)
        self.ach_select.clear()
        self.ach_select.addItem("Add new achievement…", None)
        for ach in self.achievements:
            label = ach.get("achievement_title") or f"#{ach['achievement_id']}"
            self.ach_select.addItem(label, ach["achievement_id"])
        self.ach_select.setCurrentIndex(0)
        self.current_ach_id = None
        self._clear_ach_fields()
        self.ach_select.blockSignals(False)

    def _clear_ach_fields(self) -> None:
        self.ach_title.clear()
        self.ach_result.clear()
        self.ach_awards.clear()
        self.ach_notes.clear()
        self.ach_date.clear()

    def _on_ach_select(self, idx: int) -> None:
        ach_id = self.ach_select.currentData()
        if not ach_id:
            self.current_ach_id = None
            self._clear_ach_fields()
            return
        for a in self.achievements:
            if a["achievement_id"] == ach_id:
                self.current_ach_id = ach_id
                self.ach_title.setText(a.get("achievement_title") or "")
                self.ach_result.setText(a.get("result_recognition") or "")
                self.ach_awards.setText(a.get("specific_awards") or "")
                self.ach_notes.setPlainText(a.get("notes") or "")
                self.ach_date.setText(a.get("awarded_at") or "")
                return

    def _ach_new(self) -> None:
        self.ach_select.setCurrentIndex(0)
        self.current_ach_id = None
        self._clear_ach_fields()

    def _save_achievement(self) -> None:
        title = self.ach_title.text().strip()
        if not title:
            QMessageBox.warning(
                self, "Missing", "Achievement title is required."
            )
            return
        result = self.ach_result.text().strip()
        awards = self.ach_awards.text().strip()
        notes = self.ach_notes.toPlainText().strip()
        date = self.ach_date.text().strip() or None

        try:
            if self.current_ach_id:
                data = {
                    "achievement_title": title,
                    "result_recognition": result or None,
                    "specific_awards": awards or None,
                    "notes": notes or None,
                    "awarded_at": date,
                }
                update_achievement(self.current_ach_id, data)
            else:
                data = {
                    "competition_id": self.item_id,
                    "achievement_title": title,
                    "result_recognition": result or None,
                    "specific_awards": awards or None,
                    "notes": notes or None,
                    "awarded_at": date,
                }
                self.current_ach_id = create_achievement(data)

            self._load_achievements()
            if self.current_ach_id:
                for i in range(self.ach_select.count()):
                    if self.ach_select.itemData(i) == self.current_ach_id:
                        self.ach_select.setCurrentIndex(i)
                        break
            QMessageBox.information(
                self, "Saved", "Achievement saved successfully."
            )
        except Exception as e:
            QMessageBox.critical(self, "Save failed", str(e))

    def _delete_achievement(self) -> None:
        if not self.current_ach_id:
            return
        if (
            QMessageBox.question(
                self,
                "Confirm delete",
                "Delete this achievement?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        try:
            delete_achievement(self.current_ach_id)
            self.current_ach_id = None
            self._load_achievements()
        except Exception as e:
            QMessageBox.critical(self, "Delete failed", str(e))


# ---- manual run ----
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    w = ShowcaseAdminEditDialog("competition", 1)
    w.resize(1100, 650)
    w.show()
    sys.exit(app.exec())
