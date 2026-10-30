from io import BytesIO
from uuid import uuid4

import streamlit as st
from PIL import Image

@st.dialog("Capture or upload photos")
def add_photos_dialog():
    st.write("Add classroom photos to scan for attendance.")

    if "photo_dialog_batch_id" not in st.session_state:
        st.session_state.photo_dialog_batch_id = uuid4().hex
    batch_id = st.session_state.photo_dialog_batch_id
    camera_key = f"dialog_cam_{batch_id}"
    upload_key = f"dialog_upload_{batch_id}"

    if "photo_tab" not in st.session_state:
        st.session_state.photo_tab = "camera"

    t1, t2 = st.columns(2)

    with t1:
        type_camera = "primary" if st.session_state.photo_tab == "camera" else "tertiary"
        if st.button("Camera", type=type_camera, width="stretch"):
            st.session_state.photo_tab = "camera"

    with t2:
        type_upload = "primary" if st.session_state.photo_tab == "upload" else "tertiary"
        if st.button("Upload photos", type=type_upload, width="stretch"):
            st.session_state.photo_tab = "upload"

    selected_images = []
    if st.session_state.photo_tab == "camera":
        cam_photo = st.camera_input("Take Snapshot", key=camera_key)
        if cam_photo:
            selected_images.append(cam_photo.getvalue())

    if st.session_state.photo_tab == "upload":
        uploaded_files = st.file_uploader(
            "Choose image files",
            type=["jpg", "png", "jpeg"],
            accept_multiple_files=True,
            key=upload_key,
        )
        if uploaded_files:
            selected_images.extend(uploaded_file.getvalue() for uploaded_file in uploaded_files)

    st.divider()
    if st.button("Done", type="primary", width="stretch"):
        if not selected_images:
            st.warning("Add or capture at least one photo before clicking Done.")
            return

        st.session_state.setdefault("attendance_images", [])
        st.session_state.attendance_images.extend(
            Image.open(BytesIO(image_bytes)).copy()
            for image_bytes in selected_images
        )
        st.session_state.photo_dialog_batch_id = uuid4().hex
        st.toast(f"Added {len(selected_images)} photo(s) for attendance.")
        st.rerun()
