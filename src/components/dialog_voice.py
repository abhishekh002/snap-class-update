from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from postgrest.exceptions import APIError

from src.database.config import supabase
from src.database.db import create_attendance
from src.pipelines.voice_pipeline import process_bulk_audio


@st.dialog("Voice Attendance")
def voice_attendance_dialog(selected_subject_id):
    pending_key = f"voice_attendance_results_{selected_subject_id}"
    pending = st.session_state.get(pending_key)

    if pending is None:
        st.write(
            "Record classroom audio while students say, "
            "“I am present,” so the AI can identify enrolled voice profiles."
        )
        audio_data = st.audio_input("Record classroom audio")

        if st.button(
            "Analyze Audio",
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
                st.warning("No students are enrolled in this course.")
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

    st.write("Review attendance before confirming.")
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
