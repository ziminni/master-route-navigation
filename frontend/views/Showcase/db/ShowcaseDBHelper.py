# views/Showcase/db/ShowcaseDBHelper.py
from __future__ import annotations
import os, sqlite3
from datetime import datetime
from typing import Any, Iterable, Mapping, Sequence

# source of truth for DB location + bootstrap
# ShowcaseDBInitialize should ONLY contain:
#   - db_path()
#   - SCHEMA_DDL / seed-data
#   - ensure_bootstrap()
from .ShowcaseDBInitialize import db_path, ensure_bootstrap  # noqa: F401


# ---------- connection ----------
def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path()))
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sqlite3.Row
    return con


def _rows(cur: sqlite3.Cursor) -> list[dict[str, Any]]:
    return [dict(r) for r in cur.fetchall()]


def _now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------- util: relative time like “2h ago” ----------
def _rel_time(ts: str | None) -> str:
    if not ts:
        return ""
    # parse as naive local time
    try:
        dt = datetime.strptime(ts[:19], "%Y-%m-%d %H:%M:%S")
    except Exception:
        try:
            dt = datetime.fromisoformat(ts.split(".")[0].replace("Z", ""))
        except Exception:
            return ""
    now = datetime.now()  # local naive
    s = int((now - dt).total_seconds())
    if s < 0:
        s = 0  # guard against future/zone mismatches

    if s < 60:
        return f"{s}s ago"
    m = s // 60
    if m < 60:
        return f"{m}m ago"
    h = m // 60
    if h < 24:
        return f"{h}h ago"
    d = h // 24
    if d < 30:
        return f"{d}d ago"
    mo = d // 30
    if mo < 12:
        return f"{mo}mo ago"
    y = mo // 12
    return f"{y}y ago"


def _blurb(text: str | None, limit: int = 160) -> str:
    t = (text or "").strip().replace("\n", " ")
    return t if len(t) <= limit else t[: limit - 1].rstrip() + "…"


def _basename(p: str | None) -> str | None:
    if not p:
        return None
    return os.path.basename(p)


# ---------- low-level generic helpers (use these instead of inline SQL) ----------
def fetch_all(sql: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]:
    """Run a SELECT and return list[dict]."""
    with _conn() as con:
        cur = con.execute(sql, params)
        return _rows(cur)


def fetch_one(sql: str, params: Sequence[Any] = ()) -> dict[str, Any] | None:
    """Run a SELECT ... LIMIT 1 and return a single dict or None."""
    with _conn() as con:
        cur = con.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None


def exec_sql(sql: str, params: Sequence[Any] = ()) -> None:
    """Run INSERT/UPDATE/DELETE with no return value."""
    with _conn() as con:
        con.execute(sql, params)


def insert_row(table: str, data: Mapping[str, Any]) -> int:
    """
    Generic INSERT helper.

    Example:
        insert_row("competitions", {
            "name": "...",
            "description": "...",
            "created_at": _now_ts(),
        })
    """
    if not data:
        raise ValueError("insert_row() requires at least one column")
    cols = list(data.keys())
    vals = [data[c] for c in cols]
    placeholders = ",".join(["?"] * len(cols))
    sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
    with _conn() as con:
        cur = con.execute(sql, vals)
        return int(cur.lastrowid)


def update_row(
    table: str,
    pk_col: str,
    pk_value: Any,
    data: Mapping[str, Any],
) -> None:
    """
    Generic UPDATE helper.

    Example:
        update_row(
            "competitions",
            "competition_id",
            5,
            {"status": "published", "updated_at": _now_ts()},
        )
    """
    if not data:
        return
    sets = [f"{k} = ?" for k in data.keys()]
    params: list[Any] = list(data.values())
    params.append(pk_value)
    sql = f"UPDATE {table} SET {', '.join(sets)} WHERE {pk_col} = ?"
    with _conn() as con:
        con.execute(sql, params)


def delete_row(table: str, pk_col: str, pk_value: Any) -> None:
    """
    Generic DELETE helper.

    Example:
        delete_row("competitions", "competition_id", 5)
    """
    sql = f"DELETE FROM {table} WHERE {pk_col} = ?"
    with _conn() as con:
        con.execute(sql, (pk_value,))


