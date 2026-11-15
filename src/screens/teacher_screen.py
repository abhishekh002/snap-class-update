
import hashlib
import hmac
import time
from src.database.notes_db import get_note_download, get_notes_for_teacher, delete_note
from src.components.dialog_upload_note import upload_note_dialog
from src.components.dialog_blackboard_digitizer import blackboard_digitizer_dialog
from src.components.dialog_interactive_reader import interactive_reader_dialog
from src.components.dialog_ai_chat import ai_chat_dialog

from datetime import datetime, timezone

import streamlit as st
from supabase import PostgrestAPIError as APIError

from src.components.footer import footer_dashboard
from src.components.dialog_create_subject import create_subject_dialog
from src.ui.base_layout import style_background_dashboard, style_base_layout

from src.components.header import header_dashboard

from src.database.db import (
    check_teacher_exists,
    check_teacher_email_exists,
    create_teacher,
    delete_teacher_subject,
    get_attendance_for_teacher,
    get_teacher_subject,
    teacher_login,
    update_teacher_password,
)
from src.components.password_reset import (
    request_password_reset,
    validate_reset_token,
)

from src.components.subject_card import Subject_card

from src.components.dialog_share_subject import share_subject_dialog
from src.components.dialog_add_photo import add_photos_dialog
from src.components.dialog_attendance_result import attendance_result_dialog
from src.components.dialog_voice import voice_attendance_dialog

from src.pipelines.face_pipeline import predict_attendance

import numpy as np

from src.database.config import supabase

import pandas as pd

from src.database.config import supabase

@st.dialog("Delete Subject")
def confirm_delete_subject(subject_id, subject_name, teacher_id):
    st.warning(
        f"Delete **{subject_name}**? This will also permanently delete its student "
        "enrollments and attendance records."
    )
    cancel_col, delete_col = st.columns(2)
    with cancel_col:
        if st.button("Cancel", width="stretch", key=f"cancel_delete_{subject_id}"):
            st.rerun()
    with delete_col:
        if st.button(
            "Delete Subject",
            type="primary",
            width="stretch",
            key=f"confirm_delete_{subject_id}",
        ):
            try:
                deleted = delete_teacher_subject(subject_id, teacher_id)
            except Exception as error:
                st.error(f"Could not delete the subject: {error}")
                return

            if not deleted:
                st.error("Subject not found or you do not have permission to delete it.")
                return

            st.toast(f"{subject_name} and its related records were deleted.")
            st.rerun()


def register_teacher(
    teacher_username,
    teacher_name,
    teacher_email,
    teacher_pass,
    teacher_pass_confirm,
):
    if not all((teacher_username, teacher_name, teacher_email, teacher_pass, teacher_pass_confirm)):
        return False, "All fields are required."
    email_parts = teacher_email.strip().rsplit("@", 1)
    if len(email_parts) != 2 or not email_parts[0] or "." not in email_parts[1]:
        return False, "Enter a valid email address."
    if teacher_pass != teacher_pass_confirm:
        return False, "Passwords don't match."

    if len(teacher_pass) < 6:
        return False, "Password must be at least 6 characters."

    try:
        if check_teacher_exists(teacher_username):
            return False, "That username is already taken."
        if check_teacher_email_exists(teacher_email):
            return False, "That email address is already in use."
        create_teacher(teacher_username, teacher_pass, teacher_name, teacher_email)
    except APIError as error:
        if error.code == "42703" and "teachers.email" in error.message:
            return (
                False,
                "Teacher email support is not enabled in the database yet. "
                "In Supabase, open SQL Editor and run the SQL in "
                "supabase/migrations/20261029220000_add_teacher_email.sql, "
                "then try again.",
            )
        return False, f"Could not register the teacher: {error.message}"
    return True, "Account created successfully. Log in now."


def teacher_screen():
    style_background_dashboard()
    style_base_layout()
    if st.session_state.get("teacher_data") is not None:
        teacher_dashboard()
    elif "teacher_login_type" not in st.session_state or st.session_state.teacher_login_type == "login":
        teacher_screen_login()
    elif st.session_state.teacher_login_type == "register":
        teacher_screen_register()

