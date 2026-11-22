
from html import escape

from src.database.notes_db import get_note_download, get_notes_for_student
from src.components.dialog_ai_chat import ai_chat_dialog
from src.components.dialog_interactive_reader import interactive_reader_dialog
from src.components.markdown_utils import sanitize_mermaid_blocks
from src.components.gpa_forecaster import render_gpa_forecaster
from src.components.study_buddy_matcher import render_study_buddy_matcher
from src.database.assessments_db import get_student_dashboard_assessments

import numpy as np
import streamlit as st
from PIL import Image
from supabase import PostgrestAPIError as APIError

from src.components.footer import footer_dashboard
from src.components.header import LOGO_DATA_URI
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

    student_name = escape(str(student_data.get("name") or "Student"))
    student_registration = escape(
        str(student_data.get("registration_number") or "Pending setup")
    )
    logo_column, home_column = st.columns([3, 1], vertical_alignment="center")
    with logo_column:
        st.markdown(f"""
            <div style="display:flex; align-items:center; min-height:74px;">
              <img src="{LOGO_DATA_URI}" alt="SmartClass AI"
                style="display:block; width:min(360px,100%); height:auto;" />
            </div>
        """, unsafe_allow_html=True)
    with home_column:
        if st.button("Back to Home", type="secondary", key="loginbackbtn", width="stretch", icon=":material/home:"):
            st.session_state["is_logged_in"] = False
            st.session_state["user_role"] = None
            st.session_state.pop("student_data", None)
            st.rerun()

    st.markdown("""
        <style>
            .st-key-student_learning_journey {
                box-sizing: border-box;
                width: 100%;
                margin: 0 0 1rem;
                padding: 24px 28px 18px;
                border: 1px solid #31545b;
                border-radius: 22px;
                background: linear-gradient(130deg,#203a43,#315b54 72%,#3c6658);
                box-shadow: 0 14px 30px rgba(32,58,67,.18);
            }
            .st-key-student_learning_journey [data-testid="stMarkdownContainer"] p {
                color: #e1ebe3 !important;
            }
            .st-key-student_top_ai_btn button {
                background: #d8ef9b !important;
                border-color: #d8ef9b !important;
                color: #203a43 !important;
            }
        </style>
    """, unsafe_allow_html=True)
    with st.container(key="student_learning_journey"):
        st.markdown(f"""
            <div style="color:#d8ef9b; font-size:.68rem; font-weight:700;
                letter-spacing:.15em;">YOUR LEARNING JOURNEY</div>
            <div style="margin:10px 0 4px; color:#fffefa; font-size:1.8rem;
                font-weight:700; line-height:1.2;">{student_name}</div>
            <div style="display:inline-block;margin:4px 0 10px;padding:5px 10px;
                border:1px solid #d8ef9b66;border-radius:999px;
                background:#ffffff14;color:#e7f4c4;font-size:.78rem;">
                Registration No. {student_registration}</div>
            <div style="margin:0 0 7px; color:#d8ef9b; font-size:1.05rem;
                font-weight:650; line-height:1.3;">A space to learn and grow</div>
            <p style="margin:0; color:#e1ebe3; font-size:.96rem; line-height:1.55;">
                Pick up where you left off and keep moving forward.</p>
            <div style="display:flex; flex-wrap:wrap; gap:8px; margin-top:16px;">
              <span style="padding:7px 12px; border-radius:999px; background:#ffffff18;
                  color:#fffefa; font-size:.78rem;">My classes</span>
              <span style="padding:7px 12px; border-radius:999px; background:#ffffff18;
                  color:#fffefa; font-size:.78rem;">Assessments</span>
              <span style="padding:7px 12px; border-radius:999px; background:#ffffff18;
                  color:#fffefa; font-size:.78rem;">Study tools</span>
            </div>
        """, unsafe_allow_html=True)
        _, ai_corner = st.columns([5, 1.35])
        with ai_corner:
            if st.button(
                "Ask AI Tutor",
                key="student_top_ai_btn",
                icon=":material/auto_awesome:",
                type="primary",
                width="stretch",
            ):
                ai_chat_dialog()
    try:
        student_notes = get_notes_for_student(student_id)
    except (APIError, PermissionError, RuntimeError) as error:
        st.error(f"Could not load course notes: {error}")
        student_notes = []
    st.markdown("""
        <style>
            div[data-testid="stTabs"] > div[role="tablist"] {
                display: flex;
                flex-wrap: wrap;
                gap: .4rem;
                padding: .45rem;
                border: 1px solid #dce1d6;
                border-radius: 15px;
                background: #eef2eb;
            }
            div[data-testid="stTabs"] button[role="tab"] {
                flex: 1 1 145px;
                min-height: 2.7rem;
                border: 1px solid transparent;
                border-radius: 11px;
                color: #526457;
                font-size: .88rem;
                font-weight: 600;
                transition: background .18s ease, color .18s ease, box-shadow .18s ease;
            }
            div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
                border-color: #315b54;
                background: #315b54;
                color: #fffefa;
                box-shadow: 0 4px 11px rgba(32,58,67,.13);
            }
            div[data-testid="stTabs"] button[role="tab"]:focus-visible {
                outline: 3px solid #bd7654;
                outline-offset: 2px;
            }
            .student-assessment-heading {
                margin: .25rem 0 1rem;
                padding: 18px 22px;
                border: 1px solid #dce1d6;
                border-left: 5px solid #bd7654;
                border-radius: 16px;
                background: linear-gradient(120deg,#fffefa,#f7eee8);
                box-shadow: 0 7px 20px rgba(32,58,67,.055);
            }
            .student-assessment-heading span {
                color: #bd7654;
                font-size: .68rem;
                font-weight: 700;
                letter-spacing: .14em;
            }
            .student-assessment-heading div {
                margin-top: 5px;
                color: #26382e;
                font-size: 1.4rem;
                font-weight: 700;
                line-height: 1.25;
            }
            [class*="st-key-student_assessment_"] {
                border-color: #dce1d6 !important;
                border-radius: 16px !important;
                background: #fffefa;
                box-shadow: 0 6px 18px rgba(32,58,67,.045);
            }
            @media (max-width: 700px) {
                div[data-testid="stTabs"] > div[role="tablist"] {
                    gap: .3rem;
                    padding: .35rem;
                }
                div[data-testid="stTabs"] button[role="tab"] {
                    flex-basis: 125px;
                    padding-inline: .45rem;
                    font-size: .82rem;
                }
            }
        </style>
    """, unsafe_allow_html=True)

    main_nav_key = f"student_dashboard_section_{student_id}"
    if main_nav_key not in st.session_state:
        st.session_state[main_nav_key] = "subjects"
    hub_nav_key = f"student_learning_section_{student_id}"
    if hub_nav_key not in st.session_state:
        st.session_state[hub_nav_key] = "notes"

    def _student_nav_button(label, section, state_key, active, icon):
        if st.button(
            label,
            key=f"student_nav_{state_key}_{section}_{student_id}",
            icon=icon,
            type="primary" if active == section else "tertiary",
            width="stretch",
        ):
            st.session_state[state_key] = section
            st.rerun()

    nav_subjects, nav_assessments, nav_learning = st.columns(3, gap="small")
    with nav_subjects:
        _student_nav_button("Enrolled Subjects", "subjects", main_nav_key, st.session_state[main_nav_key], ":material/menu_book:")
    with nav_assessments:
        _student_nav_button("Assessments", "assessments", main_nav_key, st.session_state[main_nav_key], ":material/assignment:")
    with nav_learning:
        _student_nav_button("Learning Hub", "learning", main_nav_key, st.session_state[main_nav_key], ":material/auto_stories:")

    if st.session_state[main_nav_key] == "learning":
        learning_subject_nodes = get_students_subjects(student_id)
        learning_logs = get_student_attendance(student_id)
        learning_stats = {}
        for attendance_log in learning_logs:
            subject_id = attendance_log.get(
                "subject_id", attendance_log.get("subjects_id")
            )
            if subject_id is None:
                continue
            stats = learning_stats.setdefault(
                str(subject_id), {"total": 0, "attended": 0}
            )
            stats["total"] += 1
            if attendance_log.get("is_present"):
                stats["attended"] += 1
        subjects_stats_list = []
        enrolled_subjects_data = []
        for subject_node in learning_subject_nodes:
            subject = subject_node.get("subjects")
            if not subject:
                continue
            subject_stats = learning_stats.get(
                str(subject["subject_id"]), {"total": 0, "attended": 0}
            )
            subjects_stats_list.append({
                "subject_id": subject["subject_id"],
                "name": subject["name"],
                "code": subject["subject_code"],
                "section": subject.get("section", ""),
                "total": subject_stats["total"],
                "attended": subject_stats["attended"],
            })
            enrolled_subjects_data.append(subject)

        learning_nav = st.columns(4, gap="small")
        for column, (label, section, icon) in zip(
            learning_nav,
            [
                ("Course Notes", "notes", ":material/description:"),
                ("Grade Impact Simulator", "impact", ":material/monitoring:"),
                ("Study Buddy Matcher", "buddy", ":material/group:"),
                ("Voice Profile", "voice", ":material/graphic_eq:"),
            ],
        ):
            with column:
                _student_nav_button(label, section, hub_nav_key, st.session_state[hub_nav_key], icon)

    if st.session_state[main_nav_key] == "learning" and st.session_state[hub_nav_key] == "voice":
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

    if st.session_state[main_nav_key] == "assessments":
        st.markdown("""
            <section class="student-assessment-heading">
              <span>CHECK YOUR PROGRESS</span>
              <div>Assessments for Your Subjects</div>
            </section>
        """, unsafe_allow_html=True)
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
                    with st.container(
                        key=f"student_assessment_{assessment['id']}",
                        border=True,
                    ):
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

    if st.session_state[main_nav_key] == "subjects":
        subject_heading, enroll_action = st.columns([3, 1], vertical_alignment="center")
        with subject_heading:
            st.markdown("""
                <section style="padding:18px 22px; border:1px solid #dce1d6;
                    border-left:5px solid #315b54; border-radius:16px;
                    background:linear-gradient(120deg,#fffefa,#eef3eb);
                    box-shadow:0 7px 20px rgba(32,58,67,.055);">
                  <span style="color:#bd7654; font-size:.68rem; font-weight:700;
                    letter-spacing:.14em;">YOUR LEARNING SPACE</span>
                  <div style="margin:5px 0 3px; color:#26382e; font-size:1.45rem;
                    font-weight:700; line-height:1.25;">Your enrolled subjects</div>
                  <p style="margin:0; color:#65746a; font-size:.9rem;">
                    Open a class to check your attendance and course details.</p>
                </section>
            """, unsafe_allow_html=True)
        with enroll_action:
            if st.button(
                "Quick Enrollment",
                type="primary",
                width="stretch",
                icon=":material/add_circle:",
            ):
                enroll_dialog()

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
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

    if st.session_state[main_nav_key] == "learning" and st.session_state[hub_nav_key] == "impact":
        if subjects_stats_list:
            render_gpa_forecaster(subjects_stats_list)
        else:
            st.info("Enroll in a subject to use the attendance simulator.")

    if st.session_state[main_nav_key] == "learning" and st.session_state[hub_nav_key] == "buddy":
        if enrolled_subjects_data:
            render_study_buddy_matcher(enrolled_subjects_data, student_id)
        else:
            st.info("Enroll in a subject to find study partners.")

    if st.session_state[main_nav_key] == "learning" and st.session_state[hub_nav_key] == "notes":
        st.markdown("""
            <style>
                .student-notes-intro {
                    margin: .25rem 0 1rem; padding: 1.15rem 1.35rem;
                    border: 1px solid #dce1d6; border-left: 5px solid #829a79;
                    border-radius: 16px; background: #fffefa;
                    box-shadow: 0 8px 24px rgba(48,66,51,.045);
                }
                .student-notes-intro span {
                    color: #829a79; font-size: .7rem; font-weight: 700;
                    letter-spacing: .13em; text-transform: uppercase;
                }
                .student-notes-intro h2 {
                    margin: .3rem 0 .35rem; color: #385844;
                    font-size: clamp(1.45rem,2.8vw,2rem); line-height: 1.2;
                }
                .student-notes-intro p { margin: 0; color: #65746a; line-height: 1.55; }
                [class*="st-key-student_note_"] {
                    border-color: #dce1d6 !important; border-radius: 16px !important;
                    background: #fffefa; box-shadow: 0 7px 20px rgba(48,66,51,.05);
                }
                .st-key-student_notes_ai_btn button { min-height: 3rem; white-space: nowrap; }
            </style>
            <section class="student-notes-intro">
              <span>Learning resources</span>
              <h2>Course Notes &amp; Study Materials</h2>
              <p>Explore notes and study guides shared by your teachers for your enrolled subjects.</p>
            </section>
        """, unsafe_allow_html=True)
        _, c_nai = st.columns([3, 1])
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
                    with st.container(key=f"student_note_{note['id']}", border=True):
                        c_ntext, c_nactions = st.columns([3, 1])
                        with c_ntext:
                            st.markdown(f"**{note['title']}**")
                            if note.get("description"):
                                st.markdown(sanitize_mermaid_blocks(note["description"]))
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

    col1, col2 = st.columns([3, 1], vertical_alignment="center", gap="large")
    with col1:
        st.markdown(f"""
            <div style="display:flex;align-items:center;justify-content:flex-start;
                min-height:74px;width:100%;">
              <img src="{LOGO_DATA_URI}" alt="SmartClass AI"
                style="display:block;width:min(380px,100%);height:auto;margin:0;" />
            </div>
        """, unsafe_allow_html=True)
    with col2:
        if st.button(
            "Back to Home",
            type="secondary",
            key="loginbackbtn",
        ):
            st.session_state["login_type"] = None
            st.rerun()

    st.markdown("""
        <style>
            .face-login-hero {
                margin: 1rem 0 1.2rem;
                padding: 1.45rem 1.6rem;
                border: 1px solid #dce1d6;
                border-radius: 22px;
                background: linear-gradient(125deg, #e6ecdf, #dbe6d5 62%, #e8eadc);
                box-shadow: 0 12px 30px rgba(48,66,51,.07);
                text-align: center;
            }
            .face-login-hero .eyebrow {
                color: #829a79;
                font-size: .7rem;
                font-weight: 700;
                letter-spacing: .14em;
                text-transform: uppercase;
            }
            .face-login-hero h1 {
                margin: .35rem 0 .4rem;
                color: #26382e;
                font-size: clamp(1.65rem, 3.5vw, 2.35rem);
                line-height: 1.15;
            }
            .face-login-hero p {
                margin: 0;
                color: #526457;
                line-height: 1.55;
            }
            .st-key-face-login-camera {
                max-width: 720px;
                margin: 0 auto;
                padding: 1rem 1.25rem .65rem;
                border: 1px solid #dce1d6;
                border-radius: 18px;
                background: #fffefa;
                box-shadow: 0 8px 24px rgba(48,66,51,.055);
            }
            @media (max-width: 640px) {
                .face-login-hero { padding: 1.15rem; }
                .st-key-face-login-camera { padding: .8rem; }
            }
        </style>
        <section class="face-login-hero">
          <span class="eyebrow">Student access</span>
          <h1>Sign in with Face ID</h1>
          <p>Center your face in the camera to securely open your student workspace.</p>
        </section>
    """, unsafe_allow_html=True)

    show_registration = False
    with st.container(key="face-login-camera"):
        st.markdown("**Ready when you are**")
        st.caption("Allow camera access, look toward the camera, then capture a clear photo.")
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
        st.markdown("""
            <style>
                .st-key-student_registration_panel {
                    border-color: #d5e1d9 !important;
                    border-radius: 20px !important;
                    background: #fffefa;
                    box-shadow: 0 12px 28px rgba(32,58,67,.08);
                }
                .st-key-student_voice_enrollment {
                    margin: 1rem 0 .5rem;
                    border-color: #dce1d6 !important;
                    border-radius: 15px !important;
                    background: #f6f7f1;
                }
            </style>
        """, unsafe_allow_html=True)
        with st.container(key="student_registration_panel", border=True):
            st.markdown("""
                <section style="margin-bottom:1rem;padding:18px 20px;
                    border:1px solid #31545b;border-radius:16px;
                    background:linear-gradient(128deg,#203a43,#315b54 72%,#3c6658);">
                  <span style="color:#d8ef9b;font-size:.68rem;font-weight:700;
                    letter-spacing:.14em;text-transform:uppercase;">Student access</span>
                  <h2 style="margin:5px 0 3px;color:#fffefa;font-size:1.45rem;">
                    Register a New Profile</h2>
                  <p style="margin:0;color:#e1ebe3;">Add your details and face profile to create your account.</p>
                </section>
            """, unsafe_allow_html=True)
            new_name = st.text_input(
                "Enter your name",
                placeholder="E.g. Abhishekh Tiwari",
            )
            registration_number = st.text_input(
                "Registration number",
                placeholder="For example, 2307060023",
                key="student_registration_number",
            )

            with st.container(key="student_voice_enrollment", border=True):
                st.subheader("Optional: Voice Enrollment")
                st.caption("Enroll your voice for voice-only attendance. You can skip this for now.")
                audio_data = st.audio_input(
                    "Record a short phrase for voice-only attendance"
                )

            if st.button("Create Account", type="primary"):
                if not new_name.strip():
                    st.warning("Please enter your name.")
                elif not registration_number.strip():
                    st.warning("Please enter your registration number.")
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
                                registration_number=registration_number.strip(),
                                face_embedding=face_embedding,
                                voice_embedding=voice_embedding,
                            )

                            if response_data:
                                train_classifier()
                                st.session_state.is_logged_in = True
                                st.session_state.user_role = "student"
                                st.session_state.student_data = response_data[0]
                                st.toast(
                                    "Profile created! Registration number: "
                                    f"{registration_number.strip()}"
                                )
                                st.rerun()
                            else:
                                st.error("Could not create the student profile.")

    footer_dashboard()
