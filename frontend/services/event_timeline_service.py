from typing import Dict, List, Optional
from services.api_client import get, post
import os
import json

FILENAME = "event_timeline.json"


def _load_local_timeline() -> Dict:
    """
    Loads the global event timeline from event_timeline.json (original functionality).
    Returns a dict with a 'timeline' key containing a list of events.
    """
    frontend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    json_path = os.path.join(frontend_root, "utils", FILENAME)
    if not os.path.exists(json_path):
        return {"timeline": []}
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "timeline" in data:
            return {**data, "source": "local"}
        elif isinstance(data, list):
            return {"timeline": data, "source": "local"}
        else:
            return {"timeline": [], "source": "local"}
    except Exception:
        return {"timeline": [], "source": "local"}


def _map_backend_to_timeline_format(events_data: List[Dict]) -> List[Dict]:
    """Convert backend events format to frontend timeline format"""
    timeline = []
    
    for ev in events_data:
        # Get schedule blocks from various possible field names
        blocks = ev.get("schedule_blocks") or ev.get("timeline") or ev.get("schedules") or []
        
        # If no schedule blocks, create at least one entry from the main event
        if not blocks:
            entry = {
                "day": ev.get("date") or ev.get("start_date") or "",
                "time": ev.get("time") or ev.get("start_time") or "",
                "activity": ev.get("title") or ev.get("name") or "",
                "eventName": ev.get("title") or ev.get("name") or "",
                "description": ev.get("description") or "",
                "location": ev.get("location") or "",
            }
            timeline.append(entry)
        else:
            # Process each schedule block
            for b in blocks:
                entry = {
                    "day": b.get("day") or b.get("date") or ev.get("date") or "",
                    "time": b.get("time") or b.get("start_time") or ev.get("time") or "",
                    "activity": b.get("activity") or b.get("name") or ev.get("title") or "",
                    "eventName": ev.get("title") or ev.get("name") or "",
                    "description": b.get("description") or ev.get("description") or "",
                    "location": b.get("location") or ev.get("location") or "",
                }
                timeline.append(entry)
    
    return timeline


def load_timeline(event_name: Optional[str] = None) -> Dict:
    """Load timeline from backend events endpoint, fall back to local JSON if API fails or returns empty.

    Returns {'timeline': [...], 'source': 'backend'|'local'}.
    """
    try:
        # Try backend API first
        data = get("api/organizations/events/")
        
        # Handle different response formats
        if isinstance(data, dict):
            items = data.get("results", [])
            if not items and isinstance(data.get("data"), list):
                items = data.get("data", [])
        else:
            items = data or []
        
        # If backend returns events, process them
        if items:
            timeline = _map_backend_to_timeline_format(items)
            
            # Filter by event name if specified
            if event_name:
                filtered = [it for it in timeline if it.get("eventName") == event_name]
                return {"eventName": event_name, "timeline": filtered, "source": "backend"}
            
            return {"timeline": timeline, "source": "backend"}
        
        # If backend returns empty, fall back to local JSON
        print("Backend returned empty events, falling back to local JSON timeline")
        return _load_timeline_with_event_filter(event_name)
        
    except Exception as e:
        # If API call fails, fall back to local JSON
        print(f"API call failed: {e}, falling back to local JSON timeline")
        return _load_timeline_with_event_filter(event_name)


def _load_timeline_with_event_filter(event_name: Optional[str] = None) -> Dict:
    """Load local timeline and apply event name filter if needed"""
    local_data = _load_local_timeline()
    timeline = local_data.get("timeline", [])
    
    if event_name:
        filtered = [it for it in timeline if it.get("eventName") == event_name]
        return {"eventName": event_name, "timeline": filtered, "source": "local"}
    
    return local_data


def add_timeline_item(day: str, time: str, activity: str, event_name: Optional[str] = None) -> Dict:
    """
    Try to add timeline item to backend first, fall back to local JSON if API fails.
    """
    try:
        # Try backend API first - you might need to create an event or schedule block
        backend_data = {
            "title": activity,
            "date": day,
            "start_time": time,
            "name": event_name or activity,
        }
        
        # Attempt backend POST to create a new event
        response = post("api/organizations/events/", json=backend_data)
        if response:
            print("Timeline item added to backend successfully")
            item = {"day": day, "time": time, "activity": activity, "source": "backend"}
            if event_name:
                item["eventName"] = event_name
            return item
        
        # If backend fails, fall back to local
        print("Backend add failed, saving locally")
        return _add_timeline_item_local(day, time, activity, event_name)
        
    except Exception as e:
        print(f"Backend add failed: {e}, saving locally")
        return _add_timeline_item_local(day, time, activity, event_name)


