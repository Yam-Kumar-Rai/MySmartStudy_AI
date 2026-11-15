
from models.study_notes_manager import (
    get_modules,
    get_study_connection,
    initialize_study_database
)

initialize_study_database()

conn = get_study_connection()

print("\nDATABASE TABLES:")

tables = conn.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
""").fetchall()

for table in tables:
    print("-", table["name"])

print("\nACADEMIC MODULES:")

modules = get_modules()

for module in modules:
    print(module)

print("\nTOTAL MODULES:", len(modules))

conn.close()
