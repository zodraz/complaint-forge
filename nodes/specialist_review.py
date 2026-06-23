import logging

from otel import add_event, function_trace, record_metric, set_attribute
from tools.a2a_specialist_tool import request_specialist_review

logger = logging.getLogger(__name__)


@function_trace()
def specialist_review(state: dict) -> dict:
    add_event("SpecialistReviewRequested", {
        "resolution_type": state.get("resolution", {}).get("resolution_type", ""),
        "escalation_reason": str(state.get("resolution", {}).get("action_needed", ""))[:255],
    })
    logger.info("Requesting A2A specialist review", extra={"resolution_type": state.get("resolution", {}).get("resolution_type", ""), "reason": str(state.get("resolution", {}).get("action_needed", ""))[:255]})
    recommendation = request_specialist_review(state)
    set_attribute("specialist_review.status", recommendation.get("status", ""))
    record_metric("specialist_review.requested", 1)
    status = recommendation.get("status", "")
    if status == "error":
        logger.error("A2A specialist review failed", extra={"status": status, "detail": str(recommendation.get("message", ""))[:255]})
    else:
        logger.info("A2A specialist review completed", extra={"status": status, "source": recommendation.get("source", "")})
    return {
        "specialist_review": recommendation,
        "actions_taken": [{
            "action": "a2a_specialist_review",
            "result": recommendation,
        }],
    }