def teacher_dashboard():
    teacher = st.session_state.teacher_data
    section_titles = {
        "take_attendance": "Take Attendance",
        "manage_subjects": "Manage Subjects",
        "attendance_records": "Attendance Records",
        "course_notes": "Course Notes",
    }
    current_tab = st.session_state.get("current_teacher_tab")
    if current_tab not in section_titles:
        current_tab = "take_attendance"
        st.session_state.current_teacher_tab = current_tab

    header_dashboard()
    c_w, c_b = st.columns([2, 1], vertical_alignment="center")
    with c_w:
        st.subheader(f"Welcome, {teacher['name']}")
    with c_b:
        btn_ai_col, btn_log_col = st.columns(2)
        with btn_ai_col:
            if st.button("🤖 AI Assistant", key="teacher_ai_header_btn"):
                ai_chat_dialog()
        with btn_log_col:
            if st.button("Logout", type="secondary", key="teacher_logout"):
                del st.session_state["teacher_data"]
                st.session_state["teacher_login_type"] = "login"
                st.session_state.pop("current_teacher_tab", None)
                st.rerun()

    tab1, tab2, tab3, tab4 = st.columns(4)
    with tab1:
        type1 = "primary" if st.session_state.current_teacher_tab == "take_attendance" else 'tertiary'
        if st.button("Take Attendance", width="stretch", type=type1, icon=":material/fact_check:", key="take_attendance"):
            st.session_state.current_teacher_tab = "take_attendance"
            st.rerun()
    with tab2:
        type2 = "primary" if st.session_state.current_teacher_tab == "manage_subjects" else 'tertiary'
        if st.button("Manage Subjects", width="stretch", type=type2, icon=":material/menu_book:", key="manage_subjects"):
            st.session_state.current_teacher_tab = "manage_subjects"
            st.rerun()
    with tab3:
        type3 = "primary" if st.session_state.current_teacher_tab == "attendance_records" else 'tertiary'
        if st.button("Attendance Records", width="stretch", type=type3, icon=":material/assignment:", key="attendance_records"):
            st.session_state.current_teacher_tab = "attendance_records"
            st.rerun()
    with tab4:
        type4 = "primary" if st.session_state.current_teacher_tab == "course_notes" else 'tertiary'
        if st.button("Course Notes", width="stretch", type=type4, icon=":material/folder_shared:", key="course_notes"):
            st.session_state.current_teacher_tab = "course_notes"
            st.rerun()
    st.divider()
    if st.session_state.current_teacher_tab == "take_attendance":
        teacher_tab_take_attendance()
    if st.session_state.current_teacher_tab == "manage_subjects":
        teacher_tab_manage_subjects()
    if st.session_state.current_teacher_tab == "attendance_records":
        teacher_tab_attendance_records()
    if st.session_state.current_teacher_tab == "course_notes":
        teacher_tab_course_notes()
    footer_dashboard()


