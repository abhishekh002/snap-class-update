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

from src.database.db import get_teacher_by_email, get_teacher_for_password_reset

RESET_TOKEN_LIFETIME_SECONDS = 3600


def _setting(secret_name, environment_name=None):
    value = os.environ.get(environment_name) if environment_name else None
    if not value:
        value = st.secrets.get(secret_name)
    if not value:
        raise RuntimeError(f"Configure {secret_name} in Streamlit secrets.")
    value = str(value)
    if secret_name == "password_reset_secret" and len(value) < 32:
        raise RuntimeError("password_reset_secret must be at least 32 characters.")
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
        "username": teacher["username"],
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
    secret = _setting("password_reset_secret", "SNAPCLASS_PASSWORD_RESET_SECRET")
    try:
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
        if int(payload["expires"]) <= int(time.time()):
            return None
        username = payload["username"]
        expected_version = payload["password_version"]
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return None

    teacher = get_teacher_for_password_reset(username)
    if teacher is None:
        return None
    if not hmac.compare_digest(
        _password_version(teacher["password_hash"], secret),
        expected_version,
    ):
        return None
    return teacher


def _build_reset_url(token):
    public_url = (
        os.environ.get("AI_ATTENDANCE_PUBLIC_URL")
        or st.secrets.get("public_app_url")
        or os.environ.get("SNAPCLASS_PUBLIC_URL")
    )
    public_url = public_url or st.context.url
    if not public_url:
        raise RuntimeError(
            "Configure public_app_url in Streamlit secrets or "
            "AI_ATTENDANCE_PUBLIC_URL."
        )

    parsed_url = urlsplit(public_url)
    if not parsed_url.netloc or parsed_url.scheme not in {"https", "http"}:
        raise RuntimeError("The configured public_app_url must be an absolute HTTP(S) URL.")
    if parsed_url.scheme != "https" and parsed_url.hostname not in {
        "localhost",
        "127.0.0.1",
        "::1",
    }:
        raise RuntimeError("Password reset links require HTTPS.")

    return urlunsplit(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path.rstrip("/") or "/",
            urlencode({"reset_token": token}),
            "",
        )
    )


def _send_reset_email(recipient, reset_url):
    api_key = _setting("brevo_api_key")
    sender = _setting("brevo_from_email")
    email_text = (
        "We received a request to reset your AI Attendance teacher password.\n\n"
        f"Use this link within one hour:\n{reset_url}\n\n"
        "If you did not request this, you can ignore this email."
    )
    payload = json.dumps(
        {
            "sender": {"email": sender, "name": "AI Attendance"},
            "to": [{"email": recipient}],
            "subject": "Reset your AI Attendance teacher password",
            "textContent": email_text,
        }
    ).encode("utf-8")
    request = Request(
        "https://api.brevo.com/v3/smtp/email",
        data=payload,
        headers={
            "api-key": api_key,
            "Content-Type": "application/json",
            "User-Agent": "AI-Attendance/1.0",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=20) as response:
            if response.status != 201:
                raise RuntimeError(
                    f"Brevo returned unexpected status {response.status}."
                )
    except HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Brevo rejected the reset email (HTTP {error.code}): {error_body}"
        ) from error
    except URLError as error:
        raise RuntimeError(f"Could not connect to Brevo: {error.reason}") from error


def request_password_reset(email):
    secret = _setting("password_reset_secret", "SNAPCLASS_PASSWORD_RESET_SECRET")
    teacher = get_teacher_by_email(email.strip().lower())
    if teacher is None:
        return False

    token = _create_reset_token(teacher, secret)
    reset_url = _build_reset_url(token)
    _send_reset_email(teacher["email"], reset_url)
    return True
