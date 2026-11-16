import os
from datetime import date
from pathlib import Path
from uuid import uuid4

import streamlit as st
from supabase import create_client

from src.database.config import supabase


ASSESSMENT_BUCKET = "course-assessments"
MAX_SUBMISSION_SIZE = 20 * 1024 * 1024
ALLOWED_FILE_TYPES = {"pdf", "docx", "txt", "png", "jpg", "jpeg", "pptx"}


def _validate_file(file_name: str, file_bytes: bytes) -> None:
    if Path(file_name).suffix.lower().lstrip(".") not in ALLOWED_FILE_TYPES:
        raise ValueError("Use a PDF, DOCX, TXT, PNG, JPG, JPEG, or PPTX file.")
    if not file_bytes:
        raise ValueError("Choose a non-empty file.")
    if len(file_bytes) > MAX_SUBMISSION_SIZE:
        raise ValueError("The file must be 20 MB or smaller.")


def _upload_file(
    folder: str,
    file_name: str,
    file_bytes: bytes,
    content_type: str,
    storage_client=None,
) -> str:
    safe_name = Path(file_name).name.replace(" ", "_")
    storage_path = f"{folder}/{uuid4().hex}_{safe_name}"
    client = storage_client or supabase
    client.storage.from_(ASSESSMENT_BUCKET).upload(
        storage_path,
        file_bytes,
        {"content-type": content_type or "application/octet-stream", "upsert": "false"},
    )
    return storage_path


def _get_assessment_admin_client():
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not service_key:
        service_key = st.secrets.get("supabase_service_role_key")
    if not service_key:
        raise RuntimeError(
            "Configure the server-only supabase_service_role_key in Streamlit secrets "
            "to publish assessments."
        )
    return create_client(st.secrets["supabase_url"], str(service_key))


def create_assessment(
    *,
    note_id: str,
    subject_id: int | str,
    teacher_id: int | str,
    title: str,
    instructions: str,
    due_date: date,
    submission_mode: str,
    max_score: float,
    assignment_file_name: str | None = None,
    assignment_file_bytes: bytes | None = None,
    assignment_file_type: str = "",
) -> dict:
    if submission_mode not in {"online", "physical"}:
        raise ValueError("Choose either file upload or physical submission.")
    if max_score <= 0:
        raise ValueError("Maximum score must be greater than zero.")
    if due_date < date.today():
        raise ValueError("The submission deadline cannot be in the past.")
    if not title.strip():
        raise ValueError("Enter an assessment title.")
    if not instructions.strip() and not assignment_file_bytes:
        raise ValueError("Add assessment instructions or attach the assessment sheet.")

    admin_client = _get_assessment_admin_client()
    owned_subject = (
        admin_client.table("subjects")
        .select("subject_id")
        .eq("subject_id", subject_id)
        .eq("teacher_id", teacher_id)
        .limit(1)
        .execute()
    )
    if not owned_subject.data:
        raise PermissionError("You can only publish assessments for your own subjects.")

    assessment_id = str(uuid4())
    assignment_file_path = None
    if assignment_file_bytes and assignment_file_name:
        _validate_file(assignment_file_name, assignment_file_bytes)
        assignment_file_path = _upload_file(
            f"{assessment_id}/assignment",
            assignment_file_name,
            assignment_file_bytes,
            assignment_file_type,
            storage_client=admin_client,
        )

    assessment = {
        "id": assessment_id,
        "note_id": str(note_id),
        "subject_id": str(subject_id),
        "teacher_id": str(teacher_id),
        "title": title.strip(),
        "instructions": instructions.strip(),
        "due_date": due_date.isoformat(),
        "submission_mode": submission_mode,
        "max_score": max_score,
        "assignment_file_name": assignment_file_name,
        "assignment_file_path": assignment_file_path,
        "results_released": False,
    }
    response = admin_client.table("course_assessments").insert(assessment).execute()
    if not response.data:
        raise RuntimeError("The assessment was not saved.")
    return response.data[0]


