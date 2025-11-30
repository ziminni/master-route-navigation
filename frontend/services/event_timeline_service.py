
from typing import Dict, List, Optional
from services.api_client import get

FILENAME = "event_timeline.json"


def load_timeline(event_name: Optional[str] = None) -> Dict:
    """Load timeline from backend events endpoint. Returns {'timeline': [...]}.

    Backend-only: on error returns empty timeline.
    """
    try:
        data = get("api/events/")
        items = data.get("results") if isinstance(data, dict) else data
        timeline = []
        for ev in items:
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
        # Backend-only policy: return empty timeline on error
        return {"timeline": []}


def add_timeline_item(day: str, time: str, activity: str, event_name: Optional[str] = None) -> Dict:
    # Local add unsupported in backend-only mode; return created object locally
    item = {"day": day, "time": time, "activity": activity}
    if event_name:
        item["eventName"] = event_name
    return item


def update_timeline_item(day: str, time: str, new_activity: str, event_name: Optional[str] = None) -> bool:
    # No-op for backend-only placeholder (requires API implementation)
    return False


def delete_timeline_item(day: str, time: str, event_name: Optional[str] = None) -> bool:
    # No-op for backend-only placeholder
    return False


def items_for_day(day: str) -> List[Dict]:
    res = load_timeline()
    return [i for i in res.get("timeline", []) if i.get("day") == day]

