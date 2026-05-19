import asyncio
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("AZURE_OPENAI_API_KEY", "test-key")
os.environ.setdefault("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com/")
os.environ.setdefault("AZURE_OPENAI_DEPLOYMENT_NAME", "test-deployment")

import main_fastapi


class Interrupt:
    def __init__(self, value, id="interrupt-1"):
        self.value = value
        self.id = id


class DummyGraph:
    def __init__(self, result):
        self.result = result
        self.calls = []

    async def ainvoke(self, input_value, config):
        self.calls.append((input_value, config))
        return self.result

    def get_state(self, config):
        return SimpleNamespace(
            interrupts=(),
            values={"ok": True},
            next=(),
        )


class MainFastApiTests(unittest.TestCase):
    def setUp(self):
        main_fastapi.review_runs.clear()

    def test_finalize_completed_workflow_updates_zendesk(self):
        async def fake_update_ticket_status_via_mcp(ticket_id, workflow_result, comment):
            return {
                "status": "success",
                "ticket_id": ticket_id,
                "comment": comment,
                "summary": workflow_result["resolution"],
            }

        with patch.object(
            main_fastapi,
            "update_ticket_status_via_mcp",
            fake_update_ticket_status_via_mcp,
        ):
            result = asyncio.run(main_fastapi._finalize_completed_workflow(
                thread_id="thread-1",
                ticket_id=123,
                result={"resolution": {"resolution_type": "apology"}},
            ))

        self.assertEqual(result["zendesk_update"]["status"], "success")
        self.assertEqual(result["zendesk_update"]["ticket_id"], 123)
        self.assertEqual(main_fastapi.review_runs["thread-1"]["status"], "completed")

    def test_process_complaint_async_records_pending_review_on_interrupt(self):
        interrupt = Interrupt({"reason": "Needs human"})
        graph = DummyGraph({"__interrupt__": [interrupt]})

        async def fail_if_called(**kwargs):
            raise AssertionError("Zendesk finalization should not run while interrupted")

        with (
            patch.object(main_fastapi, "complaint_graph", graph),
            patch.object(main_fastapi, "_finalize_completed_workflow", fail_if_called),
        ):
            result = asyncio.run(main_fastapi.process_complaint_async(
                complaint_text="Subject: problem\n\nRefund me",
                ticket_id=456,
                email="ada@example.com",
                thread_id="thread-2",
            ))

        self.assertEqual(result["status"], "pending_review")
        self.assertEqual(result["thread_id"], "thread-2")
        self.assertEqual(result["interrupts"], [{
            "id": "interrupt-1",
            "value": {"reason": "Needs human"},
        }])
        self.assertEqual(main_fastapi.review_runs["thread-2"]["status"], "pending_review")
        self.assertEqual(graph.calls[0][1], {"configurable": {"thread_id": "thread-2"}})

    def test_process_complaint_async_finalizes_completed_result(self):
        graph = DummyGraph({"resolution": {"resolution_type": "apology"}})

        async def fake_finalize(thread_id, ticket_id, result):
            result["zendesk_update"] = {"status": "success", "ticket_id": ticket_id}
            main_fastapi._record_run(thread_id, status="completed", result=result)
            return result

        with (
            patch.object(main_fastapi, "complaint_graph", graph),
            patch.object(main_fastapi, "_finalize_completed_workflow", fake_finalize),
        ):
            result = asyncio.run(main_fastapi.process_complaint_async(
                complaint_text="Subject: problem\n\nRefund me",
                ticket_id=789,
                email="ada@example.com",
                thread_id="thread-3",
            ))

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["thread_id"], "thread-3")
        self.assertEqual(result["result"]["zendesk_update"], {"status": "success", "ticket_id": 789})
        self.assertEqual(main_fastapi.review_runs["thread-3"]["status"], "completed")


if __name__ == "__main__":
    unittest.main()
