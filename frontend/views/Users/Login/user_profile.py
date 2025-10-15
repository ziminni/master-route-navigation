# """
# CISC – Virtual Hub | User Profile (QWidget)
# Content-only profile page with avatar picker. To be embedded under your app's
# global header/sidebar (LayoutManager), not self-rendered here.
# """

# from PyQt6.QtCore import Qt
# from PyQt6.QtGui import QPixmap, QPainter, QPainterPath
# from PyQt6.QtWidgets import (
#     QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
#     QFrame, QFileDialog, QMessageBox, QStackedWidget
# )

# class ProfileWidget(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.setStyleSheet("background:#f8f9fa;")

#         root = QVBoxLayout(self)
#         root.setContentsMargins(24, 24, 24, 24)
#         root.setSpacing(16)

#         # stack holds: [0]=profile summary, [1]=change picture
#         self.stack = QStackedWidget()
#         root.addWidget(self.stack, 1)

#         # ---- Profile page ----
#         profile_page = QWidget()
#         p = QVBoxLayout(profile_page)
#         p.setContentsMargins(0, 0, 0, 0)
#         p.setSpacing(20)

#         title = QLabel("User Profile")
#         title.setStyleSheet("font:24px bold;color:#1e4d2b")
#         p.addWidget(title)

#         card = QFrame()
#         card.setStyleSheet("background:white;border:1px solid #dee2e6;border-radius:12px")
#         c = QVBoxLayout(card)
#         c.setContentsMargins(24, 24, 24, 24)
#         c.setSpacing(16)

#         self.avatar_lbl = QLabel("👨‍💼")
#         self.avatar_lbl.setFixedSize(160, 160)
#         self.avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
#         self.avatar_lbl.setStyleSheet("border:3px solid #dee2e6;border-radius:80px;font-size:72px")
#         c.addWidget(self.avatar_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)

#         name = QLabel("Welcome, Carlos!")
#         name.setStyleSheet("font:22px bold;color:#1e4d2b")
#         c.addWidget(name, alignment=Qt.AlignmentFlag.AlignHCenter)

#         for k, v in [("Name", "Carlos Fidel Castro"),
#                      ("Course", "BSIT"),
#                      ("Email", "s.castro.carlosfidel@coc.edu.ph"),
#                      ("Role", "Student")]:
#             row = QHBoxLayout()
#             row.addWidget(QLabel(k + ":", styleSheet="font-weight:bold;color:#374151"))
#             row.addWidget(QLabel(v, styleSheet="color:#374151"))
#             row.addStretch()
#             c.addLayout(row)

#         btn = QPushButton("Change Profile Picture")
#         btn.setFixedSize(200, 42)
#         btn.setStyleSheet("background:#28a745;color:white;border:none;border-radius:8px;font-weight:bold")
#         btn.clicked.connect(self.show_change_page)
#         c.addWidget(btn, alignment=Qt.AlignmentFlag.AlignHCenter)

#         p.addWidget(card)
#         p.addStretch()

#         # ---- Change picture page ----
#         change_page = QWidget()
#         ch = QVBoxLayout(change_page)
#         ch.setContentsMargins(0, 0, 0, 0)
#         ch.setSpacing(16)

#         ch_title = QLabel("Change Profile Picture")
#         ch_title.setStyleSheet("font:22px bold;color:#1e4d2b")
#         ch.addWidget(ch_title, alignment=Qt.AlignmentFlag.AlignHCenter)

#         self.preview_lbl = QLabel("👨‍💼")
#         self.preview_lbl.setFixedSize(150, 150)
#         self.preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
#         self.preview_lbl.setStyleSheet("border:2px solid #dee2e6;border-radius:75px")
#         ch.addWidget(self.preview_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)

#         choose_btn = QPushButton("Choose File")
#         choose_btn.setFixedSize(140, 38)
#         choose_btn.setStyleSheet("background:#007bff;color:white;border:none;border-radius:8px")
#         choose_btn.clicked.connect(self.choose_avatar)

#         save_btn = QPushButton("Save")
#         save_btn.setFixedSize(140, 38)
#         save_btn.setStyleSheet("background:#28a745;color:white;border:none;border-radius:8px")
#         save_btn.clicked.connect(self.save_avatar)

#         back_btn = QPushButton("Back")
#         back_btn.setFixedSize(140, 38)
#         back_btn.setStyleSheet("background:#6c757d;color:white;border:none;border-radius:8px")
#         back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))

#         h_btns = QHBoxLayout()
#         h_btns.addStretch()
#         h_btns.addWidget(choose_btn)
#         h_btns.addWidget(save_btn)
#         h_btns.addWidget(back_btn)
#         h_btns.addStretch()
#         ch.addLayout(h_btns)
#         ch.addStretch()

#         self.stack.addWidget(profile_page)
#         self.stack.addWidget(change_page)
#         self.stack.setCurrentIndex(0)

