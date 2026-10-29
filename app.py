
from pathlib import Path

import streamlit as st

from src.screens.home_screen import home_screen
from src.screens.teacher_screen import teacher_screen
from src.screens.student_screen import student_screen

PAGE_ICON_PATH = Path(__file__).resolve().parent / "src" / "assets" / "page-icon.png"


def main():
    st.set_page_config(
        page_title='SnapClass - AI-Powered Classroom Attendance',
        page_icon=str(PAGE_ICON_PATH)
    )
    for key, default in {
        "login_type": None,
        "teacher_data": None,
        "student_data": None,
        "is_logged_in": False,
        "user_role": None,
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default

    if st.query_params.get("reset_token"):
        st.session_state["login_type"] = "teacher"
        st.session_state["teacher_login_type"] = "login"

    match st.session_state['login_type']:
        case 'teacher':
            teacher_screen()

        case 'student':
            student_screen()
        
        case None:
            home_screen()


    join_code = st.query_params.get('join-code')
    if join_code:
        if st.session_state.login_type != 'student':
            st.session_state.login_type = 'student'
            st.rerun()
        if st.session_state.get('is_logged_in') and st.session_state.get('user_role') == 'student':
            auto_enroll_dialog(join_code)
main()