def teacher_tab_course_notes():
    teacher_id = st.session_state.teacher_data.get("teacher_id", st.session_state.teacher_data.get("id"))
    st.header("Course Notes & Materials")
    st.write("Upload notes and study guides for your classes. Enrolled students will have immediate access.")

    col_up, col_bb, col_ai = st.columns([1, 1, 1])
    with col_up:
        if st.button("➕ Upload Note", type="primary", icon=":material/upload_file:", key="btn_upload_note_modal", width="stretch"):
            upload_note_dialog()
    with col_bb:
        if st.button("📷 Blackboard to Notes", icon=":material/photo_camera:", key="btn_bb_digitize", width="stretch", help="Transcribe chalkboard/whiteboard into LaTeX & Markdown"):
            blackboard_digitizer_dialog()
    with col_ai:
        if st.button("🤖 AI Assistant", icon=":material/smart_toy:", key="btn_teacher_notes_ai", width="stretch"):
            ai_chat_dialog()

    st.divider()
    notes = get_notes_for_teacher(teacher_id)
    if not notes:
        st.info("You haven't uploaded any notes yet. Click 'Upload Note' or 'Blackboard to Notes' above to get started.")
        return

    subjects_map = {}
    for n in notes:
        s_name = n.get("subject_name", "General")
        subjects_map.setdefault(s_name, []).append(n)

    for subj_name, subj_notes in subjects_map.items():
        st.subheader(f"📖 {subj_name}")
        for note in subj_notes:
            with st.container(border=True):
                c_info, c_action = st.columns([3, 1])
                with c_info:
                    st.markdown(f"**{note['title']}**")
                    if note.get("description"):
                        st.write(note["description"])
                    st.caption(f"Uploaded: {note.get('created_at', '')} | Size: {note.get('file_size_kb', 0)} KB")
                with c_action:
                    if st.button("📖 Interactive Reader", key=f"read_teacher_{note['id']}", width="stretch", icon=":material/menu_book:"):
                        interactive_reader_dialog(note)
                    download = get_note_download(note)
                    if download:
                        file_bytes, file_name = download
                        st.download_button(
                            label="⬇️ Download",
                            data=file_bytes,
                            file_name=file_name,
                            key=f"dl_teacher_{note['id']}",
                            width="stretch",
                        )
                    if st.button("🗑️ Delete", key=f"del_note_{note['id']}", width="stretch"):
                        delete_note(note["id"], teacher_id)
                        st.toast("Note deleted.")
                        st.rerun()


