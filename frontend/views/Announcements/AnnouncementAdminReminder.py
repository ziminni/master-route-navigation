# views/AnnouncementAdminReminder.py
from __future__ import annotations

import sys, sqlite3
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QDateTime, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox,
    QHBoxLayout, QVBoxLayout, QScrollArea, QFrame, QSizePolicy, QMessageBox,
    QDateTimeEdit, QCheckBox
)

HERE = Path(__file__).resolve().parent

# ---- DB path import (works as script or package) ----
try:
    from db.AnnouncementDBInitialize import db_path, ensure_bootstrap
except Exception:
    DB_DIR = HERE / "db"
    sys.path.insert(0, str(DB_DIR))
    from AnnouncementDBInitialize import db_path, ensure_bootstrap  # type: ignore

# ---- theme ----
GREEN="#146c43"; TEXT="#1f2937"; BG="#f3f4f6"; BORDER="#e5e7eb"; WHITE="#ffffff"

# ---- user/session stub ----
CURRENT_USER_ID = 1  # replace when wiring session

# ---- assets ----
def _project_root() -> Path:
    for up in range(0, 7):
        base = HERE.parents[up] if up else HERE
        if (base / "assets").exists():
            return base
    return Path.cwd()

def _icon(name: str) -> Optional[QIcon]:
    p = _project_root() / "assets" / "icons" / name
    return QIcon(str(p)) if p.is_file() else None

# ---- db helpers ----
def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path()))
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sqlite3.Row
    return con

def _insert_active_reminder(
    *, title: str, body: str, remind_at_iso: str,
    repeat_interval: str, priority: int,
    visibility: str, scope_type: str,
    is_snoozable: int, snooze_until_iso: Optional[str],
    expires_at_iso: Optional[str], note: Optional[str],
    author_id: int, created_by: int
) -> int:
    with _conn() as con:
        cur = con.cursor()
        cur.execute("""
            INSERT INTO reminders(
                title, body, author_id, remind_at, repeat_interval,
                priority, is_active, is_snoozable, snooze_until,
                visibility, created_by, note, expires_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?)
        """, (
            title, body, author_id, remind_at_iso, repeat_interval,
            priority, is_snoozable, snooze_until_iso,
            visibility, created_by, note, expires_at_iso
        ))
        rid = cur.lastrowid
        cur.execute("""
            INSERT INTO reminder_audience(reminder_id, scope_type, scope_target_id)
            VALUES (?, ?, NULL)
        """, (rid, scope_type))
        con.commit()
        return rid

