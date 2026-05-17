from langgraph.types import interrupt


def human_review(state: dict) -> dict:
    resolution = state.get("resolution", {})
    review = interrupt({
        "reason": resolution.get("action_needed", "Escalation requested"),
        "complaint": state.get("complaint"),
        "customer_email": state.get("customer_email"),
        "order_id": state.get("order_id"),
        "customer_history": state.get("customer_history", {}),
        "analysis": state.get("analysis", {}),
        "resolution": resolution,
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
