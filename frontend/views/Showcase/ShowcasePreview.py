# views/Showcase/ShowcasePreview.py
from __future__ import annotations
from pathlib import Path
from typing import List, Dict
from PyQt6.QtCore import Qt, QPoint, QRectF
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QPainterPath, QColor, QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFrame, QPushButton, QLabel,
    QTextBrowser, QWidget, QSizePolicy
)

GREEN   = "#146c43"
TEXT    = "#1f2937"
MUTED   = "#6b7280"
BG      = "#f3f4f6"
BORDER  = "#e5e7eb"

def _find_dir(name: str) -> Path:
    here = Path(__file__).resolve()
    for up in range(0, 7):
        base = here.parents[up] if up else here.parent
        cand = base / "assets" / name
        if cand.is_dir():
            return cand
    return Path.cwd() / "assets" / name

ICON_DIR = _find_dir("icons")
IMG_DIR  = _find_dir("images")

def _icon(name: str) -> QIcon:
    p = ICON_DIR / name
    return QIcon(str(p)) if p.exists() else QIcon()

def _placeholder(w: int, h: int, label: str = "image") -> QPixmap:
    pm = QPixmap(w, h); pm.fill(QColor("#d1d5db"))
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(QColor("#9ca3af")); p.setBrush(QColor("#e5e7eb"))
    p.drawRoundedRect(0, 0, w, h, 18, 18)
    f = QFont(); f.setPointSize(12); f.setBold(True)
    p.setFont(f); p.setPen(QColor("#6b7280"))
    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, label.upper())
    p.end()
    return pm

def _load_image(fname: str | None, w: int, h: int) -> QPixmap:
    if fname:
        p = (IMG_DIR / fname) if not Path(fname).exists() else Path(fname)
        if p.exists():
            pm = QPixmap(str(p))
            if not pm.isNull():
                return pm.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                 Qt.TransformationMode.SmoothTransformation)
    return _placeholder(w, h)

class RoundedImage(QWidget):
    def __init__(self, radius: int = 18, parent: QWidget | None = None):
        super().__init__(parent)
        self.radius = radius
        self._pm = QPixmap()
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