#     def show_change_page(self):
#         self.stack.setCurrentIndex(1)

#     # ---- Avatar helpers ----
#     def set_avatar(self, path: str):
#         if path == ":default":
#             self.avatar_lbl.setText("👨‍💼")
#             self.preview_lbl.setText("👨‍💼")
#             self.avatar_lbl.setPixmap(QPixmap())
#             self.preview_lbl.setPixmap(QPixmap())
#             return
#         pixmap = QPixmap(path).scaled(
#             150, 150,
#             Qt.AspectRatioMode.KeepAspectRatioByExpanding,
#             Qt.TransformationMode.SmoothTransformation,
#         )
#         rounded = QPixmap(150, 150)
#         rounded.fill(Qt.GlobalColor.transparent)
#         p = QPainter(rounded)
#         clip = QPainterPath()
#         clip.addRoundedRect(0, 0, 150, 150, 75, 75)
#         p.setClipPath(clip)
#         p.drawPixmap(0, 0, pixmap)
#         p.end()
#         self.avatar_lbl.setPixmap(rounded)
#         self.preview_lbl.setPixmap(rounded)

#     def choose_avatar(self):
#         file, _ = QFileDialog.getOpenFileName(self, "Select Picture", "", "Images (*.png *.jpg *.jpeg *.bmp)")
#         if file:
#             self.set_avatar(file)

#     def save_avatar(self):
#         QMessageBox.information(self, "Success", "Profile picture updated!")
#         self.stack.setCurrentIndex(0)