# ---------- media helpers ----------
def list_project_media(project_id: int) -> list[dict[str, Any]]:
    with _conn() as con:
        cur = con.execute(
            """
            SELECT m.*, pmm.sort_order, pmm.is_primary
            FROM project_media_map pmm
            JOIN media m ON m.media_id = pmm.media_id
            WHERE pmm.project_id = ?
            ORDER BY pmm.is_primary DESC, COALESCE(pmm.sort_order, 9999), m.media_id
            """,
            (project_id,),
        )
        return _rows(cur)


def list_competition_media(competition_id: int) -> list[dict[str, Any]]:
    with _conn() as con:
        cur = con.execute(
            """
            SELECT m.*, cmm.sort_order, cmm.is_primary
            FROM competition_media_map cmm
            JOIN media m ON m.media_id = cmm.media_id
            WHERE cmm.competition_id = ?
            ORDER BY cmm.is_primary DESC, COALESCE(cmm.sort_order, 9999), m.media_id
            """,
            (competition_id,),
        )
        return _rows(cur)


def project_primary_image_path(project_id: int) -> str | None:
    with _conn() as con:
        row = con.execute(
            """SELECT m.path_or_url
               FROM project_media_map pmm
               JOIN media m ON m.media_id = pmm.media_id
               WHERE pmm.project_id = ? AND pmm.is_primary = 1
               ORDER BY COALESCE(pmm.sort_order, 9999), m.media_id LIMIT 1""",
            (project_id,),
        ).fetchone()
        return None if not row else row["path_or_url"]


def attach_media_to_project(
    project_id: int,
    media_id: int,
    is_primary: bool = False,
    sort_order: int | None = None,
) -> None:
    exec_sql(
        """
        INSERT OR IGNORE INTO project_media_map (project_id, media_id, sort_order, is_primary)
        VALUES (?, ?, ?, ?)
        """,
        (project_id, media_id, sort_order, int(bool(is_primary))),
    )


def attach_media_to_competition(
    competition_id: int,
    media_id: int,
    is_primary: bool = False,
    sort_order: int | None = None,
) -> None:
    exec_sql(
        """
        INSERT OR IGNORE INTO competition_media_map (competition_id, media_id, sort_order, is_primary)
        VALUES (?, ?, ?, ?)
        """,
        (competition_id, media_id, sort_order, int(bool(is_primary))),
    )


def remove_project_media_link(project_id: int, media_id: int) -> None:
    exec_sql(
        "DELETE FROM project_media_map WHERE project_id = ? AND media_id = ?",
        (project_id, media_id),
    )


def remove_competition_media_link(competition_id: int, media_id: int) -> None:
    exec_sql(
        "DELETE FROM competition_media_map WHERE competition_id = ? AND media_id = ?",
        (competition_id, media_id),
    )


def delete_media(media_id: int) -> None:
    # remove any mappings first, then media
    with _conn() as con:
        con.execute("DELETE FROM project_media_map WHERE media_id = ?", (media_id,))
        con.execute(
            "DELETE FROM competition_media_map WHERE media_id = ?", (media_id,)
        )
        con.execute("DELETE FROM media WHERE media_id = ?", (media_id,))


