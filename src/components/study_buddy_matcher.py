import streamlit as st
from supabase import PostgrestAPIError

from src.ai.agent import ask_snapclass_ai


def render_study_buddy_matcher(
    enrolled_subjects: list[dict], student_id: int | str
):
    """
    Renders the AI Study-Buddy Matcher component on the Student Dashboard.
    """
    if not enrolled_subjects:
        return

    st.subheader("AI Study-Buddy Matcher (Peer Learning Network)")
    st.write(
        "Find classmates enrolled in the same subject and generate a shared "
        "study challenge."
    )

    subject_names = [subject["name"] for subject in enrolled_subjects]
    chosen_subject = st.selectbox(
        "Select a subject",
        subject_names,
        key="buddy_subject_select",
    )
    subject = next(
        subject for subject in enrolled_subjects if subject["name"] == chosen_subject
    )

    from src.database.config import supabase

    try:
        response = (
            supabase.table("subject_students")
            .select("student_id, students(student_id, name)")
            .eq("subject_id", subject["subject_id"])
            .execute()
        )
    except PostgrestAPIError as error:
        st.error(f"Could not load classmates: {error.message}")
        return

    peers = []
    for enrollment in response.data or []:
        peer = enrollment.get("students")
        if (
            peer
            and peer.get("student_id") is not None
            and str(peer["student_id"]) != str(student_id)
            and peer.get("name")
        ):
            peers.append(peer["name"])

    st.markdown(f"#### Classmates enrolled in **{chosen_subject}**")
    if peers:
        for peer_name in peers:
            st.markdown(f"- {peer_name}")
    else:
        st.info("There are no other enrolled classmates to show for this subject.")

    st.divider()
    st.markdown("**Generate a collaborative study challenge**")
    st.caption("Create a short paired problem for you and a classmate to solve.")

    if st.button(
        f"Generate challenge for {chosen_subject}",
        key=f"gen_challenge_{subject['subject_id']}",
    ):
        with st.spinner("AI Tutor is creating a collaborative challenge..."):
            prompt = (
                f"Create an engaging, collaborative 5-minute study problem for two students "
                f"enrolled in the subject '{chosen_subject}'. "
                f"Include: 1) The Challenge Scenario, 2) Question for Student A to solve, "
                f"3) Question for Student B to solve, and 4) How their solutions connect."
            )
            st.session_state[f"buddy_challenge_{subject['subject_id']}"] = (
                ask_snapclass_ai(prompt)
            )

    challenge_key = f"buddy_challenge_{subject['subject_id']}"
    if challenge_key in st.session_state:
        st.info(st.session_state[challenge_key])
