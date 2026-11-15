
import sqlite3
from pathlib import Path


# =====================================================
# DATABASE CONFIGURATION
# =====================================================

BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "database"
DB_PATH = DB_DIR / "study_notes.db"

DB_DIR.mkdir(parents=True, exist_ok=True)


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def fetch_all(query, params=()):
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def fetch_one(query, params=()):
    with get_connection() as conn:
        row = conn.execute(query, params).fetchone()
        return dict(row) if row else None


# =====================================================
# DATABASE INITIALIZATION AND MIGRATION
# =====================================================

def initialize_study_database():

    with get_connection() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS study_modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_name TEXT NOT NULL UNIQUE,
                description TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_name TEXT NOT NULL,
                parent_id INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id)
                    REFERENCES knowledge_folders(id)
                    ON DELETE CASCADE
            )
        """)

        existing = conn.execute("""
            SELECT sql
            FROM sqlite_master
            WHERE type = 'table'
            AND name = 'study_notes'
        """).fetchone()

        if existing is None:

            conn.execute("""
                CREATE TABLE study_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    module_id INTEGER,
                    folder_id INTEGER,
                    tags TEXT DEFAULT '',
                    is_favorite INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (module_id)
                        REFERENCES study_modules(id)
                        ON DELETE CASCADE,
                    FOREIGN KEY (folder_id)
                        REFERENCES knowledge_folders(id)
                        ON DELETE CASCADE
                )
            """)

        elif "CHECK" in (existing["sql"] or "").upper():

            # Upgrade the old table so notes can exist
            # without a module or a folder.
            conn.execute("PRAGMA foreign_keys = OFF")

            conn.execute("DROP TABLE IF EXISTS study_notes_new")

            conn.execute("""
                CREATE TABLE study_notes_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    module_id INTEGER,
                    folder_id INTEGER,
                    tags TEXT DEFAULT '',
                    is_favorite INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (module_id)
                        REFERENCES study_modules(id)
                        ON DELETE CASCADE,
                    FOREIGN KEY (folder_id)
                        REFERENCES knowledge_folders(id)
                        ON DELETE CASCADE
                )
            """)

            conn.execute("""
                INSERT INTO study_notes_new (
                    id,
                    title,
                    content,
                    module_id,
                    folder_id,
                    tags,
                    is_favorite,
                    created_at,
                    updated_at
                )
                SELECT
                    id,
                    title,
                    content,
                    module_id,
                    folder_id,
                    tags,
                    is_favorite,
                    created_at,
                    updated_at
                FROM study_notes
            """)

            conn.execute("DROP TABLE study_notes")

            conn.execute("""
                ALTER TABLE study_notes_new
                RENAME TO study_notes
            """)

            conn.execute("PRAGMA foreign_keys = ON")

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_notes_module
            ON study_notes(module_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_notes_folder
            ON study_notes(folder_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_notes_favorite
            ON study_notes(is_favorite)
        """)

        # Keep the five existing academic modules.
        for i in range(1, 6):
            conn.execute("""
                INSERT OR IGNORE INTO study_modules (module_name)
                VALUES (?)
            """, (f"Module {i}",))

    print("Study Notes database initialized successfully!")


# =====================================================
# ACADEMIC MODULE FUNCTIONS
# =====================================================

def create_module(module_name, description=""):

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO study_modules (
                module_name,
                description
            )
            VALUES (?, ?)
        """, (module_name, description))

        return cursor.lastrowid


def get_modules():

    return fetch_all("""
        SELECT *
        FROM study_modules
        ORDER BY id
    """)


def update_module(module_id, module_name, description=""):

    with get_connection() as conn:
        conn.execute("""
            UPDATE study_modules
            SET module_name = ?,
                description = ?
            WHERE id = ?
        """, (module_name, description, module_id))


def delete_module(module_id):

    with get_connection() as conn:
        conn.execute("""
            DELETE FROM study_modules
            WHERE id = ?
        """, (module_id,))


# =====================================================
# KNOWLEDGE FOLDER FUNCTIONS
# Kept for compatibility with existing saved folders.
# =====================================================

def create_folder(folder_name, parent_id=None):

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO knowledge_folders (
                folder_name,
                parent_id
            )
            VALUES (?, ?)
        """, (folder_name, parent_id))

        return cursor.lastrowid


