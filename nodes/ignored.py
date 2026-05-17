def ignored(state: dict) -> dict:
    triage_result = state.get("triage", {})
    return {
        "final_response": "",
        "actions_taken": [{
            "action": "ignored_non_complaint",
            "reason": triage_result.get("reason", "Triage classified ticket as not a complaint"),
        }],
    }
