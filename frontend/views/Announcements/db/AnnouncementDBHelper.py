# db/AnnouncementDBHelper.py
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Iterable, Optional, Sequence
try:
    from .AnnouncementDBInitialize import (
        db_path,
        ensure_bootstrap,
        ensure_bootstrap_and_seed,
    )
except Exception:
    from AnnouncementDBInitialize import (  # type: ignore
        db_path,
        ensure_bootstrap,
        ensure_bootstrap_and_seed,
    )


# ---- connect ----
def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path()), timeout=10.0)
    con.execute("PRAGMA foreign_keys = ON")
    try:
        con.execute("PRAGMA journal_mode = WAL")
    except Exception:
        # journal_mode not critical; ignore if it fails
        pass
    con.row_factory = sqlite3.Row
    return con


# ---- utils ----
def _as_dict(row: Optional[sqlite3.Row]) -> Optional[dict]:
    return dict(row) if row else None


def _allowed(fields: dict, whitelist: Sequence[str]) -> dict:
    return {k: v for k, v in fields.items() if k in whitelist}


# ---- bootstrap ----
def init_db(seed: bool = True) -> Path:
    """
    Convenience wrapper so the rest of the app can call:
        init_db()  # with seeding
    """
    return ensure_bootstrap_and_seed() if seed else ensure_bootstrap()


# ---- users ----
def add_user(
    username: str,
    email: str | None = None,
    full_name: str | None = None,
) -> int:
    with _conn() as con:
        cur = con.execute(
            "INSERT INTO auth_user(username, email, full_name) VALUES (?, ?, ?)",
            (username, email, full_name),
        )
        return int(cur.lastrowid)


# ---- announcements CRUD ----
_ANN_FIELDS = (
    "title",
    "body",
    "author_id",
    "publish_at",
    "expire_at",
    "location",
    "approval_id",
    "status",
    "visibility",
    "priority",
    "is_pinned",
    "pinned_until",
    "created_by",
    "updated_at",
    "updated_by",
    "deleted_at",
    "note",
)


def add_announcement(**fields) -> int:
    data = _allowed(fields, _ANN_FIELDS)
    if "title" not in data:
        raise ValueError("title is required")
    cols = ",".join(data.keys())
    qs = ",".join("?" for _ in data)
    vals = tuple(data.values())
    with _conn() as con:
        cur = con.execute(f"INSERT INTO announcements({cols}) VALUES ({qs})", vals)
        return int(cur.lastrowid)


def update_announcement(announcement_id: int, **fields) -> int:
    data = _allowed(fields, _ANN_FIELDS)
    if not data:
        return 0
    sets = ",".join(f"{k}=?" for k in data.keys())
    vals = tuple(data.values()) + (announcement_id,)
    with _conn() as con:
        cur = con.execute(
            f"UPDATE announcements SET {sets} WHERE announcement_id=?", vals
        )
        return int(cur.rowcount)


def delete_announcement(announcement_id: int) -> int:
    with _conn() as con:
        cur = con.execute(
            "DELETE FROM announcements WHERE announcement_id=?",
            (announcement_id,),
        )
        return int(cur.rowcount)

def get_user_id_by_username(username: str) -> Optional[int]:
    """
    Resolve auth_user.user_id for a given username.
    Returns None if not found or username is empty.
    """
    if not username:
        return None
    with _conn() as con:
        row = con.execute(
            "SELECT user_id FROM auth_user WHERE username=?",
            (username,),
        ).fetchone()
        return int(row["user_id"]) if row else None



def get_announcement(
    announcement_id: int,
    include_tags: bool = True,
) -> Optional[dict]:
    with _conn() as con:
        row = con.execute(
            "SELECT * FROM announcements WHERE announcement_id=?",
            (announcement_id,),
        ).fetchone()
        d = _as_dict(row)
        if not d or not include_tags:
            return d
        tags = con.execute(
            """
            SELECT t.tag_name
            FROM announcement_tag_map m
            JOIN tags t ON t.tag_id = m.tag_id
            WHERE m.announcement_id=?
            """,
            (announcement_id,),
        ).fetchall()
        d["tags"] = [r["tag_name"] for r in tags]
        return d


