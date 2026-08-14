import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta

# A relative DB_PATH is resolved against this file's directory, not the current
# working directory — otherwise the database silently moves depending on where the
# bot was launched from. Absolute paths (e.g. Railway's /data/leetcode.db) are used
# as-is.
_configured_path = os.environ.get("DB_PATH", "leetcode.db")
DB_PATH = (
    _configured_path
    if os.path.isabs(_configured_path)
    else os.path.join(os.path.dirname(os.path.abspath(__file__)), _configured_path)
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    username TEXT NOT NULL,
    session_type TEXT NOT NULL CHECK (session_type IN ('leetcode', 'system_design')),
    topic TEXT,
    difficulty TEXT,
    minutes INTEGER,
    notes TEXT,
    session_date TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sessions_user_date ON sessions(user_id, session_date);
"""


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    # sqlite3 raises a bare "unable to open database file" when the parent directory
    # is missing, which is the usual symptom of a persistent volume not being mounted
    # where DB_PATH expects it. Say so explicitly rather than making someone read a
    # traceback. Deliberately not creating the directory: on a host with a volume,
    # silently writing to the container's ephemeral disk would look like it worked
    # and then lose every check-in on the next deploy.
    parent = os.path.dirname(DB_PATH)
    if parent and not os.path.isdir(parent):
        raise RuntimeError(
            f"Cannot open the database: directory {parent!r} does not exist "
            f"(DB_PATH={DB_PATH!r}).\n"
            f"If this host has a persistent volume, attach it and set its mount path "
            f"to {parent!r}, or set DB_PATH to wherever the volume is actually "
            f"mounted. Unset DB_PATH to fall back to a file next to bot.py (not "
            f"persistent across deploys)."
        )
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def add_session(user_id, username, session_type, topic, difficulty, minutes, notes):
    today = date.today().isoformat()
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO sessions "
            "(user_id, username, session_type, topic, difficulty, minutes, notes, session_date, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, username, session_type, topic, difficulty, minutes, notes, today, now),
        )


def _session_dates(user_id):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT session_date FROM sessions WHERE user_id = ?",
            (user_id,),
        ).fetchall()
    return {date.fromisoformat(r["session_date"]) for r in rows}


def current_streak(user_id):
    dates = _session_dates(user_id)
    if not dates:
        return 0
    day = date.today()
    if day not in dates:
        day -= timedelta(days=1)
        if day not in dates:
            return 0
    streak = 0
    while day in dates:
        streak += 1
        day -= timedelta(days=1)
    return streak


def longest_streak(user_id):
    dates = sorted(_session_dates(user_id))
    if not dates:
        return 0
    longest = run = 1
    for prev, curr in zip(dates, dates[1:]):
        if (curr - prev).days == 1:
            run += 1
            longest = max(longest, run)
        else:
            run = 1
    return longest


def user_stats(user_id):
    with get_conn() as conn:
        total = conn.execute(
            "SELECT COUNT(*) c FROM sessions WHERE user_id = ?", (user_id,)
        ).fetchone()["c"]
        by_type = conn.execute(
            "SELECT session_type, COUNT(*) c FROM sessions WHERE user_id = ? GROUP BY session_type",
            (user_id,),
        ).fetchall()
        week_ago = (date.today() - timedelta(days=6)).isoformat()
        days_this_week = conn.execute(
            "SELECT COUNT(DISTINCT session_date) c FROM sessions WHERE user_id = ? AND session_date >= ?",
            (user_id, week_ago),
        ).fetchone()["c"]
    return {
        "total": total,
        "by_type": {r["session_type"]: r["c"] for r in by_type},
        "days_this_week": days_this_week,
        "current_streak": current_streak(user_id),
        "longest_streak": longest_streak(user_id),
    }


def leaderboard():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT user_id, username, COUNT(*) total, MAX(session_date) last_date "
            "FROM sessions GROUP BY user_id"
        ).fetchall()
    board = [
        {
            "user_id": r["user_id"],
            "username": r["username"],
            "total": r["total"],
            "current_streak": current_streak(r["user_id"]),
            "last_date": r["last_date"],
        }
        for r in rows
    ]
    board.sort(key=lambda x: (x["current_streak"], x["total"]), reverse=True)
    return board


def recent_sessions(user_id, limit=5):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM sessions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return rows


def checked_in_today(user_id):
    today = date.today().isoformat()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) c FROM sessions WHERE user_id = ? AND session_date = ?",
            (user_id, today),
        ).fetchone()
    return row["c"] > 0
