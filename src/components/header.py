import base64
from pathlib import Path

import streamlit as st


LOGO_PATH = Path(__file__).resolve().parents[1] / "assets" / "snapclass-logo-animated.svg"
LOGO_DATA_URI = f"data:image/svg+xml;base64,{base64.b64encode(LOGO_PATH.read_bytes()).decode('ascii')}"


def header_home():

    logo_url = LOGO_DATA_URI
    st.markdown(f"""
        <div style="display:flex; align-items:center; justify-content:center; margin-bottom:30px; margin-top:30px">
            <img src='{logo_url}' alt='Snap Class logo' style='width:min(460px, 95vw); height:auto;' />
        </div>   
                
                """, unsafe_allow_html=True)


def header_dashboard():

    logo_url = LOGO_DATA_URI
    st.markdown(f"""
        <div style="display:flex; align-items:center; justify-content:center">
            <img src='{logo_url}' alt='Snap Class logo' style='width:min(280px, 90vw); height:auto;' />
        </div>   
                
                """, unsafe_allow_html=True)