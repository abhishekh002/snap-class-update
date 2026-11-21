from io import BytesIO
from uuid import uuid4

import streamlit as st
from PIL import Image


def _angle_photo_uploader(number, title, description, key):
    with st.container(border=True):
        st.markdown(f"""
            <div style="display:flex;align-items:center;gap:.7rem;margin-bottom:.25rem">
              <span style="display:grid;place-items:center;width:2rem;height:2rem;border-radius:50%;
                           background:#e2eadc;color:#385844;font-weight:700">{number}</span>
              <strong style="color:#385844;font-size:1.05rem">{title}</strong>
            </div>
            <div style="margin:0 0 .55rem 2.7rem;color:#65746a;font-size:.9rem">{description}</div>
        """, unsafe_allow_html=True)
        photo = st.file_uploader(
            f"Choose {title.lower()} photo",
            type=["jpg", "jpeg", "png"],
            key=key,
        )
        st.caption("JPG or PNG | Up to 200 MB per file")
        if photo:
            st.success(f"{photo.name} ready")
        return photo


@st.dialog("Capture or upload photos", width="large")
def add_photos_dialog():
    st.markdown("""
        <style>
            .photo-dialog-intro {
                margin:.2rem 0 1rem;padding:1.1rem 1.25rem;border:1px solid #dce1d6;
                border-left:5px solid #829a79;border-radius:16px;
                background:linear-gradient(125deg,#e6ecdf,#fffefa);
            }
            .photo-dialog-intro .eyebrow {
                color:#829a79;font-size:.7rem;font-weight:700;letter-spacing:.13em;text-transform:uppercase;
            }
            .photo-dialog-intro h3 { margin:.28rem 0 .35rem!important;color:#385844!important;font-size:1.3rem!important; }
            .photo-dialog-intro p { margin:0;color:#65746a!important;line-height:1.55; }
            [data-testid="stVerticalBlockBorderWrapper"] {
                border-color:#dce1d6;border-radius:16px;background:#fffefa;
            }
        </style>
        <section class="photo-dialog-intro">
          <span class="eyebrow">Smart attendance</span>
          <h3>Capture or upload classroom photos</h3>
          <p>Add one clear room photo, or use multiple angles for a large auditorium. Overlapping views are deduplicated during analysis.</p>
        </section>
    """, unsafe_allow_html=True)

    if "photo_dialog_batch_id" not in st.session_state:
        st.session_state.photo_dialog_batch_id = uuid4().hex
    batch_id = st.session_state.photo_dialog_batch_id

    if "photo_tab" not in st.session_state:
        st.session_state.photo_tab = "panoramic"

    t1, t2, t3 = st.columns(3)

    with t1:
        type_pano = "primary" if st.session_state.photo_tab == "panoramic" else "tertiary"
        if st.button("Auditorium: 3 angles", type=type_pano, width="stretch", help="Capture left, center, and right views for a large lecture hall."):
            st.session_state.photo_tab = "panoramic"

    with t2:
        type_camera = "primary" if st.session_state.photo_tab == "camera" else "tertiary"
        if st.button("Take a photo", type=type_camera, width="stretch"):
            st.session_state.photo_tab = "camera"

    with t3:
        type_upload = "primary" if st.session_state.photo_tab == "upload" else "tertiary"
        if st.button("Upload photos", type=type_upload, width="stretch"):
            st.session_state.photo_tab = "upload"

    selected_images = []

    if st.session_state.photo_tab == "panoramic":
        st.markdown("### Auditorium multi-shot roll call")
        st.caption("Capture any two or three views. SmartClass AI scans them together and removes duplicate student matches across overlapping angles.")
        c_left, c_center, c_right = st.columns(3)

        with c_left:
            p_left = _angle_photo_uploader("1", "Left wing", "Cover the left side of the room.", f"pano_left_{batch_id}")
            if p_left:
                selected_images.append(p_left.getvalue())

        with c_center:
            p_center = _angle_photo_uploader("2", "Center hall", "Capture the middle seating area.", f"pano_center_{batch_id}")
            if p_center:
                selected_images.append(p_center.getvalue())

        with c_right:
            p_right = _angle_photo_uploader("3", "Right wing", "Cover the right side of the room.", f"pano_right_{batch_id}")
            if p_right:
                selected_images.append(p_right.getvalue())

    elif st.session_state.photo_tab == "camera":
        st.markdown("### Take a classroom photo")
        st.caption("Frame the room so student faces are visible, then capture one clear image.")
        camera_key = f"dialog_cam_{batch_id}"
        cam_photo = st.camera_input("Take Snapshot", key=camera_key)
        if cam_photo:
            selected_images.append(cam_photo.getvalue())

    elif st.session_state.photo_tab == "upload":
        st.markdown("### Choose classroom photos")
        st.caption("Select one or more JPG or PNG photos. Up to 200 MB per file.")
        upload_key = f"dialog_upload_{batch_id}"
        uploaded_files = st.file_uploader(
            "Select image files",
            type=["jpg", "png", "jpeg"],
            accept_multiple_files=True,
            key=upload_key,
        )
        if uploaded_files:
            selected_images.extend(uploaded_file.getvalue() for uploaded_file in uploaded_files)

    st.divider()
    if selected_images:
        st.success(f"{len(selected_images)} photo(s) ready to add to attendance.")

    if st.button("Add photos to attendance", type="primary", width="stretch"):
        if not selected_images:
            st.warning("Add or capture at least one photo before clicking Add photos to attendance.")
            return

        st.session_state.setdefault("attendance_images", [])
        st.session_state.attendance_images.extend(
            Image.open(BytesIO(image_bytes)).copy()
            for image_bytes in selected_images
        )
        st.session_state.photo_dialog_batch_id = uuid4().hex
        st.toast(f"Added {len(selected_images)} photo(s) for attendance.")
        st.rerun()
