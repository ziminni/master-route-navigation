from typing import Dict, List, Optional
from services.api_client import get, post
from .json_paths import read_json_file, write_json_file  # Keep your old JSON utilities


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


def _map_local_to_backend_format(record: Dict) -> Dict:
    """Convert local JSON format to match the backend response structure"""
    return {
        "student": {
            "id": record.get("studentId", ""),
            "name": record.get("name", ""),
            "full_name": record.get("name", ""),
            "year": record.get("year", ""),
            "section": record.get("section", ""),
            "course": record.get("course", ""),
            "gender": record.get("gender", "")
        },
        "status": record.get("status", ""),
        "time_in": record.get("timeIn", ""),
        "time_out": record.get("timeOut", ""),
        "notes": record.get("notes", ""),
        "id": record.get("id", "")  # Local records might not have ID
    }


def load_attendance(event_name: Optional[str] = None) -> Dict:
    """Try to load attendance from backend API, fall back to local JSON if API fails or returns empty."""
    try:
        # Try backend API first
        items = get("api/organizations/event-attendance/")
        records = []
        
        if isinstance(items, dict):
            items_list = items.get("results") or items.get("data") or []
        else:
            items_list = items
            
        for it in items_list:
            records.append(_map_backend_attendance_item(it))
        
        # If backend returns data, use it
        if records:
            return {"records": records, "source": "backend"}
        
        # If backend returns empty, fall back to local JSON
        print("Backend returned empty results, falling back to local JSON data")
        return _load_local_attendance(event_name)
        
    except Exception as e:
        # If API call fails, fall back to local JSON
        print(f"API call failed: {e}, falling back to local JSON data")
        return _load_local_attendance(event_name)


def _load_local_attendance(event_name: Optional[str] = None) -> Dict:
    """Load attendance from local JSON file (original functionality)"""
    data = read_json_file(FILENAME) or {"records": []}
    
    if not event_name:
        return {**data, "source": "local"}
    
    if data.get("event") == event_name:
        return {**data, "source": "local"}
    
    return {"event": event_name, "records": [], "source": "local"}


def add_record(record: Dict) -> None:
    """
    Try to add record to backend, fall back to local JSON if API fails.
    This maintains offline capability while preferring backend when available.
    """
    try:
        # Try backend API first
        backend_data = {
            "student": record.get("studentId"),
            "event": record.get("eventId"),  # You might need to provide event ID
            "status": record.get("status", "present"),
            "time_in": record.get("timeIn"),
            "time_out": record.get("timeOut"),
            "notes": record.get("notes", "")
        }
        
        # Remove None values
        backend_data = {k: v for k, v in backend_data.items() if v is not None}
        
        # Only attempt backend POST if we have required fields
        if backend_data.get("student") and backend_data.get("event"):
            response = post("api/organizations/event-attendance/", json=backend_data)
            if response:
                print("Record added to backend successfully")
                return
        
        # If backend fails or missing required fields, fall back to local
        print("Backend add failed or missing required fields, saving locally")
        _add_record_local(record)
        
    except Exception as e:
        print(f"Backend add failed: {e}, saving locally")
        _add_record_local(record)


def _add_record_local(record: Dict) -> None:
    """Add record to local JSON file (original functionality)"""
    data = read_json_file(FILENAME) or {"records": []}
    data.setdefault("records", []).append(record)
    write_json_file(FILENAME, data)
    print("Record saved to local JSON file")


def search_by_student(student_id: str) -> List[Dict]:
    """
    Try backend search first, fall back to local JSON search if API fails.
    """
    try:
        # Try backend API with filter parameter
        items = get("api/organizations/event-attendance/", params={"student": student_id})
        
        if isinstance(items, dict):
            items_list = items.get("results") or items.get("data") or []
        else:
            items_list = items
            
        if items_list:
            return [_map_backend_attendance_item(it) for it in items_list]
        
        # If backend returns empty, try local search
        print("Backend search returned empty, trying local JSON")
        return _search_by_student_local(student_id)
        
    except Exception as e:
        print(f"Backend search failed: {e}, trying local JSON")
        return _search_by_student_local(student_id)


def _search_by_student_local(student_id: str) -> List[Dict]:
    """Search by student in local JSON file (original functionality)"""
    data = read_json_file(FILENAME) or {"records": []}
    return [r for r in data.get("records", []) if r.get("studentId") == student_id]


# Optional: Sync function to push local data to backend when connection is available
def sync_local_to_backend() -> Dict:
    """
    Sync local JSON records to backend when backend becomes available.
    This is useful for migrating data or handling offline scenarios.
    """
    local_data = read_json_file(FILENAME) or {"records": []}
    local_records = local_data.get("records", [])
    
    if not local_records:
        return {"synced": 0, "errors": 0, "message": "No local records to sync"}
    
    synced = 0
    errors = 0
    
    for record in local_records:
        try:
            # Check if record already exists in backend (you might need a way to identify duplicates)
            existing = search_by_student(record.get("studentId", ""))
            if not existing:  # Only add if doesn't exist
                add_record(record)
                synced += 1
        except Exception as e:
            print(f"Failed to sync record {record.get('studentId')}: {e}")
            errors += 1
    
    return {
        "synced": synced,
        "errors": errors,
        "total": len(local_records),
        "message": f"Synced {synced} records, {errors} errors"
    }