import os
from typing import Any

import requests


A2A_SPECIALIST_URL = os.getenv("A2A_SPECIALIST_URL")
A2A_SPECIALIST_AUTH_TOKEN = os.getenv("A2A_SPECIALIST_AUTH_TOKEN")


def request_specialist_review(state: dict[str, Any]) -> dict[str, Any]:
    """Call the external A2A specialist service for an escalation recommendation."""
    if not A2A_SPECIALIST_URL:
        return {
            "status": "skipped",
            "reason": "A2A_SPECIALIST_URL is not configured",
        }

    headers = {"Accept": "application/json"}
    if A2A_SPECIALIST_AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {A2A_SPECIALIST_AUTH_TOKEN}"

    payload = {
        "complaint": state.get("complaint"),
        "triage": state.get("triage", {}),
        "customer_email": state.get("customer_email"),
        "order_id": state.get("order_id"),
        "customer_history": state.get("customer_history", {}),
        "analysis": state.get("analysis", {}),
        "resolution": state.get("resolution", {}),
        "policy_result": state.get("policy_result", {}),
        "eval_results": state.get("eval_results", {}),
        "actions_taken": state.get("actions_taken", []),
    }

    try:
        response = requests.post(
            A2A_SPECIALIST_URL.rstrip("/") + "/tasks/refund-specialist",
            json=payload,
            headers=headers,
            timeout=60,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "service_url": A2A_SPECIALIST_URL,
        }
