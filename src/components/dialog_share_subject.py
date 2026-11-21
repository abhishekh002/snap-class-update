import io
import os
from html import escape
from urllib.parse import urlencode, urlsplit, urlunsplit

import segno
import streamlit as st


def _get_app_base_url():
    configured_url = (
        os.environ.get("AI_ATTENDANCE_PUBLIC_URL")
        or st.secrets.get("public_app_url")
        or os.environ.get("SNAPCLASS_PUBLIC_URL")
    )
    app_url = configured_url or st.context.url
    if not app_url:
        return None

    parsed_url = urlsplit(app_url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        return None

    base_path = parsed_url.path.rstrip("/")
    return urlunsplit((parsed_url.scheme, parsed_url.netloc, base_path, "", ""))


@st.dialog("Share Class Link", width="large")
def share_subject_dialog(subject_name, subject_code):
    app_base_url = _get_app_base_url()
    if app_base_url is None:
        st.error(
            "Could not determine the app URL. Set AI_ATTENDANCE_PUBLIC_URL or "
            "public_app_url, or open the app through its public URL."
        )
        return

    join_url = f"{app_base_url}/?{urlencode({'join-code': subject_code})}"
    st.markdown(f"""
        <style>
            .share-class-intro {{
                margin: .2rem 0 1rem;
                padding: 1.1rem 1.25rem;
                border: 1px solid #dce1d6;
                border-left: 5px solid #829a79;
                border-radius: 16px;
                background: linear-gradient(125deg, #e6ecdf, #fffefa);
            }}
            .share-class-intro .eyebrow {{
                color: #829a79;
                font-size: .7rem;
                font-weight: 700;
                letter-spacing: .13em;
                text-transform: uppercase;
            }}
            .share-class-intro h3 {{
                margin: .28rem 0 .35rem !important;
                color: #385844 !important;
                font-size: 1.35rem !important;
            }}
            .share-class-intro p {{ margin: 0; color: #65746a !important; line-height: 1.5; }}
            .share-qr-heading {{ color:#385844; font-weight:700; font-size:1.15rem; margin-bottom:.4rem; }}
            .share-link-heading {{ color:#385844; font-weight:700; font-size:1.15rem; margin-bottom:.35rem; }}
            [data-testid="stCode"] {{ border:1px solid #dce1d6; border-radius:12px; }}
        </style>
        <section class="share-class-intro">
          <span class="eyebrow">Class invitation</span>
          <h3>{escape(str(subject_name))}</h3>
          <p>Share this class link or let students scan the QR code to join.</p>
        </section>
    """, unsafe_allow_html=True)

    qr = segno.make(join_url)
    out = io.BytesIO()
    qr.save(out, kind='png', scale=10, border=1)

    col1, col2 = st.columns([1.15, 0.85], gap="large", vertical_alignment="center")

    with col1:
        with st.container(border=True):
            st.markdown('<div class="share-link-heading">Copy link</div>', unsafe_allow_html=True)
            st.caption("Students can open this link to join the class.")
            st.code(join_url, language="text")
            st.markdown('<div class="share-link-heading">Class join code</div>', unsafe_allow_html=True)
            st.code(str(subject_code), language="text")
            st.caption("Use the copy button on either code block to share it by message or email.")

    with col2:
        with st.container(border=True):
            st.markdown('<div class="share-qr-heading">Scan to join</div>', unsafe_allow_html=True)
            st.image(out.getvalue(), width=220)
            st.caption("Open your phone camera and point it at this code.")
