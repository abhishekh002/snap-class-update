from src.database.config import supabase

import bcrypt


def hash_pass(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_pass(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def check_teacher_exists(username: str) -> bool:
    response = supabase.table("teachers").select("username").eq("username", username).execute()
    return bool(response.data)


def create_teacher(username: str, password: str, name: str, email: str):
    data = {
        "username": username,
        "password_hash": hash_pass(password),
        "name": name,
        "email": email.strip().lower(),
    }
    response = supabase.table("teachers").insert(data).execute()
    return response.data


def get_teacher_by_email(email: str):
    response = (
        supabase.table("teachers")
        .select("teacher_id, username, email, password_hash, name")
        .eq("email", email.strip().lower())
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def get_teacher_by_id(teacher_id: int):
    response = (
        supabase.table("teachers")
        .select("teacher_id, username, email, password_hash, name")
        .eq("teacher_id", teacher_id)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def get_teacher_for_password_reset(username: str):
    response = (
        supabase.table("teachers")
        .select("teacher_id, username, email, password_hash, name")
        .eq("username", username)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def update_teacher_password(identifier, password: str):
    new_hash = hash_pass(password)
    # If numeric id or int, update by teacher_id primary key
    if isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit()):
        res = (
            supabase.table("teachers")
            .update({"password_hash": new_hash})
            .eq("teacher_id", int(identifier))
            .select("teacher_id, username")
            .execute()
        )
        if res.data:
            return True

    # If email address
    if isinstance(identifier, str) and "@" in identifier:
        res = (
            supabase.table("teachers")
            .update({"password_hash": new_hash})
            .eq("email", identifier.strip().lower())
            .select("teacher_id, username")
            .execute()
        )
        if res.data:
            return True

    # Otherwise update by username
    res = (
        supabase.table("teachers")
        .update({"password_hash": new_hash})
        .eq("username", str(identifier))
        .select("teacher_id, username")
        .execute()
    )
    return bool(res.data)


def teacher_login(email: str, password: str):
    response = (
        supabase.table("teachers")
        .select("*")
        .eq("email", email.strip().lower())
        .limit(1)
        .execute()
    )
    if response.data:
        teacher = response.data[0]
        if check_pass(password, teacher["password_hash"]):
            teacher.pop("password_hash", None)
            return teacher
        return None
    return None


def check_teacher_email_exists(email: str) -> bool:
    response = (
        supabase.table("teachers")
        .select("username")
        .eq("email", email.strip().lower())
        .limit(1)
        .execute()
    )
    return bool(response.data)


def get_all_students():
    response = supabase.table("students").select("*").execute()
    return response.data


def create_student(
    new_name,
    registration_number=None,
    face_embedding=None,
    voice_embedding=None,
):
    data = {
        "name": new_name,
        "registration_number": registration_number,
        "face_embedding": face_embedding,
        "voice_embedding": voice_embedding,
    }
    response = supabase.table("students").insert(data).execute()
    return response.data


def update_student_voice_embedding(student_id, voice_embedding):
    if not voice_embedding:
        raise ValueError("A valid voice recording is required.")
    response = (
        supabase.table("students")
        .update({"voice_embedding": voice_embedding})
        .eq("student_id", student_id)
        .select("student_id")
        .execute()
    )
    return bool(response.data)


def create_subject(subject_code: str, name: str, section: str, teacher_id: int):
    data = {
        "subject_code": subject_code,
        "name": name,
        "section": section,
        "teacher_id": teacher_id,
    }
    response = supabase.table("subjects").insert(data).execute()
    return response.data

def get_teacher_subject(teacher_id):
    response = (
        supabase.table("subjects")
        .select("*,subject_students(count),attendance_logs(count)")
        .eq("teacher_id", teacher_id)
        .execute()
    )
    subjects = response.data or []

    for subject in subjects:
        student_counts = subject.get("subject_students", [])
        subject["total_students"] = student_counts[0].get("count", 0) if student_counts else 0
        attendance_counts = subject.get("attendance_logs", [])
        subject["total_attendance_records"] = (
            attendance_counts[0].get("count", 0) if attendance_counts else 0
        )
        subject.pop("subject_students", None)
        subject.pop("attendance_logs", None)
    return subjects


def delete_teacher_subject(subject_id, teacher_id):
    subject = (
        supabase.table("subjects")
        .select("subject_id")
        .eq("subject_id", subject_id)
        .eq("teacher_id", teacher_id)
        .limit(1)
        .execute()
    )
    if not subject.data:
        return False

    supabase.table("attendance_logs").delete().eq("subject_id", subject_id).execute()
    supabase.table("subject_students").delete().eq("subject_id", subject_id).execute()
    deleted = (
        supabase.table("subjects")
        .delete()
        .eq("subject_id", subject_id)
        .eq("teacher_id", teacher_id)
        .select("subject_id")
        .execute()
    )
    return bool(deleted.data)


def get_subject_by_code(subject_code):
    response = (
        supabase.table("subjects")
        .select("subject_id, name, subject_code, section")
        .eq("subject_code", subject_code)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def enroll_student_to_subject(student_id, subject_id):
    existing = (
        supabase.table("subject_students")
        .select("student_id")
        .eq("student_id", student_id)
        .eq("subject_id", subject_id)
        .limit(1)
        .execute()
    )
    if existing.data:
        return None

    data = {"student_id": student_id, "subject_id": subject_id}
    response = supabase.table("subject_students").insert(data).execute()
    return response.data


def unenroll_student_to_subject(student_id, subject_id):
    response = (
        supabase.table("subject_students")
        .delete()
        .eq("student_id", student_id)
        .eq("subject_id", subject_id)
        .execute()
    )
    return response.data


def get_students_subjects(student_id):
    response = (
        supabase.table("subject_students")
        .select("*, subjects(*)")
        .eq("student_id", student_id)
        .execute()
    )
    return response.data


def get_student_attendance(student_id):
    response = (
        supabase.table("attendance_logs")
        .select("*, subjects(*)")
        .eq("student_id", student_id)
        .execute()
    )
    return response.data

def create_attendance(logs):
    if not logs:
        raise ValueError("There are no attendance records to save.")
    response = supabase.table("attendance_logs").insert(logs).execute()
    return response.data

def get_attendance_for_teacher(teacher_id):
    response = (
        supabase.table("attendance_logs")
        .select(
            "*, subjects!inner(*), "
            "students(student_id, name, registration_number)"
        )
        .eq("subjects.teacher_id", teacher_id)
        .execute()
    )
    return response.data
