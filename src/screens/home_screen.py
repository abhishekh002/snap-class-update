import streamlit as st
import streamlit.components.v1 as components
from src.components.header import header_home
from src.components.footer import footer_home
from src.components.dialog_ai_chat import ai_chat_dialog
from src.ui.base_layout import style_base_layout, style_background_home

@st.dialog("SnapClass AI walkthrough", width="large")
def _show_home_tutorial():
    components.html(
        """
        <div style="width:100%; margin:0 auto; padding:12px; border-radius:24px; background:linear-gradient(135deg,#111c35,#174f62 58%,#67c7aa); box-shadow:0 24px 60px rgba(15,35,60,.22);">
            <div style="padding:10px 10px 16px; color:#f8fbff; font:600 14px/1.4 sans-serif; letter-spacing:.04em;">A QUICK TOUR OF YOUR CLASSROOM</div>
            <iframe
                width="100%"
                height="500"
                src="https://www.youtube.com/embed/3TwQtB3KcM4?rel=0"
                title="SnapClass AI walkthrough"
                frameborder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                referrerpolicy="strict-origin-when-cross-origin"
                allowfullscreen
                style="border-radius:1rem;">
            </iframe>
        </div>
        """,
        height=570,
    )


def home_screen():

    header_home()
    style_background_home()
    style_base_layout()

    st.markdown("""
        <style>
            .home-intro {
                max-width: 760px;
                margin: .25rem auto 2.4rem;
                text-align: center;
            }
            .home-intro .eyebrow {
                display: inline-block;
                margin-bottom: .85rem;
                padding: .4rem .8rem;
                border: 1px solid #dce1d6;
                border-radius: 999px;
                background: #e2eadc;
                color: #385844;
                font-size: .75rem;
                font-weight: 700;
                letter-spacing: .12em;
            }
            .home-intro h1 {
                margin: 0 0 .75rem !important;
                color: #26382e !important;
                font-size: clamp(2.2rem, 5vw, 3.5rem) !important;
                line-height: 1.05 !important;
            }
            .home-intro p {
                max-width: 52ch;
                margin: 0 auto;
                color: #65746a !important;
                font-size: 1.05rem;
                line-height: 1.65;
            }
            .portal-copy .portal-kicker {
                display: inline-flex;
                margin: 0 0 .7rem;
                padding: .38rem .7rem;
                border: 1px solid #dce7d9;
                border-radius: 999px;
                background: #eef3eb;
                color: #52745c;
                font-size: .68rem;
                font-weight: 700;
                letter-spacing: .12em;
                text-transform: uppercase;
            }
            .portal-copy h2 {
                margin: 0 0 .4rem !important;
                color: #385844 !important;
                font-size: clamp(1.65rem, 2.6vw, 1.95rem) !important;
                line-height: 1.2 !important;
            }
            .portal-copy h2 a,
            .portal-copy h2 [data-testid="stHeaderLink"] {
                display: none !important;
            }
            .portal-copy > p:not(.portal-kicker) {
                min-height: 2.6rem;
                margin: 0 0 .6rem;
                color: #65746a !important;
                line-height: 1.55;
            }
            .portal-highlights {
                display: flex;
                flex-wrap: wrap;
                gap: 6px;
                margin: .1rem 0 .65rem;
            }
            .portal-highlights span {
                padding: 5px 9px;
                border: 1px solid #e1e7dd;
                border-radius: 999px;
                background: #f7f8f3;
                color: #65746a;
                font-size: .73rem;
                font-weight: 600;
            }
            .portal-art {
                display: grid;
                width: 70px;
                height: 70px;
                margin: .25rem 0 .75rem;
                place-items: center;
                border: 1px solid #d7e2d5;
                border-radius: 21px;
                background: linear-gradient(145deg, #edf3e9, #dce8d9);
                box-shadow: inset 0 1px 0 rgba(255,255,255,.8),
                            0 8px 18px rgba(48,66,51,.06);
                transition: transform .2s ease, box-shadow .2s ease;
            }
            .portal-art svg { width: 40px; height: 40px; }
            .stApp div[data-testid="stColumn"]:has(.portal-copy) {
                border: 1px solid #dce5d9 !important;
                border-top: 4px solid #829a79 !important;
                padding: 1.45rem !important;
                min-height: 0;
                background: linear-gradient(155deg,#fffefa 35%,#f7f8f2) !important;
                transition: transform .2s ease, box-shadow .2s ease;
            }
            .stApp div[data-testid="stColumn"]:has(.portal-student) {
                border-color: #c9e0dd !important;
                border-top-color: #36888a !important;
                background: linear-gradient(155deg,#fffefa 22%,#e8f4f1) !important;
            }
            .stApp div[data-testid="stColumn"]:has(.portal-teacher) {
                border-color: #eadbd1 !important;
                border-top-color: #bd7654 !important;
                background: linear-gradient(155deg,#fffefa 25%,#f8eee7) !important;
            }
            .portal-student .portal-kicker {
                border-color: #cde3df !important;
                background: #e8f4f1 !important;
                color: #287477 !important;
            }
            .stApp div[data-testid="stColumn"]:has(.portal-student) .portal-highlights span {
                border-color: #d2e5e2;
                background: #f4faf8;
            }
            .stApp div[data-testid="stColumn"]:has(.portal-student) .portal-art {
                border-color: #cde3df;
                background: linear-gradient(145deg,#e5f2ef,#cfe7e2);
            }
            .stApp div[data-testid="stColumn"]:has(.portal-student) .stButton > button[kind="primary"] {
                border-color: #287477 !important;
                background: #287477 !important;
            }
            .portal-teacher .portal-kicker {
                border-color: #efddd2 !important;
                background: #fbf0e9 !important;
                color: #a45f43 !important;
            }
            .stApp div[data-testid="stColumn"]:has(.portal-teacher) .portal-highlights span {
                border-color: #eddfd5;
                background: #fff8f3;
            }
            .stApp div[data-testid="stColumn"]:has(.portal-teacher) .portal-art {
                border-color: #ead6c9;
                background: linear-gradient(145deg,#fbf0e9,#f1dfd2);
            }
            .stApp div[data-testid="stColumn"]:has(.portal-teacher) .stButton > button[kind="primary"] {
                border-color: #a96043 !important;
                background: #a96043 !important;
            }
            .stApp div[data-testid="stColumn"]:has(.portal-copy):hover {
                transform: translateY(-4px);
                box-shadow: 0 20px 44px rgba(48,66,51,.13) !important;
            }
            .stApp div[data-testid="stColumn"]:has(.portal-copy) .stButton > button {
                min-height: 2.8rem;
                padding-block: .42rem !important;
                font-size: .96rem;
                letter-spacing: .01em;
                box-shadow: 0 7px 16px rgba(48,66,51,.13);
            }
            @media (max-width: 640px) {
                .home-intro { margin-bottom: 1.5rem; }
                .portal-copy > p:not(.portal-kicker) { min-height: 0; }
            }
        </style>
        <div class="home-intro">
            <span class="eyebrow">SMART LEARNING · CONNECTED CLASSROOMS</span>
            <h1>Your classroom, in sync.</h1>
            <p>Attendance, study support, and classroom tools come together in one simple space.</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("""
            <div class="portal-copy portal-student">
              <p class="portal-kicker">For students</p>
              <h2>Student space</h2>
              <p>Check in to class and continue learning with your teacher.</p>
              <div class="portal-highlights"><span>Face ID check-in</span><span>Course notes</span></div>
            </div>
            <div class="portal-art" aria-hidden="true">
              <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M24 14c-6-4-12-4-17-2v23c5-2 11-2 17 2m0-23c6-4 12-4 17-2v23c-5-2-11-2-17 2m0-23v23" stroke="#385844" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M31 14v7l3-2 3 2v-8" fill="#B97453"/>
              </svg>
            </div>
        """, unsafe_allow_html=True)
        if st.button('Student Portal', type='primary', icon=':material/arrow_outward:', icon_position='right', width='stretch'):
            st.session_state['login_type']='student'
            st.rerun()

    with col2:
        st.markdown("""
            <div class="portal-copy portal-teacher">
              <p class="portal-kicker">For teachers</p>
              <h2>Teacher space</h2>
              <p>Manage attendance, subjects, notes, and classroom activity.</p>
              <div class="portal-highlights"><span>AI attendance</span><span>Class tools</span></div>
            </div>
            <div class="portal-art" aria-hidden="true">
              <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="m5 17 19-9 19 9-19 9-19-9Z" stroke="#385844" stroke-width="2.6" stroke-linejoin="round"/>
                <path d="M12 21v11c7 5 17 5 24 0V21l-12 6-12-6Z" fill="#829A79"/>
                <path d="M42 18v13m0 0-3 5m3-5 3 5" stroke="#B97453" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
        """, unsafe_allow_html=True)
        if st.button('Teacher Portal', type='primary', icon=':material/arrow_outward:', icon_position='right', width='stretch'):
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

