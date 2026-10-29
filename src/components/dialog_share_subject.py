import io
import os
from urllib.parse import urlencode, urlsplit, urlunsplit

import segno
import streamlit as st


def _get_app_base_url():
    configured_url = os.environ.get("SNAPCLASS_PUBLIC_URL")
    app_url = configured_url or st.context.url
    if not app_url:
        return None

    parsed_url = urlsplit(app_url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        return None

    base_path = parsed_url.path.rstrip("/")
    return urlunsplit((parsed_url.scheme, parsed_url.netloc, base_path, "", ""))


@st.dialog("Share Class Link")
def share_subject_dialog(subject_name, subject_code):
    app_base_url = _get_app_base_url()
    if app_base_url is None:
        st.error(
            "Could not determine the app URL. Set SNAPCLASS_PUBLIC_URL or open the app "
            "through its public URL."
        )
        return

    join_url = f"{app_base_url}/?{urlencode({'join-code': subject_code})}"
    st.write(f"Share **{subject_name}** with your students:")
    st.header("Scan to Join")

    qr = segno.make(join_url)
    out = io.BytesIO()
    qr.save(out, kind='png', scale=10, border=1)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('### Copy Link')
        st.code(join_url, language="text")
        st.code(subject_code, language="text")
        st.info('Copy this link to share on Whatsapp or Email')

    with col2:
        st.markdown('### Scan to Join')
        st.image(out.getvalue(), caption='QR code for class joining')