from PyQt6.QtWidgets import QStackedWidget, QLabel, QVBoxLayout, QWidget
from PyQt6.QtGui import QFont
from utils.db_helper import NavigationDataHelper, get_path_for_main, get_path_for_modular
from importlib import import_module
import os, sys

class Router:
    def __init__(self, user_role: str | None, user_session: dict | None = None):
        # sys.path: project root
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        if project_root not in sys.path:
            sys.path.append(project_root)
        print(f"Router: Added {project_root} to sys.path")

        self.stack = QStackedWidget()
        self.nav_helper = NavigationDataHelper(json_file="navbar.json")

        self.user_session = user_session or {}
        self.user_role = self._resolve_role(user_role)

        self.page_map: dict[str, int] = {}
        self.allowed_keys: set[str] = set()

        self._page_classes = self._build_page_classes()
        self._preload_pages()

    # ---------- role from token (Module 7) ----------
    def _resolve_role(self, fallback: str | None) -> str:
        try:
            from utils import session
            role = session.get_role()
            print(f"Router: role from token = {role}")
            return role
        except Exception as e:
            print(f"Router: session.get_role() unavailable ({e}); using fallback = {fallback}")
            if not fallback:
                raise RuntimeError("No role available. Ensure token is set via utils.session.set_token().")
            return fallback

    # ---------- imports ----------
    def _build_page_classes(self) -> dict[str, type]:
        page_classes: dict[str, type] = {}

        for parent in self.nav_helper.data.get("parents", []):
            parent_id = parent.get("id")
            print(f"Router: Processing parent ID {parent_id}")

            for main in parent.get("mains", []):
                main_id = main.get("id")
                func = (main.get("function") or "").replace("()", "")
                module_path = get_path_for_main(main_id)
                print(f"Router: main {main_id} -> {module_path}.{func}")

                if module_path and func:
                    try:
                        module = import_module(module_path)
                        page_classes[f"main_{main_id}"] = getattr(module, func)
                        print(f"Router: Imported class {func} for main_{main_id}")
                    except Exception as e:
                        print(f"Router: Import failed for main_{main_id}: {e}")

                # modulars
                for modular in main.get("modulars", []):
                    mod_id = modular.get("id")
                    mfunc = (modular.get("function") or "").replace("()", "")
                    mpath = get_path_for_modular(mod_id)
                    print(f"Router: modular {mod_id} -> {mpath}.{mfunc}")

                    if mpath and mfunc:
                        try:
                            module = import_module(mpath)
                            page_classes[f"mod_{main_id}_{mod_id}"] = getattr(module, mfunc)
                            print(f"Router: Imported class {mfunc} for mod_{main_id}_{mod_id}")
                        except Exception as e:
                            print(f"Router: Import failed for mod_{main_id}_{mod_id}: {e}")

        return page_classes

    # ---------- preload allowed pages ----------
    def _preload_pages(self) -> None:
        # Access Denied baseline
        access_denied = self._create_default_widget("Access Denied", "You do not have permission to view this page.")
        self.access_denied_index = self.stack.addWidget(access_denied)
        self.page_map["access_denied"] = self.access_denied_index

        role = self.user_role

        for parent in self.nav_helper.data.get("parents", []):
            for main in parent.get("mains", []):
                main_id = main.get("id")
                main_name = main.get("name", f"Main {main_id}")
                if self._is_allowed(main.get("access"), role):
                    key = f"main_{main_id}"
                    page = self._instantiate_page(key, main_name, f"Page for {main_name}")
                    idx = self.stack.addWidget(page)
                    self.page_map[key] = idx
                    self.allowed_keys.add(key)
                    print(f"Router: Added {key} (idx {idx})")

                # each modular uses its OWN access list
                for modular in main.get("modulars", []):
                    mod_id = modular.get("id")
                    mod_name = modular.get("name", f"Mod {mod_id}")
                    if self._is_allowed(modular.get("access"), role):
                        mkey = f"mod_{main_id}_{mod_id}"
                        page = self._instantiate_page(mkey, mod_name, f"Sub-page for {mod_name}")
                        idx = self.stack.addWidget(page)
                        self.page_map[mkey] = idx
                        self.allowed_keys.add(mkey)
                        print(f"Router: Added {mkey} (idx {idx})")

    # ---------- helpers ----------
    @staticmethod
    def _is_allowed(access, role: str) -> bool:
        # access may be list[str], str, or missing
        if access is None:
            return True  # treat missing as open; backend still enforces
        if isinstance(access, str):
            return access == role
        if isinstance(access, list):
            return role in access
        return False

    def _instantiate_page(self, key: str, title_fallback: str, desc_fallback: str) -> QWidget:
        page_class = self._page_classes.get(key)
        if page_class:
            try:
                return page_class(
                    username=self.user_session.get("username", ""),
                    roles=self.user_session.get("roles", []),
                    primary_role=self.user_session.get("primary_role", ""),
                    token=self.user_session.get("token", "")
                )
            except Exception as e:
                print(f"Router: constructing {key} failed: {e}")
        return self._create_default_widget(title_fallback, desc_fallback)

    # ---------- navigation with guard ----------
    def navigate(self, page_id: int, is_modular: bool = False, parent_main_id: int | None = None):
        key = f"mod_{parent_main_id}_{page_id}" if is_modular else f"main_{page_id}"
        print(f"Router: navigate -> {key}")

        if key not in self.allowed_keys:
            print(f"Router: {key} not allowed for role={self.user_role}. Deny.")
            self.stack.setCurrentIndex(self.access_denied_index)
            return

        idx = self.page_map.get(key)
        if idx is None:
            print(f"Router: {key} not preloaded. Deny.")
            self.stack.setCurrentIndex(self.access_denied_index)
            return

        self.stack.setCurrentIndex(idx)

    # ---------- maintenance ----------
    def clear_pages(self):
        while self.stack.count() > 0:
            w = self.stack.widget(0)
            self.stack.removeWidget(w)
            w.deleteLater()
        self.page_map.clear()
        self.allowed_keys.clear()
        access_denied = self._create_default_widget("Access Denied", "You do not have permission to view this page.")
        self.access_denied_index = self.stack.addWidget(access_denied)
        self.page_map["access_denied"] = self.access_denied_index

    # ---------- default widget ----------
    def _create_default_widget(self, title: str, desc: str) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout()
        t = QLabel(title); t.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        d = QLabel(desc);  d.setFont(QFont("Arial", 12))
        lay.addWidget(t); lay.addWidget(d); lay.addStretch()
        w.setLayout(lay)
        return w
