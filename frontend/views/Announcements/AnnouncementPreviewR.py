# views/AnnouncementPreviewR.py
from __future__ import annotations

import os, sys
from typing import Dict

from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextBrowser, QWidget
)

GREEN = "#146c43"; TEXT = "#1f2937"; MUTED = "#6b7280"; BG = "#f3f4f6"; BORDER = "#e5e7eb"

def _chip(text: str) -> QLabel:
    lab = QLabel(text)
    lab.setProperty("class", "chip")
    lab.setStyleSheet(
        f'QLabel[class="chip"]{{background:#ecfdf5;color:{GREEN};border:1px solid #c7f0df;'
        'border-radius:10px;padding:2px 8px;font-size:11px;}}'
    )
    return lab

class AnnouncementPreviewReminderDialog(QDialog):
    """Preview dialog for a single reminder card."""
    def __init__(self, item: Dict, parent=None):
        super().__init__(parent)
        self.item = item or {}
        self.drag_pos = QPoint()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setModal(True)
        self.resize(620, 420)
        self.setStyleSheet(
            f"QDialog{{background:{BG};border:1px solid {BORDER};border-radius:12px;}}"
            f"QPushButton[kind='tool']{{background:{GREEN};color:white;border:none;border-radius:12px;"
            "padding:6px;min-width:28px;min-height:28px;}}"
            f'QLabel[class="title"]{{color:{GREEN};font-weight:700;font-size:18px;}}'
            f'QLabel[class="meta"]{{color:{MUTED};font-size:12px;}}'
        )

        v = QVBoxLayout(self); v.setContentsMargins(18, 18, 18, 18); v.setSpacing(12)

        top = QHBoxLayout(); top.setSpacing(6)
        drag_btn = QPushButton(); drag_btn.setProperty("kind", "tool"); drag_btn.setText("☰")
        drag_btn.setCursor(Qt.CursorShape.SizeAllCursor)
        top.addWidget(drag_btn, 0, Qt.AlignmentFlag.AlignLeft)
        top.addStretch(1)
        close_btn = QPushButton(); close_btn.setProperty("kind", "tool"); close_btn.setText("✕"); close_btn.clicked.connect(self.reject)
        top.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignRight)
        v.addLayout(top)

        title = QLabel(self.item.get("title", "")); title.setProperty("class", "title")
        v.addWidget(title)

        meta = QLabel(f"by {self.item.get('author_name','Unknown')} • "
                      f"{self.item.get('created_at') or self.item.get('remind_at') or ''}")
        meta.setProperty("class", "meta"); v.addWidget(meta)

        chips_row = QHBoxLayout(); chips_row.setSpacing(6)
        if self.item.get("visibility"): chips_row.addWidget(_chip(self.item["visibility"]))
        try:
            pr = int(self.item.get("priority", 0))
            if pr > 0: chips_row.addWidget(_chip(f"priority {pr}"))
        except Exception:
            pass
        if self.item.get("repeat_interval"): chips_row.addWidget(_chip(self.item["repeat_interval"]))
        chips_w = QWidget(); chips_w.setLayout(chips_row); v.addWidget(chips_w)

        body = QTextBrowser(); body.setOpenExternalLinks(True)
        body.setStyleSheet(f"QTextBrowser{{border:1px solid {BORDER};background:white;border-radius:12px;padding:8px;}}")
        body.setHtml(f"<p style='color:{TEXT};font-size:13px;line-height:1.5'>{(self.item.get('body') or '').strip()}</p>")
        v.addWidget(body, 1)

    # drag
    def mousePressEvent(self, e):  # type: ignore
        if e.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):  # type: ignore
        if e.buttons() & Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self.drag_pos)
        super().mouseMoveEvent(e)

    def keyPressEvent(self, e):  # type: ignore
        if e.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(e)
