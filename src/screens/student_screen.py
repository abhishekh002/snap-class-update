import numpy as np
import streamlit as st
from PIL import Image

from src.components.footer import footer_dashboard
from src.components.header import header_dashboard
from src.database.db import create_student, get_all_students
from src.pipelines.face_pipeline import (
    get_face_embeddings,
    predict_attendance,
    train_classifier,
)
from src.pipelines.voice_pipeline import get_voice_embedding
from src.ui.base_layout import style_background_dashboard, style_base_layout


def student_dashboard():
    st.header("DASHBOARD HERE")


def student_screen():
    style_background_dashboard()
    style_base_layout()

    if st.session_state.get("student_data") is not None:
        student_dashboard()
        return

    col1, col2 = st.columns(2, vertical_alignment="center", gap="large")
    with col1:
        header_dashboard()
    with col2:
        if st.button(
            "GO BACK TO HOME",
            type="secondary",
            key="loginbackbtn",
            shortcut="Ctrl+Backspace",
        ):
            st.session_state["login_type"] = None
            st.rerun()

    st.header("Login using Face_ID", text_alignment="center")
    st.space()
    st.space()

    show_registration = False
    photo = st.camera_input("Position your face in the center")

    if photo is not None:
        image = np.array(Image.open(photo))

        with st.spinner("AI is scanning..."):
            detected_students, _, num_faces = predict_attendance(image)

        if num_faces == 0:
            st.warning("No face detected. Please try again.")
        elif num_faces > 1:
            st.warning("Multiple faces found. Please make sure only your face is visible.")
        elif detected_students:
            student_id = next(iter(detected_students))
            students = get_all_students()
            student = next(
                (
                    record
                    for record in students
                    if str(record.get("student_id")) == str(student_id)
                ),
                None,
            )

            if student is None:
                st.error("The recognized student profile could not be found.")
            else:
                st.session_state.is_logged_in = True
                st.session_state.user_role = "student"
                st.session_state.student_data = student
                st.toast(f"Welcome back, {student['name']}!")
                st.rerun()
        else:
            st.info("Face not recognized. You can register a new student profile.")
            show_registration = True

    if show_registration:
        with st.container(border=True):
            st.header("Register new Profile")
            new_name = st.text_input(
                "Enter your name",
                placeholder="E.g. Abhishekh Tiwari",
            )

            st.subheader("Optional: Voice Enrollment")
            st.info("Enroll your voice for voice-only attendance.")
            audio_data = st.audio_input(
                "Record a short phrase, such as “I am present. My name is ...”"
            )

            if st.button("Create Account", type="primary"):
                if not new_name.strip():
                    st.warning("Please enter your name.")
                elif photo is None:
                    st.error("Please capture your face before registering.")
                else:
                    with st.spinner("Creating profile..."):
                        encodings = get_face_embeddings(image)

                        if not encodings:
                            st.error(
                                "Could not capture facial features. Please take another photo."
                            )
                        else:
                            face_embedding = encodings[0].tolist()
                            voice_embedding = (
                                get_voice_embedding(audio_data.getvalue())
                                if audio_data is not None
                                else None
                            )
                            response_data = create_student(
                                new_name.strip(),
                                face_embedding=face_embedding,
                                voice_embedding=voice_embedding,
                            )

                            if response_data:
                                train_classifier()
                                st.session_state.is_logged_in = True
                                st.session_state.user_role = "student"
                                st.session_state.student_data = response_data[0]
                                st.toast(f"Profile created! Hi, {new_name.strip()}!")
                                st.rerun()
                            else:
                                st.error("Could not create the student profile.")

    footer_dashboard()
