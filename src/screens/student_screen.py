
from src.database.notes_db import get_note_download, get_notes_for_student
from src.components.dialog_ai_chat import ai_chat_dialog
from src.components.dialog_interactive_reader import interactive_reader_dialog
from src.components.gpa_forecaster import render_gpa_forecaster
from src.components.study_buddy_matcher import render_study_buddy_matcher
from src.database.assessments_db import get_student_dashboard_assessments

import numpy as np
import streamlit as st
from PIL import Image
from supabase import PostgrestAPIError as APIError

from src.components.footer import footer_dashboard
from src.components.header import header_dashboard
from src.database.db import (
    create_student,
    enroll_student_to_subject,
    get_all_students,
    get_student_attendance,
    get_students_subjects,
    update_student_voice_embedding,
    unenroll_student_to_subject,
)
from src.pipelines.face_pipeline import (
    get_face_embeddings,
    predict_attendance,
    train_classifier,
)
from src.pipelines.voice_pipeline import get_voice_embedding
from src.ui.base_layout import style_background_dashboard, style_base_layout

from src.components.dialog_enroll import enroll_dialog
from src.components.subject_card import Subject_card

def student_dashboard():
    student_data = st.session_state.get("student_data")
    if student_data is None:
        st.session_state["is_logged_in"] = False
        st.session_state["user_role"] = None
        st.rerun()
        return
    student_id = student_data["student_id"]

    c1, c2 = st.columns(2, vertical_alignment="center", gap="large")
    with c1:
        header_dashboard()
    with c2:
        st.subheader(f"Good to see you, {student_data['name']}!")
        b1, b2 = st.columns(2)
        with b1:
            if st.button("🤖 Ask AI Tutor", key="student_top_ai_btn", icon=":material/smart_toy:", width="stretch"):
                ai_chat_dialog()
        with b2:
            if st.button("Logout", type="secondary", key="loginbackbtn", width="stretch"):
                st.session_state["is_logged_in"] = False
                st.session_state["user_role"] = None
                st.session_state.pop("student_data", None)
                st.rerun()

    try:
        student_notes = get_notes_for_student(student_id)
    except (APIError, PermissionError, RuntimeError) as error:
        st.error(f"Could not load course notes: {error}")
        student_notes = []
    subjects_tab, assessments_tab, learning_hub_tab = st.tabs(
        ["Enrolled Subjects", "Assessments", "Learning Hub"]
    )
    with learning_hub_tab:
        notes_tab, impact_tab, study_buddy_tab, voice_profile_tab = st.tabs(
            [
                "Course Notes",
                "Grade Impact Simulator",
                "Study Buddy Matcher",
                "Voice Profile",
            ]
        )

    with voice_profile_tab:
        st.subheader(
            "Set up voice attendance"
            if not student_data.get("voice_embedding")
            else "Update voice profile"
        )
        st.write(
            "Record a short phrase in a quiet place. Your voice profile will be "
            "saved to this student account."
        )
        voice_recording = st.audio_input(
            "Record your voice",
            key=f"student_voice_setup_{student_id}",
        )
        if st.button(
            "Save voice profile",
            type="primary",
            key=f"save_student_voice_{student_id}",
        ):
            if voice_recording is None:
                st.warning("Record your voice before saving.")
            else:
                try:
                    voice_embedding = get_voice_embedding(voice_recording.getvalue())
                    if voice_embedding is None:
                        st.error("Could not create a voice profile. Please record again.")
                    elif update_student_voice_embedding(student_id, voice_embedding):
                        st.session_state.student_data["voice_embedding"] = voice_embedding
                        st.toast("Voice profile saved.")
                        st.rerun()
                    else:
                        st.error("The voice profile was not saved. Please try again.")
                except APIError as error:
                    st.error(f"Could not save your voice profile: {error.message}")
                except (RuntimeError, ValueError) as error:
                    st.error(f"Could not process the recording: {error}")

    with assessments_tab:
        st.subheader("📝 Assessments for Your Subjects")
        try:
            assessments = get_student_dashboard_assessments(
                student_id, student_notes
            )
        except (APIError, PermissionError, RuntimeError) as error:
            st.error(f"Could not load assessments: {error}")
        else:
            if not assessments:
                st.info("No assessments have been assigned to your enrolled subjects yet.")
            else:
                seen_key = f"seen_assessment_ids_{student_id}"
                seen_ids = set(st.session_state.get(seen_key, []))
                new_assessments = [
                    assessment
                    for assessment in assessments
                    if str(assessment["id"]) not in seen_ids
                ]
                if new_assessments:
                    st.info(
                        f"You have {len(new_assessments)} new assessment"
                        f"{'s' if len(new_assessments) != 1 else ''}."
                    )
                    if st.button(
                        "Clear assessment notice",
                        key=f"clear_assessment_notice_{student_id}",
                    ):
                        seen_ids.update(
                            str(assessment["id"]) for assessment in assessments
                        )
                        st.session_state[seen_key] = list(seen_ids)
                        st.rerun()

                notes_by_id = {str(note["id"]): note for note in student_notes}
                for assessment in assessments:
                    with st.container(border=True):
                        st.markdown(f"**{assessment['title']}**")
                        st.caption(
                            f"{assessment['subject_name']} · "
                            f"Due: {assessment['due_date']} · "
                            f"Maximum score: {assessment['max_score']}"
                        )
                        if assessment.get("instructions"):
                            st.write(assessment["instructions"])
                        note = notes_by_id.get(str(assessment["note_id"]))
                        if note and st.button(
                            "Open note to view or submit",
                            key=f"student_dashboard_assessment_{assessment['id']}",
                        ):
                            interactive_reader_dialog(note)
                        elif not note:
                            st.info(
                                "Open this subject's course notes to access the assessment."
                            )

    with subjects_tab:
        enroll_col, _ = st.columns(2)
        with enroll_col:
            st.subheader("Your enrolled subjects")
            if st.button("Enroll in a subject", type="primary", width="stretch"):
                enroll_dialog()

        st.divider()
        with st.spinner("Loading your enrolled subjects..."):
            subjects = get_students_subjects(student_id)
            logs = get_student_attendance(student_id)
        stats_map = {}
        for log in logs:
            subject_id = log.get("subject_id", log.get("subjects_id"))
            if subject_id is None:
                continue

            subject_stats = stats_map.setdefault(
                str(subject_id), {"total": 0, "attended": 0}
            )
            subject_stats["total"] += 1
            if log.get("is_present"):
                subject_stats["attended"] += 1

        if not subjects:
            st.info("You are not enrolled in any subjects yet.")

        # Build stats list for GPA forecaster and study buddy matcher
        subjects_stats_list = []
        enrolled_subjects_data = []
        for subject_node in subjects:
            subj = subject_node.get("subjects")
            if not subj:
                continue
            s_id = subj["subject_id"]
            stat = stats_map.get(str(s_id), {"total": 0, "attended": 0})
            subjects_stats_list.append({
                "subject_id": s_id,
                "name": subj["name"],
                "code": subj["subject_code"],
                "section": subj.get("section", ""),
                "total": stat["total"],
                "attended": stat["attended"],
            })
            enrolled_subjects_data.append(subj)

        cols = st.columns(2)
        for i, subject_node in enumerate(subjects):
            subject = subject_node.get("subjects")
            if not subject:
                continue

            subject_id = subject["subject_id"]
            stats = stats_map.get(str(subject_id), {"total": 0, "attended": 0})

            def unenroll_button(current_subject_id=subject_id, subject_name=subject["name"]):
                if st.button(
                    "Unenroll from this subject",
                    type="tertiary",
                    width="stretch",
                    icon=":material/person_remove:",
                    key=f"unenroll_{current_subject_id}",
                ):
                    unenroll_student_to_subject(student_id, current_subject_id)
                    st.toast(f"You have been unenrolled from {subject_name}.")
                    st.rerun()

            with cols[i % 2]:
                Subject_card(
                    name=subject["name"],
                    code=subject["subject_code"],
                    section=subject["section"],
                    stats=[
                        ("📅", "Total", stats["total"]),
                        ("✅", "Attended", stats["attended"]),
                    ],
                    footer_callback=unenroll_button,
                )

    with impact_tab:
        if subjects_stats_list:
            render_gpa_forecaster(subjects_stats_list)
        else:
            st.info("Enroll in a subject to use the attendance simulator.")

    with study_buddy_tab:
        if enrolled_subjects_data:
            render_study_buddy_matcher(enrolled_subjects_data, student_id)
        else:
            st.info("Enroll in a subject to find study partners.")

    with notes_tab:
        c_nhdr, c_nai = st.columns([2, 1], vertical_alignment="center")
        with c_nhdr:
            st.subheader("📚 Course Notes & Study Materials")
            st.caption("Materials uploaded by your teachers for your enrolled subjects.")
        with c_nai:
            if st.button("🤖 Ask AI Tutor", icon=":material/smart_toy:", key="student_notes_ai_btn", width="stretch"):
                ai_chat_dialog()

        if not student_notes:
            st.info("No study notes have been uploaded yet for your enrolled subjects.")
        else:
            notes_by_subject = {}
            for n in student_notes:
                notes_by_subject.setdefault(n["subject_name"], []).append(n)

            for s_name, s_notes in notes_by_subject.items():
                st.markdown(f"#### 📖 {s_name}")
                for note in s_notes:
                    with st.container(border=True):
                        c_ntext, c_nactions = st.columns([3, 1])
                        with c_ntext:
                            st.markdown(f"**{note['title']}**")
                            if note.get("description"):
                                st.write(note["description"])
                            st.caption(f"Teacher: {note.get('teacher_name')} | Uploaded: {note.get('created_at')} | {note.get('file_size_kb', 0)} KB")
                        with c_nactions:
                            if st.button("📖 Interactive Reader", key=f"read_student_{note['id']}", width="stretch", type="primary", icon=":material/menu_book:"):
                                interactive_reader_dialog(note)
                            download = get_note_download(note)
                            if download:
                                data_bytes, file_name = download
                                st.download_button(
                                    label="⬇️ Download",
                                    data=data_bytes,
                                    file_name=file_name,
                                    key=f"dl_student_{note['id']}",
                                    width="stretch",
                                )
                            if st.button("💡 Ask AI Tutor", key=f"ask_ai_{note['id']}", width="stretch"):
                                ai_chat_dialog(initial_prompt=f"Can you explain the key concepts of '{note['title']}' for the subject '{note['subject_name']}'? Overview: {note.get('description', '')}")

    footer_dashboard()