class ShowcasePreviewDialog(QDialog):
    def __init__(self, items: List[Dict], start_index: int = 0, parent=None):
        super().__init__(parent)
        self.items = items
        self.idx = start_index
        self.img_idx = 0
        self.drag_pos = QPoint()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setModal(True)
        self.resize(960, 620)
        self.setStyleSheet(f"""
            QDialog {{ background:{BG}; border:1px solid {BORDER}; border-radius:12px; }}
            QPushButton[kind="tool"] {{
                background:{GREEN}; color:white; border:none; border-radius:12px;
                padding:6px; min-width:28px; min-height:28px;
            }}
            QLabel.title {{ color:{GREEN}; font-size:18px; font-weight:700; }}
            QLabel.meta  {{ color:{MUTED}; font-size:12px; }}
            QLabel.chip  {{ background:#ecfdf5; color:{GREEN}; border:1px solid #c7f0df;
                            border-radius:10px; padding:2px 8px; font-size:11px; }}
        """)

        v = QVBoxLayout(self); v.setContentsMargins(18, 18, 18, 18); v.setSpacing(12)

        # Image area with overlay controls
        self.img_wrap = QFrame(self)
        iv = QVBoxLayout(self.img_wrap); iv.setContentsMargins(0,0,0,0); iv.setSpacing(0)

        top_bar = QHBoxLayout(); top_bar.setContentsMargins(8,8,8,8); top_bar.setSpacing(6)
        self.drag_btn = QPushButton(); self.drag_btn.setProperty("kind","tool")
        self.drag_btn.setIcon(_icon("icon_menu.png")); self.drag_btn.setCursor(Qt.CursorShape.SizeAllCursor)
        top_bar.addWidget(self.drag_btn, 0, Qt.AlignmentFlag.AlignLeft)
        top_bar.addStretch(1)
        self.counter_lbl = QLabel(""); self.counter_lbl.setProperty("class", "meta"); self.counter_lbl.setObjectName("counter")
        self.counter_lbl.setStyleSheet("QLabel#counter{color:white; background:rgba(0,0,0,.4); padding:2px 8px; border-radius:9px;}")
        top_bar.addWidget(self.counter_lbl, 0, Qt.AlignmentFlag.AlignRight)
        self.close_btn = QPushButton(); self.close_btn.setProperty("kind","tool")
        self.close_btn.setIcon(_icon("icon_close.png")); self.close_btn.clicked.connect(self.reject)
        top_bar.addWidget(self.close_btn, 0, Qt.AlignmentFlag.AlignRight)
        iv.addLayout(top_bar)

        self.rounded = RoundedImage(18, self.img_wrap)
        self.rounded.setMinimumHeight(360)
        iv.addWidget(self.rounded, 1)

        nav_row = QHBoxLayout(); nav_row.setContentsMargins(0,6,0,0); nav_row.setSpacing(0)
        self.prev_btn = QPushButton(); self.prev_btn.setProperty("kind","tool"); self.prev_btn.setIcon(_icon("icon_chevron_left.png"))
        self.next_btn = QPushButton(); self.next_btn.setProperty("kind","tool"); self.next_btn.setIcon(_icon("icon_chevron_right.png"))
        self.prev_btn.clicked.connect(self._prev_image); self.next_btn.clicked.connect(self._next_image)
        nav_row.addWidget(self.prev_btn, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        nav_row.addStretch(1)
        nav_row.addWidget(self.next_btn, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        iv.addLayout(nav_row)

        v.addWidget(self.img_wrap, 1)

        # Text + meta
        text_frame = QFrame(self)
        tb = QVBoxLayout(text_frame); tb.setContentsMargins(8,8,8,8); tb.setSpacing(6)

        head_row = QHBoxLayout(); head_row.setSpacing(8)
        self.title_lbl = QLabel("Title"); self.title_lbl.setObjectName("title"); self.title_lbl.setProperty("class","title")
        self.status_chip = QLabel("");  self.status_chip.setProperty("class","chip")
        head_row.addWidget(self.title_lbl, 1); head_row.addWidget(self.status_chip, 0, Qt.AlignmentFlag.AlignRight)
        tb.addLayout(head_row)

        self.meta_lbl = QLabel(""); self.meta_lbl.setProperty("class","meta")
        tb.addWidget(self.meta_lbl)

        self.desc = QTextBrowser(); self.desc.setOpenExternalLinks(True)
        self.desc.setStyleSheet("QTextBrowser{border:1px solid %s; background:white; border-radius:12px; padding:8px;}" % BORDER)
        tb.addWidget(self.desc, 1)
        v.addWidget(text_frame, 1)

        self._refresh()

    # ----- helpers -----
    def _images_for_current(self) -> List[str]:
        item = self.items[self.idx]
        imgs = item.get("images") or ([item.get("image")] if item.get("image") else [])
        if not imgs:
            imgs = ["1.jpg"]
        return imgs

    def _meta_text(self, it: Dict) -> str:
        parts: List[str] = []
        if it.get("author_display"): parts.append(f"by {it['author_display']}")
        if it.get("posted_ago"):     parts.append(it["posted_ago"])
        if it.get("category"):       parts.append(it["category"])
        if it.get("context"):        parts.append(it["context"])
        nimg = it.get("images_count")
        if isinstance(nimg, int):    parts.append(f"{nimg} image{'s' if nimg != 1 else ''}")
        return " • ".join(parts)

    # ----- UI refresh -----
    def _refresh(self):
        it = self.items[self.idx]

        # title + status
        self.title_lbl.setText(it.get("title",""))
        st = it.get("status") or ""
        self.status_chip.setText(st)
        self.status_chip.setVisible(bool(st))

        # meta
        self.meta_lbl.setText(self._meta_text(it))

        # description
        body = (it.get("long_text") or it.get("blurb") or "").strip()
        self.desc.setHtml(f"<p style='color:{TEXT};font-size:13px;line-height:1.5'>{body}</p>")

        # images
        imgs = self._images_for_current()
        self.img_idx = self.img_idx % len(imgs)
        pm = _load_image(imgs[self.img_idx], self.rounded.width() or 800, self.rounded.height() or 360)
        self.rounded.setPixmap(pm)
        self.counter_lbl.setText(f"{self.img_idx+1}/{len(imgs)}")

    # ----- events -----
    def resizeEvent(self, e): super().resizeEvent(e); self._refresh()
    def _prev_image(self): self.img_idx = (self.img_idx - 1) % len(self._images_for_current()); self._refresh()
    def _next_image(self): self.img_idx = (self.img_idx + 1) % len(self._images_for_current()); self._refresh()

    # dragging frameless dialog
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self.drag_pos)
        super().mouseMoveEvent(e)

    # keyboard navigation
    def keyPressEvent(self, e):
        if e.key() in (Qt.Key.Key_Left, Qt.Key.Key_A):  self._prev_image()
        elif e.key() in (Qt.Key.Key_Right, Qt.Key.Key_D): self._next_image()
        elif e.key() in (Qt.Key.Key_Escape,): self.reject()
        else: super().keyPressEvent(e)
