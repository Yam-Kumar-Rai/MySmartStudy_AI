
import streamlit as st

from study_notes_manager import  (
    get_modules,
    get_notes,
    get_note,
    search_notes,
    save_note,
    update_note,
    delete_note,
    toggle_favorite,
    get_favorite_notes
)


# =====================================================
# PAGE STYLING
# =====================================================


def apply_study_notes_style():

    st.markdown("""
    <style>

    /* Main text */
    [data-testid="stAppViewContainer"] h1,
    [data-testid="stAppViewContainer"] h2,
    [data-testid="stAppViewContainer"] h3,
    [data-testid="stAppViewContainer"] p,
    [data-testid="stAppViewContainer"] label,
    [data-testid="stAppViewContainer"] .stMarkdown {
        color: #F8FAFC !important;
    }

    /* Text area background and text */
    [data-testid="stTextArea"] textarea {
        background-color: #111827 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        caret-color: #60A5FA !important;
        border: 1px solid #475569 !important;
        border-radius: 10px !important;
    }

    /* Text area placeholder */
    [data-testid="stTextArea"] textarea::placeholder {
        color: #94A3B8 !important;
        -webkit-text-fill-color: #94A3B8 !important;
        opacity: 1 !important;
    }

    /* Text input */
    [data-testid="stTextInput"] input {
        background-color: #111827 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        caret-color: #60A5FA !important;
        border: 1px solid #475569 !important;
        border-radius: 8px !important;
    }

    /* Text input placeholder */
    [data-testid="stTextInput"] input::placeholder {
        color: #94A3B8 !important;
        -webkit-text-fill-color: #94A3B8 !important;
        opacity: 1 !important;
    }

    /* Select box */
    [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        background-color: #111827 !important;
        color: #FFFFFF !important;
        border-color: #475569 !important;
    }

    [data-testid="stSelectbox"] div[data-baseweb="select"] span {
        color: #FFFFFF !important;
    }

    /* Dropdown options */
    [role="listbox"] [role="option"] {
        background-color: #111827 !important;
        color: #FFFFFF !important;
    }

    /* Checkbox */
    [data-testid="stCheckbox"] label,
    [data-testid="stCheckbox"] p {
        color: #F8FAFC !important;
    }

    /* Note cards */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: rgba(148, 163, 184, 0.22);
        border-radius: 12px;
    }

    /* Captions */
    [data-testid="stCaptionContainer"] {
        color: #AAB8CC !important;
    }

    /* Buttons */
    [data-testid="stButton"] button {
        border-radius: 8px;
        font-weight: 600;
    }

    </style>
    """, unsafe_allow_html=True)


# =====================================================
# NOTE DISPLAY
# =====================================================

def display_notes(notes, key_prefix="notes"):

    if not notes:
        st.info("No notes here yet. Save your first note above.")
        return

    for note in notes:

        note_id = note["id"]

        with st.container(border=True):

            col1, col2 = st.columns([5, 1])

            with col1:
                st.markdown(f"### {note['title']}")

            with col2:
                if note.get("is_favorite"):
                    st.markdown("⭐")
                else:
                    st.markdown("☆")

            content = note.get("content", "")

            st.write(content)

            if note.get("tags"):
                st.caption(f"Tags: {note['tags']}")

            if note.get("module_id"):

                st.caption(
                    f"📘 Academic module: {note.get('module_name', 'Module note')}"
                )

            if note.get("folder_id"):

                st.caption(
                    f"📁 Previously saved in: {note.get('folder_name', 'Knowledge Library')}"
                )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "✏️ Edit",
                    key=f"{key_prefix}_edit_{note_id}",
                    use_container_width=True
                ):

                    st.session_state["editing_note_id"] = note_id
                    st.rerun()

            with col2:

                favorite_label = (
                    "★ Important"
                    if note.get("is_favorite")
                    else "☆ Mark Important"
                )

                if st.button(
                    favorite_label,
                    key=f"{key_prefix}_favorite_{note_id}",
                    use_container_width=True
                ):

                    toggle_favorite(note_id)
                    st.rerun()


# =====================================================
# QUICK NOTE EDITOR
# =====================================================

def render_note_editor():

    editing_id = st.session_state.get("editing_note_id")

    if not editing_id:
        return

    note = get_note(editing_id)

    if note is None:

        st.session_state.pop("editing_note_id", None)
        st.warning("This note no longer exists.")
        return

    st.divider()

    st.subheader("✏️ Edit Note")

    with st.container(border=True):

        with st.form(f"edit_note_form_{editing_id}"):

            title = st.text_input(
                "Title",
                value=note["title"]
            )

            content = st.text_area(
                "Your note",
                value=note["content"],
                height=220
            )

            tags = st.text_input(
                "Tags",
                value=note.get("tags") or "",
                placeholder="Python, AI, Important..."
            )

            col1, col2 = st.columns(2)

            with col1:

                save_clicked = st.form_submit_button(
                    "Save Changes",
                    use_container_width=True
                )

            with col2:

                cancel_clicked = st.form_submit_button(
                    "Cancel",
                    use_container_width=True
                )

        if save_clicked:

            if not content.strip():

                st.error("Note content cannot be empty.")

            else:

                if not title.strip():
                    title = content.strip().split("\n")[0][:55]

                update_note(
                    editing_id,
                    title.strip(),
                    content.strip(),
                    tags.strip()
                )

                st.session_state.pop("editing_note_id", None)

                st.success("Note updated successfully!")
                st.rerun()

        if cancel_clicked:

            st.session_state.pop("editing_note_id", None)
            st.rerun()

        st.divider()

        if st.button(
            "🗑️ Delete This Note",
            key=f"delete_note_{editing_id}",
            use_container_width=True
        ):

            st.session_state["confirm_delete_note"] = editing_id

        if st.session_state.get("confirm_delete_note") == editing_id:

            st.warning(
                "Are you sure you want to permanently delete this note?"
            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "Yes, Delete",
                    key=f"confirm_delete_{editing_id}",
                    use_container_width=True
                ):

                    delete_note(editing_id)

                    st.session_state.pop("editing_note_id", None)
                    st.session_state.pop("confirm_delete_note", None)

                    st.success("Note deleted.")
                    st.rerun()

            with col2:

                if st.button(
                    "Cancel",
                    key=f"cancel_delete_{editing_id}",
                    use_container_width=True
                ):

                    st.session_state.pop("confirm_delete_note", None)
                    st.rerun()


