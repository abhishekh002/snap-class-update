from html import escape

import streamlit as st
from src.components.markdown_utils import sanitize_mermaid_blocks
from supabase import PostgrestAPIError

from src.ai.agent import ask_snapclass_ai


@st.dialog("Collaborative study challenge", width="large")
def _show_study_challenge(subject_name: str, challenge: str):
    st.caption(f"AI study challenge · {subject_name} · 5 minutes")
    st.markdown(sanitize_mermaid_blocks(challenge))


def render_study_buddy_matcher(
    enrolled_subjects: list[dict], student_id: int | str
):
    """
    Renders the AI Study-Buddy Matcher component on the Student Dashboard.
    """
    if not enrolled_subjects:
        return

    st.markdown("""
        <style>
            .study-buddy-hero {
                margin: .2rem 0 1rem;
                padding: 20px 22px;
                border: 1px solid #d5e1d9;
                border-left: 5px solid #315b54;
                border-radius: 17px;
                background: linear-gradient(120deg,#fffefa,#eaf1eb);
                box-shadow: 0 8px 22px rgba(32,58,67,.06);
            }
            .study-buddy-hero span {
                color: #bd7654;
                font-size: .68rem;
                font-weight: 700;
                letter-spacing: .14em;
                text-transform: uppercase;
            }
            .study-buddy-hero h2 {
                margin: 5px 0 5px;
                color: #26382e;
                font-size: clamp(1.25rem,2.4vw,1.65rem);
                line-height: 1.25;
            }
            .study-buddy-hero p {
                margin: 0;
                color: #65746a;
                line-height: 1.5;
            }
            .study-buddy-peer {
                display: inline-block;
                margin: 3px 5px 3px 0;
                padding: 7px 11px;
                border: 1px solid #d5e1d9;
                border-radius: 999px;
                background: #f2f5ef;
                color: #385844;
                font-size: .88rem;
                font-weight: 600;
            }
        </style>
        <section class="study-buddy-hero">
          <span>Learn together</span>
          <h2>AI Study-Buddy Matcher (Peer Learning Network)</h2>
          <p>Find classmates in your subjects and practice together with an AI-made challenge.</p>
        </section>
    """, unsafe_allow_html=True)

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

    st.markdown(f"#### Classmates in {chosen_subject}")
    if peers:
        peer_pills = "".join(
            f'<span class="study-buddy-peer">{escape(str(peer_name))}</span>'
            for peer_name in peers
        )
        st.markdown(peer_pills, unsafe_allow_html=True)
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
        _show_study_challenge(
            chosen_subject,
            st.session_state[f"buddy_challenge_{subject['subject_id']}"],
        )

    challenge_key = f"buddy_challenge_{subject['subject_id']}"
    if challenge_key in st.session_state:
        st.caption("Your latest collaborative challenge is saved for this session.")
        if st.button(
            "Read latest challenge",
            icon=":material/open_in_full:",
            key=f"open_challenge_{subject['subject_id']}",
        ):
            _show_study_challenge(chosen_subject, st.session_state[challenge_key])
