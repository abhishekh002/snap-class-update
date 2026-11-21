# Course notes in Supabase

Course notes and their attachments are stored in the private `course_notes` table
and `course-note-files` storage bucket.

1. Run `migrations/20261121000000_course_notes.sql` in the Supabase SQL Editor.
2. Set `supabase_service_role_key` in the ignored `.streamlit/secrets.toml` file.
   Keep this key server-side; never put it in browser code or commit it.
3. From the repository root, validate the local notes first:

   ```powershell
   .\venv\Scripts\python.exe -m src.database.migrate_local_notes --dry-run
   ```

The migration checks that every referenced local attachment exists before it
uploads anything. It uses note IDs as upsert keys, so retrying after an
interruption does not create duplicate note rows. Once the dry run succeeds, run
the same command without `--dry-run` to upload the notes. The migration leaves
local JSON and attachment files untouched as a backup; deleting a note from the
teacher interface removes its corresponding local backup too. Linked assessments,
submissions, and grades are intentionally preserved when a note is deleted.
