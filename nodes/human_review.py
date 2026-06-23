import logging

from langgraph.types import interrupt
from otel import add_event, function_trace, record_metric, set_attribute

logger = logging.getLogger(__name__)


@function_trace()
def human_review(state: dict) -> dict:
    resolution = state.get("resolution", {})

    set_attribute("human_review.reason", str(resolution.get("action_needed", ""))[:255])
    record_metric("human_review.triggered", 1)
    add_event("HumanReviewTriggered", {
        "reason": str(resolution.get("action_needed", "Escalation requested"))[:255],
        "resolution_type": resolution.get("resolution_type", ""),
        "has_specialist_review": bool(state.get("specialist_review")),
    })
    logger.warning("Human review required, workflow paused", extra={"reason": str(resolution.get("action_needed", "Escalation requested"))[:255], "resolution_type": resolution.get("resolution_type", ""), "customer_email": str(state.get("customer_email", ""))})

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