def _add_timeline_item_local(day: str, time: str, activity: str, event_name: Optional[str] = None) -> Dict:
    """Add timeline item to local JSON file"""
    local_data = _load_local_timeline()
    timeline = local_data.get("timeline", [])
    
    item = {"day": day, "time": time, "activity": activity}
    if event_name:
        item["eventName"] = event_name
    
    timeline.append(item)
    local_data["timeline"] = timeline
    
    # Save back to local file
    frontend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    json_path = os.path.join(frontend_root, "utils", FILENAME)
    
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(local_data, f, indent=2)
    except Exception as e:
        print(f"Error saving to local timeline file: {e}")
    
    return {**item, "source": "local"}


def update_timeline_item(day: str, time: str, new_activity: str, event_name: Optional[str] = None) -> bool:
    """
    Try to update timeline item in backend first, fall back to local JSON if API fails.
    """
    try:
        # This would require knowing the specific event ID to update
        # For now, we'll implement local update and note that backend update needs event ID
        print("Backend update not implemented yet, updating locally")
        return _update_timeline_item_local(day, time, new_activity, event_name)
        
    except Exception as e:
        print(f"Backend update failed: {e}, updating locally")
        return _update_timeline_item_local(day, time, new_activity, event_name)


def _update_timeline_item_local(day: str, time: str, new_activity: str, event_name: Optional[str] = None) -> bool:
    """Update timeline item in local JSON file"""
    local_data = _load_local_timeline()
    timeline = local_data.get("timeline", [])
    
    updated = False
    for item in timeline:
        if (item.get("day") == day and item.get("time") == time and 
            (not event_name or item.get("eventName") == event_name)):
            item["activity"] = new_activity
            updated = True
            break
    
    if updated:
        local_data["timeline"] = timeline
        # Save back to local file
        frontend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        json_path = os.path.join(frontend_root, "utils", FILENAME)
        
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(local_data, f, indent=2)
        except Exception as e:
            print(f"Error saving updated timeline to local file: {e}")
    
    return updated


def delete_timeline_item(day: str, time: str, event_name: Optional[str] = None) -> bool:
    """
    Try to delete timeline item from backend first, fall back to local JSON if API fails.
    """
    try:
        # This would require knowing the specific event ID to delete
        # For now, we'll implement local delete and note that backend delete needs event ID
        print("Backend delete not implemented yet, deleting locally")
        return _delete_timeline_item_local(day, time, event_name)
        
    except Exception as e:
        print(f"Backend delete failed: {e}, deleting locally")
        return _delete_timeline_item_local(day, time, event_name)


def _delete_timeline_item_local(day: str, time: str, event_name: Optional[str] = None) -> bool:
    """Delete timeline item from local JSON file"""
    local_data = _load_local_timeline()
    timeline = local_data.get("timeline", [])
    
    original_length = len(timeline)
    timeline = [item for item in timeline 
                if not (item.get("day") == day and 
                       item.get("time") == time and 
                       (not event_name or item.get("eventName") == event_name))]
    
    deleted = len(timeline) < original_length
    
    if deleted:
        local_data["timeline"] = timeline
        # Save back to local file
        frontend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        json_path = os.path.join(frontend_root, "utils", FILENAME)
        
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(local_data, f, indent=2)
        except Exception as e:
            print(f"Error saving updated timeline to local file: {e}")
    
    return deleted


def items_for_day(day: str) -> List[Dict]:
    """Get all timeline items for a specific day"""
    res = load_timeline()
    return [i for i in res.get("timeline", []) if i.get("day") == day]


# Optional: Sync function to push local timeline data to backend
def sync_local_timeline_to_backend() -> Dict:
    """
    Sync local timeline records to backend when backend becomes available.
    """
    local_data = _load_local_timeline()
    timeline = local_data.get("timeline", [])
    
    if not timeline:
        return {"synced": 0, "errors": 0, "message": "No local timeline to sync"}
    
    synced = 0
    errors = 0
    
    for item in timeline:
        try:
            # Check if item already exists in backend
            existing = items_for_day(item.get("day", ""))
            item_exists = any(
                existing_item.get("time") == item.get("time") and 
                existing_item.get("activity") == item.get("activity")
                for existing_item in existing
            )
            
            if not item_exists:
                add_timeline_item(
                    item.get("day", ""),
                    item.get("time", ""),
                    item.get("activity", ""),
                    item.get("eventName")
                )
                synced += 1
        except Exception as e:
            print(f"Failed to sync timeline item {item.get('activity')}: {e}")
            errors += 1
    
    return {
        "synced": synced,
        "errors": errors,
        "total": len(timeline),
        "message": f"Synced {synced} timeline items, {errors} errors"
    }