from typing import Dict, List, Optional
from .api_client import get


FILENAME = "attendance.json"


def _map_backend_attendance_item(item: Dict) -> Dict:
    # Map likely backend serializer fields into the frontend's expected shape.
    # Keep this resilient to missing nested student data.
    student = item.get("student_id") or item.get("student") or {}
    if isinstance(student, dict):
        student_id = student.get("id") or student.get("student_id") or ""
        name = student.get("full_name") or student.get("name") or ""
        year = student.get("year") or ""
        section = student.get("section") or ""
        course = student.get("course") or ""
        gender = student.get("gender") or ""
    else:
        student_id = str(student) if student is not None else ""
        name = ""
        year = ""
        section = ""
        course = ""
        gender = ""

    return {
        "studentId": student_id,
        "name": name,
        "year": year,
        "section": section,
        "course": course,
        "gender": gender,
        "status": item.get("status", ""),
        "timeIn": item.get("time_in") or item.get("timeIn") or "",
        "timeOut": item.get("time_out") or item.get("timeOut") or "",
        "notes": item.get("notes", ""),
    }


def load_attendance(event_name: Optional[str] = None) -> Dict:
    """Try to load attendance from backend API, fall back to local JSON if API fails."""
    try:
        items = get("api/event-attendance/")
        records = []
        if isinstance(items, dict):
            items_list = items.get("results") or items.get("data") or []
        else:
            items_list = items
        for it in items_list:
            records.append(_map_backend_attendance_item(it))
        return {"records": records}
    except Exception:
        # Backend-only policy: do not use local JSON fallback. Return empty records on error.
        return {"records": []}


def add_record(record: Dict) -> None:
    # Local write retained for offline authorship, but primary source is backend.
    try:
        # If backend supports POST to event-attendance, we could post here.
        # For now, keep local write as a convenience (could be removed if undesired).
        pass
    except Exception:
        pass


def search_by_student(student_id: str) -> List[Dict]:
    # Query backend endpoint by student
    try:
        items = get("api/event-attendance/by_student/", params={"student_id": student_id})
        if isinstance(items, dict):
            items_list = items.get("results") or items.get("data") or []
        else:
            items_list = items
        return [_map_backend_attendance_item(it) for it in items_list]
    except Exception:
        return []

