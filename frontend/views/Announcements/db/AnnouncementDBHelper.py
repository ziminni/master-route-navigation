# db/AnnouncementDBHelper.py
from __future__ import annotations
import os, sqlite3
from pathlib import Path
from typing import Iterable, Optional, Sequence

try:
    from .AnnouncementDBInitialize import (
        db_path,
        ensure_bootstrap,
        ensure_bootstrap_and_seed,
        get_announcements,
        get_reminders,
    )
except Exception:
    from AnnouncementDBInitialize import (
        db_path,
        ensure_bootstrap,
        ensure_bootstrap_and_seed,
        get_announcements,
        get_reminders,
    )

try:
    from .AnnouncementAdminApproval import AnnouncementAdminApprovalPage
except Exception:
    from AnnouncementAdminApproval import AnnouncementAdminApprovalPage 

# ---- connect ----
def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path()))
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sqlite3.Row
    return con

# ---- utils ----
def _as_dict(row: Optional[sqlite3.Row]) -> Optional[dict]:
    return dict(row) if row else None

def _allowed(fields: dict, whitelist: Sequence[str]) -> dict:
    return {k: v for k, v in fields.items() if k in whitelist}

# ---- bootstrap ----
def init_db(seed: bool = True) -> Path:
    """Create tables and optionally seed 6 announcements + 6 reminders."""
    return ensure_bootstrap_and_seed() if seed else ensure_bootstrap()

# ---- users ----
def add_user(username: str, email: str | None = None, full_name: str | None = None) -> int:
    with _conn() as con:
        cur = con.execute(
            "INSERT INTO auth_user(username, email, full_name) VALUES (?, ?, ?)",
            (username, email, full_name),
        )
        return cur.lastrowid

# ---- announcements CRUD ----
_ANN_FIELDS = (
    "title","body","author_id","publish_at","expire_at","location","approval_id",
    "status","visibility","priority","is_pinned","pinned_until",
    "created_by","updated_at","updated_by","deleted_at","note"
)

def add_announcement(**fields) -> int:
    """Usage: add_announcement(title='...', body='...', author_id=1, status='draft', ...)."""
    data = _allowed(fields, _ANN_FIELDS)
    if "title" not in data:
        raise ValueError("title is required")
    cols = ",".join(data.keys())
    qs   = ",".join("?" for _ in data)
    vals = tuple(data.values())
    with _conn() as con:
        cur = con.execute(f"INSERT INTO announcements({cols}) VALUES ({qs})", vals)
        return cur.lastrowid

def update_announcement(announcement_id: int, **fields) -> int:
    data = _allowed(fields, _ANN_FIELDS)
    if not data:
        return 0
    sets = ",".join(f"{k}=?" for k in data.keys())
    vals = tuple(data.values()) + (announcement_id,)
    with _conn() as con:
        cur = con.execute(f"UPDATE announcements SET {sets} WHERE announcement_id=?", vals)
        return cur.rowcount

def delete_announcement(announcement_id: int) -> int:
    with _conn() as con:
        cur = con.execute("DELETE FROM announcements WHERE announcement_id=?", (announcement_id,))
        return cur.rowcount

def get_announcement(announcement_id: int, include_tags: bool = True) -> Optional[dict]:
    with _conn() as con:
        row = con.execute("SELECT * FROM announcements WHERE announcement_id=?", (announcement_id,)).fetchone()
        d = _as_dict(row)
        if not d or not include_tags:
            return d
        tags = con.execute("""
            SELECT t.tag_name
            FROM announcement_tag_map m
            JOIN tags t ON t.tag_id = m.tag_id
            WHERE m.announcement_id=?
        """, (announcement_id,)).fetchall()
        d["tags"] = [r["tag_name"] for r in tags]
        return d

