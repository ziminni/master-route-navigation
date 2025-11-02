import os
import json

def load_event_timeline():
    """
    Loads the global event timeline from event_timeline.json.
    Returns a dict with a 'timeline' key containing a list of events.
    """
    frontend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) )
    json_path = os.path.join(frontend_root, "utils", "event_timeline.json")
    if not os.path.exists(json_path):
        return {"timeline": []}
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "timeline" in data:
            return data
        elif isinstance(data, list):
            return {"timeline": data}
        else:
            return {"timeline": []}
    except Exception:
        return {"timeline": []}
