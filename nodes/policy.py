from typing import Any

import newrelic.agent


def _append_reason(reasons: list[str], condition: bool, reason: str) -> None:
    if condition:
        reasons.append(reason)


def _complaint_mentions_excluded_product(complaint: str, analysis: dict[str, Any]) -> bool:
    text = " ".join([
        complaint or "",
        str(analysis.get("key_details", "")),
        str(analysis.get("issue_type", "")),
    ]).lower()
    return any(term in text for term in ("digital", "download", "custom", "personalized"))


@newrelic.agent.function_trace()
def policy(state: dict[str, Any]) -> dict[str, Any]:
    """Apply deterministic business policy before drafting or external actions."""
    resolution = dict(state.get("resolution", {}))
    history = state.get("customer_history", {})
    analysis = state.get("analysis", {})
    complaint = state.get("complaint", "")

    reasons: list[str] = []
    refund_amount = float(resolution.get("refund_amount") or 0)
    credit_amount = float(resolution.get("credit_amount") or 0)
    confidence = float(resolution.get("confidence") or 0)
    is_excluded_product = _complaint_mentions_excluded_product(complaint, analysis)

    _append_reason(
        reasons,
        confidence < 0.85,
        "Resolution confidence below 0.85",
    )
    _append_reason(
        reasons,
        refund_amount > 500,
        "Refund amount exceeds $500 approval limit",
    )
    _append_reason(
        reasons,
        bool(history.get("error")),
        f"Customer history lookup failed: {history.get('error')}",
    )
    _append_reason(
        reasons,
        resolution.get("resolution_type") in {"full_refund", "partial_refund"}
        and not history.get("matched_order"),
        "Refund requires a matched Salesforce order",
    )
    _append_reason(
        reasons,
        is_excluded_product
        and resolution.get("resolution_type") in {"full_refund", "partial_refund"},
        "Digital or custom products cannot be refunded automatically",
    )

    newrelic.agent.add_custom_attribute("policy.approved", not bool(reasons))
    newrelic.agent.add_custom_attribute("policy.escalation_reasons_count", len(reasons))
    newrelic.agent.record_custom_metric("Custom/Policy/Escalated", 1 if reasons else 0)
    newrelic.agent.record_custom_event("PolicyDecision", {"approved": not bool(reasons), "reasons_count": len(reasons), "refund_amount": refund_amount, "confidence": confidence, "is_excluded_product": is_excluded_product})

    if reasons:
        newrelic.agent.record_log_event("Policy escalation triggered", level="WARNING", attributes={"reasons": "; ".join(reasons)[:255], "refund_amount": refund_amount, "confidence": confidence})
    else:
        newrelic.agent.record_log_event("Policy approved resolution", level="INFO", attributes={"resolution_type": resolution.get("resolution_type",""), "refund_amount": refund_amount, "confidence": confidence})

    if reasons:
        resolution.update({
            "resolution_type": "escalate",
            "refund_amount": 0,
            "credit_amount": credit_amount if is_excluded_product else 0,
            "action_needed": "; ".join(reasons),
            "confidence": min(confidence, 0.0),
        })
        return {
            "resolution": resolution,
            "policy_result": {
                "approved": False,
                "reasons": reasons,
            },
            "actions_taken": [{
                "action": "policy_escalation",
                "reason": "; ".join(reasons),
            }],
        }

    return {
        "policy_result": {
            "approved": True,
            "reasons": [],
        },
    }
