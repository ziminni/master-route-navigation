from typing import Dict, List, Optional
from .json_paths import read_json_file, write_json_file


FILENAME = "curriculum.json"


def load_curriculum(year_name: Optional[str] = None) -> Dict:
    data = read_json_file(FILENAME) or {}
    if not year_name:
        return data
    for yr in data.get("years", []):
        if yr.get("year") == year_name:
            return yr
    return {"year": year_name, "semesters": []}


def find_subject(code: str) -> Dict | None:
    data = read_json_file(FILENAME) or {}
    for yr in data.get("years", []):
        for sem in yr.get("semesters", []):
            for subj in sem.get("subjects", []):
                if subj.get("code") == code:
                    return subj
    return None


def add_subject(year_name: str, semester_name: str, subject: Dict) -> None:
    data = read_json_file(FILENAME) or {"years": []}
    years: List[Dict] = data.setdefault("years", [])
    for yr in years:
        if yr.get("year") == year_name:
            semesters: List[Dict] = yr.setdefault("semesters", [])
            for sem in semesters:
                if sem.get("name") == semester_name:
                    sem.setdefault("subjects", []).append(subject)
                    write_json_file(FILENAME, data)
                    return
            semesters.append({"name": semester_name, "subjects": [subject]})
            write_json_file(FILENAME, data)
            return
    years.append({"year": year_name, "semesters": [{"name": semester_name, "subjects": [subject]}]})
    write_json_file(FILENAME, data)

