from typing import Dict, List, Optional
from .json_paths import read_json_file, write_json_file


FILENAME = "schedule.json"


def load_schedule(student_id: Optional[str] = None) -> Dict:
    data = read_json_file(FILENAME) or {}
    if not student_id:
        return data
    schedules = data.get("schedules", {})
    return schedules.get(student_id, {"weekly": {}, "today": []})


def search_classes_by_day(day: str, student_id: Optional[str] = None) -> List[Dict]:
    data = load_schedule(student_id)
    weekly = data.get("weekly", {})
    return weekly.get(day, [])


def add_class(student_id: str, day: str, time: str, subject: str, room: str) -> Dict:
    root = read_json_file(FILENAME) or {}
    schedules = root.setdefault("schedules", {})
    sched = schedules.setdefault(student_id, {"weekly": {}, "today": []})
    weekly = sched.setdefault("weekly", {})
    weekly.setdefault(day, []).append({"time": time, "subject": subject, "room": room})
    write_json_file(FILENAME, root)
    return {"time": time, "subject": subject, "room": room}

