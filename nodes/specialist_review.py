from tools.a2a_specialist_tool import request_specialist_review


def specialist_review(state: dict) -> dict:
    recommendation = request_specialist_review(state)
    return {
        "specialist_review": recommendation,
        "actions_taken": [{
            "action": "a2a_specialist_review",
            "result": recommendation,
        }],
    }
