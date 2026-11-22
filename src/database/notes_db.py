import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import streamlit as st
from postgrest.exceptions import APIError
from storage3.exceptions import StorageApiError

from src.database.config import get_supabase_admin_client
from src.database.db import get_students_subjects


BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "notes"
FILES_DIR = DATA_DIR / "files"
NOTES_FILE = DATA_DIR / "notes.json"
NOTES_TABLE = "course_notes"
NOTES_BUCKET = "course-note-files"


def _current_teacher_id() -> str:
    teacher = st.session_state.get("teacher_data")
    teacher_id = (teacher.get("teacher_id") or teacher.get("id")) if teacher else None
    if teacher_id is None:
        raise PermissionError("Log in as a teacher to manage course notes.")
    return str(teacher_id)


def _require_teacher(teacher_id: int | str) -> None:
    if _current_teacher_id() != str(teacher_id):
        raise PermissionError("You can only manage your own course notes.")


def _resolve_note_file_path(file_path: str | None) -> str | None:
    if not file_path:
        return file_path

    path = Path(file_path)
    if path.is_file():
        return str(path)

    portable_path = Path(file_path.replace("\\", "/"))
    if not portable_path.is_absolute():
        repo_path = BASE_DIR / portable_path
        if repo_path.is_file():
            return str(repo_path)

    deployed_path = FILES_DIR / portable_path.name
    if deployed_path.is_file():
        return str(deployed_path)

    return file_path


def load_local_notes_for_migration() -> list[dict[str, Any]]:
    if not NOTES_FILE.is_file():
        return []

    with open(NOTES_FILE, "r", encoding="utf-8") as file:
        notes = json.load(file)
    if not isinstance(notes, list) or not all(isinstance(note, dict) for note in notes):
        raise ValueError(f"{NOTES_FILE} must contain a JSON array of note objects.")
    return notes


def _prepare_local_backup_deletion(
    note_id: str,
) -> tuple[list[dict], list[Path], bool]:
    notes = load_local_notes_for_migration()
    remaining_notes = []
    attachment_paths = []
    files_root = FILES_DIR.resolve()
    found = False

    for note in notes:
        if str(note.get("id")) != str(note_id):
            remaining_notes.append(note)
            continue

        found = True
        file_path = note.get("file_path")
        resolved_path = _resolve_note_file_path(file_path)
        if resolved_path and Path(resolved_path).is_file():
            path = Path(resolved_path).resolve()
            if path != files_root and files_root not in path.parents:
                raise PermissionError(
                    "The local note attachment is outside the course-notes folder."
                )
            attachment_paths.append(path)

    return remaining_notes, attachment_paths, found


def _remove_local_backup_note(
    remaining_notes: list[dict], attachment_paths: list[Path], found: bool
) -> None:
    if found and NOTES_FILE.is_file():
        temporary_path = NOTES_FILE.with_name("notes.json.tmp")
        with open(temporary_path, "w", encoding="utf-8") as file:
            json.dump(remaining_notes, file, indent=2, ensure_ascii=False)
        os.replace(temporary_path, NOTES_FILE)

    for attachment_path in attachment_paths:
        try:
            attachment_path.unlink(missing_ok=True)
        except OSError as error:
            raise RuntimeError(
                "The note was deleted from Supabase, but its local backup attachment "
                "could not be removed."
            ) from error


def get_note_download(note: dict) -> tuple[bytes, str] | None:
    """Return the uploaded original attachment, never a generated text substitute."""
    file_path = note.get("file_path")
    if not file_path:
        return None
    if (
        "(AI Blackboard Notes)" in str(note.get("title") or "")
        and str(note.get("file_name") or "").endswith("_digitized_notes.md")
    ):
        # Legacy digitizer records stored only a generated transcription, not the photo.
        return None

    client = get_supabase_admin_client()
    file_bytes = client.storage.from_(NOTES_BUCKET).download(file_path)
    file_name = note.get("file_name") or Path(file_path).name
    return bytes(file_bytes), Path(file_name).name


