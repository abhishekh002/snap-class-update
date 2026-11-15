import io
import streamlit as st
from PIL import Image
from src.ai.digitizer import digitize_blackboard_image
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

    st.write(
        "Snap or upload a photo of the classroom blackboard/whiteboard. "
        "Gemini AI will automatically transcribe equations into **LaTeX**, code into **Markdown**, "
        "and publish a clean study guide for your enrolled students!"
    )

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

                # Create text file from transcription
                txt_bytes = transcription.encode("utf-8")
                class MockUpload:
                    def __init__(self, name, data):
                        self.name = name
                        self.data = data
                    def getvalue(self):
                        return self.data

                safe_title = "".join(c if c.isalnum() else "_" for c in title.strip()[:25])
                mock_file = MockUpload(f"{safe_title}_digitized_notes.md", txt_bytes)

                note = create_note(
                    subject_id=chosen_subject.get("subject_id", chosen_subject.get("id")),
                    subject_name=chosen_subject["name"],
                    teacher_id=teacher_id,
                    teacher_name=teacher.get("name", "Teacher"),
                    title=title.strip() + " (AI Blackboard Notes)",
                    description=f"Auto-digitized blackboard notes with LaTeX & Markdown.\n\n" + transcription[:280] + "...",
                    uploaded_file=mock_file,
                )

                st.session_state["last_digitized_preview"] = transcription
                st.toast(f"✅ Digitized study guide '{title}' published to enrolled students!")
                st.rerun()
            except Exception as e:
                st.error(f"Digitization failed: {e}")

    if "last_digitized_preview" in st.session_state:
        st.divider()
        st.subheader("📄 Latest Digitized Study Guide Preview")
        st.markdown(st.session_state["last_digitized_preview"])
