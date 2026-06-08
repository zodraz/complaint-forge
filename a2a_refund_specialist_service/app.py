import json
import os
import sys
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from llm_factory import get_chat_llm

load_dotenv()

app = FastAPI(
    title="Refund Specialist A2A Service",
    description="CrewAI-powered specialist reviewer for ComplaintForge escalations",
    version="0.1.0",
)

AUTH_TOKEN = os.getenv("A2A_SPECIALIST_AUTH_TOKEN")


class SpecialistRequest(BaseModel):
    complaint: str
    triage: dict[str, Any] = Field(default_factory=dict)
    customer_email: str | None = None
    order_id: str | None = None
    customer_history: dict[str, Any] = Field(default_factory=dict)
    analysis: dict[str, Any] = Field(default_factory=dict)
    resolution: dict[str, Any] = Field(default_factory=dict)
    policy_result: dict[str, Any] = Field(default_factory=dict)
    eval_results: dict[str, Any] = Field(default_factory=dict)
    actions_taken: list[dict[str, Any]] = Field(default_factory=list)


def _authorize(authorization: str | None) -> None:
    if not AUTH_TOKEN:
        return
    if authorization != f"Bearer {AUTH_TOKEN}":
        raise HTTPException(status_code=401, detail="Invalid specialist service token")


def _fallback_recommendation(reason: str) -> dict[str, Any]:
    return {
        "status": "success",
        "source": "fallback",
        "recommendation": {
            "decision": "human_review_required",
            "risk_level": "unknown",
            "approved": False,
            "refund_amount": 0,
            "credit_amount": 0,
            "reasoning": reason,
            "human_reviewer_notes": [
                "CrewAI could not run, so review the escalation manually.",
                "Check Salesforce order, cases, returns, and policy before approving action.",
            ],
            "draft_response": (
                "Thank you for your patience. Your case is being reviewed by our "
                "support team, and we will follow up shortly."
            ),
        },
    }


def _extract_json(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:].strip()
    return json.loads(raw)


def _crewai_import_failure_reason(error: Exception) -> str:
    reason = f"CrewAI import failed: {error}"
    if sys.version_info >= (3, 14):
        version = ".".join(map(str, sys.version_info[:3]))
        reason += (
            f". Current Python is {version}, but CrewAI releases currently require "
            "Python >=3.10,<3.14. Run this service with Python 3.13 or earlier."
        )
    return reason


async def run_crewai_review(request: SpecialistRequest) -> dict[str, Any]:
    try:
        from crewai import Agent, Crew, Process, Task
    except Exception as e:
        return _fallback_recommendation(_crewai_import_failure_reason(e))

    try:
        llm = get_chat_llm(temperature=1)
        specialist = Agent(
            role="Refund and Escalation Specialist",
            goal=(
                "Review escalated complaint cases and prepare a concise, policy-aware "
                "recommendation for a human approver."
            ),
            backstory=(
                "You are a senior support operations specialist. You do not execute "
                "refunds. You prepare evidence-based recommendations for humans."
            ),
            llm=llm,
            verbose=True,
        )

        task = Task(
            description=(
                "Review this escalated complaint package and return ONLY JSON.\n\n"
                "Complaint package:\n"
                f"{request.model_dump_json(indent=2)}\n\n"
                "The JSON must include: decision, risk_level, approved, refund_amount, "
                "credit_amount, reasoning, human_reviewer_notes, draft_response.\n"
                "Use approved=false unless the evidence clearly supports automation. "
                "This is advisory only; a human remains final authority."
            ),
            expected_output=(
                "A JSON object with decision, risk_level, approved, refund_amount, "
                "credit_amount, reasoning, human_reviewer_notes, and draft_response."
            ),
            agent=specialist,
        )

        crew = Crew(
            agents=[specialist],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )
    except Exception as e:
        return _fallback_recommendation(f"CrewAI setup failed: {e}")

    try:
        output = await crew.kickoff_async()
        raw = getattr(output, "raw", str(output))
        return {
            "status": "success",
            "source": "crewai",
            "recommendation": _extract_json(raw),
        }
    except Exception as e:
        return _fallback_recommendation(f"CrewAI execution failed: {e}")


@app.get("/.well-known/agent-card.json")
async def agent_card():
    return {
        "name": "refund-specialist",
        "description": "Reviews escalated refund, credit, and replacement cases for human approval.",
        "version": "0.1.0",
        "url": "/tasks/refund-specialist",
        "capabilities": [
            "refund_review",
            "credit_review",
            "replacement_review",
            "human_reviewer_packet",
        ],
    }


@app.post("/tasks/refund-specialist")
async def refund_specialist(
    request: SpecialistRequest,
    authorization: str | None = Header(default=None),
):
    _authorize(authorization)
    return await run_crewai_review(request)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "refund-specialist-a2a"}
