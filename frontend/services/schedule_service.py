from typing import Dict, List, Optional
from .json_paths import read_json_file, write_json_file
from .api_client import get
from datetime import datetime


FILENAME = "schedule.json"


def _parse_iso_time_to_hhmm(iso_ts: Optional[str]) -> str:
    if not iso_ts:
        return ""
    try:
        # some backend values may include timezone; use fromisoformat if available
        dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        return dt.strftime("%H:%M")
    except Exception:
        # fallback — try to extract HH:MM
        try:
            return iso_ts.split("T")[1][:5]
        except Exception:
            return iso_ts


def _normalize_semester_name(raw: str) -> str:
    if not raw:
        return "1st Semester"
    r = raw.lower()
    if "1" in r or "first" in r or "1st" in r:
        return "1st Semester"
    if "2" in r or "second" in r or "2nd" in r:
        return "2nd Semester"
    # fallback to raw capitalized
    return raw


def _build_frontend_schedule_from_backend(resp: Dict) -> Dict:
    """Convert backend student schedule response into the frontend's expected structure.

    Frontend expects a mapping of semester -> { "weekly": { DayName: [ {time, subject, room}, ... ] }, "today": [...] }
    """
    # initialize two semesters for safety
    out: Dict = {
        "1st Semester": {"weekly": {}, "today": []},
        "2nd Semester": {"weekly": {}, "today": []},
    }

    semester_raw = resp.get("semester") if isinstance(resp, dict) else None
    semester_key = _normalize_semester_name(semester_raw)

    items = resp.get("schedule") if isinstance(resp, dict) else []
    for it in items:
        course_title = it.get("course_title") or it.get("course_code") or ""
        course_code = it.get("course_code") or ""
        subj = f"{course_code} {course_title}".strip()
        room = it.get("schedule_entry", {}).get("additional_context") or ""
        entry = it.get("schedule_entry") or {}
        day = entry.get("day_of_week") or entry.get("day_of_week_code") or entry.get("day") or ""
        # Try to normalize day (backend may return codes)
        if isinstance(day, str) and len(day) == 3:
            # common code like 'mon' -> 'Monday'
            mapping = {"mon": "Monday", "tue": "Tuesday", "wed": "Wednesday", "thu": "Thursday", "fri": "Friday", "sat": "Saturday", "sun": "Sunday"}
            day = mapping.get(day.lower(), day)
        time_str = _parse_iso_time_to_hhmm(entry.get("start_time") or entry.get("time") or "")
        frontend_item = {"time": time_str, "subject": subj, "room": room}
        if day:
            out.setdefault(semester_key, {"weekly": {}, "today": []}).setdefault("weekly", {}).setdefault(day, []).append(frontend_item)

    return out


def load_schedule(student_id: Optional[str] = None) -> Dict:
    """Try to load schedule from backend; fall back to local JSON file.

    If `student_id` is None, attempt to use the "my-schedule" endpoint.
    """
        try:
            if student_id:
                path = f"api/student-schedules/{student_id}/schedule/"
            else:
                path = "api/student-schedules/my-schedule/"
            resp = get(path)
            return _build_frontend_schedule_from_backend(resp)
        except Exception:
            # Backend-only policy: return empty schedule (no JSON file usage)
            return {}


def search_classes_by_day(day: str, student_id: Optional[str] = None) -> List[Dict]:
    data = load_schedule(student_id)
    # try current-semester selection — since frontend chooses semester by text we'll just merge weeks
    weekly = {}
    if isinstance(data, dict):
        for sem_val in data.values():
            if isinstance(sem_val, dict):
                weekly.update(sem_val.get("weekly", {}))
    return weekly.get(day, [])


def add_class(student_id: str, day: str, time: str, subject: str, room: str) -> Dict:
    root = read_json_file(FILENAME) or {}
    schedules = root.setdefault("schedules", {})
    sched = schedules.setdefault(student_id, {"weekly": {}, "today": []})
    weekly = sched.setdefault("weekly", {})
    weekly.setdefault(day, []).append({"time": time, "subject": subject, "room": room})
    write_json_file(FILENAME, root)
    return {"time": time, "subject": subject, "room": room}

