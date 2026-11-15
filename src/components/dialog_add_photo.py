from io import BytesIO
from uuid import uuid4

import streamlit as st
from PIL import Image

@st.dialog("Capture or upload photos", width="large")
def add_photos_dialog():
    st.write("Add classroom photos to scan for attendance.")

    if "photo_dialog_batch_id" not in st.session_state:
        st.session_state.photo_dialog_batch_id = uuid4().hex
    batch_id = st.session_state.photo_dialog_batch_id

    if "photo_tab" not in st.session_state:
        st.session_state.photo_tab = "panoramic"

    t1, t2, t3 = st.columns(3)

    with t1:
        type_pano = "primary" if st.session_state.photo_tab == "panoramic" else "tertiary"
        if st.button("📐 Panoramic Multi-Shot", type=type_pano, width="stretch", help="For large lecture halls (100-250 students)"):
            st.session_state.photo_tab = "panoramic"

    with t2:
        type_camera = "primary" if st.session_state.photo_tab == "camera" else "tertiary"
        if st.button("📸 Single Camera", type=type_camera, width="stretch"):
            st.session_state.photo_tab = "camera"

    with t3:
        type_upload = "primary" if st.session_state.photo_tab == "upload" else "tertiary"
        if st.button("📁 Upload Photos", type=type_upload, width="stretch"):
            st.session_state.photo_tab = "upload"

    selected_images = []

    if st.session_state.photo_tab == "panoramic":
        st.info("📐 **Auditorium Multi-Shot Roll Call**: Take 2 or 3 quick angle photos (e.g. Left Wing, Center Hall, Right Wing). The AI will scan all photos together and automatically deduplicate students visible in overlapping angles.")
        c_left, c_center, c_right = st.columns(3)

        with c_left:
            st.markdown("##### 1. Left Wing")
            p_left = st.file_uploader("Upload Left Angle", type=["jpg", "png", "jpeg"], key=f"pano_left_{batch_id}")
            if p_left:
                selected_images.append(p_left.getvalue())

        with c_center:
            st.markdown("##### 2. Center Hall")
            p_center = st.file_uploader("Upload Center Angle", type=["jpg", "png", "jpeg"], key=f"pano_center_{batch_id}")
            if p_center:
                selected_images.append(p_center.getvalue())

        with c_right:
            st.markdown("##### 3. Right Wing")
            p_right = st.file_uploader("Upload Right Angle", type=["jpg", "png", "jpeg"], key=f"pano_right_{batch_id}")
            if p_right:
                selected_images.append(p_right.getvalue())

    elif st.session_state.photo_tab == "camera":
        camera_key = f"dialog_cam_{batch_id}"
        cam_photo = st.camera_input("Take Snapshot", key=camera_key)
        if cam_photo:
            selected_images.append(cam_photo.getvalue())

    elif st.session_state.photo_tab == "upload":
        upload_key = f"dialog_upload_{batch_id}"
        uploaded_files = st.file_uploader(
            "Choose image files (Select one or multiple photos)",
            type=["jpg", "png", "jpeg"],
            accept_multiple_files=True,
            key=upload_key,
        )
        if uploaded_files:
            selected_images.extend(uploaded_file.getvalue() for uploaded_file in uploaded_files)

    st.divider()
    if st.button("Done & Add to Attendance", type="primary", width="stretch"):
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
