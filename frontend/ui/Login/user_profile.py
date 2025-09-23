"""
CISC – Virtual Hub  |  User Profile (QWidget)
Clean spacing, text-only nav-bar, avatar file picker
"""

from PyQt6.QtCore import Qt, QDir
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFrame, QScrollArea, QLineEdit, QFileDialog, QMessageBox, QStackedWidget
)


# ---------------- Sidebar helpers ----------------
class NavItem(QFrame):
    def __init__(self, text, is_main=False, is_sub=False, has_badge=False):
        super().__init__()
        self.setFixedHeight(45 if is_main else 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(20 if is_main else 40, 0, 15, 0)

        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"font-size:14px;color:{'white' if is_main else '#b8c5ba'};"
            f"font-weight:{'bold' if is_main else 'normal'};"
        )
        lay.addWidget(lbl)

        if has_badge:
            badge = QLabel("●")
            badge.setStyleSheet("color:#dc3545;font-size:12px")
            lay.addWidget(badge)

        lay.addStretch()
        self.setStyleSheet(
            "NavItem{background:transparent;} "
            "NavItem:hover{background:rgba(255,255,255,30);}"
        )


class HeaderBar(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(70)
        self.setStyleSheet("background:white;border-bottom:1px solid #dee2e6;")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 0, 20, 0)

        lay.addWidget(QLabel("CISC Virtual Hub System",
                             styleSheet="font:18px bold;color:#1e4d2b"))
        lay.addStretch()

        search = QLineEdit(placeholderText="Search here…")
        search.setFixedSize(300, 36)
        search.setStyleSheet(
            "border:1px solid #dee2e6;border-radius:18px;padding-left:15px;"
            "background:#f8f9fa;font-size:14px"
        )
        lay.addWidget(search)
        lay.addStretch()

        def badge(emoji, cnt, bg="#007bff"):
            f = QFrame()
            v = QVBoxLayout(f)
            v.setContentsMargins(0, 0, 0, 0)
            v.addWidget(QLabel(emoji, styleSheet="font-size:20px"),
                        alignment=Qt.AlignmentFlag.AlignCenter)
            b = QLabel(cnt)
            b.setStyleSheet(f"background:{bg};color:white;border-radius:9px;font:10px bold")
            b.setFixedSize(18, 18)
            v.addWidget(b, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
            return f

        lay.addWidget(badge("✉️", "3"))
        lay.addWidget(badge("🔔", "1", "#ffc107"))

        profile = QFrame()
        h = QHBoxLayout(profile)
        pic = QLabel("👤")
        pic.setFixedSize(36, 36)
        pic.setStyleSheet("background:#6f42c1;border-radius:18px;color:white;font:16px")
        h.addWidget(pic)
        h.addWidget(QLabel("CARLOS FIDEL CASTRO\nStudent",
                           styleSheet="font:12px bold;color:#1e4d2b"))
        h.addWidget(QLabel("▼", styleSheet="color:#6c757d;font-size:12px"))
        lay.addWidget(profile)


# ----------------------------------------------------------------------
# Main profile widget
# ----------------------------------------------------------------------
class ProfileWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background:#f8f9fa;")

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---------- Sidebar ----------
        sidebar = QFrame()
        sidebar.setFixedWidth(280)
        sidebar.setStyleSheet("background:#1e4d2b;")
        v = QVBoxLayout(sidebar)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        top = QFrame()
        top.setFixedHeight(60)
        top.setStyleSheet("background:#ffc107;")
        h = QHBoxLayout(top)
        h.setContentsMargins(15, 0, 15, 0)
        h.addWidget(QLabel("☰"))
        h.addWidget(QLabel("Virtual Hub"))
        v.addWidget(top)

        nav = [
            ("Dashboard",),
            ("Academics", ["Classes", "Schedule", "Progress", "Appointments"]),
            ("Organizations", ["Browser", ("Membership", True), "Events"]),
            ("Campus", ["Calendar", "Announcement", "House System", "Showcase"]),
            ("Tools", ["Documents", "Messages", "Student Service"]),
        ]

        for entry in nav:
            if len(entry) == 1:
                v.addWidget(NavItem(entry[0], is_main=True))
            else:
                v.addWidget(NavItem(entry[0], is_main=True))
                for sub in entry[1]:
                    if isinstance(sub, tuple):
                        text, badge = sub
                        v.addWidget(NavItem(text, is_sub=True, has_badge=badge))
                    else:
                        v.addWidget(NavItem(sub, is_sub=True))
        v.addStretch()

        # ---------- Content ----------
        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(HeaderBar())

        self.stack = QStackedWidget()
        lay.addWidget(self.stack)

        # ---- Profile page ----
        profile_page = QWidget()
        p = QVBoxLayout(profile_page)
        p.setContentsMargins(40, 40, 40, 40)
        p.setSpacing(30)

        card = QFrame()
        card.setFixedHeight(400)
        card.setStyleSheet("background:white;border:1px solid #dee2e6;border-radius:15px")
        c = QVBoxLayout(card)
        c.setContentsMargins(40, 30, 40, 30)

        self.avatar_lbl = QLabel("👨‍💼")
        self.avatar_lbl.setFixedSize(180, 180)
        self.avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_lbl.setStyleSheet("border:3px solid #dee2e6;border-radius:90px;font-size:80px")
        c.addWidget(self.avatar_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)

        c.addWidget(QLabel("Welcome, Carlos!",
                           styleSheet="font:32px bold;color:#1e4d2b"),
                    alignment=Qt.AlignmentFlag.AlignCenter)

        for k, v in [("Name", "Carlos Fidel Castro"),
                     ("Course", "BSIT"),
                     ("Email", "s.castro.carlosfidel@coc.edu.ph"),
                     ("Role", "Student")]:
            row = QHBoxLayout()
            row.addWidget(QLabel(k + ":", styleSheet="font-weight:bold"))
            row.addWidget(QLabel(v))
            row.addStretch()
            c.addLayout(row)

        btn = QPushButton("Change Profile Picture")
        btn.setFixedSize(200, 45)
        btn.setStyleSheet("background:#28a745;color:white;border:none;border-radius:8px;font-weight:bold")
        btn.clicked.connect(self.show_change_page)
        c.addWidget(btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        p.addWidget(card)
        p.addStretch()

        # ---- Change picture page ----
        change_page = QWidget()
        ch = QVBoxLayout(change_page)
        ch.setContentsMargins(40, 40, 40, 40)
        ch.setSpacing(20)

        ch.addWidget(QLabel("Change Profile Picture",
                            styleSheet="font:28px bold;color:#1e4d2b"),
                     alignment=Qt.AlignmentFlag.AlignCenter)

        self.preview_lbl = QLabel("👨‍💼")
        self.preview_lbl.setFixedSize(150, 150)
        self.preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_lbl.setStyleSheet("border:2px solid #dee2e6;border-radius:75px")
        ch.addWidget(self.preview_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)

        choose_btn = QPushButton("Choose File")
        choose_btn.setFixedSize(150, 40)
        choose_btn.setStyleSheet("background:#007bff;color:white;border:none;border-radius:8px")
        choose_btn.clicked.connect(self.choose_avatar)

        save_btn = QPushButton("Save")
        save_btn.setFixedSize(150, 40)
        save_btn.setStyleSheet("background:#28a745;color:white;border:none;border-radius:8px")
        save_btn.clicked.connect(self.save_avatar)

        back_btn = QPushButton("Back")
        back_btn.setFixedSize(150, 40)
        back_btn.setStyleSheet("background:#6c757d;color:white;border:none;border-radius:8px")
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        h_btns = QHBoxLayout()
        h_btns.addStretch()
        h_btns.addWidget(choose_btn)
        h_btns.addWidget(save_btn)
        h_btns.addWidget(back_btn)
        h_btns.addStretch()
        ch.addLayout(h_btns)
        ch.addStretch()

        self.stack.addWidget(profile_page)
        self.stack.addWidget(change_page)
        self.stack.setCurrentIndex(0)

        root.addWidget(sidebar)
        root.addWidget(content)
        root.setStretch(0, 1)
        root.setStretch(1, 4)

    def show_change_page(self):
        """Switch to the change profile picture page"""
        self.stack.setCurrentIndex(1)

    # ---------------- Avatar helpers ----------------
    def set_avatar(self, path: str):
        if path == ":default":
            self.avatar_lbl.setText("👨‍💼")
            self.preview_lbl.setText("👨‍💼")
            return
        pixmap = QPixmap(path).scaled(150, 150,
                                      Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                      Qt.TransformationMode.SmoothTransformation)
        rounded = QPixmap(150, 150)
        rounded.fill(Qt.GlobalColor.transparent)
        p = QPainter(rounded)
        path_clip = QPainterPath()
        path_clip.addRoundedRect(0, 0, 150, 150, 75, 75)
        p.setClipPath(path_clip)
        p.drawPixmap(0, 0, pixmap)
        p.end()
        self.avatar_lbl.setPixmap(rounded)
        self.preview_lbl.setPixmap(rounded)

    def choose_avatar(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Select Picture", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file:
            self.set_avatar(file)

    def save_avatar(self):
        QMessageBox.information(self, "Success", "Profile picture updated!")
        self.stack.setCurrentIndex(0)