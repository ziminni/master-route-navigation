import os
import requests
from typing import Any, Dict, Optional

# Base URL for backend API. Can be overridden with env var FRONTEND_API_BASE
API_BASE = os.environ.get("FRONTEND_API_BASE", "http://127.0.0.1:8000/")
# Optional token for Authorization header. Use env var or set before calling.
API_TOKEN = os.environ.get("FRONTEND_API_TOKEN")


def _build_url(path: str) -> str:
    return API_BASE.rstrip("/") + "/" + path.lstrip("/")


def _build_headers(extra: Optional[Dict] = None) -> Dict[str, str]:
    headers: Dict[str, str] = {"Accept": "application/json"}
    token = API_TOKEN or os.environ.get("FRONTEND_API_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if extra:
        headers.update(extra)
    return headers


def get(path: str, params: Optional[Dict] = None, timeout: int = 5, headers: Optional[Dict] = None) -> Any:
    url = _build_url(path)
    resp = requests.get(url, params=params, timeout=timeout, headers=_build_headers(headers))
    resp.raise_for_status()
    return resp.json()


def post(path: str, data: Optional[Dict] = None, json: Optional[Dict] = None, timeout: int = 5, headers: Optional[Dict] = None) -> Any:
    url = _build_url(path)
    resp = requests.post(url, data=data, json=json, timeout=timeout, headers=_build_headers(headers))
    resp.raise_for_status()
    # some endpoints return no content
    if resp.text:
        try:
            return resp.json()
        except Exception:
            return resp.text
    return {}
