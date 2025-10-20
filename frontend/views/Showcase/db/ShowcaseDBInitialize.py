# views/Showcase/db/ShowcaseDBInitialize.py
from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime

# ---------- location ----------
def db_path() -> Path:
    return Path(__file__).resolve().parent / "showcase.db"

# ---------- connect ----------
def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path()))
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sqlite3.Row
    return con

# ---------- schema ----------
SCHEMA_DDL: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS auth_user (
        auth_user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username     TEXT,
        email        TEXT UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS media (
        media_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        media_type   TEXT NOT NULL CHECK (media_type IN ('image','video','audio','file','link')),
        path_or_url  TEXT NOT NULL,
        mime_type    TEXT,
        size_bytes   INTEGER,
        checksum     TEXT,
        caption      TEXT,
        alt_text     TEXT,
        uploaded_by  INTEGER,
        created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (uploaded_by) REFERENCES auth_user(auth_user_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS projects (
        projects_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        title           TEXT NOT NULL,
        description     TEXT,
        submitted_by    INTEGER,
        course_id       INTEGER,
        organization_id INTEGER,
        status          TEXT,
        is_public       INTEGER CHECK (is_public IN (0,1)),
        publish_at      TIMESTAMP,
        created_at      TIMESTAMP,
        updated_at      TIMESTAMP,
        category        TEXT,
        context         TEXT,
        external_url    TEXT,
        author_display  TEXT,
        FOREIGN KEY (submitted_by) REFERENCES auth_user(auth_user_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS project_members (
        project_members_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id         INTEGER,
        user_id            INTEGER,
        role               TEXT,
        contributions      TEXT,
        FOREIGN KEY (project_id) REFERENCES projects(projects_id),
        FOREIGN KEY (user_id)   REFERENCES auth_user(auth_user_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS project_tags (
        tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name   TEXT UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS project_tag_map (
        project_id INTEGER NOT NULL,
        tag_id     INTEGER NOT NULL,
        PRIMARY KEY (project_id, tag_id),
        FOREIGN KEY (project_id) REFERENCES projects(projects_id),
        FOREIGN KEY (tag_id)     REFERENCES project_tags(tag_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS project_media_map (
        media_id    INTEGER NOT NULL,
        project_id  INTEGER NOT NULL,
        sort_order  INTEGER,
        is_primary  INTEGER DEFAULT 0 CHECK (is_primary IN (0,1)),
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (media_id, project_id),
        FOREIGN KEY (media_id)   REFERENCES media(media_id),
        FOREIGN KEY (project_id) REFERENCES projects(projects_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS competitions (
        competition_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name           TEXT NOT NULL,
        organizer      TEXT,
        start_date     DATE,
        end_date       DATE,
        related_event_id INTEGER,
        description    TEXT,
        event_type     TEXT,
        external_url   TEXT,
        submitted_by   INTEGER,
        status         TEXT DEFAULT 'draft',
        is_public      INTEGER DEFAULT 0 CHECK (is_public IN (0,1)),
        publish_at     TIMESTAMP,
        created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (submitted_by) REFERENCES auth_user(auth_user_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS competition_media_map (
        media_id       INTEGER NOT NULL,
        competition_id INTEGER NOT NULL,
        sort_order     INTEGER,
        is_primary     INTEGER DEFAULT 0 CHECK (is_primary IN (0,1)),
        created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (media_id, competition_id),
        FOREIGN KEY (media_id)       REFERENCES media(media_id),
        FOREIGN KEY (competition_id) REFERENCES competitions(competition_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS competition_achievements (
        achievement_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        competition_id     INTEGER,
        achievement_title  TEXT NOT NULL,
        result_recognition TEXT,
        specific_awards    TEXT,
        notes              TEXT,
        awarded_at         DATE,
        FOREIGN KEY (competition_id) REFERENCES competitions(competition_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS competition_achievement_projects (
        achievement_id INTEGER NOT NULL,
        project_id     INTEGER NOT NULL,
        PRIMARY KEY (achievement_id, project_id),
        FOREIGN KEY (achievement_id) REFERENCES competition_achievements(achievement_id),
        FOREIGN KEY (project_id)     REFERENCES projects(projects_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS competition_achievement_users (
        achievement_id INTEGER NOT NULL,
        user_id        INTEGER NOT NULL,
        role           TEXT,
        PRIMARY KEY (achievement_id, user_id),
        FOREIGN KEY (achievement_id) REFERENCES competition_achievements(achievement_id),
        FOREIGN KEY (user_id)        REFERENCES auth_user(auth_user_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_project_media_map_project  ON project_media_map(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_project_media_map_media    ON project_media_map(media_id)",
    "CREATE INDEX IF NOT EXISTS idx_competition_media_map_comp ON competition_media_map(competition_id)",
    "CREATE INDEX IF NOT EXISTS idx_competition_media_map_media ON competition_media_map(media_id)",
]

# ---------- seed ----------
def _is_empty(con: sqlite3.Connection, table: str) -> bool:
    return con.execute(f"SELECT 1 FROM {table} LIMIT 1").fetchone() is None

def _now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _seed(con: sqlite3.Connection) -> None:
    if _is_empty(con, "auth_user"):
        con.executemany(
            "INSERT INTO auth_user (username, email) VALUES (?,?)",
            [("alice","alice@example.com"), ("bob","bob@example.com"), ("carol","carol@example.com")],
        )

    if _is_empty(con, "project_tags"):
        con.executemany("INSERT INTO project_tags (name) VALUES (?)", [("AI",), ("IoT",), ("Education",)])

    if _is_empty(con, "projects"):
        con.executemany(
            """
            INSERT INTO projects
              (title, description, submitted_by, status, is_public, created_at, updated_at, category, context, external_url, author_display)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            [
                ("Smart Bin", "An IoT waste-segregation bin.", 1, "pending", 1, _now_ts(), _now_ts(), "capstone", "hardware", "https://example.com/smart-bin", "Alice, Bob"),
                ("Study Buddy", "A student helper app.", 2, "approved", 1, _now_ts(), _now_ts(), "software", "mobile", "https://example.com/study-buddy", "Carol"),
            ],
        )

    if _is_empty(con, "project_members"):
        con.executemany(
            "INSERT INTO project_members (project_id, user_id, role, contributions) VALUES (?,?,?,?)",
            [(1,1,"Leader","Design, Assembly"), (1,2,"Developer","Firmware, Cloud"), (2,3,"Solo","Android app")],
        )

    if _is_empty(con, "project_tag_map"):
        con.executemany("INSERT OR IGNORE INTO project_tag_map (project_id, tag_id) VALUES (?,?)", [(1,2),(1,3),(2,1)])

    # --- sample images in assets/images ---
    if _is_empty(con, "media"):
        rows = []
        for i in range(1, 8):
            rel = f"assets/images/{i}.jpg"
            rows.append((
                "image", rel, "image/jpeg", None, None,
                f"Sample {i}", f"Sample image {i}", ((i - 1) % 3) + 1  # rotate uploaded_by 1..3
            ))
        con.executemany(
            """
            INSERT INTO media (media_type, path_or_url, mime_type, size_bytes, checksum, caption, alt_text, uploaded_by)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            rows,
        )

    if _is_empty(con, "project_media_map"):
        # media ids 1..7 if fresh DB; map to projects
        con.executemany(
            "INSERT INTO project_media_map (media_id, project_id, sort_order, is_primary) VALUES (?,?,?,?)",
            [
                (1, 1, 1, 1),
                (2, 1, 2, 0),
                (3, 1, 3, 0),
                (4, 2, 1, 1),
                (5, 2, 2, 0),
            ],
        )

    if _is_empty(con, "competitions"):
        con.execute(
            """
            INSERT INTO competitions
              (name, organizer, start_date, end_date, description, event_type, external_url, submitted_by, status, is_public, publish_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            ("TechFest 2025", "CMU", "2025-03-01", "2025-03-03",
             "Annual technology fair.", "expo", "https://example.com/techfest",
             1, "published", 1, _now_ts()),
        )

    if _is_empty(con, "competition_media_map"):
        con.executemany(
            "INSERT INTO competition_media_map (media_id, competition_id, sort_order, is_primary) VALUES (?,?,?,?)",
            [
                (6, 1, 1, 1),  # primary poster
                (7, 1, 2, 0),
            ],
        )

    if _is_empty(con, "competition_achievements"):
        con.execute(
            """
            INSERT INTO competition_achievements
              (competition_id, achievement_title, result_recognition, specific_awards, notes, awarded_at)
            VALUES (?,?,?,?,?,?)
            """,
            (1, "Best IoT Demo", "Champion", "Gold Medal", "Clean presentation", "2025-03-03"),
        )

    if _is_empty(con, "competition_achievement_projects"):
        con.execute("INSERT INTO competition_achievement_projects (achievement_id, project_id) VALUES (?,?)", (1, 1))

    if _is_empty(con, "competition_achievement_users"):
        con.executemany(
            "INSERT INTO competition_achievement_users (achievement_id, user_id, role) VALUES (?,?,?)",
            [(1,1,"Presenter"), (1,2,"Developer")],
        )

# ---------- API ----------
def ensure_bootstrap(seed: bool = True) -> None:
    db_path().parent.mkdir(parents=True, exist_ok=True)
    with _conn() as con:
        for stmt in SCHEMA_DDL:
            con.execute(stmt)
        if seed:
            _seed(con)
        con.commit()

def reset_database(seed: bool = True) -> None:
    p = db_path()
    if p.exists():
        p.unlink()
    ensure_bootstrap(seed=seed)

if __name__ == "__main__":
    ensure_bootstrap(True)
    print(f"OK: {db_path()}")