def list_announcements(
    status: Optional[str] = None,
    visibility: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    audience_scopes: Sequence[str] | None = None,
) -> list[dict]:
    """
    Core listing query used by all announcement pages.

    Returns each row with:
      - a.* (all announcement columns)
      - author_name    (from auth_user)
      - tags_csv       (comma-separated tag names)
      - file_path      (sample attachment path, if any)
      - doc_count      (number of visible attachments)
    """
    sql = """
        SELECT
            a.*,
            COALESCE(u.full_name, u.username, 'Unknown') AS author_name,
            IFNULL(GROUP_CONCAT(DISTINCT t.tag_name), '') AS tags_csv,
            MIN(d.file_path) AS file_path,
            COUNT(d.document_id) AS doc_count
        FROM announcements a
        LEFT JOIN auth_user u
            ON u.user_id = a.author_id
        LEFT JOIN announcement_tag_map m
            ON m.announcement_id = a.announcement_id
        LEFT JOIN tags t
            ON t.tag_id = m.tag_id
        LEFT JOIN documents d
            ON d.announcement_id = a.announcement_id
           AND d.visible = 1
    """

    where: list[str] = []
    args: list[object] = []

    if status:
        where.append("a.status = ?")
        args.append(status)

    if audience_scopes:
        scope_conds: list[str] = []
        for scope in audience_scopes:
            scope = scope.strip()
            if not scope:
                continue
            scope_conds.append("a.visibility LIKE ?")
            args.append(f"%{scope}%")
        if scope_conds:
            where.append("(" + " OR ".join(scope_conds) + ")")
    elif visibility:
        where.append("a.visibility = ?")
        args.append(visibility)

    if search:
        where.append("(a.title LIKE ? OR a.body LIKE ?)")
        like = f"%{search}%"
        args.extend([like, like])

    if where:
        sql += " WHERE " + " AND ".join(where)

    sql += """
        GROUP BY a.announcement_id
        ORDER BY COALESCE(a.publish_at, a.created_at) DESC
        LIMIT ?
    """
    args.append(limit)

    with _conn() as con:
        return [dict(r) for r in con.execute(sql, args).fetchall()]



# ---- tags ----
def get_or_create_tag(
    tag_name: str,
    con: sqlite3.Connection | None = None,
) -> int:
    tag_name = tag_name.strip()
    if not tag_name:
        raise ValueError("empty tag name")

    owns_con = con is None
    if owns_con:
        con = _conn()

    try:
        row = con.execute(
            "SELECT tag_id FROM tags WHERE tag_name=?",
            (tag_name,),
        ).fetchone()
        if row:
            return int(row["tag_id"])

        cur = con.execute(
            "INSERT INTO tags(tag_name) VALUES (?)",
            (tag_name,),
        )
        return int(cur.lastrowid)
    finally:
        if owns_con and con is not None:
            con.close()


def set_tags(announcement_id: int, tag_names: Iterable[str]) -> None:
    clean = [t.strip() for t in tag_names if t and t.strip()]
    if not clean:
        return

    with _conn() as con:
        con.execute(
            "DELETE FROM announcement_tag_map WHERE announcement_id=?",
            (announcement_id,),
        )
        for name in clean:
            tid = get_or_create_tag(name, con)
            con.execute(
                """
                INSERT INTO announcement_tag_map(announcement_id, tag_id)
                VALUES (?, ?)
                """,
                (announcement_id, tid),
            )
        con.commit()


# ---- documents ----
_DOC_FIELDS = (
    "file_name",
    "file_path",
    "mime_type",
    "file_size_bytes",
    "checksum",
    "uploaded_by",
    "uploaded_at",
    "visible",
    "expires_at",
    "version",
    "description",
)


def add_document(announcement_id: int, **fields) -> int:
    data = _allowed(fields, _DOC_FIELDS)
    if "file_name" not in data or "file_path" not in data:
        raise ValueError("file_name and file_path are required")
    cols = "announcement_id," + ",".join(data.keys())
    qs = "?," + ",".join("?" for _ in data)
    vals = (announcement_id,) + tuple(data.values())
    with _conn() as con:
        cur = con.execute(f"INSERT INTO documents({cols}) VALUES ({qs})", vals)
        return int(cur.lastrowid)


def list_documents(announcement_id: int) -> list[dict]:
    with _conn() as con:
        return [
            dict(r)
            for r in con.execute(
                """
                SELECT *
                FROM documents
                WHERE announcement_id=? AND visible=1
                ORDER BY uploaded_at DESC
                """,
                (announcement_id,),
            ).fetchall()
        ]


