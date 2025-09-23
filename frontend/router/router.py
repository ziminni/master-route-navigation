from PyQt6.QtWidgets import QStackedWidget, QLabel, QVBoxLayout, QWidget
from PyQt6.QtGui import QFont
from utils.db_helper import NavigationDataHelper
from importlib import import_module
import os

class Router:
    def __init__(self, user_role):
        self.stack = QStackedWidget()
        self.nav_helper = NavigationDataHelper()
        self.user_role = user_role
        self.page_map = {}
        self._page_classes = self._build_page_classes()
        self._preload_pages()

    def _build_page_classes(self):
        """Parse navbar.json 'function' fields to build {id_or_key: ClassObject} map."""
        page_classes = {}
        for parent in self.nav_helper.data["parents"]:
            parent_name = parent["name"]  # Use as-is (e.g., "Academics")
            parent_id = parent["id"]

            print(f"Router: Processing parent '{parent_name}' (ID: {parent_id})")

            # Handle mains
            for main in parent["mains"]:
                main_id = main["id"]
                function_str = main["function"]
                class_name = function_str.replace("()", "")  # e.g., "ClassesPage"

                try:
                    # Assume module path: views.<parent_name>.<class_name.lower()>
                    module_path = f"views.{parent_name}.{class_name.lower()}"
                    file_path = os.path.join("views", parent_name, f"{class_name.lower()}.py")
                    print(f"Router: Attempting to import {module_path}, file: {file_path}, exists: {os.path.exists(file_path)}")
                    module = import_module(module_path)
                    page_class = getattr(module, class_name)
                    page_classes[f"main_{main_id}"] = page_class  # Key matches page_map
                    print(f"Router: Successfully imported {class_name} for main ID {main_id}")
                except (ImportError, AttributeError) as e:
                    print(f"Warning: Could not import {class_name} from {module_path}: {e}")
                    # Fallback: page_classes[f"main_{main_id}"] = None (handled later)

            # Handle modulars (extend key with parent main_id)
            for main in parent["mains"]:
                main_id = main["id"]
                for modular in main["modulars"]:
                    mod_id = modular["id"]
                    function_str = modular.get("function", "")  # Optional for modulars
                    if function_str:
                        class_name = function_str.replace("()", "")
                        try:
                            module_path = f"views.{parent_name}.{class_name.lower()}"
                            file_path = os.path.join("views", parent_name, f"{class_name.lower()}.py")
                            print(f"Router: Attempting to import {module_path} for modular, file: {file_path}, exists: {os.path.exists(file_path)}")
                            module = import_module(module_path)
                            page_class = getattr(module, class_name)
                            page_classes[f"mod_{main_id}_{mod_id}"] = page_class
                            print(f"Router: Successfully imported {class_name} for modular ID {mod_id}")
                        except (ImportError, AttributeError) as e:
                            print(f"Warning: Could not import modular {class_name}: {e}")

        return page_classes

    def _preload_pages(self):
        # Default "Access Denied" page
        access_denied_widget = self._create_default_widget("Access Denied", "You do not have permission to view this page.")
        self.stack.addWidget(access_denied_widget)
        self.page_map["access_denied"] = 0

        # Load pages from navbar.json
        for parent in self.nav_helper.data["parents"]:
            for main in parent["mains"]:
                main_id = main["id"]
                access = main["access"]
                name = main["name"]
                key = f"main_{main_id}"

                # Check role access
                if (isinstance(access, str) and (access == self.user_role or self.user_role == "super_admin")) or \
                   (isinstance(access, list) and (self.user_role in access or self.user_role == "super_admin")):
                    page_class = self._page_classes.get(key)
                    page = page_class() if page_class else self._create_default_widget(name, f"Page for {name}")
                    index = self.stack.addWidget(page)
                    self.page_map[key] = index

                # Load modulars
                for modular in main["modulars"]:
                    mod_id = modular["id"]
                    mod_name = modular["name"]
                    mod_key = f"mod_{main_id}_{mod_id}"

                    if (isinstance(access, str) and (access == self.user_role or self.user_role == "super_admin")) or \
                       (isinstance(access, list) and (self.user_role in access or self.user_role == "super_admin")):
                        page_class = self._page_classes.get(mod_key)
                        page = page_class() if page_class else self._create_default_widget(mod_name, f"Sub-page for {mod_name}")
                        index = self.stack.addWidget(page)
                        self.page_map[mod_key] = index

    def _create_default_widget(self, title, desc):
        """Fallback widget if class not found."""
        widget = QWidget()
        layout = QVBoxLayout()
        t = QLabel(title)
        t.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        d = QLabel(desc)
        d.setFont(QFont("Arial", 12))
        layout.addWidget(t)
        layout.addWidget(d)
        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def navigate(self, page_id, is_modular=False, parent_main_id=None):
        key = f"mod_{parent_main_id}_{page_id}" if is_modular else f"main_{page_id}"
        index = self.page_map.get(key)
        if index is not None:
            self.stack.setCurrentWidget(self.stack.widget(index))
        else:
            missing_page = self._create_default_widget("⚠️ Missing Page", f"No page found for ID {key}")
            index = self.stack.addWidget(missing_page)
            self.page_map[key] = index
            self.stack.setCurrentWidget(missing_page)

    def clear_pages(self):
        while self.stack.count() > 0:
            widget = self.stack.widget(0)
            self.stack.removeWidget(widget)
            widget.deleteLater()
        self.page_map.clear()
        access_denied = self._create_default_widget("Access Denied", "You do not have permission to view this page.")
        self.stack.addWidget(access_denied)
        self.page_map["access_denied"] = 0