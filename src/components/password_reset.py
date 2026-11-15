import base64
import hashlib
import hmac
import json
import os
import secrets
import smtplib
import time
from email.message import EmailMessage
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


def _send_email_via_brevo(recipient, subject, email_text, html_content=None, api_key=None, sender=None):
    api_key = api_key or _smtp_value("BREVO_API_KEY", "brevo_api_key")
    sender = sender or _smtp_value("BREVO_FROM_EMAIL", "brevo_from_email")
    if not api_key or not sender:
        raise RuntimeError("Brevo is not configured: brevo_api_key and brevo_from_email are required.")

    body = {
        "sender": {"email": sender, "name": "SnapClass"},
        "to": [{"email": recipient}],
        "subject": subject,
        "textContent": email_text,
    }
    if html_content:
        body["htmlContent"] = html_content

    payload = json.dumps(body).encode("utf-8")
    request = Request(
        "https://api.brevo.com/v3/smtp/email",
        data=payload,
        headers={
            "api-key": api_key,
            "Content-Type": "application/json",
            "User-Agent": "SnapClass/1.0",
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
            f"Brevo rejected the email (HTTP {error.code}): {error_body}"
        ) from error
    except URLError as error:
        raise RuntimeError(f"Could not connect to Brevo: {error.reason}") from error


def _send_reset_email(recipient, reset_url):
    email_text = (
        "We received a request to reset your SnapClass teacher password.\n\n"
        f"Use this link within one hour to choose a new password:\n{reset_url}\n\n"
        "If you did not request this, you can safely ignore this email."
    )
    _send_email_via_brevo(
        recipient,
        "Reset your SnapClass teacher password",
        email_text,
    )


def _smtp_value(*names):
    for name in names:
        value = os.environ.get(name)
        if value not in (None, ""):
            return str(value).strip()
    for name in names:
        try:
            value = st.secrets.get(name)
            if value not in (None, ""):
                return str(value).strip()
        except Exception:
            pass
    return None


def _send_email_via_smtp(
    recipient,
    subject,
    email_text,
    from_email=None,
    host=None,
    port=None,
    username=None,
    password=None,
):
    from_email = from_email or _smtp_value("SMTP_FROM_EMAIL", "smtp_from_email")
    host = host or _smtp_value("SMTP_HOST", "smtp_host")
    port = port or _smtp_value("SMTP_PORT", "smtp_port")
    username = username or _smtp_value("SMTP_USERNAME", "smtp_username")
    password = password or _smtp_value("SMTP_PASSWORD", "smtp_password")

    if not host or not from_email:
        raise RuntimeError("SMTP email delivery is not configured: SMTP_HOST and SMTP_FROM_EMAIL are required.")

    port_value = int(port or 587)
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_email
    message["To"] = recipient
    message.set_content(email_text)

    try:
        if port_value == 465:
            server = smtplib.SMTP_SSL(host, port_value, timeout=20)
        else:
            server = smtplib.SMTP(host, port_value, timeout=20)
            server.starttls()
        if username and password:
            server.login(username, password)
        server.send_message(message)
        server.quit()
        return True
    except Exception:
        try:
            server.quit()
        except Exception:
            pass
        raise


def _send_reset_email_via_smtp(recipient, reset_url, from_email=None):
    email_text = (
        "We received a request to reset your SnapClass teacher password.\n\n"
        f"Use this link within one hour to choose a new password:\n{reset_url}\n\n"
        "If you did not request this, you can safely ignore this email."
    )
    return _send_email_via_smtp(
        recipient,
        "Reset your SnapClass teacher password",
        email_text,
        from_email=from_email,
    )


def _send_transactional_email(email, subject, email_text, html_content=None):
    brevo_api_key = _smtp_value("BREVO_API_KEY", "brevo_api_key")
    brevo_from_email = _smtp_value("BREVO_FROM_EMAIL", "brevo_from_email")

    brevo_error = None
    if brevo_api_key and brevo_from_email:
        try:
            _send_email_via_brevo(
                email,
                subject,
                email_text,
                html_content=html_content,
                api_key=brevo_api_key,
                sender=brevo_from_email,
            )
            return
        except Exception as error:
            brevo_error = error

    smtp_host = _smtp_value("SMTP_HOST", "smtp_host")
    smtp_from = _smtp_value("SMTP_FROM_EMAIL", "smtp_from_email")
    if smtp_host and smtp_from:
        try:
            _send_email_via_smtp(
                email,
                subject,
                email_text,
            )
            return
        except Exception as error:
            if brevo_error:
                raise RuntimeError(
                    f"Brevo delivery failed: {brevo_error}. SMTP delivery failed: {error}"
                ) from error
            raise

    if brevo_error:
        raise RuntimeError(f"Brevo delivery failed: {brevo_error}") from brevo_error
    raise RuntimeError(
        "Email delivery is not configured. Set BREVO_API_KEY and BREVO_FROM_EMAIL, "
        "or configure SMTP_HOST and SMTP_FROM_EMAIL."
    )


def send_password_reset_code(email, code):
    email_text = (
        f"Your SnapClass password reset verification code is: {code}\n\n"
        "This code will expire in 10 minutes.\n\n"
        "If you did not request a password reset, please ignore this email."
    )
    html_content = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 520px; margin: 0 auto; padding: 32px 24px; border: 1px solid #e2e8f0; border-radius: 12px; background-color: #ffffff;">
        <h2 style="color: #0f172a; margin-top: 0; font-size: 24px; font-weight: 700;">SnapClass Password Reset</h2>
        <p style="color: #475569; font-size: 15px; line-height: 1.6;">
            We received a request to reset your SnapClass teacher account password. Use the verification code below to complete the reset:
        </p>
        <div style="text-align: center; margin: 28px 0;">
            <div style="display: inline-block; font-size: 34px; font-weight: 700; letter-spacing: 6px; color: #2563eb; background-color: #eff6ff; padding: 12px 28px; border-radius: 8px; border: 1px dashed #93c5fd;">
                {code}
            </div>
        </div>
        <p style="color: #64748b; font-size: 13px; line-height: 1.5;">
            ⏱️ This code is valid for <strong>10 minutes</strong>. If you did not request this, you can safely ignore this email.
        </p>
        <hr style="border: none; border-top: 1px solid #f1f5f9; margin: 24px 0;" />
        <p style="color: #94a3b8; font-size: 12px; text-align: center; margin-bottom: 0;">
            SnapClass • AI-Powered Classroom Attendance
        </p>
    </div>
    """
    _send_transactional_email(
        email,
        "Your SnapClass password reset code",
        email_text,
        html_content=html_content,
    )


def request_password_reset(email):
    teacher = get_teacher_by_email(email.strip().lower())
    if teacher is None:
        return False, None

    code = f"{secrets.randbelow(1_000_000):06d}"
    email_sent = False
    delivery_note = None

    try:
        send_password_reset_code(teacher["email"], code)
        email_sent = True
    except Exception as error:
        delivery_note = str(error)

    key = secrets.token_bytes(32)
    st.session_state["password_reset_otp"] = {
        "email": teacher["email"].strip().lower(),
        "teacher_id": teacher["teacher_id"],
        "key": key.hex(),
        "digest": hmac.new(key, code.encode("ascii"), hashlib.sha256).hexdigest(),
        "sent_at": time.time(),
        "expires_at": time.time() + 600,
        "attempts": 0,
        "code": code if not email_sent else None,
        "delivery_note": delivery_note,
    }
    if not email_sent:
        st.session_state["password_reset_code"] = code

    return True, ("email_sent" if email_sent else "direct_code")
