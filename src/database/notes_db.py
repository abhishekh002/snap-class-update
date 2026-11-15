import os
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from src.database.db import get_students_subjects

# Directory paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "notes"
FILES_DIR = DATA_DIR / "files"
NOTES_FILE = DATA_DIR / "notes.json"

def _ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    FILES_DIR.mkdir(parents=True, exist_ok=True)
    if not NOTES_FILE.exists():
        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


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


def _load_notes() -> list:
    _ensure_dirs()
    try:
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            notes = json.load(f)
        for note in notes:
            if isinstance(note, dict) and note.get("file_path"):
                note["file_path"] = _resolve_note_file_path(note["file_path"])
        return notes
    except Exception:
        return []

def _save_notes(notes: list):
    _ensure_dirs()
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, indent=2, ensure_ascii=False)

def create_note(
    subject_id: int | str,
    subject_name: str,
    teacher_id: int | str,
    teacher_name: str,
    title: str,
    description: str = "",
    uploaded_file=None,
) -> dict:
    """
    Creates a new course note uploaded by a teacher.
    Saves attached file (PDF, TXT, DOCX, image, etc.) if provided.
    """
    _ensure_dirs()
    note_id = str(uuid.uuid4())[:8]
    file_name = None
    file_path = None
    file_size_kb = 0

    if uploaded_file is not None:
        file_name = uploaded_file.name
        safe_name = f"{note_id}_{file_name.replace(' ', '_')}"
        target_path = FILES_DIR / safe_name
        with open(target_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        file_path = target_path.relative_to(BASE_DIR).as_posix()
        file_size_kb = round(len(uploaded_file.getvalue()) / 1024, 1)

    new_note = {
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

    notes = _load_notes()
    notes.insert(0, new_note)
    _save_notes(notes)
    return new_note

def get_notes_for_teacher(teacher_id: int | str) -> list:
    """Returns all notes uploaded by a specific teacher."""
    notes = _load_notes()
    return [n for n in notes if str(n.get("teacher_id")) == str(teacher_id)]

def get_notes_for_student(student_id: int | str) -> list:
    """
    Strict Access Control:
    Returns ONLY the notes for subjects that the student is actively enrolled in.
    """
    enrolled_data = get_students_subjects(student_id)
    if not enrolled_data:
        return []

    enrolled_subject_ids = set()
    for item in enrolled_data:
        subj = item.get("subjects")
        if subj and "subject_id" in subj:
            enrolled_subject_ids.add(str(subj["subject_id"]))

    all_notes = _load_notes()
    return [n for n in all_notes if str(n.get("subject_id")) in enrolled_subject_ids]

def delete_note(note_id: str, teacher_id: int | str) -> bool:
    """Deletes a note and its attached file if owned by the teacher."""
    notes = _load_notes()
    remaining = []
    deleted = False

    for n in notes:
        if n["id"] == note_id:
            if str(n.get("teacher_id")) != str(teacher_id):
                return False  # Not authorized
            deleted = True
            # Remove file if it exists
            if n.get("file_path") and os.path.exists(n["file_path"]):
                try:
                    os.remove(n["file_path"])
                except Exception:
                    pass
        else:
            remaining.append(n)

    if deleted:
        _save_notes(remaining)
    return deleted
