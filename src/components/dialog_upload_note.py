import streamlit as st
from postgrest.exceptions import APIError
from storage3.exceptions import StorageApiError

from src.database.notes_db import create_note
from src.database.db import get_teacher_subject

@st.dialog("Upload Course Notes", width="large")
def upload_note_dialog():
    teacher = st.session_state.get("teacher_data")
    if not teacher:
        st.error("Please login as a teacher.")
        return

    teacher_id = teacher.get("teacher_id") or teacher.get("id")
    if teacher_id is None:
        st.error("Your teacher account is missing an ID. Please log in again.")
        return

    subjects = get_teacher_subject(teacher_id)

    if not subjects:
        st.warning("You must create at least one subject before uploading notes.")
        return

    st.markdown("""
        <div style="margin:.25rem 0 1rem;padding:1rem 1.1rem;border:1px solid #dce1d6;
                    border-left:4px solid #829a79;border-radius:14px;
                    background:linear-gradient(125deg,#e6ecdf,#fffefa);color:#526457;line-height:1.55;">
          Choose a class, give the material a clear title, and add a short summary so students know what it covers.
        </div>
    """, unsafe_allow_html=True)

    subject_options = {f"{s['name']} ({s['subject_code']})": s for s in subjects}
    selected_label = st.selectbox("Select Subject", list(subject_options.keys()))
    selected_subject = subject_options[selected_label]

    title = st.text_input("Note Title *", placeholder="e.g. Chapter 3: Data Structures & Trees")
    description = st.text_area(
        "Description / Key Points",
        placeholder="Brief overview or key topics covered in these notes...",
        help="Optional text summary for your students.",
    )

    uploaded_file = st.file_uploader(
        "Attach Study Material (PDF, DOCX, TXT, Images, etc.)",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg", "ppt", "pptx", "zip"],
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Cancel", width="stretch"):
            st.rerun()

    with col2:
        if st.button("Upload Course Notes", type="primary", width="stretch"):
            if not title.strip():
                st.error("Please enter a title for the note.")
                return

            try:
                new_note = create_note(
                    subject_id=selected_subject["subject_id"],
                    subject_name=selected_subject["name"],
                    teacher_id=teacher_id,
                    teacher_name=teacher.get("name", "Teacher"),
                    title=title,
                    description=description,
                    uploaded_file=uploaded_file,
                )
                st.toast(f"✅ Note '{title}' uploaded successfully!")
                st.rerun()
            except (
                APIError,
                PermissionError,
                RuntimeError,
                StorageApiError,
                ValueError,
                OSError,
            ) as e:
                st.error(f"Failed to upload note: {e}")
