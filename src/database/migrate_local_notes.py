import argparse
import mimetypes
from pathlib import Path

from src.database.config import get_supabase_admin_client
from src.database.notes_db import (
    NOTES_BUCKET,
    NOTES_TABLE,
    _resolve_note_file_path,
    load_local_notes_for_migration,
)


NOTE_COLUMNS = {
    "id",
    "subject_id",
    "subject_name",
    "teacher_id",
    "teacher_name",
    "title",
    "description",
    "file_name",
    "file_path",
    "file_size_kb",
    "created_at",
}


def migrate_local_notes(dry_run: bool = False) -> int:
    notes = load_local_notes_for_migration()
    if not notes:
        print("No local notes found to migrate.")
        return 0

    prepared_notes = []
    missing_files = []
    for note in notes:
        note_id = str(note.get("id") or "").strip()
        if not note_id:
            raise ValueError("A local note is missing its id; migration stopped.")
        required_fields = (
            "subject_id",
            "subject_name",
            "teacher_id",
            "teacher_name",
            "title",
            "created_at",
        )
        if any(not note.get(field) for field in required_fields):
            raise ValueError(
                f"Local note ID {note_id} is missing required fields; migration stopped."
            )

        payload = {key: note[key] for key in NOTE_COLUMNS if key in note}
        payload["id"] = note_id
        payload["subject_id"] = str(note.get("subject_id") or "")
        payload["teacher_id"] = str(note.get("teacher_id") or "")
        payload["description"] = note.get("description") or ""

        local_file_path = None
        if note.get("file_path"):
            resolved_path = _resolve_note_file_path(note["file_path"])
            if not resolved_path or not Path(resolved_path).is_file():
                missing_files.append(note_id)
            else:
                local_file_path = Path(resolved_path)
        prepared_notes.append((note, payload, local_file_path))

    if missing_files:
        missing_ids = ", ".join(missing_files)
        raise FileNotFoundError(
            "Migration stopped before uploading anything because local note "
            f"attachments are missing for note IDs: {missing_ids}. Restore those "
            "files or handle them before retrying."
        )

    if dry_run:
        print(f"Ready to migrate {len(prepared_notes)} notes and their attachments.")
        return len(prepared_notes)

    client = get_supabase_admin_client()
    for note, payload, local_file_path in prepared_notes:
        if local_file_path:
            file_name = Path(note.get("file_name") or local_file_path.name).name
            storage_path = f"{payload['id']}/{file_name.replace(' ', '_')}"
            content_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
            client.storage.from_(NOTES_BUCKET).upload(
                storage_path,
                local_file_path.read_bytes(),
                {"content-type": content_type, "upsert": "true"},
            )
            payload["file_path"] = storage_path
            payload["file_name"] = file_name
        else:
            payload["file_path"] = None

        response = (
            client.table(NOTES_TABLE)
            .upsert(payload, on_conflict="id")
            .execute()
        )
        if not response.data:
            raise RuntimeError(
                f"Supabase did not confirm migration of note ID {payload['id']}."
            )

    print(f"Migrated {len(prepared_notes)} notes to Supabase.")
    return len(prepared_notes)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate local course notes to Supabase.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate local notes and attachments without uploading anything.",
    )
    arguments = parser.parse_args()
    migrate_local_notes(dry_run=arguments.dry_run)
