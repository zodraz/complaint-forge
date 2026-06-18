import unittest
from unittest.mock import patch

import tools.a2a_specialist_tool as specialist_tool
import nodes.human_review as human_review_node
import nodes.specialist_review as specialist_review_node


class NodeTests(unittest.TestCase):
    def test_specialist_review_records_recommendation(self):
        recommendation = {
            "status": "success",
            "recommendation": {"decision": "human_review_required"},
        }

        with patch.object(
            specialist_review_node,
            "request_specialist_review",
            lambda state: recommendation,
        ):
            result = specialist_review_node.specialist_review({"complaint": "Refund me"})

        self.assertEqual(result["specialist_review"], recommendation)
        self.assertEqual(result["actions_taken"], [{
            "action": "a2a_specialist_review",
            "result": recommendation,
        }])

    def test_specialist_review_handles_external_service_error(self):
        error_response = {
            "status": "error",
            "message": "Service unavailable",
        }

        with patch.object(
            specialist_review_node,
            "request_specialist_review",
            lambda state: error_response,
        ):
            result = specialist_review_node.specialist_review({"complaint": "Refund me"})

        self.assertEqual(result["specialist_review"], error_response)
        self.assertEqual(result["actions_taken"], [{
            "action": "a2a_specialist_review",
            "result": error_response,
        }])

    def test_specialist_review_outage_fallback_reached(self):
        def fake_post(url, json, headers, timeout):
            raise specialist_tool.requests.exceptions.ConnectionError("connection refused")

        with (
            patch.object(specialist_tool, "A2A_SPECIALIST_URL", "http://specialist"),
            patch.object(specialist_tool.requests, "post", fake_post),
            patch.object(specialist_tool.time, "sleep", lambda _: None),
        ):
            result = specialist_review_node.specialist_review({"complaint": "Refund me"})

        self.assertEqual(result["specialist_review"]["status"], "error")
        self.assertEqual(result["specialist_review"]["fallback"], "retry_exhausted")
        self.assertEqual(result["actions_taken"][0]["action"], "a2a_specialist_review")

    def test_human_review_interrupt_payload_includes_specialist_review(self):
        captured = {}

        def fake_interrupt(payload):
            captured.update(payload)
            return {
                "approved": True,
                "final_response": "Approved response",
            }

        with patch.object(human_review_node, "interrupt", fake_interrupt):
            result = human_review_node.human_review({
                "complaint": "Refund me",
                "customer_email": "ada@example.com",
                "order_id": "ORD-1",
                "customer_history": {"has_prior_cases": True},
                "analysis": {"urgency": "high"},
                "resolution": {
                    "resolution_type": "escalate",
                    "action_needed": "High value refund",
                },
                "specialist_review": {"recommendation": {"risk_level": "medium"}},
            })

        self.assertEqual(captured["specialist_review"], {"recommendation": {"risk_level": "medium"}})
        self.assertEqual(captured["reason"], "High value refund")
        self.assertIs(result["human_review"]["approved"], True)
        self.assertEqual(result["final_response"], "Approved response")
        self.assertEqual(result["actions_taken"][0]["action"], "escalate_to_human")


if __name__ == "__main__":
    unittest.main()