def teacher_tab_take_attendance():
    teacher_id = st.session_state.teacher_data['teacher_id']
    st.header('Take Attendance with AI')

    if 'attendance_images' not in st.session_state:
        st.session_state.attendance_images = []

    subjects = get_teacher_subject(teacher_id)
    if not subjects:
        st.warning("You haven't created any subjects yet. Create one to get started.")
        return

    subject_options = {f"{s['name']} - {s['subject_code']}": s['subject_id'] for s in subjects}

    col1, col2 = st.columns([3, 1],vertical_alignment='bottom')

    with col1:
        selected_subject_label = st.selectbox('Select Subject', options=list(subject_options.keys()))

    with col2:
        if st.button(
            "Add Photos",
            type="primary",
            icon=":material/add_a_photo:",
            width="stretch",
        ):
            add_photos_dialog()
    selected_subject_id = subject_options[selected_subject_label]

    st.divider()
    if 'attendance_images' in st.session_state and st.session_state.attendance_images:
        st.header('Added Photos')
        gallery_cols = st.columns(4)

        for idx, img in enumerate(st.session_state.attendance_images):
            with gallery_cols[idx % 4]:
                st.image(img, width='stretch', caption=f'Photo {idx+1}')
    has_photos = bool(st.session_state.attendance_images)
    if len(st.session_state.attendance_images) > 1:
        st.info(
            f"📐 **Panoramic Multi-Shot Roll Call Active** ({len(st.session_state.attendance_images)} room angles staged). "
            "The AI pipeline will scan all room angles and automatically deduplicate students who appear in overlapping edge sections."
        )

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button(
            "Clear all photos",
            width="stretch",
            type="tertiary",
            icon=":material/delete:",
            disabled=not has_photos,
        ):
            st.session_state.attendance_images = []
            st.rerun()

    with c2:

        if st.button(
            "Run Face Analysis",
            width="stretch",
            type="secondary",
            icon=":material/analytics:",
            disabled=not has_photos,
        ):
            try:
                enrolled_res = (
                    supabase.table("subject_students")
                    .select("*, students(*)")
                    .eq("subject_id", selected_subject_id)
                    .execute()
                )
            except APIError as error:
                st.error(f"Could not load enrolled students: {error.message}")
                return

            enrolled_students = enrolled_res.data or []
            if not enrolled_students:
                st.warning("No students are enrolled in this subject.")
                return

            candidate_student_ids = [
                node["students"]["student_id"]
                for node in enrolled_students
                if node.get("students")
                and node["students"].get("student_id") is not None
            ]
            if not candidate_student_ids:
                st.warning("No valid student enrollment records were found.")
                return

            with st.spinner("Deep scanning classroom photos..."):
                detected_sources = {}
                photo_analysis = []
                student_names = {
                    str(node["students"]["student_id"]): node["students"]["name"]
                    for node in enrolled_students
                    if node.get("students")
                    and node["students"].get("student_id") is not None
                }

                for image_index, image in enumerate(
                    st.session_state.attendance_images,
                    start=1,
                ):
                    image_array = np.array(image.convert("RGB"))
                    detected, _, face_count = predict_attendance(
                        image_array,
                        candidate_student_ids=candidate_student_ids,
                    )
                    for student_id in detected:
                        detected_sources.setdefault(str(student_id), []).append(
                            f"Photo {image_index}"
                        )
                    recognized_names = [
                        student_names[str(student_id)]
                        for student_id in detected
                        if str(student_id) in student_names
                    ]
                    if recognized_names:
                        photo_analysis.append(
                            f"Photo {image_index}: recognized "
                            f"{', '.join(recognized_names)}."
                        )
                    elif face_count:
                        photo_analysis.append(
                            f"Photo {image_index}: detected {face_count} face(s), "
                            "but none confidently matched an enrolled student. "
                            "Try a closer, clearer photo with good lighting."
                        )
                    else:
                        photo_analysis.append(
                            f"Photo {image_index}: no faces detected. "
                            "Try a closer photo with good lighting."
                        )

                dedup_count = sum(1 for s in detected_sources.values() if len(s) > 1)
                if dedup_count > 0:
                    photo_analysis.insert(
                        0,
                        f"📐 Panoramic Deduplication: Automatically identified and deduplicated {dedup_count} student(s) appearing across overlapping camera angles."
                    )

                results, attendance_to_log = [], []
                logged_at = datetime.now(timezone.utc).isoformat()

                for node in enrolled_students:
                    student = node.get("students")
                    if not student:
                        continue

                    sources = detected_sources.get(str(student["student_id"]), [])
                    is_present = bool(sources)
                    results.append({
                        "Name": student["name"],
                        "ID": student["student_id"],
                        "Sources": ", ".join(sources) if is_present else "-",
                        "Status": "✅ Present" if is_present else "❌ Absent",
                    })
                    attendance_to_log.append({
                        "student_id": student["student_id"],
                        "subject_id": selected_subject_id,
                        "logged_at": logged_at,
                        "is_present": is_present,
                    })

                if not attendance_to_log:
                    st.warning("No valid student enrollment records were found.")
                    return

            attendance_result_dialog(
                pd.DataFrame(results),
                attendance_to_log,
                photo_analysis=photo_analysis,
            )
    with c3:
        if st.button(
            "Use Voice Attendance",
            type="primary",
            width="stretch",
            icon=":material/mic:",
        ):
            voice_attendance_dialog(selected_subject_id)



def teacher_tab_manage_subjects():
    teacher_id = st.session_state.teacher_data["teacher_id"]
    heading_col, create_col = st.columns(2)
    with heading_col:
        st.header('Manage Subjects', width='stretch')
    with create_col:
        if st.button('Create New Subject', width='stretch'):
            create_subject_dialog(teacher_id)

    subjects = get_teacher_subject(teacher_id)
    if subjects:
        for sub in subjects:
            stats = [
                ("👥", "Students", sub["total_students"]),
                ("⏰", "Attendance Records", sub["total_attendance_records"]),
            ]

            def subject_actions(
                subject_name=sub["name"],
                subject_code=sub["subject_code"],
                subject_id=sub["subject_id"],
            ):
                share_col, delete_col = st.columns(2)
                with share_col:
                    if st.button(
                        "Share subject code",
                        key=f"share_{subject_code}",
                        icon=":material/share:",
                        width="stretch",
                    ):
                        share_subject_dialog(subject_name, subject_code)
                with delete_col:
                    if st.button(
                        "Delete",
                        key=f"delete_{subject_id}",
                        icon=":material/delete:",
                        type="secondary",
                        width="stretch",
                    ):
                        confirm_delete_subject(subject_id, subject_name, teacher_id)

            Subject_card(
                name=sub["name"],
                code=sub["subject_code"],
                section=sub["section"],
                stats=stats,
                footer_callback=subject_actions,
            )
    else:
        st.info("No subjects found. Create one above.")
