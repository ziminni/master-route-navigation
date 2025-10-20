from typing import Dict, List, Optional
from .json_paths import read_json_file, write_json_file


FILENAME = "event_proposal.json"


def load_proposal() -> Dict:
    return read_json_file(FILENAME) or {}


def save_proposal(proposal: Dict) -> None:
    """Backward-compatible single save (overwrites)."""
    write_json_file(FILENAME, proposal)


def add_proposal(proposal: Dict) -> None:
    """Append proposal to a list keyed by 'proposals'. Ensures unique by eventName."""
    data = read_json_file(FILENAME) or {}
    proposals: List[Dict] = data.setdefault("proposals", [])
    name = (proposal.get("eventName") or "").strip()
    if name:
        proposals = [p for p in proposals if (p.get("eventName") or "").strip().lower() != name.lower()]
        proposals.append(proposal)
        data["proposals"] = proposals
    write_json_file(FILENAME, data)


def list_proposals() -> List[Dict]:
    data = read_json_file(FILENAME) or {}
    return data.get("proposals", [])


def get_proposal_by_name(name: str) -> Optional[Dict]:
    for p in list_proposals():
        if (p.get("eventName") or "").strip().lower() == (name or "").strip().lower():
            return p
    # Fallback to single stored structure
    data = read_json_file(FILENAME) or {}
    if (data.get("eventName") or "").strip().lower() == (name or "").strip().lower():
        return data
    return None


def search_proposal_by_name(name: str) -> Dict | None:
    return get_proposal_by_name(name)


def delete_proposal_by_name(name: str) -> bool:
    """Delete proposals matching `name` (case-insensitive).

    Returns True if one or more proposals were removed, False otherwise.
    Works with both the legacy single-proposal file format and the newer
    {'proposals': [...]} format.
    """
    if not name:
        return False
    data = read_json_file(FILENAME) or {}
    # If proposals list exists, filter it
    proposals = data.get("proposals")
    removed = False
    if isinstance(proposals, list):
        filtered = [p for p in proposals if (p.get("eventName") or "").strip().lower() != name.strip().lower()]
        if len(filtered) != len(proposals):
            data["proposals"] = filtered
            removed = True
    else:
        # Check legacy single-proposal saved as top-level object
        top_name = (data.get("eventName") or "").strip().lower()
        if top_name == name.strip().lower():
            # clear file
            data = {}
            removed = True

    if removed:
        write_json_file(FILENAME, data)
    return removed

