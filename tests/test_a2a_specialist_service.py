import unittest
from types import SimpleNamespace
from unittest.mock import patch

import a2a_refund_specialist_service.llm_factory as llm_factory
from a2a_refund_specialist_service.app import (
    SpecialistRequest,
    _crewai_import_failure_reason,
    run_crewai_review,
)


class A2ASpecialistServiceTests(unittest.TestCase):
    def test_crewai_import_failure_mentions_python_314_constraint(self):
        with patch("a2a_refund_specialist_service.app.sys.version_info", (3, 14, 0)):
            reason = _crewai_import_failure_reason(ModuleNotFoundError("No module named 'crewai'"))

        self.assertIn("CrewAI import failed", reason)
        self.assertIn("Python is 3.14.0", reason)
        self.assertIn("Python >=3.10,<3.14", reason)

    def test_service_llm_factory_builds_crewai_azure_llm(self):
        captured = {}

        class FakeLLM:
            def __init__(self, **kwargs):
                captured.update(kwargs)

        fake_crewai = SimpleNamespace(LLM=FakeLLM)

        with (
            patch.dict("sys.modules", {"crewai": fake_crewai}),
            patch.object(llm_factory, "AZURE_OPENAI_API_KEY", "azure-key"),
            patch.object(
                llm_factory,
                "AZURE_OPENAI_ENDPOINT",
                "https://example.openai.azure.com/",
            ),
            patch.object(llm_factory, "AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
            patch.object(llm_factory, "AZURE_OPENAI_API_VERSION", "2024-06-01"),
        ):
            llm = llm_factory.get_chat_llm(temperature=0.2)

        self.assertIsInstance(llm, FakeLLM)
        self.assertEqual(captured["model"], "azure/gpt-4o")
        self.assertEqual(captured["endpoint"], "https://example.openai.azure.com/")
        self.assertEqual(captured["api_key"], "azure-key")
        self.assertEqual(captured["api_version"], "2024-06-01")
        self.assertEqual(captured["temperature"], 0.2)


class A2ASpecialistServiceAsyncTests(unittest.IsolatedAsyncioTestCase):
    async def test_run_crewai_review_uses_async_kickoff(self):
        calls = []
        captured_agent_kwargs = {}

        class FakeAgent:
            def __init__(self, **kwargs):
                captured_agent_kwargs.update(kwargs)
                pass

        class FakeTask:
            def __init__(self, **kwargs):
                pass

        class FakeCrew:
            def __init__(self, **kwargs):
                pass

            async def kickoff_async(self):
                calls.append("kickoff_async")
                return SimpleNamespace(
                    raw='{"decision": "human_review_required", "risk_level": "medium", '
                    '"approved": false, "refund_amount": 0, "credit_amount": 0, '
                    '"reasoning": "Needs human approval.", "human_reviewer_notes": [], '
                    '"draft_response": "We are reviewing your case."}'
                )

        fake_crewai = SimpleNamespace(
            Agent=FakeAgent,
            Crew=FakeCrew,
            Process=SimpleNamespace(sequential="sequential"),
            Task=FakeTask,
        )

        with (
            patch.dict("sys.modules", {"crewai": fake_crewai}),
            patch(
                "a2a_refund_specialist_service.app.get_chat_llm",
                return_value="azure-llm",
            ),
        ):
            result = await run_crewai_review(
                SpecialistRequest(
                    complaint="Refund request",
                    customer_email="ada@example.com",
                )
            )

        self.assertEqual(calls, ["kickoff_async"])
        self.assertEqual(captured_agent_kwargs["llm"], "azure-llm")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["source"], "crewai")
        self.assertEqual(result["recommendation"]["decision"], "human_review_required")


if __name__ == "__main__":
    unittest.main()
