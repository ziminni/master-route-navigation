from typing import Optional, Dict, List
from .json_paths import read_json_file


def get_student_year(student_id: str) -> Optional[str]:
    data = read_json_file("students.json") or {}
    for s in data.get("students", []):
        if s.get("studentId") == student_id:
            return s.get("year")
    return None


def get_student(student_id: str) -> Optional[Dict]:
    data = read_json_file("students.json") or {}
    for s in data.get("students", []):
        if s.get("studentId") == student_id:
            return s
    return None


def list_students() -> List[Dict]:
    data = read_json_file("students.json") or {}
    return data.get("students", [])

