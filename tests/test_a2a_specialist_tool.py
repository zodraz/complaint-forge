import unittest
from unittest.mock import patch

import tools.a2a_specialist_tool as tool


class DummyResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class A2ASpecialistToolTests(unittest.TestCase):
    def test_request_specialist_review_skips_without_url(self):
        with patch.object(tool, "A2A_SPECIALIST_URL", None):
            result = tool.request_specialist_review({"complaint": "Where is my order?"})

        self.assertEqual(result["status"], "skipped")
        self.assertIn("A2A_SPECIALIST_URL", result["reason"])

    def test_request_specialist_review_posts_expected_payload(self):
        captured = {}

        def fake_post(url, json, headers, timeout):
            captured.update({
                "url": url,
                "json": json,
                "headers": headers,
                "timeout": timeout,
            })
            return DummyResponse({"status": "success", "recommendation": {"approved": False}})

        with (
            patch.object(tool, "A2A_SPECIALIST_URL", "http://specialist"),
            patch.object(tool, "A2A_SPECIALIST_AUTH_TOKEN", "secret"),
            patch.object(tool.requests, "post", fake_post),
        ):
            result = tool.request_specialist_review({
                "complaint": "Refund me",
                "triage": {"is_complaint": True},
                "customer_email": "ada@example.com",
                "order_id": "ORD-1",
                "customer_history": {"matched_order": {"TotalAmount": 900}},
                "analysis": {"sentiment": "very_negative"},
                "resolution": {"resolution_type": "escalate"},
                "policy_result": {"approved": False},
                "eval_results": {"empathy_score": {"score": 5}},
                "actions_taken": [{"action": "policy_escalation"}],
            })

        self.assertEqual(result["status"], "success")
        self.assertEqual(captured["url"], "http://specialist/tasks/refund-specialist")
        self.assertEqual(captured["headers"]["Authorization"], "Bearer secret")
        self.assertEqual(captured["timeout"], 60)
        self.assertEqual(captured["json"]["customer_email"], "ada@example.com")
        self.assertEqual(captured["json"]["resolution"]["resolution_type"], "escalate")


if __name__ == "__main__":
    unittest.main()
