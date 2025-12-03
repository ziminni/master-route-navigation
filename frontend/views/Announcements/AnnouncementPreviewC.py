# views/AnnouncementPreviewC.py
from __future__ import annotations

import os, sys
from pathlib import Path
from typing import List, Dict, Optional

from PyQt6.QtCore import Qt, QPoint, QRectF
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QFont
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QPushButton,
    QLabel,
    QTextBrowser,
    QWidget,
    QSizePolicy,
    QGraphicsDropShadowEffect,
)

# --- theme (light) ---
GREEN = "#146c43"
TEXT = "#111827"
MUTED = "#6b7280"
BG = "#f3f4f6"        # dialog background
SURFACE = "#ffffff"   # card background
BORDER = "#e5e7eb"


# --- DB images ---
try:
    from db.AnnouncementDBHelper import list_documents
except Exception:
    HERE = os.path.dirname(os.path.abspath(__file__))
    DB_DIR = os.path.join(HERE, "db")
    if DB_DIR not in sys.path:
        sys.path.insert(0, DB_DIR)

    try:
        from AnnouncementDBHelper import list_documents  # type: ignore
    except Exception:
        def list_documents(_announcement_id: int) -> list[dict]:
            return []


HERE = Path(__file__).resolve().parent


def _project_root() -> Path:
    for up in range(0, 7):
        base = HERE.parents[up] if up else HERE
        if (base / "assets").exists():
            return base
    return Path.cwd()


def _resolve_path(p: str | None) -> Optional[Path]:
    if not p:
        return None
    pp = Path(p)
    if pp.is_file():
        return pp
    cand = _project_root() / p
    return cand if cand.is_file() else None


def _is_image_name(name: str) -> bool:
    n = (name or "").lower()
    return any(
        n.endswith(ext)
        for ext in (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff")
    )


# --- rounded, aspect-ratio-aware image widget ---
class RoundedImage(QWidget):
    def __init__(self, radius: int = 18, parent: QWidget | None = None):
        super().__init__(parent)
        self.radius = radius
        self._pm = QPixmap()
        self.setMinimumHeight(320)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def setPixmap(self, pm: QPixmap) -> None:
        self._pm = pm or QPixmap()
        self.update()

    def paintEvent(self, _e):  # type: ignore[override]
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(r, self.radius, self.radius)
        p.setClipPath(path)

        p.fillRect(r, QColor("#e5e7eb"))

        if not self._pm.isNull():
            target_size = r.size().toSize()
            scaled = self._pm.scaled(
                target_size,
                Qt.AspectRatioMode.KeepAspectRatio,  # no stretching
                Qt.TransformationMode.SmoothTransformation,
            )
            x = r.x() + (r.width() - scaled.width()) / 2.0
            y = r.y() + (r.height() - scaled.height()) / 2.0
            p.drawPixmap(int(x), int(y), scaled)
        else:
            p.setPen(QColor("#9ca3af"))
            f = QFont()
            f.setBold(True)
            f.setPointSize(12)
            p.setFont(f)
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, "No Image")

        p.setClipping(False)
        p.setPen(QColor(BORDER))
        p.drawRoundedRect(r, self.radius, self.radius)
        p.end()


def _load_pixmap(p: Optional[Path]) -> QPixmap:
    if p and p.exists():
        pm = QPixmap(str(p))
        if not pm.isNull():
            return pm

    ph = QPixmap(1280, 720)
    ph.fill(QColor("#e5e7eb"))
    painter = QPainter(ph)
    painter.setPen(QColor("#9ca3af"))
    f = QFont()
    f.setBold(True)
    f.setPointSize(20)
    painter.setFont(f)
    painter.drawText(ph.rect(), Qt.AlignmentFlag.AlignCenter, "IMAGE PREVIEW")
    painter.end()
    return ph


def _chip(text: str) -> QLabel:
    lab = QLabel(text)
    lab.setProperty("class", "chip")
    lab.setStyleSheet(
        f"""
        QLabel[class="chip"]{{
            background:#ecfdf5;
            color:{GREEN};
            border:1px solid #bbf7d0;
            border-radius:10px;
            padding:2px 10px;
            font-size:11px;
        }}
        """
    )
    return lab


