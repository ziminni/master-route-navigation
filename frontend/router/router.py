from PyQt6.QtWidgets import QStackedWidget, QLabel, QVBoxLayout, QWidget
from PyQt6.QtGui import QFont
from utils.db_helper import NavigationDataHelper, get_path_for_main, get_path_for_modular
from importlib import import_module
import os
import sys

class Router:
    def __init__(self, user_role, user_session=None):
        # Ensure sys.path includes project root
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        if project_root not in sys.path:
            sys.path.append(project_root)
        print(f"Router: Added {project_root} to sys.path")
        print(f"Router: sys.path: {sys.path}")

        self.stack = QStackedWidget()
        self.nav_helper = NavigationDataHelper(json_file="navbar.json")
        self.user_role = user_role
        self.user_session = user_session or {}  # Store session data
        self.page_map = {}
        self._page_classes = self._build_page_classes()
        self._preload_pages()

    def _build_page_classes(self):
        """Parse navbar.json 'function' and use path helper methods to build {id_or_key: ClassObject} map."""
        page_classes = {}

        # Handle parent
        for parent in self.nav_helper.data["parents"]:
            parent_name = parent["name"]
            parent_id = parent["id"]
            print(f"Router: Processing parent '{parent_name}' (ID: {parent_id})")

            # Handle mains
            for main in parent["mains"]:
                main_id = main["id"]
                function_str = main["function"]
                class_name = function_str.replace("()", "")
                module_path = get_path_for_main(main_id)
                print(f"Router: Path for main ID {main_id} ({class_name}): {module_path}")

                try:
                    if module_path:
                        file_path = module_path.replace(".", "/") + ".py"
                        abs_file_path = os.path.abspath(file_path)
                        print(f"Router: Attempting to import {module_path}, file: {abs_file_path}, exists: {os.path.exists(abs_file_path)}")
                        module = import_module(module_path)
                        page_class = getattr(module, class_name)
                        page_classes[f"main_{main_id}"] = page_class
                        print(f"Router: Successfully imported {class_name} for main ID {main_id}")
                    else:
                        print(f"Router: No path found for main ID {main_id}, skipping {class_name}")
                except (ImportError, AttributeError) as e:
                    print(f"Router: Failed to import {class_name} from {module_path}: {e}")

                # Handle modulars
                if "modulars" in main:  # Check for modulars key
                    for modular in main["modulars"]:
                        mod_id = modular["id"]
                        function_str = modular.get("function", "")
                        module_path = get_path_for_modular(mod_id)
                        print(f"Router: Path for modular ID {mod_id}: {module_path}")
                        if function_str and module_path:
                            class_name = function_str.replace("()", "")
                            try:
                                file_path = module_path.replace(".", "/") + ".py"
                                abs_file_path = os.path.abspath(file_path)
                                print(f"Router: Attempting to import {module_path} for modular, file: {abs_file_path}, exists: {os.path.exists(abs_file_path)}")
                                module = import_module(module_path)
                                page_class = getattr(module, class_name)
                                page_classes[f"mod_{main_id}_{mod_id}"] = page_class
                                print(f"Router: Successfully imported {class_name} for modular ID {mod_id}")
                            except (ImportError, AttributeError) as e:
                                print(f"Router: Failed to import modular {class_name} from {module_path}: {e}")
                else:
                    print(f"Router: No 'modulars' key found for main ID {main_id}, skipping modulars")

        return page_classes

    def _preload_pages(self):
        # Default "Access Denied" page
        access_denied_widget = self._create_default_widget("Access Denied", "You do not have permission to view this page.")
        self.stack.addWidget(access_denied_widget)
        self.page_map["access_denied"] = 0

        # Valid roles for access
        valid_roles = {"admin", "staff", "faculty", "student"}

        # Load pages from navbar.json
        for parent in self.nav_helper.data["parents"]:
            for main in parent["mains"]:
                main_id = main["id"]
                access = main["access"]
                name = main["name"]
                key = f"main_{main_id}"
                if (isinstance(access, str) and access == self.user_role and self.user_role in valid_roles) or \
                (isinstance(access, list) and self.user_role in access and self.user_role in valid_roles):
                    print(f"Router: Loading page {key} with access {access} for user_role {self.user_role}")
                    page_class = self._page_classes.get(key)
                    if page_class:
                        # Pass user session data to dashboard initialization
                        page = page_class(
                            username=self.user_session.get("username", ""),
                            roles=self.user_session.get("roles", []),
                            primary_role=self.user_session.get("primary_role", ""),
                            token=self.user_session.get("token", "")
                        )
                    else:
                        page = self._create_default_widget(name, f"Page for {name}")
                    index = self.stack.addWidget(page)
                    self.page_map[key] = index
                    print(f"Router: Added {key} to page_map at index {index}")

                # Load modulars
                if "modulars" in main:
                    for modular in main["modulars"]:
                        mod_id = modular["id"]
                        mod_name = modular["name"]
                        mod_key = f"mod_{main_id}_{mod_id}"
                        if (isinstance(access, str) and access == self.user_role and self.user_role in valid_roles) or \
                        (isinstance(access, list) and self.user_role in access and self.user_role in valid_roles):
                            print(f"Router: Loading modular {mod_key} with access {access} for user_role {self.user_role}")
                            page_class = self._page_classes.get(mod_key)
                            if page_class:
                                # Pass user session data to modulars
                                page = page_class(
                                    username=self.user_session.get("username", ""),
                                    roles=self.user_session.get("roles", []),
                                    primary_role=self.user_session.get("primary_role", ""),
                                    token=self.user_session.get("token", "")
                                )
                            else:
                                page = self._create_default_widget(mod_name, f"Sub-page for {mod_name}")
                            index = self.stack.addWidget(page)
                            self.page_map[mod_key] = index
                            print(f"Router: Added {mod_key} to page_map at index {index}")

    def navigate(self, page_id, is_modular=False, parent_main_id=None):
        key = f"mod_{parent_main_id}_{page_id}" if is_modular else f"main_{page_id}"
        index = self.page_map.get(key)
        print(f"Router: Navigating to {key}, index: {index}, page_map: {self.page_map}")
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