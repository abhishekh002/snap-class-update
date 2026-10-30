import streamlit as st
from postgrest.exceptions import APIError

from src.database.db import create_attendance


@st.dialog("Attendance Reports")
def attendance_result_dialog(df, logs):
    st.write("Please review attendance before confirming.")
    st.dataframe(df, hide_index=True, width="stretch")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Discard", width="stretch"):
            st.rerun()

    with col2:
        if st.button("Confirm & Save", width="stretch", type="primary"):
            try:
                saved_rows = create_attendance(logs)
                if not saved_rows:
                    st.error("Supabase did not confirm that attendance records were saved.")
                    return

                st.session_state.attendance_images = []
                st.toast(f"Saved attendance for {len(saved_rows)} student(s).")
                st.rerun()
            except APIError as error:
                st.error(f"Could not save attendance: {error.message}")
            except ValueError as error:
                st.error(str(error))