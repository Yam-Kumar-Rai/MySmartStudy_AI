
from database.db import get_connection


def create_study_table():
    """Create the table for storing completed study sessions."""
    conn = get_connection()

    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()


def save_study_session(subject, duration_minutes):
    """Save a completed focus session."""
    if not subject or not subject.strip():
        raise ValueError("Subject cannot be empty.")

    if duration_minutes <= 0:
        raise ValueError("Duration must be greater than zero.")

    conn = get_connection()

    try:
        conn.execute(
            """
            INSERT INTO study_sessions (subject, duration_minutes)
            VALUES (?, ?)
            """,
            (subject.strip(), int(duration_minutes))
        )
        conn.commit()
        return True
    finally:
        conn.close()


def get_study_sessions(limit=50):
    """Retrieve recent completed study sessions."""
    conn = get_connection()

    try:
        rows = conn.execute(
            """
            SELECT id, subject, duration_minutes, completed_at
            FROM study_sessions
            ORDER BY completed_at DESC
            LIMIT ?
            """,
            (int(limit),)
        ).fetchall()

        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_study_statistics():
    """Return overall and subject-wise study statistics."""
    conn = get_connection()

    try:
        overall = conn.execute("""
            SELECT
                COUNT(*) AS completed_sessions,
                COALESCE(SUM(duration_minutes), 0) AS total_minutes
            FROM study_sessions
        """).fetchone()

        subjects = conn.execute("""
            SELECT
                subject,
                COUNT(*) AS sessions,
                SUM(duration_minutes) AS total_minutes
            FROM study_sessions
            GROUP BY subject
            ORDER BY total_minutes DESC
        """).fetchall()

        today = conn.execute("""
            SELECT
                COUNT(*) AS sessions,
                COALESCE(SUM(duration_minutes), 0) AS total_minutes
            FROM study_sessions
            WHERE DATE(completed_at, 'localtime') = DATE('now', 'localtime')
        """).fetchone()

        return {
            "completed_sessions": overall["completed_sessions"],
            "total_minutes": overall["total_minutes"],
            "today_sessions": today["sessions"],
            "today_minutes": today["total_minutes"],
            "subjects": [dict(row) for row in subjects]
        }
    finally:
        conn.close()


create_study_table()