class AnnouncementPreviewCardDialog(QDialog):
    def __init__(self, items: List[Dict], start_index: int = 0, parent=None):
        super().__init__(parent)
        self.items = items or []
        self.idx = max(0, min(start_index, len(self.items) - 1)) if self.items else 0
        self.img_idx = 0
        self._cur_imgs: List[Optional[Path]] = []
        self.drag_pos = QPoint()

        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
        )
        self.setModal(True)
        self.resize(980, 640)

        self.setStyleSheet(
            f"""
            QDialog {{
                background-color:{BG};
                border-radius:18px;
            }}
            QFrame#card {{
                background:{SURFACE};
                border-radius:16px;
                border:1px solid {BORDER};
            }}
            QPushButton[kind="icon"] {{
                background:transparent;
                border:none;
                color:{MUTED};
                font-size:14px;
                padding:4px;
                min-width:28px;
                min-height:28px;
            }}
            QPushButton[kind="icon"]:hover {{
                background:rgba(148,163,184,0.18);
                color:{TEXT};
                border-radius:999px;
            }}
            QPushButton[kind="pill"] {{
                background:white;
                border:1px solid {BORDER};
                border-radius:999px;
                padding:4px 10px;
                font-size:12px;
                color:{TEXT};
            }}
            QLabel[class="title"] {{
                color:{TEXT};
                font-weight:600;
                font-size:18px;
            }}
            QLabel[class="subtitle"] {{
                color:{MUTED};
                font-size:12px;
            }}
            QTextBrowser {{
                border-radius:12px;
                border:1px solid {BORDER};
                background:white;
                padding:8px 10px;
                font-size:13px;
                color:{TEXT};
            }}
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        # header
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)

        self.header_title = QLabel("Announcement preview")
        self.header_title.setStyleSheet(
            f"color:{MUTED};font-size:12px;font-weight:500;letter-spacing:0.04em;"
        )

        header.addWidget(self.header_title)
        header.addStretch()

        self.counter_lbl = QLabel("")
        self.counter_lbl.setObjectName("counter")
        self.counter_lbl.setStyleSheet(
            """
            QLabel#counter{
                color:#374151;
                background:rgba(229,231,235,0.9);
                padding:2px 8px;
                border-radius:9px;
                font-size:11px;
            }
            """
        )
        header.addWidget(self.counter_lbl)

        close_btn = QPushButton("✕")
        close_btn.setProperty("kind", "icon")
        close_btn.clicked.connect(self.reject)
        header.addWidget(close_btn)

        root.addLayout(header)

        # main card
        card = QFrame(self)
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(10)

        # image + nav
        img_stack = QVBoxLayout()
        img_stack.setContentsMargins(0, 0, 0, 0)
        img_stack.setSpacing(6)

        self.rounded = RoundedImage(16, card)
        img_stack.addWidget(self.rounded, 1)

        nav = QHBoxLayout()
        nav.setContentsMargins(0, 0, 0, 0)
        nav.setSpacing(6)

        self.prev_btn = QPushButton("‹")
        self.prev_btn.setProperty("kind", "pill")
        self.prev_btn.clicked.connect(self._prev_image)

        self.next_btn = QPushButton("›")
        self.next_btn.setProperty("kind", "pill")
        self.next_btn.clicked.connect(self._next_image)

        nav.addWidget(self.prev_btn, 0, Qt.AlignmentFlag.AlignLeft)
        nav.addStretch(1)
        nav.addWidget(self.next_btn, 0, Qt.AlignmentFlag.AlignRight)

        img_stack.addLayout(nav)
        card_layout.addLayout(img_stack, 2)

        # text/meta
        info = QVBoxLayout()
        info.setContentsMargins(0, 4, 0, 0)
        info.setSpacing(6)

        self.title_lbl = QLabel("Title")
        self.title_lbl.setProperty("class", "title")
        info.addWidget(self.title_lbl)

        self.meta_lbl = QLabel("")
        self.meta_lbl.setProperty("class", "subtitle")
        info.addWidget(self.meta_lbl)

        self.chip_wrap = QWidget()
        self.chip_layout = QHBoxLayout(self.chip_wrap)
        self.chip_layout.setContentsMargins(0, 0, 0, 0)
        self.chip_layout.setSpacing(6)
        info.addWidget(self.chip_wrap)

        self.body = QTextBrowser()
        self.body.setOpenExternalLinks(True)
        self.body.setMinimumHeight(120)
        info.addWidget(self.body, 1)

        card_layout.addLayout(info, 2)
        root.addWidget(card, 1)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 24))
        card.setGraphicsEffect(shadow)

    # ----- data helpers -----
    def _images_for(self, it: Dict) -> List[Optional[Path]]:
        imgs: List[Optional[Path]] = []
        try:
            # support both 'announcement_id' and 'id'
            aid = int(it.get("announcement_id") or it.get("id") or 0)
            if aid:
                docs = list_documents(aid)
                for d in docs:
                    path = d.get("file_path") or ""
                    if d.get("mime_type", "").startswith("image") or _is_image_name(path):
                        rp = _resolve_path(path)
                        if rp:
                            imgs.append(rp)
        except Exception:
            pass

        if not imgs:
            rp = _resolve_path(it.get("file_path"))
            imgs = [rp] if rp else []

        return imgs

    # ----- refresh UI -----
    def _refresh(self) -> None:
        if not self.items:
            return

        it = self.items[self.idx]

        self.title_lbl.setText(it.get("title", "").strip())

        author = it.get("author_name") or "Unknown"
        posted = it.get("publish_at") or it.get("created_at") or ""
        self.meta_lbl.setText(f"by {author} • {posted}")

        while self.chip_layout.count():
            item = self.chip_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)

        loc = (it.get("location") or "").strip()
        if loc:
            self.chip_layout.addWidget(_chip(loc))

        vis = (it.get("visibility") or "").strip()
        if vis:
            self.chip_layout.addWidget(_chip(vis))

        try:
            pr = int(it.get("priority") or 0)
        except Exception:
            pr = 0
        if pr > 0:
            self.chip_layout.addWidget(_chip(f"priority {pr}"))

        try:
            pin = int(it.get("is_pinned") or 0)
        except Exception:
            pin = 0
        if pin == 1:
            self.chip_layout.addWidget(_chip("pinned"))

        tags_csv = it.get("tags_csv") or ""
        for t in [t.strip() for t in tags_csv.split(",") if t.strip()][:6]:
            self.chip_layout.addWidget(_chip(f"#{t}"))

        self.chip_layout.addStretch(1)

        body = (it.get("body") or "").strip()
        self.body.setHtml(
            f"<div style='color:{TEXT};font-size:13px;line-height:1.55;'>{body}</div>"
        )

        self._cur_imgs = self._images_for(it) or [None]
        self.img_idx = max(0, min(self.img_idx, len(self._cur_imgs) - 1))
        pm = _load_pixmap(self._cur_imgs[self.img_idx])
        self.rounded.setPixmap(pm)

        self.counter_lbl.setText(f"{self.img_idx + 1}/{len(self._cur_imgs)}")

        multi = len(self._cur_imgs) > 1
        self.prev_btn.setVisible(multi)
        self.next_btn.setVisible(multi)

    def resizeEvent(self, e):  # type: ignore[override]
        super().resizeEvent(e)
        if self._cur_imgs:
            pm = _load_pixmap(self._cur_imgs[self.img_idx])
            self.rounded.setPixmap(pm)

    # ----- carousel -----
    def _prev_image(self) -> None:
        if not self._cur_imgs:
            return
        self.img_idx = (self.img_idx - 1) % len(self._cur_imgs)
        self._refresh()

    def _next_image(self) -> None:
        if not self._cur_imgs:
            return
        self.img_idx = (self.img_idx + 1) % len(self._cur_imgs)
        self._refresh()

    # ----- window dragging / keyboard -----
    def mousePressEvent(self, e):  # type: ignore[override]
        if e.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):  # type: ignore[override]
        if e.buttons() & Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self.drag_pos)
        super().mouseMoveEvent(e)

    def keyPressEvent(self, e):  # type: ignore[override]
        if e.key() in (Qt.Key.Key_Left, Qt.Key.Key_A):
            self._prev_image()
        elif e.key() in (Qt.Key.Key_Right, Qt.Key.Key_D):
            self._next_image()
        elif e.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(e)
