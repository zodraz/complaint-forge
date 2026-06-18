import unittest
from unittest.mock import patch

import agents.triage as triage_module


class DummyPromptTemplate:
    def __init__(self, template):
        self.template = template

    def __or__(self, other):
        return other

    @classmethod
    def from_template(cls, template):
        return cls(template)


class DummyResult:
    def __init__(self, result):
        self._result = result

    def model_dump(self):
        return self._result


class DummyStructuredOutput:
    def __init__(self, result):
        self.result = result
        self.invoked_with = None

    def invoke(self, inputs):
        self.invoked_with = inputs
        return DummyResult(self.result)


class DummyLLM:
    def __init__(self, chain):
        self._chain = chain

    def with_structured_output(self, output_model):
        return self._chain


class TriageTests(unittest.TestCase):
    def test_triage_uses_llm_structured_output_and_returns_expected_fields(self):
        dummy_result = {
            "is_complaint": True,
            "confidence": 0.94,
            "reason": "Customer request is a refund complaint.",
            "customer_email": "ada@example.com",
            "order_id": "ORD-123",
        }
        dummy_chain = DummyStructuredOutput(dummy_result)
        dummy_llm = DummyLLM(dummy_chain)

        with patch.object(triage_module, "ChatPromptTemplate", DummyPromptTemplate), \
             patch.object(triage_module, "llm", dummy_llm):
            result = triage_module.triage({"complaint": "Refund requested for missing order."})

        self.assertEqual(result["triage"], dummy_result)
        self.assertEqual(result["customer_email"], "ada@example.com")
        self.assertEqual(result["order_id"], "ORD-123")
        self.assertEqual(dummy_chain.invoked_with, {"input": "Refund requested for missing order."})

    def test_triage_returns_safe_fallback_on_llm_failure(self):
        dummy_chain = DummyStructuredOutput(None)

        def failing_invoke(inputs):
            raise RuntimeError("LLM request timed out")

        dummy_chain.invoke = failing_invoke
        dummy_llm = DummyLLM(dummy_chain)

        with patch.object(triage_module, "ChatPromptTemplate", DummyPromptTemplate), \
             patch.object(triage_module, "llm", dummy_llm):
            result = triage_module.triage({"complaint": "Refund requested for missing order."})

        self.assertEqual(result["triage"]["is_complaint"], False)
        self.assertEqual(result["triage"]["confidence"], 0.0)
        self.assertIn("LLM triage unavailable", result["triage"]["reason"])
        self.assertIsNone(result["customer_email"])
        self.assertIsNone(result["order_id"])


if __name__ == "__main__":
    unittest.main()