def teacher_tab_attendance_records():
    st.header("Attendance Records")

    teacher_id = st.session_state.teacher_data["teacher_id"]
    try:
        records = get_attendance_for_teacher(teacher_id)
    except APIError as error:
        st.error(f"Could not load attendance records: {error.message}")
        return

    if not records:
        st.info("No attendance records yet.")
        return

    rows = []
    for record in records:
        subject = record.get("subjects")
        if not isinstance(subject, dict):
            continue

        logged_at = record.get("logged_at")
        try:
            logged_time = datetime.fromisoformat(
                logged_at.replace("Z", "+00:00")
            ) if logged_at else None
        except (TypeError, ValueError):
            logged_time = None

        rows.append(
            {
                "ts_group": logged_time.isoformat() if logged_time else logged_at,
                "Time": (
                    logged_time.strftime("%Y-%m-%d %I:%M %p")
                    if logged_time
                    else "N/A"
                ),
                "Subject": subject.get("name", "Unknown"),
                "Subject Code": subject.get("subject_code", "N/A"),
                "is_present": bool(record.get("is_present", False)),
            }
        )

    if not rows:
        st.info("No displayable attendance records were found.")
        return

    records_df = pd.DataFrame(rows)
    summary = (
        records_df.groupby(
            ["ts_group", "Time", "Subject", "Subject Code"],
            dropna=False,
        )
        .agg(
            Present_Count=("is_present", "sum"),
            Total_Count=("is_present", "count"),
        )
        .reset_index()
    )
    summary["Attendance Stats"] = (
        "✅ "
        + summary["Present_Count"].astype(str)
        + " / "
        + summary["Total_Count"].astype(str)
        + " Students"
    )
    st.dataframe(
        summary[["Time", "Subject", "Subject Code", "Attendance Stats"]],
        hide_index=True,
        width="stretch",
    )



def teacher_password_reset():
    reset_token = st.query_params.get("reset_token")
    if not reset_token:
        return False
    if isinstance(reset_token, list):
        reset_token = reset_token[0]
    reset_token = str(reset_token).strip()

    c_hdr1, c_hdr2 = st.columns([3, 1], vertical_alignment="center")
    with c_hdr1:
        st.header("Reset Your Teacher Password")
    with c_hdr2:
        if st.button("Back to Login", type="secondary", key="cancel_reset_top"):
            if "reset_token" in st.query_params:
                del st.query_params["reset_token"]
            st.rerun()

    teacher = validate_reset_token(reset_token)
    if teacher is None:
        st.error("This password reset link is invalid or has expired.")
        if st.button("Return to login", key="invalid_reset_return"):
            if "reset_token" in st.query_params:
                del st.query_params["reset_token"]
            st.rerun()
        return True

    teacher_display = teacher.get("name") or teacher.get("username") or teacher.get("email")
    st.info(f"Setting new password for: **{teacher_display}** (`{teacher.get('email')}`)")

    password = st.text_input(
        "New password",
        type="password",
        placeholder="Enter at least 6 characters",
        key="teacher_reset_password",
    )
    confirm_password = st.text_input(
        "Confirm new password",
        type="password",
        placeholder="Re-enter new password",
        key="teacher_reset_password_confirm",
    )

    btn_col1, btn_col2 = st.columns([2, 1])
    with btn_col1:
        if st.button("Update password", type="primary", key="update_teacher_password", width="stretch"):
            if len(password) < 6:
                st.warning("Password must be at least 6 characters.")
            elif password != confirm_password:
                st.warning("Passwords don't match.")
            else:
                identifier = teacher.get("teacher_id") or teacher.get("email") or teacher.get("username")
                if not update_teacher_password(identifier, password):
                    st.error("Password could not be updated. Please request a new reset link.")
                else:
                    if "reset_token" in st.query_params:
                        del st.query_params["reset_token"]
                    st.session_state["teacher_login_type"] = "login"
                    st.session_state["teacher_password_reset_success"] = "Password updated successfully! You can now sign in with your new password."
                    st.rerun()
    with btn_col2:
        if st.button("Cancel", type="secondary", key="cancel_reset_bottom", width="stretch"):
            if "reset_token" in st.query_params:
                del st.query_params["reset_token"]
            st.rerun()
    return True



