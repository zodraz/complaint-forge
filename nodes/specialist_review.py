import newrelic.agent

from tools.a2a_specialist_tool import request_specialist_review


@newrelic.agent.function_trace()
def specialist_review(state: dict) -> dict:
    newrelic.agent.record_custom_event("SpecialistReviewRequested", {
        "resolution_type": state.get("resolution", {}).get("resolution_type", ""),
        "escalation_reason": str(state.get("resolution", {}).get("action_needed", ""))[:255],
    })
    newrelic.agent.record_log_event("Requesting A2A specialist review", level="INFO", attributes={"resolution_type": state.get("resolution",{}).get("resolution_type",""), "reason": str(state.get("resolution",{}).get("action_needed",""))[:255]})
    recommendation = request_specialist_review(state)
    newrelic.agent.add_custom_attribute("specialist_review.status", recommendation.get("status", ""))
    newrelic.agent.record_custom_metric("Custom/SpecialistReview/Requested", 1)
    status = recommendation.get("status","")
    if status == "error":
        newrelic.agent.record_log_event("A2A specialist review failed", level="ERROR", attributes={"status": status, "message": str(recommendation.get("message",""))[:255]})
    else:
        newrelic.agent.record_log_event("A2A specialist review completed", level="INFO", attributes={"status": status, "source": recommendation.get("source","")})
    return {
        "specialist_review": recommendation,
        "actions_taken": [{
            "action": "a2a_specialist_review",
            "result": recommendation,
        }],
    }
