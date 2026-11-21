import base64
import hashlib
import hmac
import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

import streamlit as st

from src.database.db import (
    get_teacher_by_email,
    get_teacher_by_id,
    get_teacher_for_password_reset,
)

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


def _signops_request(endpoint, fields):
    use_test_key = os.environ.get("SIGNOPS_USE_TEST_KEY")
    if use_test_key is None:
        try:
            use_test_key = st.secrets.get("signops_use_test_key", False)
        except Exception:
            use_test_key = False
    test_mode = str(use_test_key).strip().lower() in {"1", "true", "yes", "on"}

    secret_name = "signops_test_key" if test_mode else "signops_key"
    environment_name = "SIGNOPS_TEST_KEY" if test_mode else "SIGNOPS_KEY"
    api_key = os.environ.get(environment_name)
    if not api_key:
        try:
            api_key = st.secrets.get(secret_name)
        except Exception:
            api_key = None
    if not api_key:
        mode = "test" if test_mode else "live"
        raise RuntimeError(
            f"Configure the SignOps {mode} key as {secret_name} in Streamlit secrets "
            f"or {environment_name} in the app environment."
        )

    request = Request(
        f"https://api.signops.dev/v1/{endpoint.lstrip('/')}",
        data=urlencode(fields).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {str(api_key).strip()}",
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "SnapClass/1.0",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        try:
            error_body = json.loads(error.read().decode("utf-8", errors="replace"))
            detail = error_body.get("error", {})
            message = detail.get("message") or str(detail.get("code") or error.code)
        except (json.JSONDecodeError, AttributeError):
            message = f"HTTP {error.code}"
        raise RuntimeError(f"SignOps rejected the request: {message}") from error
    except URLError as error:
        raise RuntimeError(f"Could not connect to SignOps: {error.reason}") from error


def verify_password_reset_code(otp_id, code):
    result = _signops_request("otp/verify", {"otp_id": otp_id, "code": code})
    return bool(result.get("valid"))


def request_password_reset(email):
    teacher = get_teacher_by_email(email.strip().lower())
    if teacher is None:
        return False, None

    response = _signops_request(
        "otp/send",
        {"email": teacher["email"], "app_name": "SnapClass"},
    )
    otp_id = response.get("otp_id")
    if not otp_id:
        raise RuntimeError("SignOps did not return a reset code reference.")

    st.session_state["password_reset_otp"] = {
        "email": teacher["email"].strip().lower(),
        "teacher_id": teacher["teacher_id"],
        "otp_id": otp_id,
        "sent_at": time.time(),
        "expires_at": time.time() + 600,
        "attempts": 0,
        "code_verified": False,
    }
    st.session_state.pop("password_reset_code", None)

    return True, "email_sent"
