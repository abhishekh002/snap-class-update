import json
from io import BytesIO
from urllib.error import HTTPError
from unittest import TestCase
from unittest.mock import patch

from src.components.resend_email import ResendEmailError, send_password_reset_email


class ResendEmailTests(TestCase):
    @patch("src.components.resend_email.urlopen")
    def test_sends_reset_email_with_server_side_auth_and_timeout(self, mock_urlopen):
        mock_urlopen.return_value = BytesIO(b'{"id":"email_123"}')

        email_id = send_password_reset_email(
            "test-api-key", "no-reply@example.com", "teacher@example.net", "042913"
        )

        request = mock_urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(email_id, "email_123")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-api-key")
        self.assertEqual(payload["from"], "SnapClass <no-reply@example.com>")
        self.assertEqual(payload["to"], ["teacher@example.net"])
        self.assertIn("042913", payload["text"])
        self.assertEqual(mock_urlopen.call_args.kwargs["timeout"], 10)

    @patch("src.components.resend_email.urlopen")
    def test_accepts_custom_sender_display_name(self, mock_urlopen):
        mock_urlopen.return_value = BytesIO(b'{"id":"email_123"}')

        send_password_reset_email(
            "test-api-key",
            "SnapClass <no-reply@example.com>",
            "teacher@example.net",
            "042913",
        )

        payload = json.loads(mock_urlopen.call_args.args[0].data.decode("utf-8"))
        self.assertEqual(payload["from"], "SnapClass <no-reply@example.com>")

    def _raise_http_error(self, status):
        raise HTTPError(
            "https://api.resend.com/emails", status, "error", None, BytesIO(b"")
        )

    @patch("src.components.resend_email.urlopen")
    def test_reports_auth_domain_rate_and_upstream_errors(self, mock_urlopen):
        cases = (
            (401, "rejected the API key"),
            (403, "Verify your sending domain"),
            (422, "Verify your sending domain"),
            (429, "rate limit"),
            (503, "HTTP 503"),
        )
        for status, expected_message in cases:
            with self.subTest(status=status):
                mock_urlopen.side_effect = lambda *args, _status=status, **kwargs: self._raise_http_error(_status)
                with self.assertRaisesRegex(ResendEmailError, expected_message):
                    send_password_reset_email(
                        "test-api-key",
                        "no-reply@example.com",
                        "teacher@example.net",
                        "042913",
                    )

    @patch("src.components.resend_email.urlopen")
    def test_rejects_response_without_message_id(self, mock_urlopen):
        mock_urlopen.return_value = BytesIO(b'{"message":"accepted"}')

        with self.assertRaisesRegex(ResendEmailError, "did not confirm"):
            send_password_reset_email(
                "test-api-key", "no-reply@example.com", "teacher@example.net", "042913"
            )

