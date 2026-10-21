import streamlit as st
from src.components.footer import footer_dashboard
from src.ui.base_layout import style_background_dashboard, style_base_layout

from src.components.header import header_dashboard
import numpy as np


from PIL import Image

def student_screen():

    style_background_dashboard()
    style_base_layout()
    c1, c2 = st.columns(2, vertical_alignment="center", gap="large")
    with c1:
        header_dashboard()
    with c2:
        if st.button("GO BACK TO HOME", type="secondary", key="loginbackbtn", shortcut="Ctrl+Backspace"):
            st.session_state['login_type'] = None
            st.rerun()

    st.header('Login using Face_ID',text_alignment='center')
    st.space()
    st.space()
    photo = st.camera_input("Position your face in the center")
    
    if photo:
        np.array(Image.open(photo))

    footer_dashboard()