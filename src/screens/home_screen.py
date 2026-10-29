from pathlib import Path

import streamlit as st
from src.components.header import header_home
from src.components.footer import footer_home
from src.ui.base_layout import style_base_layout, style_background_home

ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"


def home_screen():


    header_home()
    style_background_home()
    style_base_layout()


    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("<h2 style='color:#000000'>I'm Student</h2>", unsafe_allow_html=True)
        st.image(str(ASSETS_DIR / "snapclass_student_logo.svg"), width=120)
        if st.button('Student Portal', type='primary', icon=':material/arrow_outward:', icon_position='right'):
            st.session_state['login_type']='student'
            st.rerun()

    with col2:
        st.markdown("<h2 style='color:#000000'>I'm Teacher</h2>", unsafe_allow_html=True)
        st.image(str(ASSETS_DIR / "snapclass_teacher_logo.svg"), width=120)
        if st.button('Teacher Portal', type='primary', icon=':material/arrow_outward:', icon_position='right'):
            st.session_state['login_type']='teacher'
            st.rerun()

    footer_home()
    