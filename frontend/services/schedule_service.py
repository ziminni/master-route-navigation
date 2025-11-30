from typing import Dict, List, Optional
from .json_paths import read_json_file, write_json_file
from services.api_client import get, post
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


def _convert_local_to_backend_format(local_data: Dict, student_id: Optional[str] = None) -> Dict:
    """Convert local JSON format to match backend response structure"""
    if not student_id:
        # Return the entire local data structure
        return local_data
    
    # Get specific student schedule from local data
    schedules = local_data.get("schedules", {})
    student_schedule = schedules.get(student_id, {"weekly": {}, "today": []})
    
    # Convert to backend-like structure with semester
    return {
        "semester": "1st Semester",  # Default for local data
        "schedule": _convert_weekly_to_backend_items(student_schedule.get("weekly", {}))
    }


def _convert_weekly_to_backend_items(weekly_schedule: Dict) -> List[Dict]:
    """Convert weekly schedule format to backend-like items"""
    backend_items = []
    
    for day, classes in weekly_schedule.items():
        for class_item in classes:
            backend_item = {
                "course_title": class_item.get("subject", ""),
                "course_code": "",
                "schedule_entry": {
                    "day_of_week": day,
                    "start_time": f"2024-01-01T{class_item.get('time', '00:00')}:00",
                    "additional_context": class_item.get("room", "")
                }
            }
            backend_items.append(backend_item)
    
    return backend_items


def load_schedule(student_id: Optional[str] = None) -> Dict:
    """Try to load schedule from backend; fall back to local JSON file if API fails or returns empty.

    If `student_id` is None, attempt to use the "my-schedule" endpoint.
    """
    try:
        if student_id:
            path = f"api/student-schedules/{student_id}/schedule/"
        else:
            path = "api/student-schedules/my-schedule/"
        resp = get(path)
        
        # Check if backend returned meaningful data
        if resp and isinstance(resp, dict):
            schedule_data = resp.get("schedule", [])
            if schedule_data:  # If we have actual schedule items
                backend_result = _build_frontend_schedule_from_backend(resp)
                return {**backend_result, "source": "backend"}
        
        # If backend returned empty, fall back to local
        print("Backend returned empty schedule, falling back to local JSON")
        return _load_local_schedule(student_id)
        
    except Exception as e:
        # If API call fails, fall back to local JSON
        print(f"API call failed: {e}, falling back to local JSON")
        return _load_local_schedule(student_id)


def _load_local_schedule(student_id: Optional[str] = None) -> Dict:
    """Load schedule from local JSON file (original functionality)"""
    data = read_json_file(FILENAME) or {}
    if not student_id:
        return {**data, "source": "local"}
    
    schedules = data.get("schedules", {})
    student_schedule = schedules.get(student_id, {"weekly": {}, "today": []})
    return {**student_schedule, "source": "local"}


def search_classes_by_day(day: str, student_id: Optional[str] = None) -> List[Dict]:
    """Search classes by day, trying backend first, then falling back to local data"""
    data = load_schedule(student_id)
    
    # Handle both backend and local data structures
    if data.get("source") == "backend":
        # Backend data structure: multiple semesters
        weekly = {}
        for sem_val in data.values():
            if isinstance(sem_val, dict) and "weekly" in sem_val:
                weekly.update(sem_val.get("weekly", {}))
        return weekly.get(day, [])
    else:
        # Local data structure: direct weekly access
        weekly = data.get("weekly", {})
        return weekly.get(day, [])


def add_class(student_id: str, day: str, time: str, subject: str, room: str) -> Dict:
    """
    Try to add class to backend first, fall back to local JSON if API fails.
    Maintains offline capability while preferring backend when available.
    """
    try:
        # Try backend API first
        backend_data = {
            "student": student_id,
            "schedule_entry": {
                "day_of_week": day,
                "start_time": f"2024-01-01T{time}:00",  # Create proper ISO format
                "additional_context": room
            },
            "course_title": subject,
            "course_code": ""  # You might need to extract this from subject
        }
        
        # Attempt backend POST
        response = post("api/student-schedules/", json=backend_data)
        if response:
            print("Class added to backend successfully")
            return {"time": time, "subject": subject, "room": room, "source": "backend"}
        
        # If backend fails, fall back to local
        print("Backend add failed, saving locally")
        return _add_class_local(student_id, day, time, subject, room)
        
    except Exception as e:
        print(f"Backend add failed: {e}, saving locally")
        return _add_class_local(student_id, day, time, subject, room)


def _add_class_local(student_id: str, day: str, time: str, subject: str, room: str) -> Dict:
    """Add class to local JSON file (original functionality)"""
    root = read_json_file(FILENAME) or {}
    schedules = root.setdefault("schedules", {})
    sched = schedules.setdefault(student_id, {"weekly": {}, "today": []})
    weekly = sched.setdefault("weekly", {})
    weekly.setdefault(day, []).append({"time": time, "subject": subject, "room": room})
    write_json_file(FILENAME, root)
    return {"time": time, "subject": subject, "room": room, "source": "local"}


# Optional: Sync function to push local schedule data to backend
def sync_local_schedule_to_backend(student_id: str) -> Dict:
    """
    Sync local schedule records to backend when backend becomes available.
    """
    local_data = read_json_file(FILENAME) or {}
    schedules = local_data.get("schedules", {})
    student_schedule = schedules.get(student_id, {"weekly": {}, "today": []})
    weekly_classes = student_schedule.get("weekly", {})
    
    if not weekly_classes:
        return {"synced": 0, "errors": 0, "message": "No local schedule to sync"}
    
    synced = 0
    errors = 0
    
    for day, classes in weekly_classes.items():
        for class_item in classes:
            try:
                # Check if class already exists in backend
                existing = search_classes_by_day(day, student_id)
                class_exists = any(
                    cls.get("time") == class_item.get("time") and 
                    cls.get("subject") == class_item.get("subject")
                    for cls in existing
                )
                
                if not class_exists:
                    add_class(student_id, day, class_item["time"], class_item["subject"], class_item["room"])
                    synced += 1
            except Exception as e:
                print(f"Failed to sync class {class_item.get('subject')} on {day}: {e}")
                errors += 1
    
    return {
        "synced": synced,
        "errors": errors,
        "total": sum(len(classes) for classes in weekly_classes.values()),
        "message": f"Synced {synced} classes, {errors} errors"
    }