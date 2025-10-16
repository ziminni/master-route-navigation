import os
import json
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFontMetrics


class NavbarSection(QWidget):
    """
    Reusable navigation bar with animated underline.
    Usage:
        navbar = NavbarSection(active_tab="Members", callback=self.on_nav_clicked)
        layout.addWidget(navbar)
    """

    def __init__(self, active_tab="Overview", callback=None, parent=None):
        super().__init__(parent)
        self.callback = callback
        self.active_tab = active_tab
        self.nav_buttons = []

        # --- Main layout ---
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(8)

        # --- Nav row ---
        self.nav_row = QHBoxLayout()
        self.nav_row.setSpacing(20)

        nav_container = QWidget()
        nav_container.setObjectName("navContainer")
        nav_container.setLayout(self.nav_row)
        self.main_layout.addWidget(nav_container)

        # --- Load nav items ---
        nav_tabs = self._load_tabs()
        for tab in nav_tabs:
            btn = QPushButton(tab)
            btn.setCheckable(True)
            btn.setChecked(tab == self.active_tab)
            btn.setObjectName("navButton")
            btn.clicked.connect(lambda checked, t=tab: self._on_tab_clicked(t))
            self.nav_row.addWidget(btn)
            self.nav_buttons.append(btn)
        self.nav_row.addStretch()

        # --- Yellow underline ---
        self.nav_highlight = QWidget(self)
        self.nav_highlight.setObjectName("navHighlight")
        self.nav_highlight.setFixedHeight(12)
        self.nav_highlight.setStyleSheet("""
            QWidget#navHighlight {
                background-color: #FDC601;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
        """)

        # --- Divider line ---
        divider = QWidget()
        divider.setFixedHeight(2)
        divider.setObjectName("dividerLine")
        divider.setStyleSheet("""
            QWidget#dividerLine {
                background-color: #084924;
                border: none;
            }
        """)
        self.main_layout.addWidget(divider)

        # --- Stylesheet for buttons ---
        self.setStyleSheet("""
            QPushButton#navButton {
                width: 122px;
                height: 31px;
                font-family: 'Poppins';
                font-weight: 310;
                font-size: 18px;
                color: #084924;
                text-align: center;
                background: transparent;
                border: none;
            }
            QPushButton#navButton:checked {
                font-weight: 600;
            }
            QPushButton#navButton:hover {
                color: #0B6630;
            }
        """)

        # Track underline animation
        self.nav_anim = None
        self.nav_highlight.raise_()
        self._initialized = False

    # -------------------------------
    # INTERNAL METHODS
    # -------------------------------

    def _load_tabs(self):
        """Load tab names from data/navbar.json if available"""
        navjson_path = "data/navbar.json"
        try:
            with open(navjson_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("tabs", ["Overview", "Events", "Members", "History", "Leaderboards"])
        except Exception:
            return ["Overview", "Events", "Members", "History", "Leaderboards"]

    def _on_tab_clicked(self, tab_name):
        """Trigger tab activation and underline animation"""
        for btn in self.nav_buttons:
            is_active = (btn.text() == tab_name)
            btn.setChecked(is_active)
            if is_active:
                self.active_tab = tab_name
                self._animate_highlight(btn)

        if self.callback:
            self.callback(tab_name)

    def _animate_highlight(self, btn):
        """Animate the underline (yellow bar) below active tab"""
        metrics = QFontMetrics(btn.font())
        text_width = metrics.horizontalAdvance(btn.text())
        btn_pos = btn.mapTo(self, btn.rect().topLeft())

        divider = self.findChild(QWidget, "dividerLine")
        divider_y = divider.mapTo(self, divider.rect().topLeft()).y()
        underline_y = divider_y - self.nav_highlight.height() + 1

        anim = QPropertyAnimation(self.nav_highlight, b"geometry")
        anim.setDuration(250)
        anim.setStartValue(self.nav_highlight.geometry())
        anim.setEndValue(QRect(
            int(btn_pos.x() + (btn.width() - text_width) / 2),
            underline_y,
            int(text_width),
            self.nav_highlight.height()
        ))
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        anim.start()
        self.nav_anim = anim  # prevent garbage collection

    def showEvent(self, event):
        """Initialize highlight position when the navbar first shows"""
        super().showEvent(event)
        if not self._initialized:
            self._initialized = True
            for btn in self.nav_buttons:
                if btn.text() == self.active_tab:
                    self._animate_highlight(btn)
                    break