# ---------- showcase card feeds for UI ----------
def list_showcase_cards(
    kind: str = "project",
    q: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """
    Returns items ready for Showcase cards.

    Each dict contains:
      - id, title, blurb, long_text
      - image (basename for your IMG_DIR loader)
      - images (list of basenames)
      - posted_ago (derived from publish_at or created_at)
      - status, author_display, category, context, images_count
      - tags (list of tag names), external_url (for projects and competitions)
    """
    assert kind in ("project", "competition")

    if kind == "project":
        sql = ["SELECT * FROM projects"]
        args: list[Any] = []
        where: list[str] = []
        if q:
            like = f"%{q}%"
            where.append("(title LIKE ? OR description LIKE ? OR author_display LIKE ?)")
            args += [like, like, like]
        if status:
            where.append("status = ?")
            args.append(status)
        if where:
            sql.append("WHERE " + " AND ".join(where))
        sql.append(
            "ORDER BY COALESCE(publish_at, created_at) DESC, projects_id DESC LIMIT ? OFFSET ?"
        )
        args += [limit, offset]

        with _conn() as con:
            rows = _rows(con.execute(" ".join(sql), args))

        cards: list[dict[str, Any]] = []
        for r in rows:
            media = list_project_media(r["projects_id"])
            image_paths = [m["path_or_url"] for m in media]
            primary = image_paths[0] if image_paths else None
            posted_src = r.get("publish_at") or r.get("created_at")

            # tags for quick preview
            try:
                tag_rows = list_project_tags(r["projects_id"])
                tag_names = [t["name"] for t in tag_rows]
            except Exception:
                tag_names = []

            cards.append(
                {
                    "id": r["projects_id"],
                    "title": r.get("title") or "",
                    "blurb": _blurb(r.get("description")),
                    "long_text": (r.get("description") or "").strip(),
                    "image": _basename(primary),
                    "images": [_basename(p) for p in image_paths],
                    "posted_ago": _rel_time(posted_src),
                    "status": r.get("status"),
                    "author_display": r.get("author_display"),
                    "category": r.get("category"),
                    "context": r.get("context"),
                    "images_count": len(image_paths),
                    "tags": tag_names,
                    "external_url": r.get("external_url"),
                }
            )
        return cards

    # competition
    sql = ["SELECT * FROM competitions"]
    args: list[Any] = []
    where: list[str] = []
    if q:
        like = f"%{q}%"
        where.append("(name LIKE ? OR organizer LIKE ? OR description LIKE ?)")
        args += [like, like, like]
    if status:
        where.append("status = ?")
        args.append(status)
    if where:
        sql.append("WHERE " + " AND ".join(where))
    sql.append(
        "ORDER BY COALESCE(publish_at, created_at) DESC, competition_id DESC LIMIT ? OFFSET ?"
    )
    args += [limit, offset]

    with _conn() as con:
        rows = _rows(con.execute(" ".join(sql), args))

    cards: list[dict[str, Any]] = []
    for r in rows:
        media = list_competition_media(r["competition_id"])
        image_paths = [m["path_or_url"] for m in media]
        primary = image_paths[0] if image_paths else None
        posted_src = r.get("publish_at") or r.get("created_at")
        cards.append(
            {
                "id": r["competition_id"],
                "title": r.get("name") or "",
                "blurb": _blurb(r.get("description")),
                "long_text": (r.get("description") or "").strip(),
                "image": _basename(primary),
                "images": [_basename(p) for p in image_paths],
                "posted_ago": _rel_time(posted_src),
                "status": r.get("status"),
                "author_display": None,  # competitions do not have this column
                "category": r.get("event_type"),
                "context": None,
                "images_count": len(image_paths),
                "tags": [],  # no tags for competitions yet
                "external_url": r.get("external_url"),
            }
        )
    return cards


# ---------- richer project helpers ----------
def list_projects(
    status: str | None = None,
    is_public: int | None = None,
    category: str | None = None,
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
    order_by: str = "created_at DESC",
) -> list[dict[str, Any]]:
    sql = ["SELECT * FROM projects"]
    where: list[str] = []
    args: list[Any] = []
    if status:
        where.append("status = ?")
        args.append(status)
    if is_public is not None:
        where.append("is_public = ?")
        args.append(int(bool(is_public)))
    if category:
        where.append("category = ?")
        args.append(category)
    if q:
        like = f"%{q}%"
        where.append("(title LIKE ? OR description LIKE ? OR author_display LIKE ?)")
        args += [like, like, like]
    if where:
        sql.append("WHERE " + " AND ".join(where))
    sql.append(f"ORDER BY {order_by} LIMIT ? OFFSET ?")
    args += [int(limit), int(offset)]
    with _conn() as con:
        return _rows(con.execute(" ".join(sql), args))


def get_project(project_id: int) -> dict[str, Any] | None:
    with _conn() as con:
        r = con.execute(
            "SELECT * FROM projects WHERE projects_id = ?", (project_id,)
        ).fetchone()
        if not r:
            return None
        proj = dict(r)
        proj["media"] = list_project_media(project_id)
        proj["tags"] = _rows(
            con.execute(
                "SELECT pt.tag_id, pt.name FROM project_tag_map pm "
                "JOIN project_tags pt ON pt.tag_id = pm.tag_id WHERE pm.project_id = ? ORDER BY pt.name",
                (project_id,),
            )
        )
        proj["members"] = _rows(
            con.execute(
                "SELECT pm.*, au.username, au.email "
                "FROM project_members pm LEFT JOIN auth_user au ON au.auth_user_id = pm.user_id "
                "WHERE pm.project_id = ? ORDER BY pm.project_members_id",
                (project_id,),
            )
        )
        proj["posted_ago"] = _rel_time(
            proj.get("publish_at") or proj.get("created_at")
        )
        return proj


def create_project(data: Mapping[str, Any]) -> int:
    cols = [
        "title",
        "description",
        "submitted_by",
        "course_id",
        "organization_id",
        "status",
        "is_public",
        "publish_at",
        "created_at",
        "updated_at",
        "category",
        "context",
        "external_url",
        "author_display",
    ]
    vals = [data.get(c) for c in cols]
    if vals[8] is None:  # created_at
        vals[8] = _now_ts()
    if vals[9] is None:  # updated_at
        vals[9] = _now_ts()
    with _conn() as con:
        cur = con.execute(
            f"INSERT INTO projects ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})",
            vals,
        )
        return int(cur.lastrowid)


def update_project(project_id: int, data: Mapping[str, Any]) -> None:
    if not data:
        return
    sets = [f"{k} = ?" for k in data.keys()]
    args = list(data.values()) + [project_id]
    with _conn() as con:
        con.execute(
            f"UPDATE projects SET {', '.join(sets)} WHERE projects_id = ?", args
        )


def set_project_status(project_id: int, status: str) -> None:
    update_project(project_id, {"status": status, "updated_at": _now_ts()})


def delete_project(project_id: int) -> None:
    with _conn() as con:
        con.execute(
            "DELETE FROM project_tag_map WHERE project_id = ?", (project_id,)
        )
        con.execute(
            "DELETE FROM project_members WHERE project_id = ?", (project_id,)
        )
        con.execute(
            "DELETE FROM project_media_map WHERE project_id = ?", (project_id,)
        )
        con.execute("DELETE FROM projects WHERE projects_id = ?", (project_id,))


# ---------- tags ----------
def ensure_tag(name: str) -> int:
    with _conn() as con:
        cur = con.execute(
            "INSERT OR IGNORE INTO project_tags (name) VALUES (?)", (name,)
        )
        if cur.lastrowid:
            return int(cur.lastrowid)
        got = con.execute(
            "SELECT tag_id FROM project_tags WHERE name = ?", (name,)
        ).fetchone()
        return int(got["tag_id"])


def set_project_tags(project_id: int, tag_names: Sequence[str]) -> None:
    tag_ids = [ensure_tag(t) for t in tag_names]
    with _conn() as con:
        con.execute(
            "DELETE FROM project_tag_map WHERE project_id = ?", (project_id,)
        )
        con.executemany(
            "INSERT OR IGNORE INTO project_tag_map (project_id, tag_id) VALUES (?,?)",
            [(project_id, tid) for tid in tag_ids],
        )


def list_project_tags(project_id: int) -> list[dict[str, Any]]:
    with _conn() as con:
        return _rows(
            con.execute(
                "SELECT pt.tag_id, pt.name FROM project_tag_map pm "
                "JOIN project_tags pt ON pt.tag_id = pm.tag_id WHERE pm.project_id = ? ORDER BY pt.name",
                (project_id,),
            )
        )


# ---------- members ----------
def add_member(
    project_id: int, user_id: int, role: str | None, contributions: str | None
) -> int:
    with _conn() as con:
        cur = con.execute(
            "INSERT INTO project_members (project_id, user_id, role, contributions) VALUES (?,?,?,?)",
            (project_id, user_id, role, contributions),
        )
        return int(cur.lastrowid)


def remove_member(project_members_id: int) -> None:
    with _conn() as con:
        con.execute(
            "DELETE FROM project_members WHERE project_members_id = ?",
            (project_members_id,),
        )


# ---------- competitions / achievements ----------
def list_competitions(
    q: str | None = None,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    sql = ["SELECT * FROM competitions"]
    where: list[str] = []
    args: list[Any] = []
    if q:
        like = f"%{q}%"
        where.append("(name LIKE ? OR organizer LIKE ? OR description LIKE ?)")
        args += [like, like, like]
    if status:
        where.append("status = ?")
        args.append(status)
    if where:
        sql.append("WHERE " + " AND ".join(where))
    sql.append("ORDER BY created_at DESC LIMIT ? OFFSET ?")
    args += [limit, offset]
    with _conn() as con:
        rows = _rows(con.execute(" ".join(sql), args))
        for r in rows:
            r["posted_ago"] = _rel_time(
                r.get("publish_at") or r.get("created_at")
            )
        return rows


def get_competition(competition_id: int) -> dict[str, Any] | None:
    row = fetch_one(
        "SELECT * FROM competitions WHERE competition_id = ?",
        (competition_id,),
    )
    if not row:
        return None
    row["media"] = list_competition_media(competition_id)
    row["posted_ago"] = _rel_time(
        row.get("publish_at") or row.get("created_at")
    )
    return row


def create_competition(data: Mapping[str, Any]) -> int:
    # flexible: keys of `data` must match column names of `competitions`
    return insert_row("competitions", data)


def update_competition(
    competition_id: int, data: Mapping[str, Any]
) -> None:
    update_row("competitions", "competition_id", competition_id, data)


def set_competition_status(competition_id: int, status: str) -> None:
    update_competition(competition_id, {"status": status, "updated_at": _now_ts()})


def delete_competition(competition_id: int) -> None:
    """
    Delete a competition and all its related rows (achievements, mappings, media).
    Mirrors the previous inline logic in ShowcaseAdminEditDialog._delete_showcase.
    """
    with _conn() as con:
        # get all achievement IDs tied to this competition
        ach_rows = con.execute(
            "SELECT achievement_id FROM competition_achievements "
            "WHERE competition_id = ?",
            (competition_id,),
        ).fetchall()
        ach_ids = [int(r["achievement_id"]) for r in ach_rows]

        if ach_ids:
            # unlink users
            con.executemany(
                "DELETE FROM competition_achievement_users "
                "WHERE achievement_id = ?",
                [(aid,) for aid in ach_ids],
            )
            # unlink projects
            con.executemany(
                "DELETE FROM competition_achievement_projects "
                "WHERE achievement_id = ?",
                [(aid,) for aid in ach_ids],
            )
            # delete achievements themselves
            con.execute(
                "DELETE FROM competition_achievements "
                "WHERE competition_id = ?",
                (competition_id,),
            )

        # media mappings
        con.execute(
            "DELETE FROM competition_media_map "
            "WHERE competition_id = ?",
            (competition_id,),
        )

        # finally the competition row
        con.execute(
            "DELETE FROM competitions WHERE competition_id = ?",
            (competition_id,),
        )


def list_showcase_categories() -> list[str]:
    """
    Return distinct 'category' values for projects and 'event_type' for competitions
    as a combined category list (without any built-in defaults).
    """
    cats: set[str] = set()
    with _conn() as con:
        for row in con.execute(
            "SELECT DISTINCT category FROM projects "
            "WHERE category IS NOT NULL AND category <> ''"
        ):
            cats.add(row["category"])
        for row in con.execute(
            "SELECT DISTINCT event_type AS category FROM competitions "
            "WHERE event_type IS NOT NULL AND event_type <> ''"
        ):
            cats.add(row["category"])
    return sorted(cats)



def list_achievements(competition_id: int | None = None) -> list[dict[str, Any]]:
    sql = [
        "SELECT ca.*, c.name AS competition_name",
        "FROM competition_achievements ca",
        "LEFT JOIN competitions c ON c.competition_id = ca.competition_id",
    ]
    args: list[Any] = []
    if competition_id:
        sql.append("WHERE ca.competition_id = ?")
        args.append(competition_id)
    sql.append("ORDER BY awarded_at DESC, ca.achievement_id DESC")
    with _conn() as con:
        return _rows(con.execute(" ".join(sql), args))


def create_achievement(data: Mapping[str, Any]) -> int:
    return insert_row("competition_achievements", data)


def update_achievement(
    achievement_id: int, data: Mapping[str, Any]
) -> None:
    update_row("competition_achievements", "achievement_id", achievement_id, data)


def delete_achievement(achievement_id: int) -> None:
    with _conn() as con:
        con.execute(
            "DELETE FROM competition_achievement_projects WHERE achievement_id = ?",
            (achievement_id,),
        )
        con.execute(
            "DELETE FROM competition_achievement_users WHERE achievement_id = ?",
            (achievement_id,),
        )
        con.execute(
            "DELETE FROM competition_achievements WHERE achievement_id = ?",
            (achievement_id,),
        )


def link_achievement_to_project(achievement_id: int, project_id: int) -> None:
    with _conn() as con:
        con.execute(
            "INSERT OR IGNORE INTO competition_achievement_projects (achievement_id, project_id) VALUES (?,?)",
            (achievement_id, project_id),
        )


def link_achievement_to_user(
    achievement_id: int, user_id: int, role: str | None
) -> None:
    with _conn() as con:
        con.execute(
            "INSERT OR REPLACE INTO competition_achievement_users (achievement_id, user_id, role) VALUES (?,?,?)",
            (achievement_id, user_id, role),
        )


# ---------- convenience: seed images if needed ----------
def seed_images_if_missing(
    paths: Iterable[str], uploaded_by: int = 1
) -> list[int]:
    ids: list[int] = []
    with _conn() as con:
        for p in paths:
            row = con.execute(
                "SELECT media_id FROM media WHERE path_or_url = ?", (p,)
            ).fetchone()
            if row:
                ids.append(int(row["media_id"]))
                continue
            cur = con.execute(
                "INSERT INTO media (media_type, path_or_url, mime_type, uploaded_by, caption, alt_text) "
                "VALUES ('image', ?, 'image/jpeg', ?, ?, ?)",
                (p, uploaded_by, f"Seed {p}", f"Seed {p}"),
            )
            ids.append(int(cur.lastrowid))
    return ids

# ---------- competitions: richer helpers for UI ----------

def competition_exists(competition_id: int) -> bool:
    """
    Lightweight existence check for competitions.
    Used by ShowcasePreviewDialog to decide if a card ID belongs to a competition.
    """
    row = fetch_one(
        "SELECT 1 FROM competitions WHERE competition_id = ? LIMIT 1",
        (competition_id,),
    )
    return bool(row)


def get_competition_with_relations(competition_id: int) -> dict[str, Any] | None:
    """
    Return a competition with nested achievements, plus their related projects and users.

    Structure:
        {
            ... competition columns ...,
            "media": [...],
            "posted_ago": "...",
            "achievements": [
                {
                    ... achievement columns ...,
                    "projects": [ {projects_id, title}, ... ],
                    "users":    [ {auth_user_id, username, email, role}, ... ],
                },
                ...
            ],
        }
    """
    comp = get_competition(competition_id)
    if not comp:
        return None

    with _conn() as con:
        ach_rows = con.execute(
            """
            SELECT *
            FROM competition_achievements
            WHERE competition_id = ?
            ORDER BY awarded_at DESC, achievement_id DESC
            """,
            (competition_id,),
        ).fetchall()

        achievements: list[dict[str, Any]] = []
        for ar in ach_rows:
            ach = dict(ar)
            aid = ach["achievement_id"]

            proj_rows = con.execute(
                """
                SELECT p.projects_id, p.title
                FROM competition_achievement_projects cap
                JOIN projects p ON p.projects_id = cap.project_id
                WHERE cap.achievement_id = ?
                ORDER BY p.title
                """,
                (aid,),
            ).fetchall()
            ach["projects"] = [dict(r) for r in proj_rows]

            user_rows = con.execute(
                """
                SELECT au.auth_user_id, au.username, au.email, cau.role
                FROM competition_achievement_users cau
                JOIN auth_user au ON au.auth_user_id = cau.user_id
                WHERE cau.achievement_id = ?
                ORDER BY au.username
                """,
                (aid,),
            ).fetchall()
            ach["users"] = [dict(r) for r in user_rows]

            achievements.append(ach)

    comp["achievements"] = achievements
    return comp

# ---------- auth users ----------

def get_auth_user_id_by_username(username: str) -> int | None:
    username = (username or "").strip()
    if not username:
        return None
    row = fetch_one(
        "SELECT auth_user_id FROM auth_user WHERE username = ?",
        (username,),
    )
    if not row:
        return None
    try:
        return int(row["auth_user_id"])
    except Exception:
        return None


def ensure_auth_user(username: str, email: str | None = None) -> int | None:
    """
    Ensure an auth_user row exists for the given username.

    Returns auth_user_id or None if username is empty.
    """
    username = (username or "").strip()
    if not username:
        return None

    existing = get_auth_user_id_by_username(username)
    if existing is not None:
        return existing

    # create new user with optional email
    return insert_row("auth_user", {"username": username, "email": email})

