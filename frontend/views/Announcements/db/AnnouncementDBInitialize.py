# db/AnnouncementDBInitialize.py
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import List


# ---- location ----
def db_path() -> Path:
    return Path(__file__).resolve().parent / "announcement.db"


# ---- internal connect (bootstrap only) ----
def _conn_bootstrap() -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path()))
    con.execute("PRAGMA foreign_keys = ON")
    return con


# ---- schema (SQLite) ----
SCHEMA_DDL: List[str] = [
    """
    CREATE TABLE IF NOT EXISTS auth_user (
        user_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        username    TEXT UNIQUE NOT NULL,
        email       TEXT,
        full_name   TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS approvals (
        approval_id INTEGER PRIMARY KEY AUTOINCREMENT,
        status      TEXT NOT NULL DEFAULT 'pending',
        approver_id INTEGER,
        approved_at TEXT,
        note        TEXT,
        FOREIGN KEY (approver_id) REFERENCES auth_user(user_id)
            ON DELETE SET NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS announcements (
        announcement_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title           TEXT NOT NULL,
        body            TEXT,
        author_id       INTEGER,
        publish_at      TEXT,
        expire_at       TEXT,
        location        TEXT,
        approval_id     INTEGER,
        status          TEXT,              -- draft / pending / approved / rejected
        visibility      TEXT,              -- audience / role / etc
        priority        INTEGER DEFAULT 0,
        is_pinned       INTEGER DEFAULT 0,
        pinned_until    TEXT,
        created_by      INTEGER,
        created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at      TEXT,
        updated_by      INTEGER,
        deleted_at      TEXT,
        note            TEXT,
        FOREIGN KEY (author_id)   REFERENCES auth_user(user_id)
            ON DELETE SET NULL,
        FOREIGN KEY (approval_id) REFERENCES approvals(approval_id)
            ON DELETE SET NULL,
        FOREIGN KEY (created_by) REFERENCES auth_user(user_id)
            ON DELETE SET NULL,
        FOREIGN KEY (updated_by) REFERENCES auth_user(user_id)
            ON DELETE SET NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS tags (
        tag_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        tag_name TEXT UNIQUE NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS announcement_tag_map (
        announcement_id INTEGER NOT NULL,
        tag_id          INTEGER NOT NULL,
        PRIMARY KEY (announcement_id, tag_id),
        FOREIGN KEY (announcement_id) REFERENCES announcements(announcement_id)
            ON DELETE CASCADE,
        FOREIGN KEY (tag_id)         REFERENCES tags(tag_id)
            ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS documents (
        document_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        announcement_id  INTEGER NOT NULL,
        file_name        TEXT NOT NULL,
        file_path        TEXT NOT NULL,
        mime_type        TEXT,
        file_size_bytes  INTEGER,
        checksum         TEXT,
        uploaded_by      INTEGER,
        uploaded_at      TEXT DEFAULT CURRENT_TIMESTAMP,
        visible          INTEGER DEFAULT 1,
        expires_at       TEXT,
        version          INTEGER DEFAULT 1,
        description      TEXT,
        FOREIGN KEY (announcement_id) REFERENCES announcements(announcement_id)
            ON DELETE CASCADE,
        FOREIGN KEY (uploaded_by)    REFERENCES auth_user(user_id)
            ON DELETE SET NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS announcement_reads (
        read_id         INTEGER PRIMARY KEY AUTOINCREMENT,
        announcement_id INTEGER NOT NULL,
        user_id         INTEGER NOT NULL,
        has_read        INTEGER NOT NULL DEFAULT 1,
        read_time       TEXT DEFAULT CURRENT_TIMESTAMP,
        device_info     TEXT,
        UNIQUE (announcement_id, user_id),
        FOREIGN KEY (announcement_id) REFERENCES announcements(announcement_id)
            ON DELETE CASCADE,
        FOREIGN KEY (user_id)        REFERENCES auth_user(user_id)
            ON DELETE CASCADE
    );
    """,
]


def _apply_schema(con: sqlite3.Connection) -> None:
    for ddl in SCHEMA_DDL:
        con.executescript(ddl)


# ---- seeding (mock data) ----
def _seed_minimal(con: sqlite3.Connection) -> None:
    # users
    cur = con.execute("SELECT COUNT(*) FROM auth_user")
    if cur.fetchone()[0] == 0:
        con.execute(
            "INSERT INTO auth_user(username, email, full_name) VALUES (?, ?, ?)",
            ("admin", "admin@example.com", "Admin"),
        )

    # announcements + tags
    cur = con.execute("SELECT COUNT(*) FROM announcements")
    if cur.fetchone()[0] == 0:
        con.execute(
            """
            INSERT INTO announcements (title, body, author_id, status)
            VALUES (?, ?, ?, ?)
            """,
            ("Welcome", "First announcement", 1, "draft"),
        )

        # ensure default tag
        con.execute(
            "INSERT OR IGNORE INTO tags(tag_name) VALUES (?)",
            ("general",),
        )

        # link first announcement to 'general' tag
        cur = con.execute(
            "SELECT announcement_id FROM announcements ORDER BY announcement_id LIMIT 1"
        )
        row = cur.fetchone()
        if row:
            ann_id = int(row[0])
            cur = con.execute(
                "SELECT tag_id FROM tags WHERE tag_name=?",
                ("general",),
            )
            tag_row = cur.fetchone()
            if tag_row:
                tag_id = int(tag_row[0])
                con.execute(
                    """
                    INSERT OR IGNORE INTO announcement_tag_map(announcement_id, tag_id)
                    VALUES (?, ?)
                    """,
                    (ann_id, tag_id),
                )


# ---- public bootstrap API ----
def ensure_bootstrap() -> Path:
    """
    Ensure the DB file and schema exist.
    Does not insert any mock data.
    """
    db_file = db_path()
    db_file.parent.mkdir(parents=True, exist_ok=True)

    with _conn_bootstrap() as con:
        _apply_schema(con)
        con.commit()

    return db_file


def ensure_bootstrap_and_seed() -> Path:
    """
    Ensure schema exists and insert minimal seed data (idempotent).
    """
    db_file = ensure_bootstrap()
    with _conn_bootstrap() as con:
        _seed_minimal(con)
        con.commit()
    return db_file
