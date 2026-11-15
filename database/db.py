
import sqlite3
from pathlib import Path

# Database location
DB_PATH = Path(__file__).resolve().parent / "smartplan.db"


# Connect to database
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# Create database tables
def create_tables():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            deadline TEXT,
            duration INTEGER,
            importance INTEGER DEFAULT 3,
            urgency INTEGER DEFAULT 3,
            status TEXT DEFAULT 'Pending'
        )
    """)

    conn.commit()
    conn.close()

    print("SmartPlan AI database created successfully!")


if __name__ == "__main__":
    create_tables()
