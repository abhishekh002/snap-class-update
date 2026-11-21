"""Minimal server-side Resend client for password reset messages."""

import json
from email.utils import parseaddr
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


RESEND_SEND_URL = "https://api.resend.com/emails"
RESEND_TIMEOUT_SECONDS = 10


class ResendEmailError(RuntimeError):
    """A safe-to-display error from the Resend email API."""


def _format_sender(from_email):
    if not isinstance(from_email, str) or "\r" in from_email or "\n" in from_email:
        raise ResendEmailError("Set a valid sender address from your verified Resend domain.")
    display_name, address = parseaddr(from_email.strip())
    if not address or address.count("@") != 1 or any(ch.isspace() for ch in address):
        raise ResendEmailError("Set a valid sender address from your verified Resend domain.")
    if display_name:
        return f"{display_name} <{address}>"
    return f"SnapClass <{address}>"


def send_password_reset_email(api_key, from_email, to_email, code):
    """Send a reset code using Resend's server-side REST API."""
    payload = {
        "from": _format_sender(from_email),
        "to": [to_email],
        "subject": "Your SnapClass password reset code",
        "text": (
            f"Your SnapClass password reset code is {code}. "
            "It expires in 10 minutes. If you did not request this, ignore this email."
        ),
        "html": (
            "<p>Your SnapClass password reset code is:</p>"
            f"<p style=\"font-size:24px;font-weight:bold;letter-spacing:4px\">{code}</p>"
            "<p>This code expires in 10 minutes. If you did not request it, "
            "you can ignore this email.</p>"
        ),
    }
    request = Request(
        RESEND_SEND_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "SnapClass/1.0",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=RESEND_TIMEOUT_SECONDS) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        error.close()
        if error.code == 401:
            raise ResendEmailError("Resend rejected the API key. Check your server secret.") from error
        if error.code == 403 or error.code == 422:
            raise ResendEmailError(
                "Resend rejected the sender or message. Verify your sending domain and sender address."
            ) from error
        if error.code == 429:
            raise ResendEmailError("Resend rate limit reached. Wait briefly, then try again.") from error
        raise ResendEmailError(f"Resend could not send the email (HTTP {error.code}).") from error
    except (URLError, TimeoutError, OSError) as error:
        raise ResendEmailError("Could not connect to Resend. Try again shortly.") from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ResendEmailError("Resend returned an unreadable response.") from error

    if not isinstance(result, dict) or not result.get("id"):
        raise ResendEmailError("Resend did not confirm that the email was accepted.")
    return result["id"]
