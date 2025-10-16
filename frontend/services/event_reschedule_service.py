from typing import Dict
from .json_paths import read_json_file, write_json_file


FILENAME = "event_reschedule.json"


def load_reschedule() -> Dict:
    return read_json_file(FILENAME) or {}


def save_reschedule(data: Dict) -> None:
    write_json_file(FILENAME, data)