# =====================================================
# QUICK NOTE CREATION
# =====================================================

def render_quick_note_form():

    st.subheader("✍️ Write Something Important")

    st.caption(
        "Save definitions, research findings, ideas, coding tips, "
        "useful facts, and anything you want to remember."
    )

    modules = get_modules()

    module_options = {
        "Quick Notes": None
    }

    for module in modules:

        module_options[module["module_name"]] = module["id"]

    with st.container(border=True):

        with st.form("quick_note_form", clear_on_submit=True):

            content = st.text_area(
                "Your note",
                placeholder=(
                    "Start writing here...\n\n"

                ),
                height=190
            )

            col1, col2 = st.columns(2)

            with col1:

                selected_location = st.selectbox(
                    "Save under",
                    list(module_options.keys())
                )

            with col2:

                tags = st.text_input(
                    "Tags (optional)",
                    placeholder="Python, AI, Research..."
                )

            important = st.checkbox(
                "⭐ Mark this as an important note"
            )

            submitted = st.form_submit_button(
                "💾 Save Note",
                use_container_width=True
            )

        if submitted:

            if not content.strip():

                st.error("Please write something before saving.")

            else:

                first_line = content.strip().split("\n")[0].strip()

                if not first_line:
                    first_line = content.strip()

                title = first_line[:55]

                if len(first_line) > 55:
                    title += "..."

                module_id = module_options[selected_location]

                note_id = save_note(
                    title=title,
                    content=content.strip(),
                    module_id=module_id,
                    tags=tags.strip()
                )

                if important:
                    toggle_favorite(note_id)

                st.success("Your note has been saved successfully!")
                st.rerun()


# =====================================================
# MAIN STUDY NOTES PAGE
# =====================================================

def render_study_notes_page():

    apply_study_notes_style()

    st.title("📚 Study Notes")

    st.caption(
        "A simple space to collect, organize, and remember what you learn."
    )

    st.divider()

    # -------------------------------------------------
    # QUICK NOTE CREATION
    # -------------------------------------------------

    render_quick_note_form()

    # -------------------------------------------------
    # EDITOR
    # -------------------------------------------------

    render_note_editor()

    st.divider()

    # -------------------------------------------------
    # SEARCH
    # -------------------------------------------------

    st.subheader("🔍 Find Your Notes")

    search_query = st.text_input(
        "Search",
        placeholder="Search by title, content, or tags...",
        key="study_notes_search"
    )

    if search_query.strip():

        results = search_notes(search_query.strip())

        st.markdown(
            f"### Search Results ({len(results)})"
        )

        display_notes(
            results,
            key_prefix="search"
        )

        st.divider()

    # -------------------------------------------------
    # NOTES SUMMARY
    # -------------------------------------------------

    all_notes = get_notes()
    important_notes = get_favorite_notes()

    total_notes = len(all_notes)
    total_important = len(important_notes)

    col1, col2 = st.columns(2)

    with col1:

        with st.container(border=True):

            st.caption("TOTAL NOTES")
            st.markdown(f"## {total_notes}")

    with col2:

        with st.container(border=True):

            st.caption("IMPORTANT NOTES")
            st.markdown(f"## ⭐ {total_important}")

    st.divider()

    # -------------------------------------------------
    # NOTE COLLECTIONS
    # -------------------------------------------------

    tab1, tab2, tab3 = st.tabs([
        "📝 All Notes",
        "⭐ Important Notes",
        "🎓 Academic Modules"
    ])

    # =================================================
    # TAB 1: ALL NOTES
    # =================================================

    with tab1:

        st.subheader("All Your Notes")

        if all_notes:

            display_notes(
                all_notes,
                key_prefix="all"
            )

        else:

            st.info(
                "You haven't saved any notes yet. "
                "Use the quick note editor above to get started."
            )

    # =================================================
    # TAB 2: IMPORTANT NOTES
    # =================================================

    with tab2:

        st.subheader("⭐ Your Important Notes")

        if important_notes:

            display_notes(
                important_notes,
                key_prefix="important"
            )

        else:

            st.info(
                "No important notes yet. "
                "Mark a note as important when saving or viewing it."
            )

    # =================================================
    # TAB 3: ACADEMIC MODULES
    # =================================================

    with tab3:

        st.subheader("🎓 Academic Module Notes")

        modules = get_modules()

        if modules:

            module_options = {
                module["module_name"]: module["id"]
                for module in modules
            }

            selected_module = st.selectbox(
                "Choose a module",
                list(module_options.keys()),
                key="academic_notes_module"
            )

            module_id = module_options[selected_module]

            module_notes = get_notes(
                module_id=module_id
            )

            st.markdown(f"### 📘 {selected_module}")

            if module_notes:

                display_notes(
                    module_notes,
                    key_prefix=f"module_{module_id}"
                )

            else:

                st.info(
                    "No notes saved under this module yet."
                )

        else:

            st.info("No academic modules are available.")
