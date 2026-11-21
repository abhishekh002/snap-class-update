import streamlit as st
from supabase import PostgrestAPIError as APIError

from src.database.db import create_attendance


@st.dialog("Attendance Review", width="large")
def attendance_result_dialog(df, logs, photo_analysis=None):
    st.markdown("""
        <style>
            .attendance-review-intro {
                margin:.2rem 0 1rem;padding:1.1rem 1.25rem;border:1px solid #dce1d6;
                border-left:5px solid #829a79;border-radius:16px;
                background:linear-gradient(125deg,#e6ecdf,#fffefa);
            }
            .attendance-review-intro .eyebrow {
                color:#829a79;font-size:.7rem;font-weight:700;letter-spacing:.13em;text-transform:uppercase;
            }
            .attendance-review-intro h3 { margin:.28rem 0 .35rem!important;color:#385844!important;font-size:1.3rem!important; }
            .attendance-review-intro p { margin:0;color:#65746a!important;line-height:1.55; }
            [data-testid="stExpander"] { border-color:#dce1d6;border-radius:14px;background:#fffefa; }
        </style>
        <section class="attendance-review-intro">
          <span class="eyebrow">Smart attendance</span>
          <h3>Review the class roll call</h3>
          <p>Check each present and absent result before adding attendance to the class record.</p>
        </section>
    """, unsafe_allow_html=True)

    present_count = sum(bool(entry.get("is_present")) for entry in logs)
    absent_count = max(0, len(logs) - present_count)
    total_count = len(logs)
    metric_cols = st.columns(3)
    with metric_cols[0]:
        st.metric("Present", present_count)
    with metric_cols[1]:
        st.metric("Absent", absent_count)
    with metric_cols[2]:
        st.metric("Students reviewed", total_count)

    if photo_analysis:
        with st.expander("Face analysis by photo"):
            for analysis in photo_analysis:
                st.write(analysis)
    with st.container(border=True):
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
