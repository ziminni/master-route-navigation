from typing import Dict, List, Optional
from .json_paths import read_json_file, write_json_file
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
        # If event_name can be resolved to an event id, client code could call
        # the event-specific endpoint. For a general listing, use the event-attendance endpoint.
        items = get("api/event-attendance/")
        # Expecting list from DRF; map to frontend record shape.
        records = []
        if isinstance(items, dict):
            # Some endpoints may return {"results": [...]} if pagination is used
            items_list = items.get("results") or items.get("data") or []
        else:
            items_list = items
        for it in items_list:
            records.append(_map_backend_attendance_item(it))
        return {"records": records}
    except Exception:
        # fallback to local JSON file for offline or when API isn't available
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

