import json
import os
import sys

class NavigationDataHelper:
    def __init__(self, json_file="frontend/utils/navbar.json"):
        # Try default path, then fallback to project root or relative paths
        self.json_file = json_file
        self._data = None
        self._load_data()

    def _load_data(self):
        absolute_path = os.path.abspath(self.json_file)
        print(f"NavigationDataHelper: Current working directory: {os.getcwd()}")
        print(f"NavigationDataHelper: Attempting to load JSON from {absolute_path}, exists: {os.path.exists(absolute_path)}")

        # Try alternative paths if the default fails
        if not os.path.exists(absolute_path):
            alternative_paths = [
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "navbar.json"),
                os.path.join(os.getcwd(), "navbar.json"),
                os.path.join(os.getcwd(), "frontend", "navbar.json")
            ]
            for alt_path in alternative_paths:
                print(f"NavigationDataHelper: Trying alternative path: {alt_path}, exists: {os.path.exists(alt_path)}")
                if os.path.exists(alt_path):
                    self.json_file = alt_path
                    absolute_path = alt_path
                    break

        if not os.path.exists(absolute_path):
            print(f"NavigationDataHelper: ERROR: File {absolute_path} does not exist. Check file path and working directory.")

        try:
            with open(self.json_file, "r") as f:
                data = json.load(f)
            print(f"NavigationDataHelper: Loaded navbar.json: {data}")
            if not isinstance(data, dict) or "parents" not in data:
                raise ValueError("Invalid JSON structure: 'parents' key missing")

            # Validate access, function, and path fields
            for parent in data["parents"]:
                for main in parent["mains"]:
                    if "access" not in main:
                        raise ValueError(f"Missing 'access' field in main item {main['id']}")
                    if not (isinstance(main["access"], str) or isinstance(main["access"], list)):
                        raise ValueError(f"Invalid 'access' field in main item {main['id']}")
                    if "function" not in main or not isinstance(main["function"], str) or not main["function"].endswith("()"):
                        raise ValueError(f"Invalid 'function' field in main item {main['id']}: must be a string ending with '()'")
                    if "path" not in main or not isinstance(main["path"], str):
                        raise ValueError(f"Missing or invalid 'path' field in main item {main['id']}")

                    # Validate modulars if present
                    for modular in main.get("modulars", []):
                        if "function" not in modular or not isinstance(modular["function"], str) or not modular["function"].endswith("()"):
                            raise ValueError(f"Invalid 'function' field in modular item {modular['id']}: must be a string ending with '()'")
                        if "path" not in modular or not isinstance(modular["path"], str):
                            raise ValueError(f"Missing or invalid 'path' field in modular item {modular['id']}")

            self._data = data
            print(f"✓ Navigation data loaded from {absolute_path}, parents found: {len(data['parents'])}")
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            print(f"❌ Error loading JSON: {e}")
            self._data = {"parents": []}  # Fallback to empty structure
            print("Using fallback empty navigation data")

    def reload_data(self):
        self._load_data()

    @property
    def data(self):
        return self._data

    def get_path_for_main(self, main_id):
        for parent in self.data["parents"]:
            for main in parent["mains"]:
                if main["id"] == main_id:
                    return main.get("path", "")
        print(f"NavigationDataHelper: No path found for main ID {main_id}")
        return ""

    def get_path_for_modular(self, modular_id):
        for parent in self.data["parents"]:
            for main in parent["mains"]:
                for modular in main["modulars"]:
                    if modular["id"] == modular_id:
                        return modular.get("path", "")
        print(f"NavigationDataHelper: No path found for modular ID {modular_id}")
        return ""

    def get_all_parents(self):
        parents = [(p["id"], p["name"]) for p in self.data["parents"]]
        print(f"NavigationDataHelper: Returning {len(parents)} parents: {parents}")
        return parents

    def get_parent_by_id(self, parent_id):
        for p in self.data["parents"]:
            if p["id"] == parent_id:
                return (p["id"], p["name"])
        return None

    def get_main_by_parent(self, parent_id):
        for p in self.data["parents"]:
            if p["id"] == parent_id:
                return [(m["id"], m["name"], m["function"], m["access"], parent_id)
                        for m in p["mains"]]
        return []

    def get_main_by_id(self, main_id):
        for p in self.data["parents"]:
            for m in p["mains"]:
                if m["id"] == main_id:
                    return (m["id"], m["name"], m["function"], m["access"], p["id"])
        return None

    def get_modular_by_main(self, main_id):
        for p in self.data["parents"]:
            for m in p["mains"]:
                if m["id"] == main_id:
                    return [(mod["id"], mod["name"], mod.get("function", ""), mod.get("access", m["access"]))
                            for mod in m["modulars"]]
        return []

    def get_modular_by_id(self, modular_id):
        for p in self.data["parents"]:
            for m in p["mains"]:
                for mod in m["modulars"]:
                    if mod["id"] == modular_id:
                        return (mod["id"], mod["name"], mod["function"], m["id"])
        return None

    def get_page_function(self, table, page_id):
        if table == "parent":
            parent = self.get_parent_by_id(page_id)
            return parent[1] if parent else None
        elif table == "main":
            main = self.get_main_by_id(page_id)
            return main[2] if main else None
        elif table == "modular":
            modular = self.get_modular_by_id(page_id)
            return modular[2] if modular else None
        return None

    def get_access_level(self, main_id):
        main = self.get_main_by_id(main_id)
        return main[3] if main else None

    def search_page(self, page_name):
        results = []
        search_term = page_name.lower()
        for p in self.data["parents"]:
            if search_term in p["name"].lower():
                results.append({"table": "parent", "id": p["id"], "name": p["name"]})
            for m in p["mains"]:
                if search_term in m["name"].lower():
                    results.append({"table": "main", "id": m["id"], "name": m["name"]})
                for mod in m["modulars"]:
                    if search_term in mod["name"].lower():
                        results.append({"table": "modular", "id": mod["id"], "name": mod["name"]})
        return results

    def get_full_navigation_tree(self):
        return self.data

    def get_navigation_summary(self):
        parent_count = len(self.data["parents"])
        main_count = sum(len(p["mains"]) for p in self.data["parents"])
        modular_count = sum(
            len(m["modulars"])
            for p in self.data["parents"]
            for m in p["mains"]
        )
        return {
            "parents": parent_count,
            "mains": main_count,
            "modulars": modular_count,
            "total": parent_count + main_count + modular_count
        }

# Global instance and convenience functions
_nav_helper = NavigationDataHelper()

def load_data():
    return _nav_helper.data

def reload_navigation_data():
    _nav_helper.reload_data()

def get_all_parents():
    return _nav_helper.get_all_parents()

def get_parent_by_id(parent_id):
    return _nav_helper.get_parent_by_id(parent_id)

def get_main_by_parent(parent_id):
    return _nav_helper.get_main_by_parent(parent_id)

def get_main_by_id(main_id):
    return _nav_helper.get_main_by_id(main_id)

def get_modular_by_main(main_id):
    return _nav_helper.get_modular_by_main(main_id)

def get_modular_by_id(modular_id):
    return _nav_helper.get_modular_by_id(modular_id)

def get_page_function(table, page_id):
    return _nav_helper.get_page_function(table, page_id)

def get_access_level(main_id):
    return _nav_helper.get_access_level(main_id)

def search_page(page_name):
    return _nav_helper.search_page(page_name)

def get_path_for_main(main_id):
    return _nav_helper.get_path_for_main(main_id)

def get_path_for_modular(modular_id):
    return _nav_helper.get_path_for_modular(modular_id)