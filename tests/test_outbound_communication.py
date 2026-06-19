import unittest
from unittest.mock import patch

from nodes.outbound_communication import communication_node
from nodes.communication_models import CommunicationPayload, DeliveryRecord


class CommunicationNodeTests(unittest.TestCase):
    def setUp(self):
        self.base_state = {
            "correlation_id": "11111111-2222-3333-4444-555555555555",
            "subject": "Order update",
            "response_draft": "Your refund has been processed.",
            "customer_email": "customer@example.com",
            "recipient_phone": "+15551234567",
            "metadata": {"order_id": "ORD-123"},
        }

    def test_email_success_returns_delivered_email(self):
        with patch("nodes.outbound_communication.send_email", return_value={
            "status": "success",
            "provider": "mailchimp",
            "provider_response": {"status_code": 202},
        }):
            result = communication_node(self.base_state)

        self.assertEqual(result["delivery_record"].final_status, "delivered_email")
        self.assertEqual(len(result["delivery_record"].attempts), 1)
        self.assertEqual(result["delivery_record"].attempts[0].provider, "mailchimp")

    def test_email_bounce_triggers_sms_fallback(self):
        with patch("nodes.outbound_communication.send_email", return_value={
            "status": "permanent_failure",
            "provider": "mailchimp",
            "provider_response": {"status_code": 400},
        }), patch("nodes.outbound_communication.send_sms", return_value={
            "status": "success",
            "provider": "mailchimp",
            "provider_response": {"sid": "SM123"},
        }):
            result = communication_node(self.base_state)

        self.assertEqual(result["delivery_record"].final_status, "delivered_sms")
        self.assertEqual(len(result["delivery_record"].attempts), 2)
        self.assertEqual(result["delivery_record"].attempts[1].provider, "mailchimp")

    def test_email_bounce_without_phone_emits_human_review(self):
        state = dict(self.base_state)
        state.pop("recipient_phone", None)

        with patch("nodes.outbound_communication.send_email", return_value={
            "status": "permanent_failure",
            "provider": "mailchimp",
            "provider_response": {"status_code": 400},
        }), patch("nodes.outbound_communication.interrupt", return_value={"reviewed": True}):
            result = communication_node(state)

        self.assertEqual(result["delivery_record"].final_status, "failed")
        self.assertIn("human_review", result)

    def test_missing_recipient_triggers_human_review(self):
        state = dict(self.base_state)
        state.pop("customer_email", None)
        state.pop("recipient_phone", None)

        with patch("nodes.outbound_communication.interrupt", return_value={"reviewed": True}):
            result = communication_node(state)

        self.assertEqual(result["delivery_record"].final_status, "failed")
        self.assertIn("human_review", result)


if __name__ == "__main__":
    unittest.main()
