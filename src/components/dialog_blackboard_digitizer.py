import io
import streamlit as st
from PIL import Image
from src.ai.digitizer import digitize_blackboard_image
from src.components.markdown_utils import sanitize_mermaid_blocks
from src.database.notes_db import create_note
from src.database.db import get_teacher_subject

@st.dialog("📷 Blackboard-to-Notes Auto-Digitizer", width="large")
def blackboard_digitizer_dialog():
    teacher = st.session_state.get("teacher_data")
    if not teacher:
        st.error("Please login as a teacher.")
        return

    teacher_id = teacher.get("teacher_id", teacher.get("id"))
    subjects = get_teacher_subject(teacher_id)
    if not subjects:
        st.warning("Please create at least one subject first.")
        return

    st.markdown("""
        <div style="margin:.25rem 0 1rem;padding:1rem 1.1rem;border:1px solid #dce1d6;
                    border-left:4px solid #b97453;border-radius:14px;
                    background:linear-gradient(125deg,#efe3d7,#fffefa);color:#526457;line-height:1.6;">
          <strong style="color:#385844">From board photo to class notes</strong><br>
          Upload or capture a board image. SmartClass AI transcribes equations into LaTeX and code into Markdown,
          then saves the study guide for your enrolled students.
        </div>
    """, unsafe_allow_html=True)

    subj_map = {f"{s['name']} ({s['subject_code']})": s for s in subjects}
    chosen_label = st.selectbox("Assign to Subject *", list(subj_map.keys()))
    chosen_subject = subj_map[chosen_label]

    title = st.text_input("Study Guide Title *", placeholder="e.g. Lecture 4: Tree Traversal & Recursion")

    upload_mode = st.radio("Input method:", ["Upload Image File", "Use Device Camera"], horizontal=True)
    image_file = None

    if upload_mode == "Upload Image File":
        image_file = st.file_uploader("Upload Blackboard Photo", type=["png", "jpg", "jpeg", "webp"])
    else:
        image_file = st.camera_input("Take Blackboard Snapshot")

    if image_file:
        st.image(image_file, caption="Blackboard Snapshot Preview", width=360)

    if st.button("✨ Digitize & Publish to Enrolled Students", type="primary", width="stretch"):
        if not title.strip():
            st.error("Please enter a title for this note.")
            return
        if not image_file:
            st.error("Please take or upload a blackboard photo first.")
            return

        with st.spinner("🧠 Gemini Vision is transcribing handwriting, LaTeX formulas, and diagrams..."):
            try:
                img_bytes = image_file.getvalue()
                transcription = digitize_blackboard_image(img_bytes, mime_type="image/jpeg")

                note = create_note(
                    subject_id=chosen_subject.get("subject_id", chosen_subject.get("id")),
                    subject_name=chosen_subject["name"],
                    teacher_id=teacher_id,
                    teacher_name=teacher.get("name", "Teacher"),
                    title=title.strip() + " (AI Blackboard Notes)",
                    description=sanitize_mermaid_blocks(transcription),
                    uploaded_file=image_file,
                )

                st.session_state["last_digitized_preview"] = sanitize_mermaid_blocks(transcription)
                st.toast(f"✅ Digitized study guide '{title}' published to enrolled students!")
                st.rerun()
            except Exception as e:
                st.error(f"Digitization failed: {e}")

    if "last_digitized_preview" in st.session_state:
        st.divider()
        st.subheader("📄 Latest Digitized Study Guide Preview")
        st.markdown(
            sanitize_mermaid_blocks(st.session_state["last_digitized_preview"])
        )
