import logging

from otel import add_event, function_trace, record_metric

logger = logging.getLogger(__name__)


@function_trace()
def ignored(state: dict) -> dict:
    triage_result = state.get("triage", {})
    record_metric("triage.non_complaint", 1)
    add_event("TicketIgnored", {
        "reason": str(triage_result.get("reason", ""))[:255],
        "confidence": triage_result.get("confidence", 0.0),
    })
    logger.info("Ticket ignored, not a complaint", extra={"reason": str(triage_result.get("reason", ""))[:255], "confidence": triage_result.get("confidence", 0.0)})
    return {
        "final_response": "",
        "actions_taken": [{
            "action": "ignored_non_complaint",
            "reason": triage_result.get("reason", "Triage classified ticket as not a complaint"),
        }],
    }
