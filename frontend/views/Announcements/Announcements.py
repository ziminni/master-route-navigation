# views/Announcements/Announcements.py
from __future__ import annotations
from importlib import import_module
from typing import List, Tuple

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QStackedWidget

# role -> (module.path, class)
ROLE_ROUTE: dict[str, Tuple[str, str]] = {
    "admin":        ("views.Announcements.AnnouncementAdmin",        "AnnouncementAdmin"),
    "faculty":      ("views.Announcements.AnnouncementFaculty",      "AnnouncementFaculty"),
    # Staff uses the same page as the old "organization" view
    "staff":        ("views.Announcements.AnnouncementOrganization", "AnnouncementOrganization"),
    "student":      ("views.Announcements.AnnouncementStudent",      "AnnouncementStudent"),
    # legacy: if something still passes "organization" as a role, treat it as staff
    "organization": ("views.Announcements.AnnouncementOrganization", "AnnouncementOrganization"),
}

FALLBACK: Tuple[str, str] = ROLE_ROUTE["student"]
PRIORITY: List[str] = ["admin", "faculty", "staff", "student"]


def _norm_roles(roles: List[str] | None) -> List[str]:
    return [(r or "").strip().lower() for r in (roles or []) if r]


def _resolve_role(roles: List[str] | None, primary_role: str | None) -> str:
    rlist = _norm_roles(roles)
    pr = (primary_role or "").strip().lower()

    # legacy mapping: "organization" behaves as "staff"
    if pr == "organization":
        pr = "staff"
    rlist = ["staff" if r == "organization" else r for r in rlist]

    # 1) same rule as Showcase: trust primary_role if it matches a key
    if pr in ROLE_ROUTE:
        return pr

    # 2) walk priority list through roles[]
    for r in PRIORITY:
        if r in rlist:
            return r

    # 3) nothing matched
    return ""


class AnnouncementsRouter(QWidget):
    def __init__(
        self,
        username: str | None = None,
        roles: List[str] | None = None,
        primary_role: str | None = None,
        token: str | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.username = username or ""
        self.roles = roles or []
        self.primary_role = primary_role or ""
        self.token = token or ""

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(QLabel("Loading Announcements…"))

        QTimer.singleShot(0, self._route)

    def _stack(self) -> QStackedWidget | None:
        p = self.parent()
        while p is not None and not isinstance(p, QStackedWidget):
            p = p.parent()
        return p if isinstance(p, QStackedWidget) else None

    def _route(self) -> None:
        key = _resolve_role(self.roles, self.primary_role)
        mod_path, cls_name = ROLE_ROUTE.get(key, FALLBACK)

        # Optional debug – helps you see what Donald actually resolves to
        print(
            "[AnnouncementsRouter]",
            "user=", repr(self.username),
            "roles=", repr(self.roles),
            "primary_role=", repr(self.primary_role),
            "-> resolved=", repr(key),
        )

        try:
            PageCls = getattr(import_module(mod_path), cls_name)
            page = PageCls(self.username, self.roles, self.primary_role, self.token)
        except Exception as e:
            err = QWidget(self)
            v = QVBoxLayout(err)
            v.addWidget(QLabel(f"Failed to load {mod_path}.{cls_name}: {e}"))
            page = err

        stack = self._stack()
        if not stack:
            (self.layout() or QVBoxLayout(self)).addWidget(page)
            return

        idx = stack.indexOf(self)
        is_current = (stack.currentWidget() is self)

        stack.insertWidget(idx, page)
        stack.removeWidget(self)
        self.deleteLater()

        if is_current:
            stack.setCurrentWidget(page)
