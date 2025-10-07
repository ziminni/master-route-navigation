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

