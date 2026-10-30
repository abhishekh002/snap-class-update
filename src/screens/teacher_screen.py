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
from src.components.dialog_attendence_result import attendance_result_dialog
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
        return False, "All fields are required!"
    email_parts = teacher_email.strip().rsplit("@", 1)
    if len(email_parts) != 2 or not email_parts[0] or "." not in email_parts[1]:
        return False, "Enter a valid email address"
    if teacher_pass != teacher_pass_confirm:
        return False, "Passwords don't match"

    if len(teacher_pass) < 6:
        return False, "Password must be at least 6 characters"

    try:
        if check_teacher_exists(teacher_username):
            return False, "Username already taken"
        if check_teacher_email_exists(teacher_email):
            return False, "Email address already in use"
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
    return True, "Successfully created! Login now."


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
    }
    current_tab = st.session_state.get("current_teacher_tab")
    if current_tab not in section_titles:
        current_tab = "take_attendance"
        st.session_state.current_teacher_tab = current_tab

    header_dashboard()
    st.subheader(f"Welcome, {teacher['name']}")
    if st.button("Logout", type="secondary", key="teacher_logout"):
        del st.session_state["teacher_data"]
        st.session_state["teacher_login_type"] = "login"
        st.session_state.pop("current_teacher_tab", None)
        st.rerun()

    tab1, tab2, tab3 = st.columns(3)
    with tab1:
        type1 = "primary" if st.session_state.current_teacher_tab == "take_attendance" else 'tertiary'
        if st.button("Take Attendance", width="stretch", type=type1,icon=":material/fact_check:", key="take_attendance"):
            st.session_state.current_teacher_tab = "take_attendance"
            st.rerun()
    with tab2:
        type2 =  "primary" if st.session_state.current_teacher_tab == "manage_subjects" else 'tertiary'
        if st.button("Manage Subjects", width="stretch", type=type2,icon=":material/menu_book:", key="manage_subjects"):
            st.session_state.current_teacher_tab = "manage_subjects"
            st.rerun()
    with tab3:
        type3 =  "primary" if st.session_state.current_teacher_tab == "attendance_records" else 'tertiary'
        if st.button("Attendance Records", width="stretch", type=type3, icon=":material/assignment:", key="attendance_records"):
            st.session_state.current_teacher_tab = "attendance_records"
            st.rerun()
    st.divider()
    if st.session_state.current_teacher_tab == "take_attendance":
        teacher_tab_take_attendance()
    if st.session_state.current_teacher_tab == "manage_subjects":
        teacher_tab_manage_subjects()
    if st.session_state.current_teacher_tab == "attendance_records":
        teacher_tab_attendance_records()
    footer_dashboard()

def teacher_tab_take_attendance():
    teacher_id = st.session_state.teacher_data['teacher_id']
    st.header('Take AI Attendance')

    if 'attendance_images' not in st.session_state:
        st.session_state.attendance_images = []

    subjects = get_teacher_subject(teacher_id)
    if not subjects:
        st.warning('You havent created any subjects yet! Please create one to begin!')
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
                st.warning("No students enrolled in this course.")
                return

            candidate_student_ids = [
                node["students"]["student_id"]
                for node in enrolled_students
                if node.get("students")
                and node["students"].get("student_id") is not None
            ]
            if not candidate_student_ids:
                st.warning("No valid enrolled student records were found.")
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
                    st.warning("No valid enrolled student records were found.")
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
        st.header('Manage Subject',width='stretch')
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

    st.header("Reset teacher password")
    teacher = validate_reset_token(reset_token)
    if teacher is None:
        st.error("This password reset link is invalid or has expired.")
        if st.button("Return to login", key="invalid_reset_return"):
            del st.query_params["reset_token"]
            st.rerun()
        return True

    password = st.text_input(
        "New password",
        type="password",
        key="teacher_reset_password",
    )
    confirm_password = st.text_input(
        "Confirm new password",
        type="password",
        key="teacher_reset_password_confirm",
    )
    if st.button("Update password", type="primary", key="update_teacher_password"):
        if len(password) < 6:
            st.warning("Password must be at least 6 characters.")
        elif password != confirm_password:
            st.warning("Passwords don't match.")
        elif not update_teacher_password(teacher["username"], password):
            st.error("Password could not be updated. Please request a new reset link.")
        else:
            del st.query_params["reset_token"]
            st.session_state["teacher_login_type"] = "login"
            st.toast("Password updated. You can now sign in.")
            st.rerun()
    return True



def teacher_screen_login():
    style_background_dashboard()
    style_base_layout()
    if "teacher_registration_message" in st.session_state:
        st.success(st.session_state.pop("teacher_registration_message"))
    if teacher_password_reset():
        footer_dashboard()
        return

    c1, c2 = st.columns(2, vertical_alignment="center", gap="large")
    with c1:
        header_dashboard()
    with c2:
        if st.button("GO BACK TO HOME", type="secondary", key="loginbackbtn"):
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
        "Enter email",
        placeholder="teacher@example.com",
        key="teacher_login_email",
    )
    teacher_pass = st.text_input("Enter password", type="password", placeholder="Enter password", key="teacher_login_password")
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
        if st.button("Register Instead", type="primary", icon=":material/person_add:", width="stretch"):
            st.session_state.teacher_login_type = "register"
            st.rerun()

    with st.expander("Forgot password?"):
        reset_email = st.text_input(
            "Teacher account email",
            key="teacher_reset_email",
        )
        if st.button("Send reset link", key="send_teacher_reset_link"):
            if not reset_email.strip():
                st.warning("Enter the email address used for your teacher account.")
            else:
                try:
                    request_password_reset(reset_email)
                except (OSError, RuntimeError, ValueError) as error:
                    st.error(f"Could not send the reset email: {error}")
                else:
                    st.info(
                        "If a teacher account exists for that email, a reset link "
                        "has been sent."
                    )
    footer_dashboard()

def teacher_screen_register():
    c1, c2 = st.columns(2, vertical_alignment="center", gap="large")
    with c1:
        header_dashboard()
    with c2:
        if st.button("GO BACK TO HOME", type="secondary", key="register_back_home"):
            st.session_state["login_type"] = None
            st.session_state["teacher_login_type"] = "login"
            st.session_state.pop("current_teacher_tab", None)
            st.rerun()
            
    st.header("Teacher Registration")

    st.space()
    st.space()

    teacher_username = st.text_input("Enter username", placeholder="@abhishekh", key="teacher_register_username")

    teacher_name = st.text_input("Enter name", placeholder="Abhishekh kumar Tiwari", key="teacher_register_name")

    teacher_email = st.text_input(
        "Enter email",
        placeholder="teacher@example.com",
        key="teacher_register_email",
    )

    teacher_pass = st.text_input("Enter password", type="password", placeholder="Enter password", key="teacher_register_password")

    teacher_pass_confirm = st.text_input("Confirm your password", type="password", placeholder="Confirm password", key="teacher_register_password_confirm")


    st.divider()

    btnc1 , btnc2 = st.columns(2)

    with btnc1:
        if st.button("Register Now", icon=":material/passkey:", width="stretch"):
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
        if st.button("Login Instead", type="primary", icon=":material/passkey:", width="stretch"):
            st.session_state.teacher_login_type = "login"
            st.rerun()
    footer_dashboard()

  


    