def teacher_screen_login():
    style_background_dashboard()
    style_base_layout()
    if "teacher_registration_message" in st.session_state:
        st.success(st.session_state.pop("teacher_registration_message"))
    if "teacher_password_reset_success" in st.session_state:
        st.success(st.session_state.pop("teacher_password_reset_success"))
    if teacher_password_reset():
        footer_dashboard()
        return

    c1, c2 = st.columns(2, vertical_alignment="center", gap="large")
    with c1:
        header_dashboard()
    with c2:
        if st.button("Back to Home", type="secondary", key="loginbackbtn"):
            st.session_state["login_type"] = None
            st.session_state["teacher_login_type"] = "login"
            st.session_state.pop("current_teacher_tab", None)
            st.rerun()

    st.space()
    st.markdown(
        """
        <h2 style="text-align:center; white-space:nowrap;
                    font-size:clamp(0.85rem, 2vw, 1.5rem);">
            Teacher Sign-In with Email
        </h2>
        """,
        unsafe_allow_html=True,
    )
    st.space()
    st.space()
    teacher_email = st.text_input(
        "Enter your email address",
        placeholder="teacher@example.com",
        key="teacher_login_email",
    )
    teacher_pass = st.text_input("Enter your password", type="password", placeholder="Enter your password", key="teacher_login_password")
    st.divider()
    btnc1 , btnc2 = st.columns(2)

    with btnc1:
        if st.button("Login", icon=":material/passkey:", width="stretch"):
            teacher = teacher_login(teacher_email, teacher_pass)
            if teacher:
                st.session_state.teacher_data = teacher
                st.rerun()
            st.error("Invalid email or password.")
    with btnc2:
        if st.button("Register instead", type="primary", icon=":material/person_add:", width="stretch"):
            st.session_state.teacher_login_type = "register"
            st.rerun()

    with st.expander(
        "Forgot password?",
        expanded=("password_reset_otp" in st.session_state),
    ):
        reset_email = st.text_input(
            "Teacher account email",
            placeholder="teacher@example.com",
            key="teacher_reset_email",
        )
        reset_email_normalized = reset_email.strip().lower()
        pending_otp = st.session_state.get("password_reset_otp")
        if pending_otp and pending_otp["email"] != reset_email_normalized:
            st.session_state.pop("password_reset_otp", None)
            st.session_state.pop("password_reset_code", None)
            pending_otp = None
            st.warning("The email address changed. Request a new reset code.")

        if st.button("Send password reset code", key="send_teacher_reset_code"):
            if not reset_email.strip():
                st.warning("Enter the email address used for your teacher account.")
            elif pending_otp and time.time() - pending_otp["sent_at"] < 60:
                st.warning("Please wait one minute before requesting another code.")
            else:
                try:
                    res = request_password_reset(reset_email)
                    if isinstance(res, tuple):
                        success = res[0]
                        mode = res[1] if len(res) > 1 else None
                    else:
                        success = res
                        mode = None
                except Exception as error:
                    st.error(f"Could not request password reset: {error}")
                else:
                    if success:
                        if mode != "direct_code":
                            st.session_state.pop("password_reset_code", None)
                            st.info(
                                "If a teacher account exists for that email, a verification code "
                                "has been sent to your email address."
                            )
                        else:
                            st.info("Verification code generated below.")
                    else:
                        st.warning("No teacher account was found with that email address.")

        pending_otp = st.session_state.get("password_reset_otp")
        if pending_otp:
            if pending_otp.get("code"):
                st.warning(
                    f"💡 **Email service is not configured.** For testing, your verification code is: **`{pending_otp['code']}`**"
                )
            else:
                st.success("A password reset code was sent to your email. It expires in 10 minutes.")
            st.text_input(
                "6-digit verification code",
                max_chars=6,
                placeholder="Enter 6-digit code",
                key="password_reset_code",
            )
            new_password = st.text_input(
                "New password",
                type="password",
                key="password_reset_new_password",
            )
            confirm_password = st.text_input(
                "Confirm new password",
                type="password",
                key="password_reset_confirm_password",
            )

            if st.button("Verify code and reset password", type="primary", key="verify_password_reset"):
                code_input = st.session_state.get("password_reset_code", "").strip()
                if time.time() >= pending_otp["expires_at"]:
                    st.session_state.pop("password_reset_otp", None)
                    st.session_state.pop("password_reset_code", None)
                    st.error("That code has expired. Request a new reset code.")
                elif pending_otp["attempts"] >= 5:
                    st.session_state.pop("password_reset_otp", None)
                    st.session_state.pop("password_reset_code", None)
                    st.error("Too many incorrect attempts. Request a new reset code.")
                else:
                    digest = hmac.new(
                        bytes.fromhex(pending_otp["key"]),
                        code_input.encode("utf-8"),
                        hashlib.sha256,
                    ).hexdigest()
                    if not hmac.compare_digest(digest, pending_otp["digest"]):
                        pending_otp["attempts"] += 1
                        st.error("Incorrect verification code.")
                    elif len(new_password) < 6:
                        st.warning("Password must be at least 6 characters.")
                    elif new_password != confirm_password:
                        st.warning("Passwords don't match.")
                    else:
                        try:
                            updated = update_teacher_password(
                                pending_otp["teacher_id"],
                                new_password,
                            )
                        except Exception as error:
                            st.error(f"Could not update password: {error}")
                        else:
                            if not updated:
                                st.error("Password could not be updated. Request a new reset code.")
                            else:
                                st.session_state.pop("password_reset_otp", None)
                                st.session_state.pop("password_reset_code", None)
                                st.session_state.pop("password_reset_new_password", None)
                                st.session_state.pop("password_reset_confirm_password", None)
                                st.session_state["teacher_password_reset_success"] = (
                                    "Password updated successfully! You can now sign in with your new password."
                                )
                                st.rerun()
    footer_dashboard()

