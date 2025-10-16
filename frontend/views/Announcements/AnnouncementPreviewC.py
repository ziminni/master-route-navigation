# views/AnnouncementPreviewC.py
from __future__ import annotations

import os, sys
from pathlib import Path
from typing import List, Dict

from PyQt6.QtCore import Qt, QPoint, QRectF
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFrame, QPushButton, QLabel,
    QTextBrowser, QWidget, QSizePolicy
)

# --- theme ---
GREEN = "#146c43"; TEXT = "#1f2937"; MUTED = "#6b7280"; BG = "#f3f4f6"; BORDER = "#e5e7eb"

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
        def list_documents(_announcement_id: int) -> list[dict]:  # fallback stub
            return []

# --- path helpers ---
HERE = Path(__file__).resolve().parent

def _project_root() -> Path:
    for up in range(0, 7):
        base = HERE.parents[up] if up else HERE
        if (base / "assets").exists():
            return base
    return Path.cwd()

def _resolve_path(p: str | None) -> Path | None:
    if not p:
        return None
    pp = Path(p)
    if pp.is_file():
        return pp
    cand = _project_root() / p
    return cand if cand.is_file() else None

def _is_image_name(name: str) -> bool:
    n = (name or "").lower()
    return any(n.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff"))

# --- rounded image widget ---
class RoundedImage(QWidget):
    def __init__(self, radius: int = 18, parent: QWidget | None = None):
        super().__init__(parent)
        self.radius = radius
        self._pm = QPixmap()
        self.setMinimumHeight(360)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def setPixmap(self, pm: QPixmap):
        self._pm = pm
        self.update()

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(r, self.radius, self.radius)
        p.setClipPath(path)
        if not self._pm.isNull():
            p.drawPixmap(r, self._pm, QRectF(self._pm.rect()))
        else:
            p.fillRect(r, QColor("#d1d5db"))
        p.setClipping(False)
        p.setPen(QColor(BORDER))
        p.drawRoundedRect(r, self.radius, self.radius)
        p.end()

def _load_and_fill(p: Path | None, w: int, h: int) -> QPixmap:
    if p and p.exists():
        pm = QPixmap(str(p))
        if not pm.isNull():
            return pm.scaled(
                max(1, w), max(1, h),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
    ph = QPixmap(max(1, w), max(1, h))
    ph.fill(QColor("#d1d5db"))
    painter = QPainter(ph)
    painter.setPen(QColor("#9ca3af"))
    f = QFont(); f.setBold(True); f.setPointSize(14)
    painter.setFont(f)
    painter.drawText(ph.rect(), Qt.AlignmentFlag.AlignCenter, "IMAGE")
    painter.end()
    return ph

def _chip(text: str) -> QLabel:
    lab = QLabel(text)
    lab.setProperty("class", "chip")
    lab.setStyleSheet(
        f'QLabel[class="chip"]{{background:#ecfdf5;color:{GREEN};border:1px solid #c7f0df;'
        'border-radius:10px;padding:2px 8px;font-size:11px;}}'
    )
    return lab

class AnnouncementPreviewCardDialog(QDialog):
    """Preview for announcement cards with optional multi-image carousel."""
    def __init__(self, items: List[Dict], start_index: int = 0, parent=None):
        super().__init__(parent)
        self.items = items or []
        self.idx = max(0, min(start_index, len(self.items) - 1)) if self.items else 0
        self.img_idx = 0
        self._cur_imgs: List[Path] = []
        self.drag_pos = QPoint()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setModal(True)
        self.resize(960, 620)
        self.setStyleSheet(
            f"QDialog{{background:{BG};border:1px solid {BORDER};border-radius:12px;}}"
            f"QPushButton[kind='tool']{{background:{GREEN};color:white;border:none;border-radius:12px;"
            "padding:6px;min-width:28px;min-height:28px;}}"
            f'QLabel[class="title"]{{color:{GREEN};font-weight:700;font-size:18px;}}'
            f'QLabel[class="meta"]{{color:{MUTED};font-size:12px;}}'
        )

        v = QVBoxLayout(self); v.setContentsMargins(18, 18, 18, 18); v.setSpacing(12)

        # top bar
        top = QHBoxLayout(); top.setSpacing(6)
        drag_btn = QPushButton(); drag_btn.setProperty("kind", "tool")
        drag_btn.setText("☰"); drag_btn.setCursor(Qt.CursorShape.SizeAllCursor)
        top.addWidget(drag_btn, 0, Qt.AlignmentFlag.AlignLeft)
        top.addStretch(1)
        self.counter_lbl = QLabel("")
        self.counter_lbl.setObjectName("counter")
        self.counter_lbl.setStyleSheet("QLabel#counter{color:white;background:rgba(0,0,0,.4);padding:2px 8px;border-radius:9px;}")
        top.addWidget(self.counter_lbl, 0, Qt.AlignmentFlag.AlignRight)
        close_btn = QPushButton(); close_btn.setProperty("kind", "tool"); close_btn.setText("✕"); close_btn.clicked.connect(self.reject)
        top.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignRight)
        v.addLayout(top)

        # image area
        self.rounded = RoundedImage(18, self)
        v.addWidget(self.rounded, 1)

        nav = QHBoxLayout(); nav.setContentsMargins(0, 0, 0, 0)
        self.prev_btn = QPushButton(); self.prev_btn.setProperty("kind", "tool"); self.prev_btn.setText("◀")
        self.next_btn = QPushButton(); self.next_btn.setProperty("kind", "tool"); self.next_btn.setText("▶")
        self.prev_btn.clicked.connect(self._prev_image); self.next_btn.clicked.connect(self._next_image)
        nav.addWidget(self.prev_btn, 0, Qt.AlignmentFlag.AlignLeft); nav.addStretch(1)
        nav.addWidget(self.next_btn, 0, Qt.AlignmentFlag.AlignRight)
        v.addLayout(nav)

        # text/meta
        tf = QFrame(self)
        tb = QVBoxLayout(tf); tb.setContentsMargins(8, 8, 8, 8); tb.setSpacing(6)

        head = QHBoxLayout(); head.setSpacing(8)
        self.title_lbl = QLabel("Title"); self.title_lbl.setProperty("class", "title")
        head.addWidget(self.title_lbl, 1)
        tb.addLayout(head)

        self.meta_lbl = QLabel(""); self.meta_lbl.setProperty("class", "meta")
        tb.addWidget(self.meta_lbl)

        self.chip_wrap = QWidget()
        self.chip_l = QHBoxLayout(self.chip_wrap); self.chip_l.setContentsMargins(0, 0, 0, 0); self.chip_l.setSpacing(6)
        tb.addWidget(self.chip_wrap)

        self.body = QTextBrowser(); self.body.setOpenExternalLinks(True)
        self.body.setStyleSheet(f"QTextBrowser{{border:1px solid {BORDER};background:white;border-radius:12px;padding:8px;}}")
        tb.addWidget(self.body, 1)

        v.addWidget(tf, 1)

        self._refresh()

    # images for an announcement
    def _images_for(self, it: Dict) -> List[Path]:
        imgs: List[Path] = []
        try:
            docs = list_documents(int(it.get("announcement_id", 0)))
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
            if rp:
                imgs = [rp]
        return imgs

    # UI refresh
    def _refresh(self):
        if not self.items:
            return
        it = self.items[self.idx]

        self.title_lbl.setText(it.get("title", ""))

        author = it.get("author_name") or "Unknown"
        posted = it.get("publish_at") or it.get("created_at") or ""
        self.meta_lbl.setText(f"by {author} • {posted}")

        while self.chip_l.count():
            ci = self.chip_l.takeAt(0); w = ci.widget()
            if w: w.setParent(None)

        loc = it.get("location"); vis = it.get("visibility"); pr = it.get("priority"); pin = it.get("is_pinned")
        if loc: self.chip_l.addWidget(_chip(loc))
        if vis: self.chip_l.addWidget(_chip(vis))
        try:
            if int(pr or 0) > 0:
                self.chip_l.addWidget(_chip(f"priority {pr}"))
        except Exception:
            pass
        try:
            if int(pin or 0) == 1:
                self.chip_l.addWidget(_chip("pinned"))
        except Exception:
            pass
        tags_csv = it.get("tags_csv") or ""
        for t in [t for t in tags_csv.split(",") if t][:5]:
            self.chip_l.addWidget(_chip(f"#{t}"))

        body = (it.get("body") or "").strip()
        self.body.setHtml(f"<p style='color:{TEXT};font-size:13px;line-height:1.5'>{body}</p>")

        self._cur_imgs = self._images_for(it) or [None]
        self.img_idx = self.img_idx % len(self._cur_imgs)
        pm = _load_and_fill(self._cur_imgs[self.img_idx], self.rounded.width() or 800, self.rounded.height() or 360)
        self.rounded.setPixmap(pm)
        self.counter_lbl.setText(f"{self.img_idx + 1}/{len(self._cur_imgs)}")
        multi = len(self._cur_imgs) > 1
        self.prev_btn.setVisible(multi); self.next_btn.setVisible(multi)

    # events
    def resizeEvent(self, e):  # type: ignore
        super().resizeEvent(e); self._refresh()

    def _prev_image(self):
        if not self._cur_imgs: return
        self.img_idx = (self.img_idx - 1) % len(self._cur_imgs)
        self._refresh()

    def _next_image(self):
        if not self._cur_imgs: return
        self.img_idx = (self.img_idx + 1) % len(self._cur_imgs)
        self._refresh()

    # drag window
    def mousePressEvent(self, e):  # type: ignore
        if e.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):  # type: ignore
        if e.buttons() & Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self.drag_pos)
        super().mouseMoveEvent(e)

    def keyPressEvent(self, e):  # type: ignore
        if e.key() in (Qt.Key.Key_Left, Qt.Key.Key_A):
            self._prev_image()
        elif e.key() in (Qt.Key.Key_Right, Qt.Key.Key_D):
            self._next_image()
        elif e.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(e)
