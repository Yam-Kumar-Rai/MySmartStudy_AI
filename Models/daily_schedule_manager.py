
import uuid
from datetime import datetime, date, time, timedelta

from database.db import get_connection


# ==========================================================
# 1. CREATE DAILY SCHEDULE TABLE
# ==========================================================

def create_daily_schedule_table():

    conn = get_connection()

    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                activity_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                category TEXT DEFAULT 'Personal',
                status TEXT DEFAULT 'Pending',
                reminder_enabled INTEGER DEFAULT 1,
                reminder_token TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()

    finally:
        conn.close()


# ==========================================================
# 2. VALIDATE DATE AND TIME
# ==========================================================

def _format_date(value):

    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")

    try:
        return datetime.strptime(
            str(value), "%Y-%m-%d"
        ).strftime("%Y-%m-%d")

    except ValueError:
        raise ValueError("Date must use YYYY-MM-DD format.")


def _format_time(value):

    if isinstance(value, time):
        return value.strftime("%H:%M")

    try:
        return datetime.strptime(
            str(value), "%H:%M"
        ).strftime("%H:%M")

    except ValueError:
        raise ValueError("Time must use HH:MM format.")


def _validate_activity(
    title,
    activity_date,
    start_time,
    end_time
):

    if not title or not title.strip():
        raise ValueError("Activity title is required.")

    activity_date = _format_date(activity_date)
    start_time = _format_time(start_time)
    end_time = _format_time(end_time)

    if end_time <= start_time:
        raise ValueError(
            "Ending time must be later than starting time."
        )

    return activity_date, start_time, end_time


# ==========================================================
# 3. CHECK FOR OVERLAPPING ACTIVITIES
# ==========================================================

def _check_overlap(
    conn,
    activity_date,
    start_time,
    end_time,
    exclude_id=None
):

    query = """
        SELECT id, title, start_time, end_time
        FROM daily_schedule
        WHERE activity_date = ?
          AND start_time < ?
          AND end_time > ?
    """

    params = [
        activity_date,
        end_time,
        start_time
    ]

    if exclude_id is not None:
        query += " AND id != ?"
        params.append(exclude_id)

    existing = conn.execute(
        query, params
    ).fetchone()

    if existing:

        raise ValueError(
            f"This time overlaps with "
            f"'{existing['title']}' "
            f"({existing['start_time']} - "
            f"{existing['end_time']})."
        )


# ==========================================================
# 4. CANCEL OLD ACTIVITY REMINDERS
# ==========================================================

def _cancel_activity_reminders(activity_id, token):

    if not token:
        return

    conn = get_connection()

    try:

        prefix = f"daily-{activity_id}-{token}-%"

        conn.execute("""
            UPDATE notifications
            SET status = 'cancelled'
            WHERE dedupe_key LIKE ?
              AND status = 'pending'
        """, (prefix,))

        conn.commit()

    except Exception as error:

        print(
            "Could not cancel old activity reminders:",
            error
        )

    finally:
        conn.close()


# ==========================================================
# 5. SCHEDULE ACTIVITY REMINDERS
# ==========================================================

def _schedule_activity_reminders(activity):

    if not activity["reminder_enabled"]:
        return

    try:

        from models.notification_manager import schedule_notification

        activity_id = activity["id"]
        token = activity["reminder_token"]

        activity_datetime = datetime.strptime(
            f"{activity['activity_date']} "
            f"{activity['start_time']}",
            "%Y-%m-%d %H:%M"
        )

        now = datetime.now()

        # Five-minute reminder
        reminder_time = activity_datetime - timedelta(
            minutes=5
        )

        if reminder_time > now:

            schedule_notification(
                title=f"Upcoming: {activity['title']}",
                message=(
                    f"Your activity starts in 5 minutes. "
                    f"Get ready for {activity['title']}!"
                ),
                scheduled_at=reminder_time,
                notification_type="daily_schedule",
                dedupe_key=(
                    f"daily-{activity_id}-{token}-before"
                )
            )

        # Activity start reminder
        if activity_datetime > now:

            schedule_notification(
                title=f"Time to start: {activity['title']}",
                message=(
                    f"Your scheduled activity starts now. "
                    f"Planned until {activity['end_time']}."
                ),
                scheduled_at=activity_datetime,
                notification_type="daily_schedule",
                dedupe_key=(
                    f"daily-{activity_id}-{token}-start"
                )
            )

    except Exception as error:

        print(
            "Could not schedule activity reminders:",
            error
        )


