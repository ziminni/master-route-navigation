from __future__ import annotations
import os, sqlite3
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtCore import Qt, QDateTime, pyqtSignal
from PyQt6.QtGui  import QIcon
from PyQt6.QtWidgets import (
    QDialog, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QLineEdit, QTextEdit, QComboBox, QMessageBox, QCheckBox, QDateTimeEdit
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

ICON_DIR=_find_dir("icons")

def _icon(fname: str) -> QIcon:
    p = ICON_DIR / fname
    return QIcon(str(p)) if p.exists() else QIcon()

# ---------- DB ----------
try:
    from .db.AnnouncementDBInitialize import db_path
except Exception:
    from db.AnnouncementDBInitialize import db_path  # type: ignore

def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path()))
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sqlite3.Row
    return con

def get_reminder(reminder_id: int) -> Optional[Dict[str, Any]]:
    with _conn() as con:
        r = con.execute("SELECT * FROM reminders WHERE reminder_id=?", (reminder_id,)).fetchone()
        return dict(r) if r else None

def update_reminder(reminder_id: int, **fields) -> int:
    allow = {
        "title","body","remind_at","repeat_interval","priority",
        "is_active","is_snoozable","snooze_until","visibility","expires_at","note",
    }
    data = {k:v for k,v in fields.items() if k in allow}
    if not data: return 0
    sets = ", ".join(f"{k}=?" for k in data.keys())
    vals = list(data.values()) + [reminder_id]
    with _conn() as con:
        cur = con.execute(f"UPDATE reminders SET {sets}, updated_at=CURRENT_TIMESTAMP WHERE reminder_id=?", vals)
        return cur.rowcount

def delete_reminder(reminder_id: int) -> int:
    with _conn() as con:
        cur = con.execute("DELETE FROM reminders WHERE reminder_id=?", (reminder_id,))
        return cur.rowcount

