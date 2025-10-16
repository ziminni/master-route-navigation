# views/Showcase/Showcase.py
from __future__ import annotations
from importlib import import_module

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QStackedWidget

# role -> (module.path, class)
ROLE_ROUTE = {
    "admin":   ("views.Showcase.ShowcaseAdmin", "ShowcaseAdminPage"),
    "faculty": ("views.Showcase.ShowcaseGeneral", "ShowcaseGeneralPage"),
    "staff":   ("views.Showcase.ShowcaseOrganization", "ShowcaseOrganizationPage"),
    "student": ("views.Showcase.ShowcaseStudent", "ShowcaseStudentPage")
}
FALLBACK = ("views.Showcase.ShowcaseGeneral", "ShowcaseGeneralPage")

PRIORITY = ["admin","faculty","staff","student"]
def _resolve_role(roles, primary_role):
    if primary_role in ROLE_ROUTE: return primary_role
    for r in PRIORITY:
        if r in (roles or []): return r
    return ""


class ShowcaseRouter(QWidget):
    def __init__(self, username: str = "", roles: list[str] | None = None,
                 primary_role: str = "", token: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.username, self.roles, self.primary_role, self.token = username, (roles or []), primary_role, token
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("Loading Showcase…"))
        QTimer.singleShot(0, self._route)

    def _find_stack(self) -> QStackedWidget | None:
        p = self.parent()
        while p is not None and not isinstance(p, QStackedWidget):
            p = p.parent()
        return p if isinstance(p, QStackedWidget) else None

    def _route(self) -> None:
        role_key = _resolve_role(self.roles, self.primary_role)
        mod_path, cls_name = ROLE_ROUTE.get(role_key, FALLBACK)
        try:
            mod = import_module(mod_path)
            PageCls = getattr(mod, cls_name)
            target = PageCls(self.username, self.roles, self.primary_role, self.token)
        except Exception as e:
            err = QWidget(self); v = QVBoxLayout(err)
            v.addWidget(QLabel(f"Failed to load {mod_path}.{cls_name}: {e}"))
            target = err

        stack = self._find_stack()
        if not stack:
            (self.layout() or QVBoxLayout(self)).addWidget(target)
            return

        idx = stack.indexOf(self)
        is_current = (stack.currentWidget() is self)

        if idx >= 0:
            stack.insertWidget(idx, target)
            stack.removeWidget(self)
            self.deleteLater()
            if is_current:
                stack.setCurrentWidget(target)