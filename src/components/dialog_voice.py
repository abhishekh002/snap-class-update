from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from supabase import PostgrestAPIError as APIError

from src.database.config import supabase
from src.database.db import create_attendance
from src.pipelines.voice_pipeline import process_bulk_audio


@st.dialog("Voice Attendance", width="large")
def voice_attendance_dialog(selected_subject_id):
    pending_key = f"voice_attendance_results_{selected_subject_id}"
    pending = st.session_state.get(pending_key)

    if pending is None:
        st.markdown("""
            <style>
                .voice-attendance-intro {
                    margin:.2rem 0 1rem;padding:1.1rem 1.25rem;border:1px solid #dce1d6;
                    border-left:5px solid #829a79;border-radius:16px;
                    background:linear-gradient(125deg,#e6ecdf,#fffefa);
                }
                .voice-attendance-intro .eyebrow {
                    color:#829a79;font-size:.7rem;font-weight:700;letter-spacing:.13em;text-transform:uppercase;
                }
                .voice-attendance-intro h3 { margin:.28rem 0 .35rem!important;color:#385844!important;font-size:1.3rem!important; }
                .voice-attendance-intro p { margin:0;color:#65746a!important;line-height:1.55; }
                .voice-recording-card {
                    padding:1rem;border:1px solid #dce1d6;border-radius:16px;background:#fffefa;
                }
            </style>
            <section class="voice-attendance-intro">
              <span class="eyebrow">Hands-free check-in</span>
              <h3>Record the class roll call</h3>
              <p>Ask students to say “I am present.” SmartClass AI compares the recording with enrolled voice profiles.</p>
            </section>
            <div class="voice-recording-card">
              <strong style="color:#385844">Before you record</strong>
              <p style="margin:.35rem 0 0;color:#65746a;line-height:1.5">Keep the microphone near the class, reduce background noise, and leave a short pause between names.</p>
            </div>
        """, unsafe_allow_html=True)
        audio_data = st.audio_input("Record classroom audio")
        if audio_data:
            st.success("Recording ready to analyze.")
        else:
            st.caption("Your recording stays in this attendance flow until you analyze or close the dialog.")

        if st.button(
            "Analyze voice attendance",
            width="stretch",
            type="primary",
            key=f"analyze_voice_audio_{selected_subject_id}",
        ):
            if audio_data is None:
                st.warning("Record classroom audio before analyzing.")
                return

            try:
                enrolled_response = (
                    supabase.table("subject_students")
                    .select("student_id, students(student_id, name, voice_embedding)")
                    .eq("subject_id", selected_subject_id)
                    .execute()
                )
            except APIError as error:
                st.error(f"Could not load enrolled students: {error.message}")
                return

            enrolled_students = [
                node["students"]
                for node in enrolled_response.data or []
                if isinstance(node.get("students"), dict)
            ]
            if not enrolled_students:
                st.warning("No students are enrolled in this subject.")
                return

            candidates = {
                str(student["student_id"]): student["voice_embedding"]
                for student in enrolled_students
                if student.get("voice_embedding") is not None
            }
            if not candidates:
                st.error("No enrolled students have registered voice profiles.")
                return

            try:
                with st.spinner("Processing audio..."):
                    detected_scores = process_bulk_audio(
                        audio_data.getvalue(),
                        candidates,
                    )
            except (RuntimeError, ValueError) as error:
                st.error(str(error))
                return

            logged_at = datetime.now(timezone.utc).isoformat()
            results = []
            logs = []
            for student in enrolled_students:
                student_id = str(student["student_id"])
                score = detected_scores.get(student_id)
                is_present = score is not None
                results.append(
                    {
                        "Name": student["name"],
                        "ID": student["student_id"],
                        "Voice Match": f"{score:.2f}" if is_present else "-",
                        "Status": "✅ Present" if is_present else "❌ Absent",
                    }
                )
                logs.append(
                    {
                        "student_id": student["student_id"],
                        "subject_id": selected_subject_id,
                        "logged_at": logged_at,
                        "is_present": is_present,
                    }
                )

            st.session_state[pending_key] = {
                "results": results,
                "logs": logs,
            }
            st.rerun()
        return

    st.markdown("""
        <style>
            .voice-attendance-intro {
                margin:.2rem 0 1rem;padding:1.1rem 1.25rem;border:1px solid #dce1d6;
                border-left:5px solid #829a79;border-radius:16px;
                background:linear-gradient(125deg,#e6ecdf,#fffefa);
            }
            .voice-attendance-intro .eyebrow {
                color:#829a79;font-size:.7rem;font-weight:700;letter-spacing:.13em;text-transform:uppercase;
            }
            .voice-attendance-intro h3 { margin:.28rem 0 .35rem!important;color:#385844!important;font-size:1.3rem!important; }
            .voice-attendance-intro p { margin:0;color:#65746a!important;line-height:1.55; }
        </style>
        <section class="voice-attendance-intro">
          <span class="eyebrow">Review before saving</span>
          <h3>Voice match results</h3>
          <p>Check the detected attendance below, then confirm to save it to the class record.</p>
        </section>
    """, unsafe_allow_html=True)
    present_count = sum(bool(row["is_present"]) for row in pending["logs"])
    total_count = len(pending["logs"])
    metric_cols = st.columns(2)
    with metric_cols[0]:
        st.metric("Voice matches", present_count)
    with metric_cols[1]:
        st.metric("No voice match", max(0, total_count - present_count))
    with st.container(border=True):
        st.dataframe(pd.DataFrame(pending["results"]), hide_index=True, width="stretch")
    save_col, discard_col = st.columns(2)

    with save_col:
        if st.button(
            "Confirm & Save",
            width="stretch",
            type="primary",
            key=f"save_voice_attendance_{selected_subject_id}",
        ):
            try:
                saved_rows = create_attendance(pending["logs"])
            except APIError as error:
                st.error(f"Could not save attendance: {error.message}")
                return
            except ValueError as error:
                st.error(str(error))
                return

            if not saved_rows:
                st.error("Supabase did not confirm that attendance records were saved.")
                return

            st.session_state.pop(pending_key, None)
            st.toast(f"Saved attendance for {len(saved_rows)} student(s).")
            st.rerun()

    with discard_col:
        if st.button(
            "Discard",
            width="stretch",
            key=f"discard_voice_attendance_{selected_subject_id}",
        ):
            st.session_state.pop(pending_key, None)
            st.rerun()
