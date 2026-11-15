
from models.study_notes_manager import (
    create_folder,
    get_folders,
    save_note,
    get_notes,
    search_notes,
    toggle_favorite,
    get_favorite_notes,
    update_note,
    delete_note,
    delete_folder
)

print("\n========== TESTING STUDY NOTES ==========\n")

# 1. Create a personal folder
folder_id = create_folder("My Test Knowledge")
print("Folder created:", folder_id)

# 2. Create a subfolder
subfolder_id = create_folder(
    "Python Concepts",
    parent_id=folder_id
)
print("Subfolder created:", subfolder_id)

# 3. Display folders
print("\nPersonal folders:")
print(get_folders())

print("\nSubfolders:")
print(get_folders(folder_id))

# 4. Save a note
note_id = save_note(
    title="Python Dictionary",
    content="A dictionary stores data in key-value pairs.",
    folder_id=subfolder_id,
    tags="Python, Dictionary, Programming"
)
print("\nNote saved:", note_id)

# 5. Retrieve notes
print("\nRetrieved notes:")
print(get_notes(folder_id=subfolder_id))

# 6. Search notes
print("\nSearch results:")
print(search_notes("dictionary"))

# 7. Mark note as favourite
toggle_favorite(note_id)
print("\nFavourite notes:")
print(get_favorite_notes())

# 8. Update note
update_note(
    note_id,
    "Python Dictionary Updated",
    "A dictionary stores information as key-value pairs.",
    "Python, Data Structures"
)

print("\nUpdated note:")
print(get_notes(folder_id=subfolder_id))

# 9. Clean up test data
delete_note(note_id)
delete_folder(folder_id)

print("\nTest note and folders deleted.")
print("\n========== TEST COMPLETED ==========")
