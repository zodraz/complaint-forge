import unittest
from unittest.mock import patch

import requests

import tools.salesforce_tool as tool


class DummyResponse:
    def __init__(self, payload, status_code=200, content=b"{}"):
        self.payload = payload
        self.status_code = status_code
        self.content = content
        self.text = str(payload)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Client Error")

    def json(self):
        if isinstance(self.payload, ValueError):
            raise self.payload
        return self.payload


class SalesforceToolTests(unittest.TestCase):
    def test_get_access_token_reports_salesforce_oauth_error_body(self):
        def fake_post(url, data, timeout):
            return DummyResponse(
                {
                    "error": "invalid_client",
                    "error_description": "invalid client credentials",
                },
                status_code=400,
            )

        with (
            patch.object(tool, "SALESFORCE_LOGIN_URL", "https://login.salesforce.com"),
            patch.object(tool, "SALESFORCE_CLIENT_ID", "client-id"),
            patch.object(tool, "SALESFORCE_CLIENT_SECRET", "client-secret"),
            patch.object(tool.requests, "post", fake_post),
        ):
            with self.assertRaises(RuntimeError) as raised:
                tool._get_access_token()

        message = str(raised.exception)
        self.assertIn("Salesforce OAuth token request failed with HTTP 400", message)
        self.assertIn("invalid_client: invalid client credentials", message)
        self.assertNotIn("client-secret", message)

    def test_get_access_token_posts_client_credentials_payload(self):
        captured = {}

        def fake_post(url, data, timeout):
            captured.update({"url": url, "data": data, "timeout": timeout})
            return DummyResponse(
                {
                    "access_token": "access-token",
                    "instance_url": "https://example.my.salesforce.com/",
                },
            )

        with (
            patch.object(tool, "SALESFORCE_LOGIN_URL", "https://test.salesforce.com/"),
            patch.object(tool, "SALESFORCE_CLIENT_ID", "client-id"),
            patch.object(tool, "SALESFORCE_CLIENT_SECRET", "client-secret"),
            patch.object(tool.requests, "post", fake_post),
        ):
            access_token, instance_url = tool._get_access_token()

        self.assertEqual(access_token, "access-token")
        self.assertEqual(instance_url, "https://example.my.salesforce.com")
        self.assertEqual(
            captured,
            {
                "url": "https://test.salesforce.com/services/oauth2/token",
                "data": {
                    "grant_type": "client_credentials",
                    "client_id": "client-id",
                    "client_secret": "client-secret",
                },
                "timeout": 30,
            },
        )


if __name__ == "__main__":
    unittest.main()
