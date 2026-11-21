import json
from io import BytesIO
from urllib.error import HTTPError
from unittest import TestCase
from unittest.mock import patch

from src.components.email_intelligence import (
    API_KEY_ENV,
    EmailIntelligenceAuthenticationError,
    EmailIntelligenceQuotaError,
    EmailIntelligenceRateLimitError,
    EmailIntelligenceResult,
    EmailIntelligenceUpstreamError,
    InvalidEmailError,
    check_email_reputation,
)


class EmailIntelligenceTests(TestCase):
    def setUp(self):
        self.key_patch = patch.dict("os.environ", {API_KEY_ENV: "test-key"})
        self.key_patch.start()
        self.addCleanup(self.key_patch.stop)

    @patch("src.components.email_intelligence.urlopen")
    def test_validates_input_before_request(self, mock_urlopen):
        with self.assertRaises(InvalidEmailError):
            check_email_reputation("not-an-email")
        mock_urlopen.assert_not_called()

    @patch("src.components.email_intelligence.urlopen")
    def test_returns_typed_minimal_result_and_uses_bearer_auth(self, mock_urlopen):
        payload = {
            "email_address": "hello@abstractapi.com",
            "suggested_correction": None,
            "email_deliverability": {
                "status": "deliverable",
                "status_detail": "valid_email",
                "is_format_valid": True,
                "is_smtp_valid": True,
                "is_mx_valid": True,
            },
            "email_quality": {"is_disposable": False},
            "email_risk": {
                "address_risk_status": "low",
                "domain_risk_status": "low",
            },
        }
        mock_urlopen.return_value = BytesIO(json.dumps(payload).encode())

        result = check_email_reputation("hello@abstractapi.com")

        self.assertEqual(
            result,
            EmailIntelligenceResult(
                email_address="hello@abstractapi.com",
                suggested_correction=None,
                deliverability_status="deliverable",
                deliverability_detail="valid_email",
                is_format_valid=True,
                is_smtp_valid=True,
                is_mx_valid=True,
                is_disposable=False,
                address_risk_status="low",
                domain_risk_status="low",
            ),
        )
        request = mock_urlopen.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer test-key")
        self.assertNotIn("api_key", request.full_url)
        self.assertEqual(mock_urlopen.call_args.kwargs["timeout"], 10)

    @patch("src.components.email_intelligence.urlopen")
    def test_preserves_unavailable_fields(self, mock_urlopen):
        mock_urlopen.return_value = BytesIO(
            json.dumps({"email_deliverability": {"status": "unknown"}}).encode()
        )

        result = check_email_reputation("hello@abstractapi.com")

        self.assertEqual(result.deliverability_status, "unknown")
        self.assertIsNone(result.is_smtp_valid)
        self.assertIsNone(result.is_disposable)

    def _raise_http_error(self, status):
        raise HTTPError(
            "https://example.invalid", status, "error", None, BytesIO(b"")
        )

    @patch("src.components.email_intelligence.urlopen")
    def test_maps_authentication_quota_and_rate_limit_errors(self, mock_urlopen):
        for status, expected in (
            (401, EmailIntelligenceAuthenticationError),
            (403, EmailIntelligenceQuotaError),
            (422, EmailIntelligenceQuotaError),
            (429, EmailIntelligenceRateLimitError),
        ):
            with self.subTest(status=status):
                mock_urlopen.side_effect = lambda *args, _status=status, **kwargs: self._raise_http_error(_status)
                with self.assertRaises(expected):
                    check_email_reputation("hello@abstractapi.com")

    @patch("src.components.email_intelligence.urlopen")
    def test_maps_other_upstream_errors(self, mock_urlopen):
        mock_urlopen.side_effect = lambda *args, **kwargs: self._raise_http_error(503)
        with self.assertRaises(EmailIntelligenceUpstreamError):
            check_email_reputation("hello@abstractapi.com")

