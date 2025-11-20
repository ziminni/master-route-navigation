import os
import requests
from typing import Any, Dict, Optional

# Base URL for backend API. Can be overridden with env var FRONTEND_API_BASE
API_BASE = os.environ.get("FRONTEND_API_BASE", "http://127.0.0.1:8000/")


def _build_url(path: str) -> str:
    return API_BASE.rstrip("/") + "/" + path.lstrip("/")


def get(path: str, params: Optional[Dict] = None, timeout: int = 5) -> Any:
    url = _build_url(path)
    resp = requests.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def post(path: str, data: Optional[Dict] = None, json: Optional[Dict] = None, timeout: int = 5) -> Any:
    url = _build_url(path)
    resp = requests.post(url, data=data, json=json, timeout=timeout)
    resp.raise_for_status()
    return resp.json()
