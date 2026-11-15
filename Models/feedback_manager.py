
import sqlite3
from datetime import datetime

from database.db import get_connection


# ==========================================
# 1. CREATE FEEDBACK TABLE
# ==========================================

def create_feedback_table():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT,
            agent_response TEXT,
            rating INTEGER NOT NULL,
            feedback_comment TEXT,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ==========================================
# 2. SAVE USER FEEDBACK
# ==========================================

def save_feedback(
    user_message,
    agent_response,
    rating,
    feedback_comment=""
):

    if rating not in (1, -1):
        raise ValueError("Rating must be 1 (positive) or -1 (negative).")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO agent_feedback (
            user_message,
            agent_response,
            rating,
            feedback_comment,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        user_message,
        agent_response,
        rating,
        feedback_comment,
        datetime.now().isoformat(timespec="seconds")
    ))

    conn.commit()
    feedback_id = cursor.lastrowid
    conn.close()

    return feedback_id


# ==========================================
# 3. RETRIEVE FEEDBACK
# ==========================================

def get_recent_feedback(limit=10):

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM agent_feedback
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    feedback = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return feedback


# ==========================================
# 4. FEEDBACK STATISTICS
# ==========================================

def get_feedback_statistics():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) AS total_feedback,
            SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) AS positive,
            SUM(CASE WHEN rating = -1 THEN 1 ELSE 0 END) AS negative
        FROM agent_feedback
    """)

    result = cursor.fetchone()
    conn.close()

    return {
        "total": result[0] or 0,
        "positive": result[1] or 0,
        "negative": result[2] or 0
    }
