import streamlit as st
import streamlit.components.v1 as components
from src.components.header import LOGO_DATA_URI
from src.components.footer import footer_home
from src.components.dialog_ai_chat import open_ai_learning_dialog
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

    style_background_home()
    style_base_layout()

    st.markdown("""
        <style>
            .home-inline-logo { margin:0 0 1.35rem; }
            .home-inline-logo img { display:block; width:min(360px,100%); height:auto; }
            .home-intro {
                position:relative;
                display:grid;
                grid-template-columns:minmax(0,1.05fr) minmax(320px,.95fr);
                align-items:center;
                gap:clamp(1.5rem,4vw,4rem);
                box-sizing:border-box;
                width:min(1280px,calc(100% - 2rem));
                margin:.25rem auto 2.2rem;
                padding:clamp(1.5rem,4vw,3.4rem);
                overflow:hidden;
                border:1px solid rgba(130,154,121,.25);
                border-radius:30px;
                background:linear-gradient(118deg,rgba(255,254,250,.96),rgba(238,246,236,.94));
                box-shadow:0 24px 60px rgba(48,66,51,.11), inset 0 1px 0 rgba(255,255,255,.85);
                text-align:left;
            }
            .home-intro:before {
                content:""; position:absolute; width:360px; height:360px; right:-100px; top:-190px;
                border-radius:50%; background:radial-gradient(circle,rgba(216,239,155,.35),transparent 70%);
                pointer-events:none;
            }
            .home-intro .eyebrow {
                display: inline-block;
                margin-bottom: 1rem;
                padding: .45rem .8rem;
                border: 1px solid #cfe0d1;
                border-radius: 999px;
                background: #edf4e9;
                color: #385844;
                font-size: .69rem;
                font-weight: 800;
                letter-spacing: .13em;
            }
            .home-intro h1 {
                max-width:13ch;
                margin:0 0 .85rem !important;
                color: #26382e !important;
                font-family:'Lora',Georgia,serif !important;
                font-size:clamp(2.55rem,5vw,4.25rem) !important;
                letter-spacing:-.055em !important;
                line-height:1.02 !important;
            }
            .home-intro h1 span { color:#287477; }
            .home-intro p {
                max-width:48ch;
                margin:0;
                color: #65746a !important;
                font-size:1.04rem;
                line-height:1.7;
            }
            .home-hero-badges { display:flex; flex-wrap:wrap; gap:.55rem; margin-top:1.4rem; }
            .home-hero-badges span {
                display:inline-flex; align-items:center; gap:.4rem; padding:.48rem .68rem;
                border:1px solid #dce7d9; border-radius:999px; background:rgba(255,255,255,.7);
                color:#526457; font-size:.75rem; font-weight:650;
            }
            .home-hero-badges svg { width:16px; height:16px; color:#287477; }
            .home-hero-art { position:relative; z-index:1; width:100%; max-width:540px; justify-self:end; }
            .home-hero-art svg { display:block; width:100%; height:auto; overflow:visible; }
            .hero-float-a { animation:heroFloat 5.5s ease-in-out infinite; transform-origin:center; }
            .hero-float-b { animation:heroFloat 6.2s ease-in-out -1.7s infinite; transform-origin:center; }
            @keyframes heroFloat { 0%,100% { transform:translateY(0); } 50% { transform:translateY(-7px); } }
            .st-key-home_learning_hub {
                position:relative;
                overflow:hidden;
                box-sizing:border-box;
                width:min(1280px,calc(100% - 2rem));
                margin:1.45rem auto 1rem;
                padding:clamp(1.15rem,2.3vw,1.8rem);
                border:1px solid #cbded4;
                border-left:5px solid #36888a;
                border-radius:24px;
                background:linear-gradient(112deg,#fffefa 8%,#edf6f1 72%,#f5f1e8);
                box-shadow:0 18px 42px rgba(32,58,67,.09),inset 0 1px 0 rgba(255,255,255,.9);
            }
            .st-key-home_learning_hub:after {
                content:""; position:absolute; width:250px; height:250px; right:-90px; top:-145px;
                border-radius:50%; background:radial-gradient(circle,rgba(216,239,155,.34),transparent 72%);
                pointer-events:none;
            }
            .stApp div.st-key-home_learning_hub div[data-testid="stColumn"] {
                min-height:0 !important; padding:0 !important; border:0 !important;
                border-radius:0 !important; background:transparent !important; box-shadow:none !important;
                box-sizing:border-box !important;
            }
            .home-hub-lockup { position:relative; z-index:1; display:flex; align-items:center; gap:1.1rem; }
            .home-hub-mark {
                display:grid; flex:0 0 68px; width:68px; height:68px; place-items:center;
                border:1px solid #cde3df; border-radius:20px;
                background:linear-gradient(145deg,#e4f1ec,#d5e9e2);
                box-shadow:inset 0 1px 0 white,0 8px 18px rgba(40,89,82,.08);
            }
            .home-hub-mark svg { width:38px; height:38px; }
            .home-hub-copy-block { min-width:0; }
            .home-hub-copy-block p { margin-left:0 !important; margin-right:0 !important; }
            .st-key-home_learning_hub .stButton > button {
                position:relative; z-index:2; min-height:3.15rem; width:100%;
                border:1px solid #287477 !important; border-radius:999px !important;
                background:linear-gradient(135deg,#287477,#315b54) !important; color:#fffefa !important;
                box-shadow:0 9px 19px rgba(40,89,82,.2) !important; font-weight:700;
                transition:transform .18s ease,box-shadow .18s ease,background .18s ease;
            }
            .st-key-home_learning_hub .stButton > button:hover {
                transform:translateY(-2px); background:#203a43 !important;
                box-shadow:0 13px 24px rgba(40,89,82,.24) !important;
            }
            .home-hub-kicker {
                margin: 0 0 .35rem;
                color: #287477;
                font-size: .66rem;
                font-weight: 800;
                letter-spacing: .15em;
                text-transform: uppercase;
            }
            .home-hub-title {
                margin: 0 0 .35rem;
                color: #26382e;
                font-family:'Lora',Georgia,serif;
                font-size: clamp(1.25rem,2vw,1.65rem);
                font-weight: 700;
                letter-spacing:-.025em;
            }
            .home-hub-copy {
                margin: 0;
                color: #65746a;
                font-size:.92rem;
                line-height: 1.55;
            }
            .home-hub-tags {
                display: flex;
                flex-wrap: wrap;
                gap: 6px;
                margin-top: .65rem;
            }
            .home-hub-tags span {
                padding: 4px 9px;
                border: 1px solid #d2e5e2;
                border-radius: 999px;
                background: rgba(255,255,255,.72);
                color: #52745c;
                font-size: .72rem;
                font-weight: 600;
            }
            .st-key-home_portal_grid {
                box-sizing:border-box;
                width:min(1280px,calc(100% - 2rem));
                margin:0 auto;
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
                .home-intro { grid-template-columns:1fr; gap:1rem; margin-bottom:1.5rem; border-radius:22px; }
                .home-intro h1 { max-width:14ch; }
                .home-inline-logo img { width:min(320px,100%); }
                .home-hero-art { max-width:430px; justify-self:center; }
                .home-hub-lockup { align-items:flex-start; gap:.8rem; }
                .home-hub-mark { flex-basis:54px; width:54px; height:54px; border-radius:16px; }
                .home-hub-mark svg { width:32px; height:32px; }
                .portal-copy > p:not(.portal-kicker) { min-height: 0; }
            }
            @media (prefers-reduced-motion: reduce) {
                .hero-float-a, .hero-float-b { animation:none; }
            }
        </style>
        <section class="home-intro">
          <div class="home-intro-copy">
            <div class="home-inline-logo"><img src="__SMARTCLASS_LOGO__" alt="SmartClass AI logo"></div>
            <span class="eyebrow">SMART LEARNING · CONNECTED CLASSROOMS</span>
            <h1>Your classroom, <span>in sync.</span></h1>
            <p>Bring attendance, study support, and classroom tools together in one welcoming space built for students and teachers.</p>
            <div class="home-hero-badges">
              <span><svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="m4 10 4 4 8-8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>Smarter attendance</span>
              <span><svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M3 5.5c2.5-1 5-.7 7 1v9c-2-1.7-4.5-2-7-1v-9Zm14 0c-2.5-1-5-.7-7 1v9c2-1.7 4.5-2 7-1v-9Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>Learning tools</span>
              <span><svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><circle cx="7" cy="7" r="2.4" stroke="currentColor" stroke-width="1.6"/><path d="M2.8 15c.4-2.2 1.9-3.4 4.2-3.4 1.2 0 2.1.3 2.8.9M13 5.2h4m-2-2v4m-2.3 7.1 1.4 1.4 2.9-3.1" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>Connected classrooms</span>
            </div>
          </div>
          <div class="home-hero-art" role="img" aria-label="Illustration of students learning together with books, classroom notes, and a progress board">
            <svg viewBox="0 0 540 390" fill="none" xmlns="http://www.w3.org/2000/svg">
              <ellipse cx="270" cy="339" rx="202" ry="24" fill="#385844" fill-opacity=".09"/>
              <circle cx="270" cy="186" r="154" fill="#E9F2E5"/>
              <circle cx="390" cy="106" r="58" fill="#D8EF9B" fill-opacity=".46"/>
              <circle cx="133" cy="253" r="42" fill="#F3E6DB"/>
              <g class="hero-float-a" filter="url(#heroShadow)">
                <rect x="87" y="52" width="366" height="218" rx="22" fill="#FFFEFA" stroke="#DCE5D9" stroke-width="2"/>
                <rect x="108" y="76" width="324" height="153" rx="14" fill="#203A43"/>
                <path d="M132 105h113M132 122h76M132 139h93" stroke="#B9D8C0" stroke-width="7" stroke-linecap="round" opacity=".8"/>
                <path d="m277 178 32-31 28 16 42-48" stroke="#D8EF9B" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
                <circle cx="277" cy="178" r="6" fill="#D8EF9B"/><circle cx="309" cy="147" r="6" fill="#D8EF9B"/><circle cx="337" cy="163" r="6" fill="#D8EF9B"/><circle cx="379" cy="115" r="6" fill="#D8EF9B"/>
                <path d="M109 250h322" stroke="#E6ECE1" stroke-width="2"/>
                <circle cx="125" cy="250" r="5" fill="#B97453"/><circle cx="142" cy="250" r="5" fill="#829A79"/><circle cx="159" cy="250" r="5" fill="#36888A"/>
              </g>
              <g class="hero-float-b" filter="url(#heroShadow)">
                <rect x="28" y="158" width="94" height="96" rx="18" fill="#FFFEFA" stroke="#DCE5D9" stroke-width="2"/>
                <circle cx="75" cy="190" r="15" fill="#E7F1EA"/>
                <path d="M67 188a8 8 0 1 1 16 0 8 8 0 0 1-16 0Zm-6 23c1-9 6-13 14-13s13 4 14 13" stroke="#287477" stroke-width="3" stroke-linecap="round"/>
                <circle cx="105" cy="223" r="12" fill="#D8EF9B"/><path d="m100 223 3 3 6-7" stroke="#385844" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
              </g>
              <g filter="url(#heroShadow)">
                <rect x="398" y="211" width="112" height="91" rx="17" fill="#FFFEFA" stroke="#E6D4C7" stroke-width="2"/>
                <rect x="414" y="228" width="36" height="45" rx="7" fill="#F4E8DF"/>
                <path d="M422 250h20m-20 8h14" stroke="#B97453" stroke-width="3" stroke-linecap="round"/>
                <path d="M462 236h29m-29 12h22m-22 12h26" stroke="#A9BBA8" stroke-width="4" stroke-linecap="round"/>
                <circle cx="482" cy="281" r="10" fill="#36888A"/><path d="m478 281 3 3 5-6" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </g>
              <g filter="url(#heroShadow)">
                <rect x="184" y="263" width="176" height="78" rx="17" fill="#385844"/>
                <path d="M271 282c-13-8-27-8-41-4v40c14-4 28-4 41 5m0-41c13-8 27-8 41-4v40c-14-4-28-4-41 5m0-41v41" stroke="#FFFEFA" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="m304 286 5 5 10-12" stroke="#D8EF9B" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
              </g>
              <defs>
                <filter id="heroShadow" x="0" y="0" width="560" height="390" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB"><feDropShadow dx="0" dy="8" stdDeviation="9" flood-color="#26382E" flood-opacity=".11"/></filter>
              </defs>
            </svg>
          </div>
        </section>
    """.replace("__SMARTCLASS_LOGO__", LOGO_DATA_URI), unsafe_allow_html=True)

    with st.container(key="home_portal_grid"):
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

    with st.container(key="home_learning_hub"):
        hub_copy, hub_action = st.columns([5, 1.55], vertical_alignment="center", gap="large")
        with hub_copy:
            st.markdown("""
                <div class="home-hub-lockup">
                  <div class="home-hub-mark" aria-hidden="true">
                    <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M24 15c-6-5-13-5-19-2v25c7-3 13-2 19 3 6-5 12-6 19-3V13c-6-3-13-3-19 2Z" fill="#FFFEFA" stroke="#287477" stroke-width="2.3" stroke-linejoin="round"/>
                      <path d="M24 16v25m-13-20c3-1 6 0 9 2m-9 5c3-1 6 0 9 2m18-9c-3-1-6 0-9 2m9 5c-3-1-6 0-9 2" stroke="#829A79" stroke-width="2" stroke-linecap="round"/>
                      <path d="m37 4 2.2 4.8L44 11l-4.8 2.2L37 18l-2.2-4.8L30 11l4.8-2.2L37 4Z" fill="#B97453"/>
                    </svg>
                  </div>
                  <div class="home-hub-copy-block">
                    <p class="home-hub-kicker">SmartClass AI · Learning studio</p>
                    <p class="home-hub-title">Study together. Teach with fresh ideas.</p>
                    <p class="home-hub-copy">Explore topics, plan study time, and build classroom-ready lessons in one welcoming space.</p>
                    <div class="home-hub-tags"><span>Topic coach</span><span>Study planner</span><span>Lesson ideas</span><span>Class discussion</span></div>
                  </div>
                </div>
            """, unsafe_allow_html=True)
        with hub_action:
            if st.button(
                "Open AI Studio",
                key="home_ai_dashboard_button",
                icon=":material/arrow_forward:",
                icon_position="right",
                type="primary",
                width="stretch",
            ):
                open_ai_learning_dialog()
            with st.container(key="home_tutorial_action"):
                if st.button(
                    "Watch tutorial",
                    key="home_tutorial_button",
                    icon=":material/play_circle:",
                    type="secondary",
                    width="stretch",
                ):
                    _show_home_tutorial()

    st.markdown("""
        <style>
            .st-key-home_learning_hub .st-key-home_tutorial_action .stButton > button {
                min-height:2.65rem;
                border-color:#b97453 !important;
                background:#b97453 !important;
                color:#fffefa !important;
                box-shadow:0 7px 16px rgba(185,116,83,.16) !important;
            }
            .st-key-home_learning_hub .st-key-home_tutorial_action .stButton > button:hover {
                border-color:#965b41 !important;
                background:#965b41 !important;
            }
        </style>
    """, unsafe_allow_html=True)
    footer_home()

