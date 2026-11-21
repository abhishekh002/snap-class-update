import base64
import hashlib
import hmac
import json
import os
import secrets as secure_random
import time
from urllib.parse import urlencode, urlsplit, urlunsplit

import streamlit as st

from src.database.db import (
    get_teacher_by_email,
    get_teacher_by_id,
    get_teacher_for_password_reset,
)
from src.components.resend_email import send_password_reset_email

RESET_TOKEN_LIFETIME_SECONDS = 3600


def _setting(secret_name, environment_name=None):
    value = os.environ.get(environment_name) if environment_name else None
    if not value:
        try:
            value = st.secrets.get(secret_name)
        except Exception:
            value = None
    if not value and secret_name == "password_reset_secret":
        base_seed = ""
        try:
            base_seed = st.secrets.get("supabase_key", "")
        except Exception:
            pass
        if not base_seed:
            base_seed = "snapclass_default_secret_key_for_reset_token_fallback_2026"
        value = hashlib.sha256(f"snapclass-secret-{base_seed}".encode()).hexdigest()
    if not value:
        raise RuntimeError(f"Configure {secret_name} in Streamlit secrets or environment variables.")
    value = str(value)
    if secret_name == "password_reset_secret" and len(value) < 32:
        value = hashlib.sha256(value.encode()).hexdigest()
    return value


def _password_version(password_hash, secret):
    return hmac.new(
        secret.encode("utf-8"),
        password_hash.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _encode_urlsafe(data):
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _decode_urlsafe(value):
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _create_reset_token(teacher, secret):
    payload = {
        "teacher_id": teacher.get("teacher_id"),
        "username": teacher.get("username", ""),
        "email": teacher.get("email", ""),
        "expires": int(time.time()) + RESET_TOKEN_LIFETIME_SECONDS,
        "password_version": _password_version(teacher["password_hash"], secret),
    }
    encoded_payload = _encode_urlsafe(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    )
    signature = hmac.new(
        secret.encode("utf-8"),
        encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{encoded_payload}.{_encode_urlsafe(signature)}"


def validate_reset_token(token):
    if not token or not isinstance(token, str):
        return None
    token = token.strip()
    try:
        secret = _setting("password_reset_secret", "SNAPCLASS_PASSWORD_RESET_SECRET")
        encoded_payload, encoded_signature = token.split(".", 1)
        expected_signature = hmac.new(
            secret.encode("utf-8"),
            encoded_payload.encode("ascii"),
            hashlib.sha256,
        ).digest()
        provided_signature = _decode_urlsafe(encoded_signature)
        if not hmac.compare_digest(expected_signature, provided_signature):
            return None

        payload = json.loads(_decode_urlsafe(encoded_payload))
        if int(payload.get("expires", 0)) <= int(time.time()):
            return None

        expected_version = payload.get("password_version")
        if not expected_version:
            return None

        username = payload.get("username")
        email = payload.get("email")
        teacher_id = payload.get("teacher_id")
    except Exception:
        return None

    teacher = None
    if teacher_id:
        teacher = get_teacher_by_id(teacher_id)
    if not teacher and email:
        teacher = get_teacher_by_email(email)
    if not teacher and username:
        teacher = get_teacher_for_password_reset(username)

    if teacher is None:
        return None
    if not hmac.compare_digest(
        _password_version(teacher["password_hash"], secret),
        expected_version,
    ):
        return None
    return teacher


def _detect_base_url():
    configured = (
        os.environ.get("SNAPCLASS_PUBLIC_URL")
        or os.environ.get("AI_ATTENDANCE_PUBLIC_URL")
        or ""
    )
    if not configured:
        try:
            configured = st.secrets.get("public_app_url") or ""
        except Exception:
            pass
    if configured:
        return configured.rstrip("/")

    try:
        ctx_url = getattr(st.context, "url", None)
        if ctx_url:
            parsed = urlsplit(ctx_url)
            if parsed.scheme and parsed.netloc:
                return f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"
    except Exception:
        pass

    try:
        headers = getattr(st.context, "headers", {})
        if headers:
            host = headers.get("host")
            proto = headers.get("x-forwarded-proto", "http")
            if host:
                return f"{proto}://{host}"
    except Exception:
        pass

    try:
        from streamlit import config
        port = config.get_option("server.port") or 8501
        address = config.get_option("server.address") or "localhost"
        if address in ("0.0.0.0", "None", ""):
            address = "localhost"
        return f"http://{address}:{port}"
    except Exception:
        pass

    return "http://localhost:8501"


def _build_reset_url(token):
    base_url = _detect_base_url()
    parsed_url = urlsplit(base_url)
    scheme = parsed_url.scheme or "http"
    netloc = parsed_url.netloc or "localhost:8501"
    path = parsed_url.path.rstrip("/") or "/"

    return urlunsplit(
        (
            scheme,
            netloc,
            path,
            urlencode({"reset_token": token}),
            "",
        )
    )


def _resend_setting(secret_name, environment_name):
    value = os.environ.get(environment_name)
    if not value:
        try:
            value = st.secrets.get(secret_name)
        except Exception:
            value = None
    if not value or not str(value).strip():
        raise RuntimeError(
            f"Configure {environment_name} in the app environment or "
            f"{secret_name} in Streamlit secrets."
        )
    return str(value).strip()


def _reset_code_digest(teacher_id, email, code):
    secret = _setting("password_reset_secret", "SNAPCLASS_PASSWORD_RESET_SECRET")
    message = f"{teacher_id}\0{email}\0{code}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def verify_password_reset_code(reset_state, code):
    if not isinstance(reset_state, dict) or not isinstance(code, str):
        return False
    if time.time() >= reset_state.get("expires_at", 0):
        return False
    if reset_state.get("attempts", 0) >= 5:
        return False
    expected = reset_state.get("otp_hash")
    if not expected:
        return False
    actual = _reset_code_digest(
        reset_state.get("teacher_id"), reset_state.get("email", ""), code
    )
    return hmac.compare_digest(str(expected), actual)


def request_password_reset(email):
    teacher = get_teacher_by_email(email.strip().lower())
    if teacher is None:
        return False, None

    api_key = _resend_setting("resend_api_key", "RESEND_API_KEY")
    from_email = _resend_setting("resend_from_email", "RESEND_FROM_EMAIL")
    normalized_email = teacher["email"].strip().lower()
    teacher_id = teacher["teacher_id"]
    code = f"{secure_random.randbelow(1_000_000):06d}"
    send_password_reset_email(api_key, from_email, normalized_email, code)

    now = time.time()
    st.session_state["password_reset_otp"] = {
        "email": normalized_email,
        "teacher_id": teacher_id,
        "otp_hash": _reset_code_digest(teacher_id, normalized_email, code),
        "sent_at": now,
        "expires_at": now + 600,
        "attempts": 0,
        "code_verified": False,
    }
    st.session_state.pop("password_reset_code", None)

    return True, "email_sent"