def get_teacher_assessments(note_id: str, teacher_id: int | str) -> list[dict]:
    _require_teacher(teacher_id)
    admin_client = _get_assessment_admin_client()
    response = (
        admin_client.table("course_assessments")
        .select("*")
        .eq("note_id", str(note_id))
        .eq("teacher_id", str(teacher_id))
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def get_student_assessments(
    note_id: str, subject_id: int | str, student_id: int | str
) -> list[dict]:
    student = st.session_state.get("student_data")
    if not student or str(student.get("student_id")) != str(student_id):
        raise PermissionError("Log in as the student to view assessments.")

    admin_client = _get_assessment_admin_client()
    enrollment = (
        admin_client.table("subject_students")
        .select("student_id")
        .eq("student_id", student_id)
        .eq("subject_id", subject_id)
        .limit(1)
        .execute()
    )
    if not enrollment.data:
        return []

    response = (
        admin_client.table("course_assessments")
        .select("*")
        .eq("note_id", str(note_id))
        .eq("subject_id", str(subject_id))
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def get_student_dashboard_assessments(
    student_id: int | str, student_notes: list[dict]
) -> list[dict]:
    student = st.session_state.get("student_data")
    if not student or str(student.get("student_id")) != str(student_id):
        raise PermissionError("Log in as the student to view assessments.")

    subject_ids_by_key = {
        str(note["subject_id"]): note["subject_id"]
        for note in student_notes
        if note.get("subject_id") is not None
    }
    if not subject_ids_by_key:
        return []

    admin_client = _get_assessment_admin_client()
    enrollment_response = (
        admin_client.table("subject_students")
        .select("subject_id")
        .eq("student_id", student_id)
        .execute()
    )
    enrolled_subject_ids = {
        str(row["subject_id"])
        for row in enrollment_response.data or []
        if row.get("subject_id") is not None
    }
    accessible_notes = [
        note
        for note in student_notes
        if str(note.get("subject_id")) in enrolled_subject_ids
    ]
    note_ids = list({str(note["id"]) for note in accessible_notes if note.get("id")})
    if not note_ids:
        return []

    assessments_response = (
        admin_client.table("course_assessments")
        .select("*")
        .in_("note_id", note_ids)
        .order("created_at", desc=True)
        .execute()
    )
    subject_names = {
        str(note["subject_id"]): note.get("subject_name", "Subject")
        for note in accessible_notes
        if note.get("subject_id") is not None
    }
    assessments = assessments_response.data or []
    for assessment in assessments:
        assessment["subject_name"] = subject_names.get(
            str(assessment.get("subject_id")), "Subject"
        )
    return assessments


def get_assessment_submissions(assessment_id: str) -> list[dict]:
    _current_teacher_id()
    admin_client = _get_assessment_admin_client()
    assessment = _get_assessment(assessment_id, admin_client)
    _require_teacher(assessment["teacher_id"])

    response = (
        admin_client.table("assessment_submissions")
        .select("*")
        .eq("assessment_id", assessment_id)
        .order("submitted_on")
        .execute()
    )
    submissions = response.data or []
    student_ids = list({submission["student_id"] for submission in submissions})
    if not student_ids:
        return submissions

    students_response = (
        admin_client.table("students")
        .select("student_id, name")
        .in_("student_id", student_ids)
        .execute()
    )
    names = {
        str(student["student_id"]): student["name"]
        for student in (students_response.data or [])
    }
    for submission in submissions:
        submission["student_name"] = names.get(
            str(submission["student_id"]), "Student"
        )
    return submissions


def get_enrolled_students(subject_id: int | str) -> list[dict]:
    teacher_id = _current_teacher_id()
    admin_client = _get_assessment_admin_client()
    owned_subject = (
        admin_client.table("subjects")
        .select("subject_id")
        .eq("subject_id", subject_id)
        .eq("teacher_id", teacher_id)
        .limit(1)
        .execute()
    )
    if not owned_subject.data:
        raise PermissionError("You can only view students in your own subjects.")

    response = (
        admin_client.table("subject_students")
        .select("student_id")
        .eq("subject_id", subject_id)
        .execute()
    )
    student_ids = [
        enrollment["student_id"]
        for enrollment in response.data or []
        if enrollment.get("student_id") is not None
    ]
    if not student_ids:
        return []

    students_response = (
        admin_client.table("students")
        .select("student_id, name")
        .in_("student_id", student_ids)
        .execute()
    )
    names = {
        str(student["student_id"]): student.get("name", "Student")
        for student in students_response.data or []
    }
    return [
        {"student_id": student_id, "name": names.get(str(student_id), "Student")}
        for student_id in student_ids
    ]


def get_student_submission(assessment_id: str, student_id: int | str) -> dict | None:
    student = st.session_state.get("student_data")
    if not student or str(student.get("student_id")) != str(student_id):
        raise PermissionError("Log in as the student to view this submission.")

    admin_client = _get_assessment_admin_client()
    assessment = _get_assessment(assessment_id, admin_client)
    if not _is_student_enrolled(
        admin_client, student_id, assessment["subject_id"]
    ):
        raise PermissionError("You are not enrolled in this assessment's subject.")

    response = (
        admin_client.table("assessment_submissions")
        .select("*")
        .eq("assessment_id", assessment_id)
        .eq("student_id", str(student_id))
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def _get_assessment(assessment_id: str, admin_client=None) -> dict:
    client = admin_client or _get_assessment_admin_client()
    response = (
        client.table("course_assessments")
        .select("*")
        .eq("id", assessment_id)
        .limit(1)
        .execute()
    )
    if not response.data:
        raise ValueError("This assessment is no longer available.")
    return response.data[0]


def _current_teacher_id() -> int | str:
    teacher = st.session_state.get("teacher_data")
    teacher_id = (teacher.get("teacher_id") or teacher.get("id")) if teacher else None
    if teacher_id is None:
        raise PermissionError("Log in as the teacher to manage assessments.")
    return teacher_id


def _require_teacher(teacher_id: int | str) -> None:
    if str(_current_teacher_id()) != str(teacher_id):
        raise PermissionError("You can only manage your own assessments.")


def _is_student_enrolled(
    admin_client, student_id: int | str, subject_id: int | str
) -> bool:
    enrollment = (
        admin_client.table("subject_students")
        .select("student_id")
        .eq("student_id", student_id)
        .eq("subject_id", subject_id)
        .limit(1)
        .execute()
    )
    return bool(enrollment.data)


def _validate_student_submission(
    assessment: dict,
    student_id: int | str,
    submission_mode: str,
    admin_client,
) -> None:
    student = st.session_state.get("student_data")
    if not student or str(student.get("student_id")) != str(student_id):
        raise PermissionError("Log in as the student to submit this assessment.")
    if assessment["submission_mode"] != submission_mode:
        raise ValueError("This assessment uses a different submission method.")
    if date.today() > date.fromisoformat(assessment["due_date"]):
        raise ValueError("The assessment deadline has passed.")
    if not _is_student_enrolled(
        admin_client, student_id, assessment["subject_id"]
    ):
        raise ValueError("You are not enrolled in this assessment's subject.")
    existing_submission = (
        admin_client.table("assessment_submissions")
        .select("id")
        .eq("assessment_id", assessment["id"])
        .eq("student_id", str(student_id))
        .limit(1)
        .execute()
    )
    if existing_submission.data:
        raise ValueError("You have already submitted this assessment.")


def submit_online_assessment(
    assessment_id: str,
    student_id: int | str,
    file_name: str,
    file_bytes: bytes,
    content_type: str,
) -> dict:
    _validate_file(file_name, file_bytes)

    admin_client = _get_assessment_admin_client()
    assessment = _get_assessment(assessment_id, admin_client)
    _validate_student_submission(
        assessment, student_id, "online", admin_client
    )
    storage_path = _upload_file(
        f"{assessment_id}/submissions/{student_id}",
        file_name,
        file_bytes,
        content_type,
        storage_client=admin_client,
    )
    response = (
        admin_client.table("assessment_submissions")
        .insert(
            {
                "assessment_id": assessment_id,
                "student_id": str(student_id),
                "submission_mode": "online",
                "submitted_on": date.today().isoformat(),
                "file_name": Path(file_name).name,
                "file_path": storage_path,
            }
        )
        .execute()
    )
    if not response.data:
        raise RuntimeError("Your submission was not saved.")
    return response.data[0]


def record_physical_submission(
    assessment_id: str,
    teacher_id: int | str,
    student_id: int | str,
    submitted_on: date,
) -> dict:
    _require_teacher(teacher_id)
    admin_client = _get_assessment_admin_client()
    assessment = _get_assessment(assessment_id, admin_client)
    if str(assessment["teacher_id"]) != str(teacher_id):
        raise ValueError("You cannot update this assessment.")
    if assessment["submission_mode"] != "physical":
        raise ValueError("This assessment accepts file uploads, not physical work.")
    if submitted_on > date.fromisoformat(assessment["due_date"]):
        raise ValueError("The recorded submission date is after the deadline.")

    if not _is_student_enrolled(admin_client, student_id, assessment["subject_id"]):
        raise ValueError("This student is not enrolled in the assessment's subject.")
    existing_submission = (
        admin_client.table("assessment_submissions")
        .select("id")
        .eq("assessment_id", assessment_id)
        .eq("student_id", str(student_id))
        .limit(1)
        .execute()
    )
    if existing_submission.data:
        raise ValueError("This student is already recorded as submitted.")

    response = (
        admin_client.table("assessment_submissions")
        .insert(
            {
                "assessment_id": assessment_id,
                "student_id": str(student_id),
                "submission_mode": "physical",
                "submitted_on": submitted_on.isoformat(),
            }
        )
        .execute()
    )
    if not response.data:
        raise RuntimeError("The physical submission was not recorded.")
    return response.data[0]


def grade_assessment_submission(
    submission_id: str,
    assessment_id: str,
    teacher_id: int | str,
    score: float,
    feedback: str,
) -> dict:
    _require_teacher(teacher_id)
    admin_client = _get_assessment_admin_client()
    assessment = _get_assessment(assessment_id, admin_client)
    if str(assessment["teacher_id"]) != str(teacher_id):
        raise ValueError("You cannot grade this assessment.")
    if assessment["results_released"]:
        raise ValueError("Grades cannot be changed after results are released.")
    if score < 0 or score > float(assessment["max_score"]):
        raise ValueError("The score must be within the assessment's score range.")

    response = (
        admin_client.table("assessment_submissions")
        .update({"score": score, "feedback": feedback.strip()})
        .eq("id", submission_id)
        .eq("assessment_id", assessment_id)
        .select("*")
        .execute()
    )
    if not response.data:
        raise ValueError("The submission could not be found.")
    return response.data[0]


def release_assessment_results(assessment_id: str, teacher_id: int | str) -> None:
    _require_teacher(teacher_id)
    admin_client = _get_assessment_admin_client()
    assessment = _get_assessment(assessment_id, admin_client)
    if str(assessment["teacher_id"]) != str(teacher_id):
        raise ValueError("You cannot release results for this assessment.")
    if date.today() <= date.fromisoformat(assessment["due_date"]):
        raise ValueError("Results can be released after the submission deadline.")

    submissions = get_assessment_submissions(assessment_id)
    if any(submission.get("score") is None for submission in submissions):
        raise ValueError("Grade all received submissions before releasing results.")

    response = (
        admin_client.table("course_assessments")
        .update({"results_released": True})
        .eq("id", assessment_id)
        .eq("teacher_id", str(teacher_id))
        .select("id")
        .execute()
    )
    if not response.data:
        raise RuntimeError("Assessment results could not be released.")


def download_assessment_file(storage_path: str) -> bytes:
    if not storage_path:
        raise ValueError("The assessment file path is missing.")

    teacher = st.session_state.get("teacher_data")
    student = st.session_state.get("student_data")
    if bool(teacher) == bool(student):
        raise PermissionError("Log in with one account to download assessment files.")

    teacher_id = (
        (teacher.get("teacher_id") or teacher.get("id")) if teacher else None
    )
    student_id = student.get("student_id") if student else None

    admin_client = _get_assessment_admin_client()
    assignment_response = (
        admin_client.table("course_assessments")
        .select("id, teacher_id, subject_id, assignment_file_path")
        .eq("assignment_file_path", storage_path)
        .limit(1)
        .execute()
    )
    assessment = assignment_response.data[0] if assignment_response.data else None
    submission_student_id = None

    if assessment is None:
        submission_response = (
            admin_client.table("assessment_submissions")
            .select("assessment_id, student_id, file_path")
            .eq("file_path", storage_path)
            .limit(1)
            .execute()
        )
        submission = (
            submission_response.data[0] if submission_response.data else None
        )
        if submission:
            submission_student_id = submission.get("student_id")
            assessment_response = (
                admin_client.table("course_assessments")
                .select("id, teacher_id, subject_id")
                .eq("id", submission["assessment_id"])
                .limit(1)
                .execute()
            )
            assessment = (
                assessment_response.data[0] if assessment_response.data else None
            )

    if assessment is None:
        raise PermissionError("You are not allowed to download this assessment file.")

    if teacher:
        authorized = (
            teacher_id is not None
            and str(assessment.get("teacher_id")) == str(teacher_id)
        )
    elif student_id is not None:
        authorized = (
            submission_student_id is None
            or str(submission_student_id) == str(student_id)
        )
        if authorized:
            enrollment_response = (
                admin_client.table("subject_students")
                .select("student_id")
                .eq("student_id", student_id)
                .eq("subject_id", assessment["subject_id"])
                .limit(1)
                .execute()
            )
            authorized = bool(enrollment_response.data)
    else:
        authorized = False

    if not authorized:
        raise PermissionError("You are not allowed to download this assessment file.")

    return admin_client.storage.from_(ASSESSMENT_BUCKET).download(storage_path)