# ---- reads ----
def mark_read(
    announcement_id: int,
    user_id: int,
    has_read: int = 1,
    device_info: str | None = None,
) -> None:
    with _conn() as con:
        row = con.execute(
            """
            SELECT read_id
            FROM announcement_reads
            WHERE announcement_id=? AND user_id=?
            """,
            (announcement_id, user_id),
        ).fetchone()
        if row:
            con.execute(
                """
                UPDATE announcement_reads
                SET has_read=?, read_time=CURRENT_TIMESTAMP, device_info=?
                WHERE read_id=?
                """,
                (has_read, device_info, row["read_id"]),
            )
        else:
            con.execute(
                """
                INSERT INTO announcement_reads(
                    announcement_id, user_id, has_read, read_time, device_info
                )
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
                """,
                (announcement_id, user_id, has_read, device_info),
            )


# ---- legacy alias ----

def get_announcements(
    limit: int = 50,
    q: str | None = None,
    status: str | None = None,
    visibility: str | None = None,
    audience_scopes: Sequence[str] | None = None,
) -> list[dict]:
    """
    Public helper used by UI pages.

    q              -> search term (title/body)
    status         -> simple status filter
    visibility     -> exact visibility match (if audience_scopes is not used)
    audience_scopes-> list of scopes to match inside visibility (LIKE '%scope%')
    """
    return list_announcements(
        status=status,
        visibility=visibility,
        search=q,
        limit=limit,
        audience_scopes=audience_scopes,
    )   

def list_pending_announcements(include_drafts: bool = True) -> list[dict]:
    """
    List announcements for the approval queue.

    Returns each row with:
      - id              (announcement_id)
      - title, body, status, created_at, publish_at, expire_at
      - visibility, location, priority, is_pinned
      - author_name     (from auth_user)
      - file_path       (sample attachment path)
      - images_count    (number of visible attachments)
    """
    sql = """
        SELECT
            a.announcement_id AS id,
            a.title,
            a.body,
            a.status,
            a.created_at,
            a.publish_at,
            a.expire_at,
            a.visibility,
            a.location,
            a.priority,
            a.is_pinned,
            COALESCE(u.full_name, u.username, 'Unknown') AS author_name,
            MIN(d.file_path) AS file_path,
            COUNT(d.document_id) AS images_count
        FROM announcements a
        LEFT JOIN auth_user u
            ON u.user_id = a.author_id
        LEFT JOIN documents d
            ON d.announcement_id = a.announcement_id
           AND d.visible = 1
        WHERE a.deleted_at IS NULL
    """
    if include_drafts:
        sql += " AND (a.status = 'pending' OR a.status = 'draft')"
    else:
        sql += " AND a.status = 'pending'"

    sql += """
        GROUP BY a.announcement_id
        ORDER BY a.created_at DESC
    """

    with _conn() as con:
        return [dict(r) for r in con.execute(sql).fetchall()]


def apply_announcement_action(pk: int, action: str) -> None:
    """
    Apply moderation action for a single announcement.

    action:
      - 'approve' -> status = 'published', set publish_at if needed
      - anything else -> status = 'declined'
    """
    with _conn() as con:
        if action == "approve":
            con.execute(
                """
                UPDATE announcements
                SET status = 'published',
                    publish_at = COALESCE(publish_at, CURRENT_TIMESTAMP),
                    updated_at = CURRENT_TIMESTAMP
                WHERE announcement_id = ?
                """,
                (pk,),
            )
        else:
            con.execute(
                """
                UPDATE announcements
                SET status = 'declined',
                    updated_at = CURRENT_TIMESTAMP
                WHERE announcement_id = ?
                """,
                (pk,),
            )

def delete_document(document_id: int) -> int:
    """
    Permanently delete a single document row.
    Returns number of rows affected (0 or 1).
    """
    with _conn() as con:
        cur = con.execute(
            "DELETE FROM documents WHERE document_id = ?",
            (document_id,),
        )
        return int(cur.rowcount)


def add_audience_scope(
    announcement_id: int,
    scope_type: str,
    scope_target_id: int | None = None,
) -> int:
    """
    Insert a row into announcement_audience.

    scope_type: e.g. 'general', 'students', 'faculty', 'organization'
    scope_target_id: optional FK to a specific group/section (currently we pass NULL)
    """
    with _conn() as con:
        cur = con.execute(
            """
            INSERT INTO announcement_audience(announcement_id, scope_type, scope_target_id)
            VALUES (?, ?, ?)
            """,
            (announcement_id, scope_type, scope_target_id),
        )
        return int(cur.lastrowid)