def teacher_screen_register():
    c1, c2 = st.columns(2, vertical_alignment="center", gap="large")
    with c1:
        header_dashboard()
    with c2:
        if st.button("Back to Home", type="secondary", key="register_back_home"):
            st.session_state["login_type"] = None
            st.session_state["teacher_login_type"] = "login"
            st.session_state.pop("current_teacher_tab", None)
            st.rerun()
            
    st.header("Teacher Registration")

    st.space()
    st.space()

    teacher_username = st.text_input("Enter a username", placeholder="@abhishekh", key="teacher_register_username")

    teacher_name = st.text_input("Enter your name", placeholder="Abhishekh Kumar Tiwari", key="teacher_register_name")

    teacher_email = st.text_input(
        "Enter your email address",
        placeholder="teacher@example.com",
        key="teacher_register_email",
    )

    teacher_pass = st.text_input("Enter your password", type="password", placeholder="Enter your password", key="teacher_register_password")

    teacher_pass_confirm = st.text_input("Confirm your password", type="password", placeholder="Confirm your password", key="teacher_register_password_confirm")

    st.divider()
    btnc1, btnc2 = st.columns(2)
    with btnc1:
        if st.button("Register now", icon=":material/passkey:", width="stretch"):
            success, message = register_teacher(
                teacher_username,
                teacher_name,
                teacher_email,
                teacher_pass,
                teacher_pass_confirm,
            )
            if success:
                st.session_state.teacher_registration_message = message
                st.session_state.teacher_login_type = "login"
                st.rerun()
            else:
                st.error(message)

    with btnc2:
        if st.button("Log in instead", type="primary", icon=":material/passkey:", width="stretch"):
            st.session_state.teacher_login_type = "login"
            st.rerun()

    footer_dashboard()

  


    
