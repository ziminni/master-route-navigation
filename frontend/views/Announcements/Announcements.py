# views/Announcements/Announcements.py
from __future__ import annotations
from importlib import import_module
from typing import List, Tuple
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QStackedWidget

# page targets
ROLE_ROUTE: dict[str, Tuple[str, str]] = {
    "admin":        ("views.Announcements.AnnouncementAdmin",        "AnnouncementAdmin"),
    "faculty":      ("views.Announcements.AnnouncementFaculty",      "AnnouncementFaculty"),
    "organization": ("views.Announcements.AnnouncementOrganization", "AnnouncementOrganization"),
    "student":      ("views.Announcements.AnnouncementStudent",      "AnnouncementStudent"),
}

ORG_ALIASES = {"organization", "org", "org_officer", "officer"}

def _resolve_role(roles: List[str] | None, primary_role: str) -> str:
    roles = [*(roles or [])]
    pr = (primary_role or "").lower()
    rset = {r.lower() for r in roles}

    if "admin" in rset or pr == "admin":
        return "admin"
    if ORG_ALIASES & rset or pr in ORG_ALIASES:
        return "organization"
    if pr in ROLE_ROUTE:
        return pr
    if "faculty" in rset:
        return "faculty"
    # staff behaves like faculty unless marked organization
    if "staff" in rset:
        return "faculty"
    if "student" in rset:
        return "student"
    return "student"

class AnnouncementsRouter(QWidget):
    def __init__(self, username: str | None = None, roles: List[str] | None = None,
                 primary_role: str | None = None, token: str | None = None,
                 parent: QWidget | None = None):
        super().__init__(parent)
        self.username = username or ""
        self.roles = roles or []
        self.primary_role = primary_role or ""
        self.token = token or ""
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0,0,0,0)
        lay.addWidget(QLabel("Loading Announcements…"))
        QTimer.singleShot(0, self._route)

    def _stack(self) -> QStackedWidget | None:
        p = self.parent()
        while p and not isinstance(p, QStackedWidget):
            p = p.parent()
        return p if isinstance(p, QStackedWidget) else None

    def _route(self) -> None:
        key = _resolve_role(self.roles, self.primary_role)
        mod_path, cls_name = ROLE_ROUTE[key]
        try:
            Page = getattr(import_module(mod_path), cls_name)
            page = Page(self.username, self.roles, self.primary_role, self.token)
        except Exception as e:
            err = QWidget(self)
            V = QVBoxLayout(err); V.addWidget(QLabel(f"Failed to load {mod_path}.{cls_name}: {e}"))
            page = err

        stack = self._stack()
        if not stack:
            (self.layout() or QVBoxLayout(self)).addWidget(page)
            return
        idx = stack.indexOf(self)
        cur = stack.currentWidget() is self
        stack.insertWidget(idx, page)
        stack.removeWidget(self)
        self.deleteLater()
        if cur: stack.setCurrentWidget(page)
