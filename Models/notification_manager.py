
from datetime import datetime, timedelta
from database.db import get_connection


def create_notification_table():
    """Create notification and alarm-control tables."""

    conn = get_connection()

    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                notification_type TEXT DEFAULT 'general',
                scheduled_at TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                dedupe_key TEXT UNIQUE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                sent_at TEXT
            )
        """)

        # Shared control between Streamlit and reminder_service.py
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alarm_control (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                is_active INTEGER DEFAULT 0,
                stop_requested INTEGER DEFAULT 0,
                notification_id INTEGER,
                started_at TEXT
            )
        """)

        conn.execute("""
            INSERT OR IGNORE INTO alarm_control
            (id, is_active, stop_requested)
            VALUES (1, 0, 0)
        """)

        conn.commit()

    finally:
        conn.close()


def schedule_notification(
    title,
    message,
    scheduled_at,
    notification_type="general",
    dedupe_key=None
):
    """Save a notification for the background service."""

    if not title or not message:
        raise ValueError("Title and message are required.")

    if isinstance(scheduled_at, datetime):
        scheduled_at = scheduled_at.strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()

    try:
        conn.execute("""
            INSERT OR IGNORE INTO notifications
            (title, message, notification_type, scheduled_at, dedupe_key)
            VALUES (?, ?, ?, ?, ?)
        """, (
            title,
            message,
            notification_type,
            scheduled_at,
            dedupe_key
        ))

        conn.commit()
        return True

    finally:
        conn.close()


def schedule_study_timer(subject, duration_minutes):
    if not subject or not subject.strip():
        raise ValueError("Please enter a subject.")

    if duration_minutes <= 0:
        raise ValueError("Duration must be greater than zero.")

    finish_time = datetime.now().replace(microsecond=0)
    finish_time += timedelta(minutes=int(duration_minutes))

    return schedule_notification(
        title="Study session completed! 🎉",
        message=f"Your {subject.strip()} study session has finished.",
        scheduled_at=finish_time,
        notification_type="study",
        dedupe_key=f"study-{finish_time.strftime('%Y%m%d%H%M%S')}"
    )


def schedule_break_timer(duration_minutes):
    if duration_minutes <= 0:
        raise ValueError("Duration must be greater than zero.")

    finish_time = datetime.now().replace(microsecond=0)
    finish_time += timedelta(minutes=int(duration_minutes))

    return schedule_notification(
        title="Break completed! ⏰",
        message="Your break is over. Time to get back to studying!",
        scheduled_at=finish_time,
        notification_type="break",
        dedupe_key=f"break-{finish_time.strftime('%Y%m%d%H%M%S')}"
    )


def get_due_notifications():
    """Return notifications whose scheduled time has arrived."""

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()

    try:
        rows = conn.execute("""
            SELECT *
            FROM notifications
            WHERE status = 'pending'
              AND scheduled_at <= ?
            ORDER BY scheduled_at ASC
        """, (now,)).fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()


def mark_notification_sent(notification_id):
    conn = get_connection()

    try:
        conn.execute("""
            UPDATE notifications
            SET status = 'sent',
                sent_at = ?
            WHERE id = ?
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            notification_id
        ))

        conn.commit()

    finally:
        conn.close()


def get_notifications(limit=30):
    conn = get_connection()

    try:
        rows = conn.execute("""
            SELECT *
            FROM notifications
            ORDER BY created_at DESC
            LIMIT ?
        """, (int(limit),)).fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()


def cancel_notification(notification_id):
    """Cancel a pending notification, not its sent history."""

    conn = get_connection()

    try:
        conn.execute("""
            UPDATE notifications
            SET status = 'cancelled'
            WHERE id = ? AND status = 'pending'
        """, (notification_id,))

        conn.commit()

    finally:
        conn.close()


# ==========================================================
# ALARM CONTROL
# ==========================================================

def begin_alarm(notification_id):
    """Tell the application that an alarm is ringing."""

    conn = get_connection()

    try:
        conn.execute("""
            UPDATE alarm_control
            SET is_active = 1,
                stop_requested = 0,
                notification_id = ?,
                started_at = ?
            WHERE id = 1
        """, (
            notification_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()

    finally:
        conn.close()


def end_alarm():
    """Mark the alarm as no longer active."""

    conn = get_connection()

    try:
        conn.execute("""
            UPDATE alarm_control
            SET is_active = 0,
                stop_requested = 0,
                notification_id = NULL
            WHERE id = 1
        """)

        conn.commit()

    finally:
        conn.close()


def request_stop_alarm():
    """Request the background service to stop ringing."""

    conn = get_connection()

    try:
        conn.execute("""
            UPDATE alarm_control
            SET stop_requested = 1
            WHERE id = 1 AND is_active = 1
        """)

        conn.commit()

    finally:
        conn.close()


def alarm_stop_requested():
    """Check whether the user requested the alarm to stop."""

    conn = get_connection()

    try:
        row = conn.execute("""
            SELECT stop_requested
            FROM alarm_control
            WHERE id = 1
        """).fetchone()

        return bool(row["stop_requested"]) if row else False

    finally:
        conn.close()


def get_alarm_status():
    """Get the current alarm status for the Streamlit interface."""

    conn = get_connection()

    try:
        row = conn.execute("""
            SELECT is_active, stop_requested, notification_id
            FROM alarm_control
            WHERE id = 1
        """).fetchone()

        if row:
            return dict(row)

        return {
            "is_active": 0,
            "stop_requested": 0,
            "notification_id": None
        }

    finally:
        conn.close()


create_notification_table()