def student_screen():
    style_background_dashboard()
    style_base_layout()

    if st.session_state.get("student_data") is not None:
        student_dashboard()
        return

    col1, col2 = st.columns(2, vertical_alignment="center", gap="large")
    with col1:
        header_dashboard()
    with col2:
        if st.button(
            "Back to Home",
            type="secondary",
            key="loginbackbtn",
        ):
            st.session_state["login_type"] = None
            st.rerun()

    st.header("Sign in with Face ID", text_alignment="center")
    st.space()
    st.space()

    show_registration = False
    photo = st.camera_input("Position your face in the center")

    if photo is not None:
        image = np.array(Image.open(photo))

        with st.spinner("AI is scanning..."):
            detected_students, _, num_faces = predict_attendance(image)

        if num_faces == 0:
            st.warning("No face detected. Please try again.")
        elif num_faces > 1:
            st.warning("Multiple faces found. Please make sure only your face is visible.")
        elif detected_students:
            student_id = next(iter(detected_students))
            students = get_all_students()
            student = next(
                (
                    record
                    for record in students
                    if str(record.get("student_id")) == str(student_id)
                ),
                None,
            )

            if student is None:
                st.warning(
                    "The recognized face has no matching student profile. "
                    "Register a new profile below."
                )
                show_registration = True
            else:
                st.session_state.is_logged_in = True
                st.session_state.user_role = "student"
                st.session_state.student_data = student
                st.toast(f"Welcome back, {student['name']}!")
                st.rerun()
        else:
            st.info("Face not recognized. You can register a new student profile.")
            show_registration = True

    if show_registration:
        with st.container(border=True):
            st.header("Register a New Profile")
            new_name = st.text_input(
                "Enter your name",
                placeholder="E.g. Abhishekh Tiwari",
            )

            st.subheader("Optional: Voice Enrollment")
            st.info("Enroll your voice for voice-only attendance.")
            audio_data = st.audio_input(
                "Record a short phrase, such as “I am present. My name is ...”"
            )

            if st.button("Create Account", type="primary"):
                if not new_name.strip():
                    st.warning("Please enter your name.")
                elif photo is None:
                    st.error("Please capture your face before registering.")
                else:
                    with st.spinner("Creating profile..."):
                        encodings = get_face_embeddings(image)

                        if not encodings:
                            st.error(
                                "Could not capture facial features. Please take another photo."
                            )
                        else:
                            face_embedding = encodings[0].tolist()
                            voice_embedding = (
                                get_voice_embedding(audio_data.getvalue())
                                if audio_data is not None
                                else None
                            )
                            response_data = create_student(
                                new_name.strip(),
                                face_embedding=face_embedding,
                                voice_embedding=voice_embedding,
                            )

                            if response_data:
                                train_classifier()
                                st.session_state.is_logged_in = True
                                st.session_state.user_role = "student"
                                st.session_state.student_data = response_data[0]
                                st.toast(f"Profile created! Hi, {new_name.strip()}!")
                                st.rerun()
                            else:
                                st.error("Could not create the student profile.")

    footer_dashboard()
