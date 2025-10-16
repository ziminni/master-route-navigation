# db/AnnouncementDBInitialize.py
from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

# ---- location ----
def db_path() -> Path:
    return Path(__file__).resolve().parent / "announcement.db"

# ---- connect ----
def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path()))
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sqlite3.Row
    return con

# ---- schema (SQLite) ----
SCHEMA_DDL: list[str] = [
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
        approver_id INTEGER,
        status      TEXT,
        comment     TEXT,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (approver_id) REFERENCES auth_user(user_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS announcements (
        announcement_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title        TEXT NOT NULL,
        body         TEXT,
        author_id    INTEGER,
        publish_at   TEXT,
        expire_at    TEXT,
        location     TEXT,
        approval_id  INTEGER,
        status       TEXT DEFAULT 'draft',
        visibility   TEXT DEFAULT 'public',
        priority     INTEGER DEFAULT 0,
        is_pinned    INTEGER DEFAULT 0,
        pinned_until TEXT,
        created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        created_by   INTEGER,
        updated_at   TIMESTAMP,
        updated_by   INTEGER,
        deleted_at   TIMESTAMP,
        note         TEXT,
        FOREIGN KEY (author_id)   REFERENCES auth_user(user_id),
        FOREIGN KEY (approval_id) REFERENCES approvals(approval_id),
        FOREIGN KEY (created_by)  REFERENCES auth_user(user_id),
        FOREIGN KEY (updated_by)  REFERENCES auth_user(user_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS tags (
        tag_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        tag_name   TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS announcement_tag_map (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        announcement_id INTEGER NOT NULL,
        tag_id          INTEGER NOT NULL,
        FOREIGN KEY (announcement_id) REFERENCES announcements(announcement_id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id)          REFERENCES tags(tag_id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS announcement_reads (
        read_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        announcement_id INTEGER NOT NULL,
        user_id        INTEGER NOT NULL,
        has_read       INTEGER DEFAULT 0,
        read_time      TIMESTAMP,
        device_info    TEXT,
        created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (announcement_id) REFERENCES announcements(announcement_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id)        REFERENCES auth_user(user_id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS announcement_audience (
        audience_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        announcement_id INTEGER NOT NULL,
        scope_type     TEXT NOT NULL,
        scope_target_id INTEGER,
        created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at     TEXT,
        note           TEXT,
        FOREIGN KEY (announcement_id) REFERENCES announcements(announcement_id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS documents (
        document_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        announcement_id INTEGER NOT NULL,
        file_name       TEXT NOT NULL,
        file_path       TEXT NOT NULL,
        mime_type       TEXT,
        file_size_bytes INTEGER,
        checksum        TEXT,
        uploaded_by     INTEGER,
        uploaded_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        visible         INTEGER DEFAULT 1,
        expires_at      TEXT,
        version         TEXT,
        description     TEXT,
        FOREIGN KEY (announcement_id) REFERENCES announcements(announcement_id) ON DELETE CASCADE,
        FOREIGN KEY (uploaded_by)     REFERENCES auth_user(user_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS reminders (
        reminder_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        title          TEXT NOT NULL,
        body           TEXT,
        author_id      INTEGER,
        remind_at      TEXT,
        repeat_interval TEXT,
        priority       INTEGER DEFAULT 0,
        is_active      INTEGER DEFAULT 1,
        is_snoozable   INTEGER DEFAULT 1,
        snooze_until   TEXT,
        visibility     TEXT DEFAULT 'private',
        created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        created_by     INTEGER,
        updated_at     TIMESTAMP,
        updated_by     INTEGER,
        expires_at     TEXT,
        note           TEXT,
        FOREIGN KEY (author_id)  REFERENCES auth_user(user_id),
        FOREIGN KEY (created_by) REFERENCES auth_user(user_id),
        FOREIGN KEY (updated_by) REFERENCES auth_user(user_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS reminder_audience (
        audience_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        reminder_id     INTEGER NOT NULL,
        scope_type      TEXT NOT NULL,
        scope_target_id INTEGER,
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at      TEXT,
        note            TEXT,
        FOREIGN KEY (reminder_id) REFERENCES reminders(reminder_id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS reminder_acknowledgements (
        ack_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        reminder_id   INTEGER NOT NULL,
        user_id       INTEGER NOT NULL,
        acknowledged  INTEGER DEFAULT 0,
        ack_time      TIMESTAMP,
        device_info   TEXT,
        created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (reminder_id) REFERENCES reminders(reminder_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id)     REFERENCES auth_user(user_id) ON DELETE CASCADE
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_ann_author   ON announcements(author_id);",
    "CREATE INDEX IF NOT EXISTS idx_ann_status   ON announcements(status);",
    "CREATE INDEX IF NOT EXISTS idx_ann_publish  ON announcements(publish_at);",
    "CREATE INDEX IF NOT EXISTS idx_reads_user   ON announcement_reads(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_tagmap_tag   ON announcement_tag_map(tag_id);",
    "CREATE INDEX IF NOT EXISTS idx_docs_ann     ON documents(announcement_id);",
    "CREATE INDEX IF NOT EXISTS idx_remind_at    ON reminders(remind_at);",
    "CREATE INDEX IF NOT EXISTS idx_tagmap_ann  ON announcement_tag_map(announcement_id);",
]

def ensure_bootstrap() -> Path:
    path = db_path()
    with _conn() as con:
        cur = con.cursor()
        for stmt in SCHEMA_DDL:
            cur.execute(stmt)
        con.commit()
    return path

# ---- seed data ----
def seed_startup_data() -> None:
    with _conn() as con:
        cur = con.cursor()

        users = [
            ("jsmith", "jsmith@example.com", "John Smith"),
            ("adoe", "adoe@example.com", "Alice Doe"),
            ("bwayne", "bwayne@example.com", "Bruce Wayne"),
        ]
        for u in users:
            cur.execute("INSERT OR IGNORE INTO auth_user(username,email,full_name) VALUES(?,?,?)", u)

        cur.execute("SELECT user_id FROM auth_user ORDER BY user_id")
        user_ids = [r["user_id"] for r in cur.fetchall()]
        if not user_ids:
            con.commit(); return

        cur.execute("SELECT COUNT(*) AS c FROM announcements")
        if cur.fetchone()["c"] == 0:
            now = datetime.utcnow()
            base_body = ("Some quick example text to build on the card title and make up the bulk of the card content. "
                         "This comes from the database seed.")
            titles = [
                "Campus Maintenance Update",
                "Library Hours Extended",
                "New Course Registration",
                "IT Scheduled Downtime",
                "Sports Fest Opening",
                "Health and Wellness Fair",
            ]
            for i, title in enumerate(titles, start=1):
                author_id = user_ids[i % len(user_ids)]
                created_at = now - timedelta(hours=2*i)
                cur.execute("""
                    INSERT INTO announcements(title, body, author_id, publish_at, status, visibility, priority, created_at, created_by)
                    VALUES(?,?,?,?,?,?,?,datetime(?),?)
                """, (
                    title, base_body, author_id,
                    created_at.isoformat(sep=" "),
                    "published", "public", i % 3,
                    created_at.isoformat(sep=" "), author_id
                ))
                ann_id = cur.lastrowid

                # always attach one image
                img_names = [f"{(i%6)+1}.jpg"]

                # make the first announcement showcase 4 images
                if i == 1:
                    extras = ["1.jpg", "3.jpg", "5.jpg"]  # pick any existing images
                    img_names += [n for n in extras if n not in img_names]

                for fname in img_names:
                    fpath = f"assets/images/{fname}"
                    cur.execute("""
                        INSERT INTO documents(announcement_id, file_name, file_path, mime_type, file_size_bytes, uploaded_by)
                        VALUES(?,?,?,?,?,?)
                    """, (ann_id, fname, fpath, "image/jpeg", 0, author_id))

        cur.execute("SELECT COUNT(*) AS c FROM reminders")
        if cur.fetchone()["c"] == 0:
            now = datetime.utcnow()
            titles = [
                "Submit Weekly Report",
                "Team Standup at 9:00",
                "Backup Your Files",
                "Pay Utility Bills",
                "Prepare Presentation",
                "Security Awareness Quiz",
            ]
            bodies = [
                "Upload report to the portal.",
                "Quick sync with the team.",
                "Run your backups today.",
                "Avoid late fees.",
                "Slides due by EOD.",
                "Finish by Friday.",
            ]
            for i, title in enumerate(titles, start=1):
                author_id = user_ids[(i+1) % len(user_ids)]
                remind_at = now + timedelta(hours=i)
                cur.execute("""
                    INSERT INTO reminders(title, body, author_id, remind_at, repeat_interval, priority, is_active, created_at, created_by)
                    VALUES(?,?,?,?,?,?,?,?,?)
                """, (
                    title, bodies[i-1], author_id,
                    remind_at.isoformat(sep=" "), "none", i % 2, 1,
                    now.isoformat(sep=" "), author_id
                ))
        con.commit()

# ---- queries for UI ----
def get_announcements(limit: int = 6, q: str | None = None) -> list[dict]:
    sql = """
        SELECT
            a.announcement_id, a.title, a.body, a.location,
            a.visibility, a.priority, a.is_pinned, a.pinned_until,
            a.publish_at, a.expire_at, a.created_at,
            COALESCE(u.full_name, u.username, 'Unknown') AS author_name,
            MAX(d.file_path) AS file_path,                           -- any one image
            COUNT(DISTINCT d.document_id) AS doc_count,
            IFNULL(GROUP_CONCAT(DISTINCT t.tag_name), '') AS tags_csv
        FROM announcements a
        LEFT JOIN auth_user u ON a.author_id = u.user_id
        LEFT JOIN documents d ON d.announcement_id = a.announcement_id
        LEFT JOIN announcement_tag_map m ON m.announcement_id = a.announcement_id
        LEFT JOIN tags t ON t.tag_id = m.tag_id
        WHERE a.deleted_at IS NULL
          AND a.status = 'published'
          AND (a.publish_at IS NULL OR a.publish_at <= CURRENT_TIMESTAMP)
          AND (a.expire_at  IS NULL OR a.expire_at  >  CURRENT_TIMESTAMP)
    """
    args: list = []
    if q:
        sql += " AND (a.title LIKE ? OR a.body LIKE ?)"
        like = f"%{q}%"; args.extend([like, like])
    sql += " GROUP BY a.announcement_id ORDER BY COALESCE(a.publish_at, a.created_at) DESC LIMIT ?"
    args.append(limit)
    with _conn() as con:
        cur = con.cursor()
        cur.execute(sql, args)
        return [dict(row) for row in cur.fetchall()]


def get_reminders(limit: int = 6, q: str | None = None) -> list[dict]:
    sql = """
        SELECT r.reminder_id, r.title, r.body, r.priority, r.created_at,
               COALESCE(u.full_name, u.username, 'Unknown') AS author_name
        FROM reminders r
        LEFT JOIN auth_user u ON r.author_id = u.user_id
        WHERE r.is_active = 1
    """
    args: list = []
    if q:
        sql += " AND (r.title LIKE ? OR r.body LIKE ?)"
        like = f"%{q}%"
        args.extend([like, like])
    sql += " ORDER BY r.created_at DESC LIMIT ?"
    args.append(limit)
    with _conn() as con:
        cur = con.cursor()
        cur.execute(sql, args)
        return [dict(row) for row in cur.fetchall()]

def ensure_bootstrap_and_seed() -> Path:
    p = ensure_bootstrap()
    seed_startup_data()
    return p

if __name__ == "__main__":
    ensure_bootstrap_and_seed()
    print(f"Initialized and seeded: {db_path()}")
