from typing import Dict, List, Optional
from .json_paths import read_json_file, write_json_file


FILENAME = "event_timeline.json"


def load_timeline(event_name: Optional[str] = None) -> Dict:
    data = read_json_file(FILENAME) or {}
    if event_name:
        events = data.get("events", {})
        return {"eventName": event_name, "timeline": events.get(event_name, [])}
    return data if data else {"timeline": []}


def add_timeline_item(day: str, time: str, activity: str, event_name: Optional[str] = None) -> Dict:
    data = read_json_file(FILENAME) or {}
    item = {"day": day, "time": time, "activity": activity}
    if event_name:
        events = data.setdefault("events", {})
        lst = events.setdefault(event_name, [])
        lst.append(item)
    else:
        data.setdefault("timeline", []).append(item)
    write_json_file(FILENAME, data)
    return item


def update_timeline_item(day: str, time: str, new_activity: str, event_name: Optional[str] = None) -> bool:
    data = read_json_file(FILENAME) or {}
    if event_name:
        events = data.get("events", {})
        lst = events.get(event_name, [])
    else:
        lst = data.get("timeline", [])
    updated = False
    for it in lst:
        if it.get("day") == day and it.get("time") == time:
            it["activity"] = new_activity
            updated = True
            break
    if updated:
        write_json_file(FILENAME, data)
    return updated


def delete_timeline_item(day: str, time: str, event_name: Optional[str] = None) -> bool:
    data = read_json_file(FILENAME) or {}
    if event_name:
        events = data.get("events", {})
        lst = events.get(event_name, [])
        new_lst = [it for it in lst if not (it.get("day") == day and it.get("time") == time)]
        if len(new_lst) != len(lst):
            events[event_name] = new_lst
            write_json_file(FILENAME, data)
            return True
        return False
    else:
        lst = data.get("timeline", [])
        new_lst = [it for it in lst if not (it.get("day") == day and it.get("time") == time)]
        if len(new_lst) != len(lst):
            data["timeline"] = new_lst
            write_json_file(FILENAME, data)
            return True
        return False


def items_for_day(day: str) -> List[Dict]:
    data = read_json_file(FILENAME) or {"timeline": []}
    return [i for i in data.get("timeline", []) if i.get("day") == day]

