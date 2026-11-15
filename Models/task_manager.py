
from database.db import get_connection


# Add a new task
def add_task(title, deadline=None, duration=None,
             importance=3, urgency=3):

    if not title.strip():
        raise ValueError("Task title cannot be empty.")

    if not 1 <= importance <= 5:
        raise ValueError("Importance must be between 1 and 5.")

    if not 1 <= urgency <= 5:
        raise ValueError("Urgency must be between 1 and 5.")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO tasks
        (title, deadline, duration, importance, urgency)
        VALUES (?, ?, ?, ?, ?)
    """, (title, deadline, duration, importance, urgency))

    conn.commit()
    task_id = cursor.lastrowid
    conn.close()

    return task_id


# View all tasks
def get_tasks():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks ORDER BY id DESC")

    tasks = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return tasks


# Mark a task as completed
def complete_task(task_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE tasks
        SET status = 'Completed'
        WHERE id = ?
    """, (task_id,))

    updated = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return updated


# Delete a task
def delete_task(task_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM tasks WHERE id = ?",
        (task_id,)
    )

    deleted = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return deleted
