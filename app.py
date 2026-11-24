
from pathlib import Path

from dotenv import load_dotenv
import streamlit as st

from src.screens.home_screen import home_screen
from src.screens.teacher_screen import teacher_screen
from src.screens.student_screen import student_screen
from src.components.dialog_ai_chat import ai_chat_screen

from src.components.dialog_auto_enroll import auto_enroll_dialog
PAGE_ICON_PATH = Path(__file__).resolve().parent / "src" / "assets" / "page-icon.png"
load_dotenv(Path(__file__).resolve().parent / ".env")


def main():
    st.set_page_config(
        page_title='SmartClass AI - Classroom Learning',
        page_icon=str(PAGE_ICON_PATH),
        layout="wide",
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
        st.session_state["teacher_data"] = None

    if st.session_state.get("smartclass_page") == "ai":
        ai_chat_screen(
            initial_prompt=st.session_state.get("smartclass_ai_initial_prompt"),
            audience=st.session_state.get("smartclass_ai_audience"),
            display_name=st.session_state.get("smartclass_ai_name"),
        )
    else:
        match st.session_state['login_type']:
            case 'teacher':
                teacher_screen()
                if st.session_state.get("teacher_data") is None:
                    st.markdown("""
                        <style>
                          .stApp .st-key-teacher_auth_actions {
                            box-sizing:border-box !important;
                            width:min(1136px,calc(100% - 2rem)) !important;
                            max-width:1136px !important;
                            margin:1.2rem auto 0 !important;
                          }
                          .stApp div[data-testid="stTextInput"] {
                            box-sizing:border-box !important;
                            width:100% !important;
                            max-width:1136px !important;
                            margin-inline:auto !important;
                          }
                        </style>
                    """, unsafe_allow_html=True)

            case 'student':
                student_screen()

            case None:
                home_screen()


    join_code = st.query_params.get("join-code")
    if join_code:
        if st.session_state.get("login_type") != "student":
            st.session_state["login_type"] = "student"
            st.rerun()
        student_data = st.session_state.get("student_data")
        if isinstance(student_data, dict) and student_data.get("student_id") is not None:
            auto_enroll_dialog(join_code)
main()
