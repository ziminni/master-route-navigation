from typing import Dict, List
from .json_paths import read_json_file


def load_buildings() -> List[Dict]:
    data = read_json_file("buildings.json") or {}
    return data.get("buildings", [])


def load_rooms(building_id: str | None = None) -> List[Dict]:
    data = read_json_file("rooms.json") or {}
    rooms = data.get("rooms", [])
    if building_id:
        return [r for r in rooms if r.get("buildingId") == building_id]
    return rooms


def load_organizers() -> List[Dict]:
    data = read_json_file("organizers.json") or {}
    return data.get("organizers", [])

