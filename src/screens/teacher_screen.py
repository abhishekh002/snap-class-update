import smtplib
import streamlit as st
from postgrest.exceptions import APIError

from src.components.footer import footer_dashboard
from src.components.dialog_create_subject import create_subject_dialog
from src.ui.base_layout import style_background_dashboard, style_base_layout

from src.components.header import header_dashboard

from src.database.db import (
    check_teacher_exists,
    check_teacher_email_exists,
    create_teacher,
    delete_teacher_subject,
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
    st.header('Take AI Attendance')

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
    st.header('Attendance record')


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
            Teacher Login with Email
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
                except (OSError, RuntimeError, ValueError, smtplib.SMTPException) as error:
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

  


    