def list_announcements(
    status: Optional[str] = None,
    visibility: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    sql = """
        SELECT a.*,
               IFNULL(GROUP_CONCAT(DISTINCT t.tag_name), '') AS tags_csv
        FROM announcements a
        LEFT JOIN announcement_tag_map m ON m.announcement_id = a.announcement_id
        LEFT JOIN tags t ON t.tag_id = m.tag_id
    """
    where, args = [], []
    if status:     where.append("a.status=?");     args.append(status)
    if visibility: where.append("a.visibility=?"); args.append(visibility)
    if search:
        where.append("(a.title LIKE ? OR a.body LIKE ?)")
        args.extend([f"%{search}%", f"%{search}%"])
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " GROUP BY a.announcement_id ORDER BY COALESCE(a.publish_at, a.created_at) DESC LIMIT ?"
    args.append(limit)
    with _conn() as con:
        return [dict(r) for r in con.execute(sql, args).fetchall()]

# ---- tags ----
def get_or_create_tag(tag_name: str) -> int:
    with _conn() as con:
        row = con.execute("SELECT tag_id FROM tags WHERE tag_name=?", (tag_name,)).fetchone()
        if row:
            return row["tag_id"]
        cur = con.execute("INSERT INTO tags(tag_name) VALUES (?)", (tag_name,))
        return cur.lastrowid

def set_tags(announcement_id: int, tag_names: Iterable[str]) -> None:
    tag_names = [t.strip() for t in tag_names if t and t.strip()]
    with _conn() as con:
        con.execute("DELETE FROM announcement_tag_map WHERE announcement_id=?", (announcement_id,))
        for name in tag_names:
            tid = get_or_create_tag(name)
            con.execute(
                "INSERT INTO announcement_tag_map(announcement_id, tag_id) VALUES (?, ?)",
                (announcement_id, tid),
            )

# ---- documents ----
_DOC_FIELDS = (
    "file_name","file_path","mime_type","file_size_bytes","checksum",
    "uploaded_by","uploaded_at","visible","expires_at","version","description"
)

def add_document(announcement_id: int, **fields) -> int:
    data = _allowed(fields, _DOC_FIELDS)
    if "file_name" not in data or "file_path" not in data:
        raise ValueError("file_name and file_path are required")
    cols = "announcement_id," + ",".join(data.keys())
    qs   = "?," + ",".join("?" for _ in data)
    vals = (announcement_id,) + tuple(data.values())
    with _conn() as con:
        cur = con.execute(f"INSERT INTO documents({cols}) VALUES ({qs})", vals)
        return cur.lastrowid

def list_documents(announcement_id: int) -> list[dict]:
    with _conn() as con:
        return [dict(r) for r in con.execute(
            "SELECT * FROM documents WHERE announcement_id=? ORDER BY uploaded_at DESC",
            (announcement_id,)
        ).fetchall()]

# ---- reads ----
def mark_read(announcement_id: int, user_id: int, has_read: int = 1, device_info: str | None = None) -> None:
    with _conn() as con:
        row = con.execute(
            "SELECT read_id FROM announcement_reads WHERE announcement_id=? AND user_id=?",
            (announcement_id, user_id)
        ).fetchone()
        if row:
            con.execute(
                "UPDATE announcement_reads SET has_read=?, read_time=CURRENT_TIMESTAMP, device_info=? WHERE read_id=?",
                (has_read, device_info, row["read_id"])
            )
        else:
            con.execute(
                "INSERT INTO announcement_reads(announcement_id, user_id, has_read, read_time, device_info) "
                "VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)",
                (announcement_id, user_id, has_read, device_info)
            )

# ---- convenience seeds ----
def seed_minimal() -> None:
    """Create one user and one draft announcement if DB is empty."""
    with _conn() as con:
        ucount = con.execute("SELECT COUNT(*) AS c FROM auth_user").fetchone()["c"]
        if ucount == 0:
            add_user("admin", "admin@example.com", "Admin")
        acount = con.execute("SELECT COUNT(*) AS c FROM announcements").fetchone()["c"]
        if acount == 0:
            aid = add_announcement(title="Welcome", body="First announcement", author_id=1, status="draft")
            set_tags(aid, ["general"])
