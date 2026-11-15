
import sqlite3
import json
from pathlib import Path
from datetime import datetime


# ==========================================================
# DATABASE CONFIGURATION
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent
LOG_DATABASE = BASE_DIR / "agent_logs.db"


# ==========================================================
# CREATE AGENT LOG TABLE
# ==========================================================

def create_agent_log_table():
    """Create the agent activity log table if it does not exist."""

    conn = sqlite3.connect(LOG_DATABASE)

    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                user_message TEXT,
                tool_name TEXT,
                arguments TEXT,
                status TEXT,
                result TEXT,
                error TEXT,
                created_at TEXT NOT NULL
            )
        """)

        conn.commit()

    finally:
        conn.close()


# ==========================================================
# SAVE AGENT ACTIVITY
# ==========================================================

def log_agent_event(
    event_type,
    user_message=None,
    tool_name=None,
    arguments=None,
    status=None,
    result=None,
    error=None
):
    """Save one agent activity event."""

    try:
        conn = sqlite3.connect(LOG_DATABASE)

        try:
            conn.execute("""
                INSERT INTO agent_logs (
                    event_type,
                    user_message,
                    tool_name,
                    arguments,
                    status,
                    result,
                    error,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(event_type),
                str(user_message)[:1000] if user_message is not None else None,
                str(tool_name) if tool_name is not None else None,
                json.dumps(arguments, default=str) if arguments is not None else None,
                str(status) if status is not None else None,
                json.dumps(result, default=str)[:3000] if result is not None else None,
                str(error)[:2000] if error is not None else None,
                datetime.now().isoformat(timespec="seconds")
            ))

            conn.commit()

        finally:
            conn.close()

        return True

    except Exception as exc:
        print(f"Agent logging warning: {exc}")
        return False


# ==========================================================
# RETRIEVE AGENT LOGS
# ==========================================================

def get_agent_logs(limit=100):

    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or limit <= 0
    ):
        raise ValueError("Limit must be a positive integer.")

    conn = sqlite3.connect(LOG_DATABASE)
    conn.row_factory = sqlite3.Row

    try:
        rows = conn.execute("""
            SELECT *
            FROM agent_logs
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()


# ==========================================================
# INITIALIZE DATABASE
# ==========================================================

create_agent_log_table()
