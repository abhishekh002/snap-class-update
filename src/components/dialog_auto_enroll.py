import streamlit as st
from supabase import PostgrestAPIError as APIError

from src.database.db import enroll_student_to_subject
from src.database.config import supabase


@st.dialog("Quick Enrollment")
def auto_enroll_dialog(subject_code):
    student_data = st.session_state.get("student_data")
    student_id = student_data.get("student_id") if isinstance(student_data, dict) else None
    if student_id is None:
        st.error("Sign in as a student to enroll in this subject.")
        if st.button("Close", key="auto_enroll_missing_student_close"):
            st.query_params.pop("join-code", None)
            st.rerun()
        return

    try:
        res = (
            supabase.table("subjects")
            .select("subject_id, name")
            .eq("subject_code", subject_code)
            .limit(1)
            .execute()
        )
    except APIError as error:
        st.error(f"Could not look up this subject: {error.message}")
        return
    if not res.data:
        st.error("Subject code not found.")
        if st.button("Close", key="auto_enroll_not_found_close"):
            st.query_params.pop("join-code", None)
            st.rerun()
        return
    subject = res.data[0]

    try:
        check = (
            supabase.table("subject_students")
            .select("student_id")
            .eq("subject_id", subject["subject_id"])
            .eq("student_id", student_id)
            .limit(1)
            .execute()
        )
    except APIError as error:
        st.error(f"Could not check your enrollment: {error.message}")
        return
    if check.data:
        st.info("You are already enrolled.")
        if st.button("Got it!", key="auto_enroll_already_enrolled"):
            st.query_params.pop("join-code", None)
            st.rerun()
        return

    st.markdown(f'Would you like to enroll in **{subject["name"]}**?')

    col1, col2 = st.columns(2)

    with col1:
        if st.button("No thanks", key="auto_enroll_cancel"):
            st.query_params.pop("join-code", None)
            st.rerun()
     

    with col2:
        if st.button("Yes, enroll now!", type="primary", width="stretch", key="auto_enroll_confirm"):
            try:
                enrolled = enroll_student_to_subject(student_id, subject["subject_id"])
            except APIError as error:
                st.error(f"Could not enroll in this subject: {error.message}")
                return

            if not enrolled:
                st.info("You are already enrolled.")
            else:
                st.success("Joined successfully!")
            st.query_params.pop("join-code", None)
            st.rerun()