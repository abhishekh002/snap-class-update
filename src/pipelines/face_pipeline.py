import dlib
import face_recognition_models
import numpy as np
import streamlit as st

from src.database.db import get_all_students

FACE_MATCH_THRESHOLD = 0.6
FACE_MATCH_MARGIN = 0.05
FACE_DETECTION_UPSAMPLE = 2


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
    faces = detector(image_np, FACE_DETECTION_UPSAMPLE)

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

    return {
        "x": embeddings,
        "y": student_ids,
    }


def train_classifier():
    get_trained_model.clear()
    return get_trained_model() is not None


def predict_attendance(class_image_np, candidate_student_ids=None):
    encodings = get_face_embeddings(class_image_np)
    model_data = get_trained_model()

    if model_data is None:
        return {}, [], len(encodings)

    candidate_ids = (
        None
        if candidate_student_ids is None
        else {str(student_id) for student_id in candidate_student_ids}
    )
    candidate_profiles = [
        (embedding, student_id)
        for embedding, student_id in zip(model_data["x"], model_data["y"])
        if candidate_ids is None or str(student_id) in candidate_ids
    ]
    embeddings = [profile[0] for profile in candidate_profiles]
    student_ids = [profile[1] for profile in candidate_profiles]
    all_students = list(dict.fromkeys(student_ids))
    detected_students = {}

    for encoding in encodings:
        distances_by_student = {}
        for embedding, student_id in zip(embeddings, student_ids):
            distance = np.linalg.norm(embedding - encoding)
            distances_by_student[student_id] = min(
                distance,
                distances_by_student.get(student_id, float("inf")),
            )

        closest_matches = sorted(
            distances_by_student.items(),
            key=lambda match: match[1],
        )
        if not closest_matches:
            continue

        best_student_id, best_distance = closest_matches[0]
        is_ambiguous = (
            len(closest_matches) > 1
            and closest_matches[1][1] - best_distance <= FACE_MATCH_MARGIN
        )
        if best_distance <= FACE_MATCH_THRESHOLD and not is_ambiguous:
            detected_students[best_student_id] = True

    return detected_students, all_students, len(encodings)