"""
CISC – Virtual Hub | User Profile (content-only)
Populates from session + /api/users/me/.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFrame, QFileDialog, QMessageBox, QStackedWidget
)

# try to reuse your API base if defined in AuthService
API_BASE = "http://127.0.0.1:8000"
try:
    from services.auth_service import BASE_API_URL as _BASE
    if _BASE:
        API_BASE = _BASE
except Exception:
    pass

class ProfileWidget(QWidget):
    def __init__(self, session: dict | None = None, user: dict | None = None):
        super().__init__()
        self.session = session or {}
        self.user = user or {}
        self.setStyleSheet("background:#f8f9fa;")

        root = QVBoxLayout(self); root.setContentsMargins(24,24,24,24); root.setSpacing(16)
        self.stack = QStackedWidget(); root.addWidget(self.stack, 1)

        # ---- Profile page ----
        profile_page = QWidget(); p = QVBoxLayout(profile_page); p.setSpacing(20)
        title = QLabel("User Profile"); title.setStyleSheet("font:24px bold;color:#1e4d2b"); p.addWidget(title)

        card = QFrame(); card.setStyleSheet("background:white;border:1px solid #dee2e6;border-radius:12px")
        c = QVBoxLayout(card); c.setContentsMargins(24,24,24,24); c.setSpacing(16)

        self.avatar_lbl = QLabel("👤"); self.avatar_lbl.setFixedSize(160,160)
        self.avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_lbl.setStyleSheet("border:3px solid #dee2e6;border-radius:80px;font-size:72px")
        c.addWidget(self.avatar_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.name_lbl   = QLabel("—"); self.name_lbl.setStyleSheet("font:22px bold;color:#1e4d2b")
        c.addWidget(self.name_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.rows = {}
        def add_row(k, key):
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{k}:", styleSheet="font-weight:bold;color:#374151"))
            val = QLabel("—"); val.setStyleSheet("color:#374151")
            row.addWidget(val); row.addStretch(); c.addLayout(row)
            self.rows[key] = val

        add_row("Institutional ID", "institutional_id")
        add_row("Email", "email")
        add_row("Role", "primary_role")
        add_row("Program", "program")
        add_row("Section", "section")
        add_row("Department", "faculty_department")
        add_row("Position", "position")
        add_row("Phone", "phone_number")
        add_row("Birth date", "birth_date")

        btn = QPushButton("Change Profile Picture")
        btn.setFixedSize(200, 42)
        btn.setStyleSheet("background:#28a745;color:white;border:none;border-radius:8px;font-weight:bold")
        btn.clicked.connect(self.show_change_page)
        c.addWidget(btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        p.addWidget(card); p.addStretch()

        # ---- Change picture page ----
        change_page = QWidget(); ch = QVBoxLayout(change_page); ch.setSpacing(16)
        ch_title = QLabel("Change Profile Picture"); ch_title.setStyleSheet("font:22px bold;color:#1e4d2b")
        ch.addWidget(ch_title, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.preview_lbl = QLabel("👤"); self.preview_lbl.setFixedSize(150,150)
        self.preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_lbl.setStyleSheet("border:2px solid #dee2e6;border-radius:75px")
        ch.addWidget(self.preview_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)

        choose_btn = QPushButton("Choose File"); choose_btn.setFixedSize(140,38)
        choose_btn.setStyleSheet("background:#007bff;color:white;border:none;border-radius:8px")
        choose_btn.clicked.connect(self.choose_avatar)

        save_btn = QPushButton("Save"); save_btn.setFixedSize(140,38)
        save_btn.setStyleSheet("background:#28a745;color:white;border:none;border-radius:8px")
        save_btn.clicked.connect(self.save_avatar)

        back_btn = QPushButton("Back"); back_btn.setFixedSize(140,38)
        back_btn.setStyleSheet("background:#6c757d;color:white;border:none;border-radius:8px")
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        hb = QHBoxLayout(); hb.addStretch(); hb.addWidget(choose_btn); hb.addWidget(save_btn); hb.addWidget(back_btn); hb.addStretch()
        ch.addLayout(hb); ch.addStretch()

        self.stack.addWidget(profile_page); self.stack.addWidget(change_page); self.stack.setCurrentIndex(0)

        # populate
        self._populate_from_session_then_me()

    # ---------- data ----------
    def _populate_from_session_then_me(self):
        # session-only first
        uname = self.session.get("username") or self.user.get("username") or "User"
        role  = (self.session.get("primary_role") or self.user.get("primary_role") or "—").title()
        self.name_lbl.setText(uname)
        self.rows["primary_role"].setText(role)

        # if login payload already had user dict
        for k in ("email","institutional_id","phone_number","birth_date"):
            if self.user.get(k):
                self.rows[k].setText(str(self.user[k]))

        # fetch /me if token is present
        token = self.session.get("token")
        if not token:
            return
        try:
            import requests
            url = f"{API_BASE.rstrip('/')}/api/users/me/"
            r = requests.get(url, headers={"Authorization": f"Bearer {token}", "Accept":"application/json"}, timeout=8)
            if r.status_code == 200:
                me = r.json() or {}
                # basic fields
                full = me.get("full_name") or " ".join(filter(None, [me.get("first_name"), me.get("last_name")])) or uname
                self.name_lbl.setText(full)
                self.rows["email"].setText(me.get("email") or "—")
                self.rows["primary_role"].setText((me.get("primary_role") or role).title())
                self.rows["institutional_id"].setText(me.get("institutional_id") or "—")
                self.rows["phone_number"].setText(me.get("phone_number") or "—")
                self.rows["birth_date"].setText(me.get("birth_date") or "—")

                # nested profiles (if serializer returns them)
                sp = me.get("student_profile") or {}
                fp = me.get("faculty_profile") or {}
                st = me.get("staff_profile") or {}

                self.rows["program"].setText(get_name(sp.get("program")) or "—")
                self.rows["section"].setText(get_name(sp.get("section")) or "—")
                self.rows["faculty_department"].setText(get_name(fp.get("faculty_department")) or get_name(st.get("faculty_department")) or "—")
                self.rows["position"].setText(get_name(fp.get("position")) or st.get("job_title") or "—")

                # avatar if provided as URL or media path
                avatar = me.get("profile_picture")
                if avatar:
                    self._set_avatar_from_url(avatar if avatar.startswith("http") else f"{API_BASE.rstrip('/')}{avatar}")
        except Exception:
            pass  # stay silent in UI

    # ---------- UI helpers ----------
    def show_change_page(self):
        self.stack.setCurrentIndex(1)

    def set_avatar(self, path: str):
        if path == ":default":
            self.avatar_lbl.setText("👤"); self.preview_lbl.setText("👤")
            self.avatar_lbl.setPixmap(QPixmap()); self.preview_lbl.setPixmap(QPixmap()); return
        pixmap = QPixmap(path).scaled(150,150, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        self._apply_rounded(pixmap)

    def choose_avatar(self):
        from PyQt6.QtWidgets import QFileDialog
        file, _ = QFileDialog.getOpenFileName(self, "Select Picture", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file:
            self.set_avatar(file)

    def save_avatar(self):
        QMessageBox.information(self, "Success", "Profile picture updated!")
        self.stack.setCurrentIndex(0)

    def _apply_rounded(self, pixmap: QPixmap):
        rounded = QPixmap(150,150); rounded.fill(Qt.GlobalColor.transparent)
        p = QPainter(rounded); clip = QPainterPath(); clip.addRoundedRect(0,0,150,150,75,75)
        p.setClipPath(clip); p.drawPixmap(0,0,pixmap); p.end()
        self.avatar_lbl.setPixmap(rounded); self.preview_lbl.setPixmap(rounded)

    def _set_avatar_from_url(self, url: str):
        try:
            import requests
            r = requests.get(url, timeout=8)
            if r.ok:
                pix = QPixmap(); pix.loadFromData(r.content)
                pix = pix.scaled(150,150, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                self._apply_rounded(pix)
        except Exception:
            pass

def get_name(obj):
    """Accept str or dict with *_name fields."""
    if not obj: return None
    if isinstance(obj, str): return obj
    for key in ("program_name","section_name","department_name","position_name","name","title"):
        if key in obj and obj[key]:
            return obj[key]
    return None
