
from typing import Dict, List, Optional
from services.json_paths import read_json_file, write_json_file
from services.api_client import get, post

FILENAME = "event_timeline.json"


def load_timeline(event_name: Optional[str] = None) -> Dict:
    """Try to load timeline from backend; fallback to local JSON."""
    try:
        # There's no dedicated timeline endpoint in backend; attempt to use events list
        data = get("api/events/")
        # data may be list or paginated dict
        items = data.get("results") if isinstance(data, dict) else data
        timeline = []
        for ev in items:
            # extract schedule blocks or custom timeline fields if present
            blocks = ev.get("schedule_blocks") or ev.get("timeline") or []
            for b in blocks:
                entry = {
                    "day": b.get("day") or b.get("date") or "",
                    "time": b.get("time") or b.get("start_time") or "",
                    "activity": b.get("activity") or ev.get("title") or "",
                    "eventName": ev.get("title") or ev.get("name") or "",
                }
                timeline.append(entry)
        if event_name:
            filtered = [it for it in timeline if it.get("eventName") == event_name]
            return {"eventName": event_name, "timeline": filtered}
        return {"timeline": timeline}
    except Exception:
        data = read_json_file(FILENAME) or {}
        timeline = data.get("timeline", [])
        if event_name:
            filtered = [it for it in timeline if it.get("eventName") == event_name]
            return {"eventName": event_name, "timeline": filtered}
        return {"timeline": timeline}


def add_timeline_item(day: str, time: str, activity: str, event_name: Optional[str] = None) -> Dict:
    data = read_json_file(FILENAME) or {}
    item = {"day": day, "time": time, "activity": activity}
    if event_name:
        item["eventName"] = event_name
    data.setdefault("timeline", []).append(item)
    write_json_file(FILENAME, data)
    return item


def update_timeline_item(day: str, time: str, new_activity: str, event_name: Optional[str] = None) -> bool:
    data = read_json_file(FILENAME) or {}
    timeline = data.get("timeline", [])
    updated = False
    for it in timeline:
        if it.get("day") == day and it.get("time") == time and (event_name is None or it.get("eventName") == event_name):
            it["activity"] = new_activity
            updated = True
            break
    if updated:
        write_json_file(FILENAME, data)
    return updated


def delete_timeline_item(day: str, time: str, event_name: Optional[str] = None) -> bool:
    data = read_json_file(FILENAME) or {}
    timeline = data.get("timeline", [])
    new_timeline = [it for it in timeline if not (it.get("day") == day and it.get("time") == time and (event_name is None or it.get("eventName") == event_name))]
    if len(new_timeline) != len(timeline):
        data["timeline"] = new_timeline
        write_json_file(FILENAME, data)
        return True
    return False


def items_for_day(day: str) -> List[Dict]:
    data = read_json_file(FILENAME) or {"timeline": []}
    return [i for i in data.get("timeline", []) if i.get("day") == day]