def get_folders(parent_id=None):

    if parent_id is None:
        return fetch_all("""
            SELECT *
            FROM knowledge_folders
            WHERE parent_id IS NULL
            ORDER BY folder_name
        """)

    return fetch_all("""
        SELECT *
        FROM knowledge_folders
        WHERE parent_id = ?
        ORDER BY folder_name
    """, (parent_id,))


def get_folder(folder_id):

    return fetch_one("""
        SELECT *
        FROM knowledge_folders
        WHERE id = ?
    """, (folder_id,))


def update_folder(folder_id, folder_name):

    with get_connection() as conn:
        conn.execute("""
            UPDATE knowledge_folders
            SET folder_name = ?
            WHERE id = ?
        """, (folder_name, folder_id))


def delete_folder(folder_id):

    with get_connection() as conn:
        conn.execute("""
            DELETE FROM knowledge_folders
            WHERE id = ?
        """, (folder_id,))


# =====================================================
# NOTE FUNCTIONS
# =====================================================

def save_note(
    title,
    content,
    module_id=None,
    folder_id=None,
    tags=""
):

    if not content or not content.strip():
        raise ValueError("Note content cannot be empty.")

    if not title or not title.strip():
        title = content.strip().split("\n")[0][:55]

    with get_connection() as conn:

        cursor = conn.execute("""
            INSERT INTO study_notes (
                title,
                content,
                module_id,
                folder_id,
                tags
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            title.strip(),
            content.strip(),
            module_id,
            folder_id,
            tags.strip()
        ))

        return cursor.lastrowid


def get_note(note_id):

    return fetch_one("""
        SELECT *
        FROM study_notes
        WHERE id = ?
    """, (note_id,))


def get_notes(
    module_id=None,
    folder_id=None,
    favorites_only=False
):

    query = """
        SELECT *
        FROM study_notes
        WHERE 1 = 1
    """

    params = []

    if module_id is not None:
        query += " AND module_id = ?"
        params.append(module_id)

    if folder_id is not None:
        query += " AND folder_id = ?"
        params.append(folder_id)

    if favorites_only:
        query += " AND is_favorite = 1"

    query += " ORDER BY updated_at DESC, id DESC"

    return fetch_all(query, tuple(params))


def update_note(
    note_id,
    title,
    content,
    tags=""
):

    if not title or not title.strip():
        title = content.strip().split("\n")[0][:55]

    with get_connection() as conn:
        conn.execute("""
            UPDATE study_notes
            SET title = ?,
                content = ?,
                tags = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            title.strip(),
            content.strip(),
            tags.strip(),
            note_id
        ))


def delete_note(note_id):

    with get_connection() as conn:
        conn.execute("""
            DELETE FROM study_notes
            WHERE id = ?
        """, (note_id,))


# =====================================================
# SEARCH
# =====================================================

def search_notes(keyword):

    search_term = f"%{keyword.strip()}%"

    return fetch_all("""
        SELECT
            study_notes.*,
            study_modules.module_name,
            knowledge_folders.folder_name
        FROM study_notes
        LEFT JOIN study_modules
            ON study_notes.module_id = study_modules.id
        LEFT JOIN knowledge_folders
            ON study_notes.folder_id = knowledge_folders.id
        WHERE
            study_notes.title LIKE ?
            OR study_notes.content LIKE ?
            OR study_notes.tags LIKE ?
        ORDER BY study_notes.updated_at DESC
    """, (search_term, search_term, search_term))


# =====================================================
# IMPORTANT / FAVOURITE NOTES
# =====================================================

def toggle_favorite(note_id):

    with get_connection() as conn:
        conn.execute("""
            UPDATE study_notes
            SET is_favorite =
                CASE
                    WHEN is_favorite = 1 THEN 0
                    ELSE 1
                END,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (note_id,))


def get_favorite_notes():

    return get_notes(favorites_only=True)


# =====================================================
# INITIALIZE DATABASE
# =====================================================

initialize_study_database()
