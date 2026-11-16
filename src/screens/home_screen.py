from pathlib import Path

import streamlit as st
from src.components.header import header_home
from src.components.footer import footer_home
from src.components.dialog_ai_chat import ai_chat_dialog
from src.ui.base_layout import style_base_layout, style_background_home

ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
TUTORIAL_VIDEO_PATH = ASSETS_DIR / "SnapClass_personal_web.mp4"


@st.dialog("SnapClass tutorial", width="large")
def _show_home_tutorial():
    st.video(str(TUTORIAL_VIDEO_PATH))


def home_screen():

    header_home()
    style_background_home()
    style_base_layout()

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("<h2 style='color:#000000'>Student Login</h2>", unsafe_allow_html=True)
        st.image(str(ASSETS_DIR / "snapclass_student_logo.svg"), width=120)
        if st.button('Student Portal', type='primary', icon=':material/arrow_outward:', icon_position='right'):
            st.session_state['login_type']='student'
            st.rerun()

    with col2:
        st.markdown("<h2 style='color:#000000'>Teacher Login</h2>", unsafe_allow_html=True)
        st.image(str(ASSETS_DIR / "snapclass_teacher_logo.svg"), width=120)
        if st.button('Teacher Portal', type='primary', icon=':material/arrow_outward:', icon_position='right'):
            st.session_state['login_type']='teacher'
            st.rerun()

    footer_home()

    st.markdown(
        """
        <style>
            .st-key-home_tutorial_button,
            .st-key-home_ai_button {
                position: fixed;
                right: 1.5rem;
                z-index: 9999;
                width: 10rem;
            }
            .st-key-home_tutorial_button {
                bottom: 5.5rem;
            }
            .st-key-home_ai_button {
                bottom: 1.5rem;
            }
            .st-key-home_tutorial_button button,
            .st-key-home_ai_button button {
                border-radius: 999px !important;
                box-shadow: 0 6px 18px rgba(0, 0, 0, 0.25) !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Watch tutorial", key="home_tutorial_button", icon=":material/play_circle:"):
        _show_home_tutorial()
    if st.button("AI Assistant", key="home_ai_button", icon=":material/smart_toy:"):
        ai_chat_dialog()
    