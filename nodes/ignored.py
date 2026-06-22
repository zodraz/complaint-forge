import newrelic.agent


@newrelic.agent.function_trace()
def ignored(state: dict) -> dict:
    triage_result = state.get("triage", {})
    newrelic.agent.record_custom_metric("Custom/Triage/NonComplaint", 1)
    newrelic.agent.record_custom_event("TicketIgnored", {
        "reason": str(triage_result.get("reason", ""))[:255],
        "confidence": triage_result.get("confidence", 0.0),
    })
    newrelic.agent.record_log_event("Ticket ignored, not a complaint", level="INFO", attributes={"reason": str(triage_result.get("reason",""))[:255], "confidence": triage_result.get("confidence", 0.0)})
    return {
        "final_response": "",
        "actions_taken": [{
            "action": "ignored_non_complaint",
            "reason": triage_result.get("reason", "Triage classified ticket as not a complaint"),
        }],
    }
