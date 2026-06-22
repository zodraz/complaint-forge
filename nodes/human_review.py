import newrelic.agent
from langgraph.types import interrupt


@newrelic.agent.function_trace()
def human_review(state: dict) -> dict:
    resolution = state.get("resolution", {})

    newrelic.agent.add_custom_attribute("human_review.reason", str(resolution.get("action_needed", ""))[:255])
    newrelic.agent.record_custom_metric("Custom/HumanReview/Triggered", 1)
    newrelic.agent.record_custom_event("HumanReviewTriggered", {
        "reason": str(resolution.get("action_needed", "Escalation requested"))[:255],
        "resolution_type": resolution.get("resolution_type", ""),
        "has_specialist_review": bool(state.get("specialist_review")),
    })
    newrelic.agent.record_log_event("Human review required, workflow paused", level="WARNING", attributes={"reason": str(resolution.get("action_needed","Escalation requested"))[:255], "resolution_type": resolution.get("resolution_type",""), "customer_email": str(state.get("customer_email",""))})

    review = interrupt({
        "reason": resolution.get("action_needed", "Escalation requested"),
        "complaint": state.get("complaint"),
        "customer_email": state.get("customer_email"),
        "customer_phone": state.get("customer_phone"),
        "order_id": state.get("order_id"),
        "customer_history": state.get("customer_history", {}),
        "analysis": state.get("analysis", {}),
        "resolution": resolution,
        "specialist_review": state.get("specialist_review", {}),
    })

    final_response = None
    if isinstance(review, dict):
        final_response = review.get("final_response")

    return {
        "human_review": review,
        "actions_taken": [{
            "action": "escalate_to_human",
            "reason": resolution.get("action_needed"),
            "review": review,
        }],
        "final_response": final_response or (
            "Thank you for reaching out. Your issue has been escalated to our "
            "support team for review, and we will follow up with you directly."
        ),
    }
