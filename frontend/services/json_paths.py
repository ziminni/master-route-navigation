import json
import os
from typing import Any


def get_project_root() -> str:
    return os.path.dirname(os.path.dirname(__file__))


def get_json_path(filename: str) -> str:
    project_root = get_project_root()
    # Use existing data directory under frontend/utils
    json_dir = os.path.join(project_root, "utils")
    os.makedirs(json_dir, exist_ok=True)
    return os.path.join(json_dir, filename)


def read_json_file(filename: str) -> Any:
    path = get_json_path(filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json_file(filename: str, data: Any) -> None:
    path = get_json_path(filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