def create_note(
    subject_id: int | str,
    subject_name: str,
    teacher_id: int | str,
    teacher_name: str,
    title: str,
    description: str = "",
    uploaded_file=None,
) -> dict:
    """Creates a course note in Supabase and stores its attachment privately."""
    _require_teacher(teacher_id)
    if not title.strip():
        raise ValueError("Enter a note title.")

    client = get_supabase_admin_client()
    owned_subject = (
        client.table("subjects")
        .select("subject_id")
        .eq("subject_id", subject_id)
        .eq("teacher_id", teacher_id)
        .limit(1)
        .execute()
    )
    if not owned_subject.data:
        raise PermissionError("You can only upload notes for your own subjects.")

    note_id = str(uuid.uuid4())[:8]
    file_name = None
    file_path = None
    file_size_kb = 0
    if uploaded_file is not None:
        file_name = Path(uploaded_file.name).name
        file_bytes = uploaded_file.getvalue()
        if not file_bytes:
            raise ValueError("Choose a non-empty note file.")
        safe_name = file_name.replace(" ", "_")
        file_path = f"{note_id}/{uuid.uuid4().hex}_{safe_name}"
        client.storage.from_(NOTES_BUCKET).upload(
            file_path,
            file_bytes,
            {
                "content-type": (
                    getattr(uploaded_file, "type", None)
                    or "application/octet-stream"
                ),
                "upsert": "false",
            },
        )
        file_size_kb = round(len(file_bytes) / 1024, 1)

    note = {
        "id": note_id,
        "subject_id": str(subject_id),
        "subject_name": subject_name,
        "teacher_id": str(teacher_id),
        "teacher_name": teacher_name,
        "title": title.strip(),
        "description": description.strip(),
        "file_name": file_name,
        "file_path": file_path,
        "file_size_kb": file_size_kb,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }

    try:
        response = client.table(NOTES_TABLE).insert(note).execute()
    except APIError:
        if file_path:
            try:
                client.storage.from_(NOTES_BUCKET).remove([file_path])
            except StorageApiError as cleanup_error:
                raise RuntimeError(
                    "The note was not saved and its uploaded file could not be "
                    "cleaned up."
                ) from cleanup_error
        raise
    if not response.data:
        raise RuntimeError("The note was not saved to Supabase.")
    return response.data[0]


def get_notes_for_teacher(teacher_id: int | str) -> list[dict]:
    """Returns Supabase notes uploaded by the logged-in teacher."""
    _require_teacher(teacher_id)
    response = (
        get_supabase_admin_client()
        .table(NOTES_TABLE)
        .select("*")
        .eq("teacher_id", str(teacher_id))
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def get_notes_for_student(student_id: int | str) -> list[dict]:
    """Returns Supabase notes for the logged-in student's enrolled subjects."""
    student = st.session_state.get("student_data")
    if not student or str(student.get("student_id")) != str(student_id):
        raise PermissionError("Log in as the student to view course notes.")

    enrolled_data = get_students_subjects(student_id)
    subject_ids = {
        str(subject["subject_id"])
        for item in enrolled_data or []
        if (subject := item.get("subjects")) and subject.get("subject_id") is not None
    }
    if not subject_ids:
        return []

    response = (
        get_supabase_admin_client()
        .table(NOTES_TABLE)
        .select("*")
        .in_("subject_id", list(subject_ids))
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def delete_note(note_id: str, teacher_id: int | str) -> bool:
    """Deletes a teacher-owned Supabase note and its private attachment."""
    _require_teacher(teacher_id)
    remaining_notes, attachment_paths, backup_found = (
        _prepare_local_backup_deletion(note_id)
    )
    client = get_supabase_admin_client()
    note_response = (
        client.table(NOTES_TABLE)
        .select("id, file_path")
        .eq("id", str(note_id))
        .eq("teacher_id", str(teacher_id))
        .limit(1)
        .execute()
    )
    if not note_response.data:
        return False

    file_path = note_response.data[0].get("file_path")
    if file_path:
        client.storage.from_(NOTES_BUCKET).remove([file_path])

    deleted = (
        client.table(NOTES_TABLE)
        .delete()
        .eq("id", str(note_id))
        .eq("teacher_id", str(teacher_id))
        .select("id")
        .execute()
    )
    if not deleted.data:
        return False

    _remove_local_backup_note(remaining_notes, attachment_paths, backup_found)
    return True