# ==========================================================
# 6. ADD NEW ACTIVITY
# ==========================================================

def add_activity(
    title,
    activity_date,
    start_time,
    end_time,
    description="",
    category="Personal",
    reminder_enabled=True
):

    activity_date, start_time, end_time = (
        _validate_activity(
            title,
            activity_date,
            start_time,
            end_time
        )
    )

    token = uuid.uuid4().hex

    conn = get_connection()

    try:

        _check_overlap(
            conn,
            activity_date,
            start_time,
            end_time
        )

        cursor = conn.execute("""
            INSERT INTO daily_schedule (
                title,
                description,
                activity_date,
                start_time,
                end_time,
                category,
                reminder_enabled,
                reminder_token
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            title.strip(),
            description.strip(),
            activity_date,
            start_time,
            end_time,
            category,
            int(reminder_enabled),
            token
        ))

        activity_id = cursor.lastrowid

        conn.commit()

    finally:
        conn.close()

    activity = get_activity(activity_id)

    if activity:
        _schedule_activity_reminders(activity)

    return activity_id


# ==========================================================
# 7. GET ONE ACTIVITY
# ==========================================================

def get_activity(activity_id):

    conn = get_connection()

    try:

        row = conn.execute("""
            SELECT *
            FROM daily_schedule
            WHERE id = ?
        """, (activity_id,)).fetchone()

        return dict(row) if row else None

    finally:
        conn.close()


# ==========================================================
# 8. GET DAILY ACTIVITIES
# ==========================================================

def get_activities(activity_date=None):

    conn = get_connection()

    try:

        if activity_date is not None:

            activity_date = _format_date(activity_date)

            rows = conn.execute("""
                SELECT *
                FROM daily_schedule
                WHERE activity_date = ?
                ORDER BY start_time ASC
            """, (activity_date,)).fetchall()

        else:

            rows = conn.execute("""
                SELECT *
                FROM daily_schedule
                ORDER BY activity_date ASC, start_time ASC
            """).fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()


# ==========================================================
# 9. UPDATE ACTIVITY
# ==========================================================

def update_activity(
    activity_id,
    title,
    activity_date,
    start_time,
    end_time,
    description="",
    category="Personal",
    reminder_enabled=True
):

    activity_date, start_time, end_time = (
        _validate_activity(
            title,
            activity_date,
            start_time,
            end_time
        )
    )

    old_activity = get_activity(activity_id)

    if not old_activity:
        raise ValueError("Activity not found.")

    _cancel_activity_reminders(
        activity_id,
        old_activity.get("reminder_token")
    )

    new_token = uuid.uuid4().hex

    conn = get_connection()

    try:

        _check_overlap(
            conn,
            activity_date,
            start_time,
            end_time,
            exclude_id=activity_id
        )

        conn.execute("""
            UPDATE daily_schedule
            SET title = ?,
                description = ?,
                activity_date = ?,
                start_time = ?,
                end_time = ?,
                category = ?,
                reminder_enabled = ?,
                reminder_token = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            title.strip(),
            description.strip(),
            activity_date,
            start_time,
            end_time,
            category,
            int(reminder_enabled),
            new_token,
            activity_id
        ))

        conn.commit()

    finally:
        conn.close()

    activity = get_activity(activity_id)

    if activity:
        _schedule_activity_reminders(activity)

    return True


# ==========================================================
# 10. COMPLETE ACTIVITY
# ==========================================================

def complete_activity(activity_id):

    conn = get_connection()

    try:

        cursor = conn.execute("""
            UPDATE daily_schedule
            SET status = 'Completed',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (activity_id,))

        conn.commit()

        return cursor.rowcount > 0

    finally:
        conn.close()


# ==========================================================
# 11. DELETE ACTIVITY
# ==========================================================

def delete_activity(activity_id):

    activity = get_activity(activity_id)

    if not activity:
        return False

    _cancel_activity_reminders(
        activity_id,
        activity.get("reminder_token")
    )

    conn = get_connection()

    try:

        cursor = conn.execute("""
            DELETE FROM daily_schedule
            WHERE id = ?
        """, (activity_id,))

        conn.commit()

        return cursor.rowcount > 0

    finally:
        conn.close()


# ==========================================================
# 12. CREATE TABLE WHEN MODULE IS IMPORTED
# ==========================================================

create_daily_schedule_table()
