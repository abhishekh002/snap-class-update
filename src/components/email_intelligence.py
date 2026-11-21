"""Server-side client for Abstract's Email Intelligence API."""

from dataclasses import dataclass
import json
import os
import re
import socket
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_URL = "https://emailreputation.abstractapi.com/v1/"
API_KEY_ENV = "ABSTRACT_EMAIL_REPUTATION_API_KEY"
REQUEST_TIMEOUT_SECONDS = 10
_EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)


class EmailIntelligenceError(Exception):
    """Base exception for Email Intelligence configuration and API failures."""


class EmailIntelligenceConfigurationError(EmailIntelligenceError):
    """Raised when the server-side API key is missing."""


class InvalidEmailError(EmailIntelligenceError, ValueError):
    """Raised when the supplied address is not a valid email shape."""


class EmailIntelligenceAuthenticationError(EmailIntelligenceError):
    """Raised when Abstract rejects the configured API key."""


class EmailIntelligenceQuotaError(EmailIntelligenceError):
    """Raised when the account has no remaining API credits."""


class EmailIntelligenceRateLimitError(EmailIntelligenceError):
    """Raised when the API request rate limit is reached."""


class EmailIntelligenceUpstreamError(EmailIntelligenceError):
    """Raised when Abstract or the network cannot complete the request."""


@dataclass(frozen=True)
class EmailIntelligenceResult:
    """Small, typed subset of reputation fields consumed by SnapClass."""

    email_address: Optional[str]
    suggested_correction: Optional[str]
    deliverability_status: Optional[str]
    deliverability_detail: Optional[str]
    is_format_valid: Optional[bool]
    is_smtp_valid: Optional[bool]
    is_mx_valid: Optional[bool]
    is_disposable: Optional[bool]
    address_risk_status: Optional[str]
    domain_risk_status: Optional[str]


def _api_key():
    key = os.environ.get(API_KEY_ENV)
    if not key:
        try:
            import streamlit as st

            key = st.secrets.get(API_KEY_ENV)
        except Exception:
            key = None
    if not key or not str(key).strip():
        raise EmailIntelligenceConfigurationError(
            f"Configure {API_KEY_ENV} in the server environment or Streamlit secrets."
        )
    return str(key).strip()


def _validate_email(email):
    if not isinstance(email, str):
        raise InvalidEmailError("Enter a valid email address.")
    value = email.strip()
    if (
        not value
        or len(value) > 254
        or len(value.rsplit("@", 1)[0]) > 64
        or not _EMAIL_PATTERN.fullmatch(value)
    ):
        raise InvalidEmailError("Enter a valid email address.")
    return value


def _optional_bool(container, key):
    value = container.get(key) if isinstance(container, dict) else None
    return value if isinstance(value, bool) else None


def _optional_string(container, key):
    value = container.get(key) if isinstance(container, dict) else None
    return value if isinstance(value, str) else None


def _parse_result(payload):
    if not isinstance(payload, dict):
        raise EmailIntelligenceUpstreamError("Abstract returned an unreadable response.")

    deliverability = payload.get("email_deliverability")
    quality = payload.get("email_quality")
    risk = payload.get("email_risk")
    return EmailIntelligenceResult(
        email_address=_optional_string(payload, "email_address"),
        suggested_correction=_optional_string(payload, "suggested_correction"),
        deliverability_status=_optional_string(deliverability, "status"),
        deliverability_detail=_optional_string(deliverability, "status_detail"),
        is_format_valid=_optional_bool(deliverability, "is_format_valid"),
        is_smtp_valid=_optional_bool(deliverability, "is_smtp_valid"),
        is_mx_valid=_optional_bool(deliverability, "is_mx_valid"),
        is_disposable=_optional_bool(quality, "is_disposable"),
        address_risk_status=_optional_string(risk, "address_risk_status"),
        domain_risk_status=_optional_string(risk, "domain_risk_status"),
    )


def check_email_reputation(email):
    """Check an email and return only the reputation fields SnapClass uses."""
    normalized_email = _validate_email(email)
    key = _api_key()
    request = Request(
        f"{API_URL}?{urlencode({'email': normalized_email})}",
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {key}",
            "User-Agent": "SnapClass/1.0",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        error.close()
        if error.code == 401:
            raise EmailIntelligenceAuthenticationError(
                "Abstract rejected the API key. Check the server secret."
            ) from error
        if error.code in (403, 422):
            raise EmailIntelligenceQuotaError(
                "Abstract API credits are exhausted. Check the account quota."
            ) from error
        if error.code == 429:
            raise EmailIntelligenceRateLimitError(
                "Abstract rate limit reached. Wait briefly and retry."
            ) from error
        raise EmailIntelligenceUpstreamError(
            f"Abstract could not complete the request (HTTP {error.code})."
        ) from error
    except (URLError, socket.timeout, TimeoutError, OSError) as error:
        raise EmailIntelligenceUpstreamError(
            "Could not reach Abstract Email Intelligence. Try again shortly."
        ) from error
    except (ValueError, UnicodeDecodeError) as error:
        raise EmailIntelligenceUpstreamError(
            "Abstract returned an unreadable response."
        ) from error

    return _parse_result(payload)
