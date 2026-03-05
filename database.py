"""
Simple SQLite-based storage for user data.
Tracks daily download counts and subscription status.
"""
import sqlite3
import datetime
from pathlib import Path

DB_PATH = Path("data/users.db")
DB_PATH.parent.mkdir(exist_ok=True)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                is_premium  INTEGER DEFAULT 0,
                premium_until TEXT,
                dl_count    INTEGER DEFAULT 0,
                dl_date     TEXT DEFAULT ''
            )
        """)
        conn.commit()


def get_or_create_user(user_id: int, username: str = "") -> sqlite3.Row:
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        if not row:
            conn.execute(
                "INSERT INTO users (user_id, username) VALUES (?, ?)",
                (user_id, username),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
    return row


def get_daily_count(user_id: int) -> int:
    """Return today's download count for user."""
    init_db()
    today = str(datetime.date.today())
    with _connect() as conn:
        row = conn.execute(
            "SELECT dl_count, dl_date FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
    if not row:
        return 0
    if row["dl_date"] != today:
        return 0
    return row["dl_count"]


def increment_daily_count(user_id: int) -> None:
    init_db()
    today = str(datetime.date.today())
    with _connect() as conn:
        row = conn.execute(
            "SELECT dl_count, dl_date FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        if row and row["dl_date"] == today:
            conn.execute(
                "UPDATE users SET dl_count = dl_count + 1 WHERE user_id = ?",
                (user_id,),
            )
        else:
            conn.execute(
                "UPDATE users SET dl_count = 1, dl_date = ? WHERE user_id = ?",
                (today, user_id),
            )
        conn.commit()


def is_premium(user_id: int) -> bool:
    init_db()
    today = str(datetime.date.today())
    with _connect() as conn:
        row = conn.execute(
            "SELECT is_premium, premium_until FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    if not row:
        return False
    if row["is_premium"] and (
        not row["premium_until"] or row["premium_until"] >= today
    ):
        return True
    return False


def set_premium(user_id: int, until_date: str) -> None:
    """Grant premium. until_date format: YYYY-MM-DD"""
    init_db()
    with _connect() as conn:
        conn.execute(
            "UPDATE users SET is_premium = 1, premium_until = ? WHERE user_id = ?",
            (until_date, user_id),
        )
        conn.commit()
