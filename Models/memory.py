
import sqlite3
from database.db import get_connection


# ==========================================
# 1. CREATE MEMORY TABLES
# ==========================================

def create_memory_tables():
    """Create tables for persistent user memory and conversation history."""

    conn = get_connection()

    try:
        cursor = conn.cursor()

        # Store important user preferences and information
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_key TEXT UNIQUE NOT NULL,
                memory_value TEXT NOT NULL,
                category TEXT DEFAULT 'preference',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Store previous conversations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_message TEXT NOT NULL,
                assistant_response TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()

    finally:
        conn.close()


# ==========================================
# 2. SAVE USER MEMORY
# ==========================================

def save_memory(memory_key, memory_value, category="preference"):
    """Save a new memory or update an existing memory."""

    memory_key = str(memory_key).strip()
    memory_value = str(memory_value).strip()
    category = str(category).strip()

    if not memory_key or not memory_value:
        raise ValueError("Memory key and value cannot be empty.")

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO user_memories
            (memory_key, memory_value, category)
            VALUES (?, ?, ?)

            ON CONFLICT(memory_key)
            DO UPDATE SET
                memory_value = excluded.memory_value,
                category = excluded.category,
                updated_at = CURRENT_TIMESTAMP
        """, (memory_key, memory_value, category))

        conn.commit()

        return True

    finally:
        conn.close()


# ==========================================
# 3. RETRIEVE ALL MEMORIES
# ==========================================

def get_memories(category=None):
    """Retrieve all saved memories, optionally by category."""

    conn = get_connection()

    try:
        cursor = conn.cursor()

        if category:
            cursor.execute("""
                SELECT * FROM user_memories
                WHERE category = ?
                ORDER BY updated_at DESC
            """, (category,))
        else:
            cursor.execute("""
                SELECT * FROM user_memories
                ORDER BY updated_at DESC
            """)

        return [dict(row) for row in cursor.fetchall()]

    finally:
        conn.close()


# ==========================================
# 4. SEARCH MEMORIES
# ==========================================

def search_memories(keyword):
    """Search saved memories by key or value."""

    keyword = str(keyword).strip()

    if not keyword:
        return []

    conn = get_connection()

    try:
        cursor = conn.cursor()

        search_term = f"%{keyword}%"

        cursor.execute("""
            SELECT * FROM user_memories
            WHERE memory_key LIKE ?
            OR memory_value LIKE ?
            ORDER BY updated_at DESC
        """, (search_term, search_term))

        return [dict(row) for row in cursor.fetchall()]

    finally:
        conn.close()


# ==========================================
# 5. SAVE CONVERSATION HISTORY
# ==========================================

def save_conversation(user_message, assistant_response):
    """Save a user message and its assistant response."""

    if not str(user_message).strip():
        raise ValueError("User message cannot be empty.")

    if not str(assistant_response).strip():
        raise ValueError("Assistant response cannot be empty.")

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO conversation_history
            (user_message, assistant_response)
            VALUES (?, ?)
        """, (user_message, assistant_response))

        conn.commit()

        return cursor.lastrowid

    finally:
        conn.close()


# ==========================================
# 6. RETRIEVE RECENT CONVERSATIONS
# ==========================================

def get_recent_conversations(limit=5):
    """Retrieve the most recent conversations."""

    if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
        raise ValueError("Limit must be a positive integer.")

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM conversation_history
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))

        return [dict(row) for row in cursor.fetchall()]

    finally:
        conn.close()


# ==========================================
# 7. INITIALIZE MEMORY DATABASE
# ==========================================

create_memory_tables()
