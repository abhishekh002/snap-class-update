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


def create_teacher(username: str, password: str, name: str):
    data = {"username": username, "password_hash": hash_pass(password), "name": name}
    response = supabase.table("teachers").insert(data).execute()
    return response.data


def teacher_login(username: str, password: str):
    response = supabase.table("teachers").select("*").eq("username", username).execute()
    if response.data:
        teacher = response.data[0]
        if check_pass(password, teacher["password_hash"]):
            teacher.pop("password_hash", None)
            return teacher
        return None
    return None


def get_all_students():
    response = supabase.table('student').select("*").execute()
    return response.data