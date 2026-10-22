import dlib
import face_recognition_models
import numpy as np
import streamlit as st
from sklearn.svm import SVC

from src.database.db import get_all_students


@st.cache_resource
def load_dlib_models():
    detector = dlib.get_frontal_face_detector()
    shape_predictor = dlib.shape_predictor(
        face_recognition_models.pose_predictor_model_location()
    )
    face_recognition_model = dlib.face_recognition_model_v1(
        face_recognition_models.face_recognition_model_location()
    )
    return detector, shape_predictor, face_recognition_model


def get_face_embeddings(image_np):
    detector, shape_predictor, face_recognition_model = load_dlib_models()
    faces = detector(image_np, 1)

    encodings = []
    for face in faces:
        shape = shape_predictor(image_np, face)
        descriptor = face_recognition_model.compute_face_descriptor(
            image_np, shape, 1
        )
        encodings.append(np.asarray(descriptor, dtype=np.float64))

    return encodings


@st.cache_resource
def get_trained_model():
    students = get_all_students()
    if not students:
        return None

    embeddings = []
    student_ids = []
    for student in students:
        embedding = student.get("face_embedding")
        student_id = student.get("student_id")
        if embedding is None or student_id is None:
            continue

        embedding = np.asarray(embedding, dtype=np.float64)
        if embedding.shape != (128,) or not np.isfinite(embedding).all():
            continue

        embeddings.append(embedding)
        student_ids.append(student_id)

    if not embeddings:
        return None

    classifier = None
    if len(set(student_ids)) > 1:
        classifier = SVC(
            kernel="linear",
            class_weight="balanced",
        )
        classifier.fit(embeddings, student_ids)

    return {
        "clf": classifier,
        "x": embeddings,
        "y": student_ids,
    }


def train_classifier():
    get_trained_model.clear()
    return get_trained_model() is not None


def predict_attendance(class_image_np):
    encodings = get_face_embeddings(class_image_np)
    model_data = get_trained_model()

    if model_data is None:
        return {}, [], len(encodings)

    embeddings = model_data["x"]
    student_ids = model_data["y"]
    all_students = list(dict.fromkeys(student_ids))
    classifier = model_data["clf"]
    detected_students = {}

    for encoding in encodings:
        if classifier is None:
            predicted_id = all_students[0]
        else:
            predicted_id = classifier.predict([encoding])[0]

        matching_embeddings = [
            embedding
            for embedding, student_id in zip(embeddings, student_ids)
            if student_id == predicted_id
        ]
        best_match_score = min(
            np.linalg.norm(embedding - encoding)
            for embedding in matching_embeddings
        )

        if best_match_score <= 0.6:
            detected_students[predicted_id] = True

    return detected_students, all_students, len(encodings)
