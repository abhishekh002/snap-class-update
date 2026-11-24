import base64
from pathlib import Path

import streamlit as st


LOGO_PATH = Path(__file__).resolve().parents[1] / "assets" / "smartclass-ai-logo-animated.svg"
LOGO_DATA_URI = f"data:image/svg+xml;base64,{base64.b64encode(LOGO_PATH.read_bytes()).decode('ascii')}"


def header_home():

    logo_url = LOGO_DATA_URI
    st.markdown(f"""
        <div style="box-sizing:border-box; display:flex; align-items:center; justify-content:flex-start; width:min(1280px,calc(100% - 2rem)); margin:18px auto 12px; padding-left:clamp(1.5rem,4vw,3.4rem);">
            <img src='{logo_url}' alt='SmartClass AI logo' style='display:block; width:min(360px,90vw); height:auto;' />
        </div>   
                
                """, unsafe_allow_html=True)


def header_dashboard():

    logo_url = LOGO_DATA_URI
    st.markdown(f"""
        <div style="display:flex; align-items:center; justify-content:center">
            <img src='{logo_url}' alt='SmartClass AI logo' style='width:min(320px, 90vw); height:auto;' />
        </div>   
                
                """, unsafe_allow_html=True)