# ---------- dialog ----------
class AnnouncementAdminEditRPage(QWidget):
    """
    Edit/Delete a reminder inside the same window.
    Emits back_requested, saved, and deleted.
    """
    back_requested = pyqtSignal()
    saved = pyqtSignal()
    deleted = pyqtSignal()

    def __init__(self, reminder_id: int, parent: QWidget | None = None):
        super().__init__(parent)
        self.reminder_id = int(reminder_id)

        self.setObjectName("RemEdit")
        self.setStyleSheet(f"""
            QWidget#RemEdit      {{ background:white; border:1px solid {GREEN}; border-radius:12px; }}
            QLabel#title         {{ color:white; font-size:20px; font-weight:700; }}
            QFrame#hdr           {{ background:{GREEN}; border-top-left-radius:12px; border-top-right-radius:12px; }}
            QLabel[role="label"] {{ color:{MUTED}; font-size:12px; }}
            QLineEdit, QTextEdit, QComboBox, QDateTimeEdit {{
                background:white; color:{TEXT}; border:1px solid {BORDER}; border-radius:8px; padding:6px;
            }}
            QCheckBox {{ color:{TEXT}; }}
            QPushButton[kind="pri"]    {{ background:{GREEN}; color:white; border:none; border-radius:8px; padding:8px 14px; }}
            QPushButton[kind="ghost"]  {{ background:transparent; color:{GREEN}; border:1px solid {GREEN}; border-radius:18px; padding:6px 10px; }}
            QPushButton[kind="danger"] {{ background:#dc3545; color:white; border:none; border-radius:8px; padding:8px 14px; }}
            QPushButton#closeBtn {{
                background: transparent; color: white; border: 1px solid white;
                border-radius: 16px; font-size: 18px; font-weight: 700;
                min-width:32px; min-height:32px;
            }}
            QPushButton#closeBtn:hover {{ background: rgba(255,255,255,0.12); }}
        """)

        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        # header
        from PyQt6.QtWidgets import QFrame, QHBoxLayout
        hdr = QFrame(); hdr.setObjectName("hdr")
        hh = QHBoxLayout(hdr); hh.setContentsMargins(14,10,10,10)
        title = QLabel("Edit Reminder"); title.setObjectName("title")
        self.closeBtn = QPushButton("←"); self.closeBtn.setObjectName("closeBtn")
        self.closeBtn.setToolTip("Back")
        self.closeBtn.clicked.connect(self.back_requested.emit)
        hh.addWidget(title, 0); hh.addStretch(1); hh.addWidget(self.closeBtn, 0)
        root.addWidget(hdr)

        # form
        from PyQt6.QtWidgets import QGridLayout, QWidget
        formW = QWidget(); grid = QGridLayout(formW); grid.setContentsMargins(12,12,12,12); grid.setHorizontalSpacing(12); grid.setVerticalSpacing(8)

        r = 0
        grid.addWidget(self._lbl("Title"), r, 0); self.in_title = QLineEdit(); grid.addWidget(self.in_title, r, 1, 1, 3); r+=1
        grid.addWidget(self._lbl("Body"),  r, 0); self.in_body  = QTextEdit(); self.in_body.setMinimumHeight(120); grid.addWidget(self.in_body, r, 1, 1, 3); r+=1

        grid.addWidget(self._lbl("Remind at"), r, 0); self.dt_remind = QDateTimeEdit(); self.dt_remind.setCalendarPopup(True); grid.addWidget(self.dt_remind, r, 1); 
        grid.addWidget(self._lbl("Repeat"),    r, 2); self.in_repeat = QComboBox(); [self.in_repeat.addItem(x) for x in ["none","daily","weekly","monthly"]]; grid.addWidget(self.in_repeat, r, 3); r+=1

        grid.addWidget(self._lbl("Priority"), r, 0); self.in_priority = QLineEdit(); self.in_priority.setPlaceholderText("0, 1, 2 …"); grid.addWidget(self.in_priority, r, 1)
        grid.addWidget(self._lbl("Visibility"), r, 2); self.in_visibility = QComboBox(); [self.in_visibility.addItem(x) for x in ["private","public","organization","faculty","students"]]; grid.addWidget(self.in_visibility, r, 3); r+=1

        grid.addWidget(self._lbl("Active / Snoozable"), r, 0)
        self.cb_active = QCheckBox("Active"); self.cb_snooze = QCheckBox("Snoozable")
        box = QHBoxLayout(); box.addWidget(self.cb_active); box.addWidget(self.cb_snooze); from PyQt6.QtWidgets import QWidget as _W; _boxW=_W(); _boxW.setLayout(box)
        grid.addWidget(_boxW, r, 1)

        grid.addWidget(self._lbl("Snooze until"), r, 2); self.dt_snooze = QDateTimeEdit(); self.dt_snooze.setCalendarPopup(True); grid.addWidget(self.dt_snooze, r, 3); r+=1

        grid.addWidget(self._lbl("Expires at"), r, 0); self.dt_expires = QDateTimeEdit(); self.dt_expires.setCalendarPopup(True); grid.addWidget(self.dt_expires, r, 1)
        grid.addWidget(self._lbl("Note"), r, 2); self.in_note = QLineEdit(); grid.addWidget(self.in_note, r, 3); r+=1

        root.addWidget(formW, 1)

        # footer
        foot = QHBoxLayout(); foot.setContentsMargins(12,0,12,12)
        self.btn_save = QPushButton("Save"); self.btn_save.setProperty("kind","pri"); self.btn_save.clicked.connect(self._save)
        self.btn_delete = QPushButton("Delete Reminder"); self.btn_delete.setProperty("kind","danger"); self.btn_delete.clicked.connect(self._delete)
        foot.addStretch(1); foot.addWidget(self.btn_save); foot.addSpacing(8); foot.addWidget(self.btn_delete)
        root.addLayout(foot)

        self._load()

    # ---- helpers ----
    def _lbl(self, text: str) -> QLabel:
        l = QLabel(text); l.setProperty("role","label"); return l

    def _qdt_from_text(self, s: Optional[str]) -> QDateTime:
        if not s: return QDateTime.currentDateTime()
        dt = QDateTime.fromString(s.replace("T"," "), "yyyy-MM-dd HH:mm:ss")
        if not dt.isValid(): dt = QDateTime.fromString(s, Qt.DateFormat.ISODate)
        return dt if dt.isValid() else QDateTime.currentDateTime()

    def _text_from_qdt(self, dt: QDateTime) -> Optional[str]:
        if not dt or not dt.isValid(): return None
        return dt.toString("yyyy-MM-dd HH:mm:ss")

    # ---- IO ----
    def _load(self):
        rec = get_reminder(self.reminder_id)
        if not rec:
            QMessageBox.critical(self, "Error", "Reminder not found.")
            self.back_requested.emit(); return
        self.in_title.setText(rec.get("title") or "")
        self.in_body.setPlainText(rec.get("body") or "")
        self.dt_remind.setDateTime(self._qdt_from_text(rec.get("remind_at")))
        self.in_repeat.setCurrentText(rec.get("repeat_interval") or "none")
        self.in_priority.setText(str(rec.get("priority") or 0))
        self.cb_active.setChecked(int(rec.get("is_active") or 0) == 1)
        self.cb_snooze.setChecked(int(rec.get("is_snoozable") or 0) == 1)
        self.dt_snooze.setDateTime(self._qdt_from_text(rec.get("snooze_until")))
        self.in_visibility.setCurrentText(rec.get("visibility") or "private")
        self.dt_expires.setDateTime(self._qdt_from_text(rec.get("expires_at")))
        self.in_note.setText(rec.get("note") or "")

    def _save(self):
        title = self.in_title.text().strip()
        if not title:
            QMessageBox.warning(self, "Missing", "Title is required.")
            return
        try:
            update_reminder(
                self.reminder_id,
                title=title,
                body=self.in_body.toPlainText().strip(),
                remind_at=self._text_from_qdt(self.dt_remind.dateTime()),
                repeat_interval=self.in_repeat.currentText().strip(),
                priority=int(self.in_priority.text().strip() or "0"),
                is_active=1 if self.cb_active.isChecked() else 0,
                is_snoozable=1 if self.cb_snooze.isChecked() else 0,
                snooze_until=self._text_from_qdt(self.dt_snooze.dateTime()),
                visibility=self.in_visibility.currentText().strip(),
                expires_at=self._text_from_qdt(self.dt_expires.dateTime()),
                note=(self.in_note.text().strip() or None),
            )
            self.saved.emit()
            self.back_requested.emit()
        except Exception as e:
            QMessageBox.critical(self, "Save failed", str(e))

    def _delete(self):
        from PyQt6.QtWidgets import QMessageBox as MB
        if MB.question(
            self, "Confirm delete", "Delete this reminder permanently?",
            MB.StandardButton.Yes | MB.StandardButton.No, MB.StandardButton.No
        ) != MB.StandardButton.Yes:
            return
        try:
            delete_reminder(self.reminder_id)
            self.deleted.emit()
            self.back_requested.emit()
        except Exception as e:
            QMessageBox.critical(self, "Delete failed", str(e))