import streamlit as st
from supabase import PostgrestAPIError as APIError

from src.database.db import enroll_student_to_subject, get_subject_by_code


@st.dialog("Enroll in a Subject")
def enroll_dialog():
    student_data = st.session_state.get("student_data")
    if not isinstance(student_data, dict) or student_data.get("student_id") is None:
        st.error("Sign in as a student to enroll in a subject.")
        return

    st.write("Enter the subject code provided by your teacher to enroll.")
    join_code = st.text_input(
        "Subject code",
        placeholder="E.g. CS101",
        key="student_enroll_subject_code",
    )

    if st.button("Enroll now", type="primary", width="stretch"):
        if not join_code.strip():
            st.warning("Please enter a subject code.")
            return

        try:
            subject = get_subject_by_code(join_code.strip())
            if subject is None:
                st.warning("No subject found with that code.")
                return

            enrollment = enroll_student_to_subject(
                student_data["student_id"],
                subject["subject_id"],
            )
        except APIError as error:
            st.error(f"Could not enroll in the subject: {error.message}")
            return

        if enrollment is None:
            st.warning("You are already enrolled in this subject.")
        elif enrollment:
            st.success(f"Successfully enrolled in {subject['name']}!")
            st.rerun()
        else:
            st.error("Could not enroll in the subject. Please try again.")
    