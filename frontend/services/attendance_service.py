from typing import Dict, List, Optional
from .json_paths import read_json_file, write_json_file


FILENAME = "attendance.json"


def load_attendance(event_name: Optional[str] = None) -> Dict:
    data = read_json_file(FILENAME) or {"records": []}
    if not event_name:
        return data
    if data.get("event") == event_name:
        return data
    return {"event": event_name, "records": []}


def add_record(record: Dict) -> None:
    data = read_json_file(FILENAME) or {"records": []}
    data.setdefault("records", []).append(record)
    write_json_file(FILENAME, data)


def search_by_student(student_id: str) -> List[Dict]:
    data = read_json_file(FILENAME) or {"records": []}
    return [r for r in data.get("records", []) if r.get("studentId") == student_id]