# ---- main widget ----
class AnnouncementAdminReminderPage(QWidget):
    # in-stack navigation + legacy
    back_requested = pyqtSignal()
    request_close = pyqtSignal()
    published = pyqtSignal(int)  # new reminder_id
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Announcements")
        self.setMinimumSize(1100, 680)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self); root.setContentsMargins(12,12,12,12); root.setSpacing(12)

        # top bar
        top = QHBoxLayout(); top.setSpacing(8)
        btnMenu = QPushButton(); btnMenu.setFixedSize(36,36)
        btnMenu.setCursor(Qt.CursorShape.PointingHandCursor)
        btnMenu.setStyleSheet(f"QPushButton{{background:{WHITE};border:1px solid {BORDER};border-radius:10px;}}")
        ico = _icon("icon_menu.png")
        if ico: btnMenu.setIcon(ico)
        title = QLabel("Announcements"); title.setStyleSheet(f"color:{GREEN};font:700 22pt;")
        top.addWidget(btnMenu,0); top.addWidget(title,0); top.addStretch(1)
        root.addLayout(top)

        # header
        head = QFrame(); head.setStyleSheet(f"QFrame{{background:{GREEN};border-radius:8px;}}")
        headL = QHBoxLayout(head); headL.setContentsMargins(16,10,12,10)
        htitle = QLabel("Publish Reminder"); htitle.setStyleSheet("color:white;font:700 20pt;")
        headL.addWidget(htitle); headL.addStretch(1)
        closeBtn = QPushButton(); closeBtn.setCursor(Qt.CursorShape.PointingHandCursor); closeBtn.setFixedSize(28,28)
        xico = _icon("icon_close2.png") or _icon("icon_close.png")
        if xico: closeBtn.setIcon(xico)
        else: closeBtn.setText("×")
        closeBtn.clicked.connect(lambda: (self.request_close.emit(), self.back_requested.emit()))
        headL.addWidget(closeBtn,0)
        root.addWidget(head)

        # form scroller
        wrap = QScrollArea(); wrap.setWidgetResizable(True); wrap.setStyleSheet("QScrollArea{border:none;}")
        host = QWidget(); wrap.setWidget(host)
        form = QVBoxLayout(host); form.setContentsMargins(8,12,8,12); form.setSpacing(12)

        # panel
        panel = QFrame()
        panel.setStyleSheet(f"QFrame{{background:{WHITE};border:1px solid {GREEN};border-radius:8px;}}")
        L = QVBoxLayout(panel); L.setContentsMargins(12,12,12,12); L.setSpacing(16)

        # row0: Post To + Visibility
        r0 = QHBoxLayout(); r0.setSpacing(12)
        self.cboPost = QComboBox(); self.cboPost.addItems(["General","Students","Faculty","Organization"])
        self._label_wrap(r0, "Post To", self.cboPost)
        self.cboVisibility = QComboBox(); self.cboVisibility.addItems(["private","public"])
        self.cboVisibility.setCurrentText("private")
        self._label_wrap(r0, "Visibility", self.cboVisibility)
        r0.addStretch(1); L.addLayout(r0)

        # row1: Title
        r1 = QHBoxLayout(); r1.setSpacing(12)
        self.txtTitle = QLineEdit(); self.txtTitle.setPlaceholderText("Enter Title"); self.txtTitle.setMinimumWidth(420)
        self._label_wrap(r1, "Title", self.txtTitle, stretch=1)
        r1.addStretch(1); L.addLayout(r1)

        # row2: Message
        lblMsg = QLabel("Enter Message"); lblMsg.setStyleSheet(f"color:{TEXT};font:600 10.5pt;")
        self.txtBody = QTextEdit(); self.txtBody.setPlaceholderText("Enter Text Here"); self.txtBody.setFixedHeight(160)
        self.txtBody.setStyleSheet(f"QTextEdit{{background:{WHITE};border:1px solid {BORDER};border-radius:8px;padding:8px 10px;font:10.5pt;color:{TEXT};}}")
        L.addWidget(lblMsg); L.addWidget(self.txtBody)

        # row3: Remind At + Repeat + Priority
        r3 = QHBoxLayout(); r3.setSpacing(12)
        self.dtWhen = QDateTimeEdit(QDateTime.currentDateTime()); self.dtWhen.setCalendarPopup(True); self.dtWhen.setDisplayFormat("yyyy-MM-dd HH:mm")
        self._label_wrap(r3, "Remind At", self.dtWhen)
        self.cboRepeat = QComboBox(); self.cboRepeat.addItems(["none","daily","weekly","monthly"])
        self._label_wrap(r3, "Repeat", self.cboRepeat)
        self.cboPrio = QComboBox(); self.cboPrio.addItems(["0","1","2"]); self.cboPrio.setCurrentText("0")
        self._label_wrap(r3, "Priority", self.cboPrio)
        r3.addStretch(1); L.addLayout(r3)

        # row4: Snooze controls
        r4 = QHBoxLayout(); r4.setSpacing(12)
        self.chkSnoozable = QCheckBox("Allow Snooze"); self.chkSnoozable.setChecked(True)
        r4.addWidget(self.chkSnoozable, 0, Qt.AlignmentFlag.AlignVCenter)
        self.dtSnoozeUntil = QDateTimeEdit(); self.dtSnoozeUntil.setCalendarPopup(True); self.dtSnoozeUntil.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.dtSnoozeUntil.setEnabled(False)
        self._label_wrap(r4, "Snooze Until", self.dtSnoozeUntil)
        r4.addStretch(1); L.addLayout(r4)
        self.chkSnoozable.stateChanged.connect(lambda _:
            self.dtSnoozeUntil.setEnabled(self.chkSnoozable.isChecked())
        )

        # row5: Expires At
        r5 = QHBoxLayout(); r5.setSpacing(12)
        self.dtExpires = QDateTimeEdit(); self.dtExpires.setCalendarPopup(True); self.dtExpires.setDisplayFormat("yyyy-MM-dd HH:mm")
        self._label_wrap(r5, "Expires At", self.dtExpires)
        r5.addStretch(1); L.addLayout(r5)

        # row6: Internal note
        self.txtNote = QTextEdit(); self.txtNote.setPlaceholderText("Administrative note (optional)")
        self.txtNote.setFixedHeight(100)
        self.txtNote.setStyleSheet(f"QTextEdit{{background:{WHITE};border:1px solid {BORDER};border-radius:8px;padding:8px 10px;font:10.5pt;color:{TEXT};}}")
        L.addWidget(self.txtNote)

        form.addWidget(panel)
        root.addWidget(wrap, 1)

        # submit
        self.btnSubmit = QPushButton("Publish")
        self.btnSubmit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnSubmit.setFixedHeight(36); self.btnSubmit.setFixedWidth(220)
        self.btnSubmit.setStyleSheet(f"QPushButton{{background:{GREEN};color:white;border:none;border-radius:8px;font:600 10.5pt;}}")
        self.btnSubmit.clicked.connect(self._on_submit)
        btnBox = QHBoxLayout(); btnBox.addStretch(1); btnBox.addWidget(self.btnSubmit,0); btnBox.addStretch(1)
        root.addLayout(btnBox)

    def _label_wrap(self, layout: QHBoxLayout, label: str, widget: QWidget, stretch: int = 0) -> None:
        lbl = QLabel(label); lbl.setStyleSheet(f"color:{TEXT};font:600 10.5pt;")
        widget.setStyleSheet(
            widget.styleSheet() + f" QLineEdit,QComboBox,QDateTimeEdit{{background:{WHITE};border:1px solid {BORDER};border-radius:8px;padding:6px 10px;font:10.5pt;color:{TEXT};}}"
        )
        layout.addWidget(lbl, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(widget, stretch or 0, Qt.AlignmentFlag.AlignTop)

    # ---- actions ----
    def _on_submit(self) -> None:
        title = self.txtTitle.text().strip()
        body  = self.txtBody.toPlainText().strip()
        if not title:
            QMessageBox.warning(self, "Missing title", "Title is required."); return
        if not body:
            QMessageBox.warning(self, "Missing message", "Message is required."); return

        def _fmt_utc(dt: QDateTime) -> str:
            return dt.toUTC().toString("yyyy-MM-dd HH:mm:ss")

        remind_at_iso = _fmt_utc(self.dtWhen.dateTime())
        repeat = self.cboRepeat.currentText()
        priority = int(self.cboPrio.currentText())
        visibility = self.cboVisibility.currentText()
        is_snoozable = 1 if self.chkSnoozable.isChecked() else 0
        snooze_until_iso = _fmt_utc(self.dtSnoozeUntil.dateTime()) if self.dtSnoozeUntil.isEnabled() and self.dtSnoozeUntil.dateTime().isValid() else None
        expires_at_iso = _fmt_utc(self.dtExpires.dateTime()) if self.dtExpires.dateTime().isValid() else None
        note = self.txtNote.toPlainText().strip() or None

        scope_map = {"General":"general","Students":"students","Faculty":"faculty","Organization":"organization"}
        scope_type = scope_map.get(self.cboPost.currentText(), "general")

        try:
            rid = _insert_active_reminder(
                title=title,
                body=body,
                remind_at_iso=remind_at_iso,
                repeat_interval=repeat,
                priority=priority,
                visibility=visibility,
                scope_type=scope_type,
                is_snoozable=is_snoozable,
                snooze_until_iso=snooze_until_iso,
                expires_at_iso=expires_at_iso,
                note=note,
                author_id=CURRENT_USER_ID,
                created_by=CURRENT_USER_ID,
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to publish: {e}"); return

        QMessageBox.information(self, "Published", f"Reminder #{rid} published.")
        self.published.emit(rid)
        self.back_requested.emit()
        self.request_close.emit()  # legacy
        self._reset_form()


    def _reset_form(self) -> None:
        self.cboPost.setCurrentIndex(0)
        self.cboVisibility.setCurrentIndex(0)
        self.txtTitle.clear()
        self.txtBody.clear()
        self.cboRepeat.setCurrentIndex(0)
        self.cboPrio.setCurrentIndex(0)
        self.chkSnoozable.setChecked(True)
        self.dtSnoozeUntil.setEnabled(False)
        self.dtWhen.setDateTime(QDateTime.currentDateTime())
        self.dtExpires.setDateTime(QDateTime())  # clears
        self.txtNote.clear()
# Back-compat alias
AnnouncementAdminReminder = AnnouncementAdminReminderPage

# ---- run standalone ----
if __name__ == "__main__":
    ensure_bootstrap()
    app = QApplication(sys.argv)
    w = AnnouncementAdminReminder()
    w.resize(1120, 720)
    w.show()
    sys.exit(app.exec())
