from types import SimpleNamespace
from typing import Any

from response_evaluators import RESPONSE_QUALITY_EVALUATORS


def apply_guardrails(eval_results: dict[str, dict[str, Any]]) -> tuple[bool, str, dict[str, Any]]:
    empathy = eval_results.get("empathy_score", {})
    resolution = eval_results.get("resolution_appropriateness", {})

    failures = []

    if empathy.get("score", 0) < 6:
        failures.append("Response empathy score below threshold")

    if resolution.get("score", 0) < 6:
        failures.append("Resolution appropriateness score below threshold")

    if failures:
        return False, "; ".join(failures), eval_results

    return True, "All response quality guardrails passed", eval_results


async def guardrails(state: dict[str, Any]) -> dict[str, Any]:
    """
    Run response quality guardrails after the response draft and before external actions.
    """
    result = dict(state)
    complaint_text = state.get("complaint", "")

    print("Running response quality evaluators...")
    eval_results = {}

    for eval_name, evaluator_func in RESPONSE_QUALITY_EVALUATORS.items():
        try:
            eval_output = evaluator_func(
                SimpleNamespace(outputs=result),
                SimpleNamespace(inputs={"complaint": complaint_text}, outputs=result),
            )
            eval_results[eval_name] = eval_output
            print(f"   {eval_name}: {eval_output.get('score', 'N/A')}")
        except Exception as e:
            eval_results[eval_name] = {"score": 0, "reasoning": str(e)}
            print(f"   {eval_name} failed: {e}")

    is_safe, guardrail_reason, guardrail_details = apply_guardrails(eval_results)

    if not is_safe:
        print(f"GUARDRAIL TRIGGERED: {guardrail_reason}")
        return {
            "resolution": {
                "resolution_type": "escalate",
                "refund_amount": 0,
                "credit_amount": 0,
                "action_needed": guardrail_reason,
                "confidence": 0.0,
            },
            "final_response": (
                "Thank you for reaching out. Your issue has been flagged for immediate "
                "review by our senior support team. We will contact you within the next 2 hours."
            ),
            "actions_taken": [{
                "action": "guardrail_escalation",
                "reason": guardrail_reason,
                "details": guardrail_details,
            }],
            "eval_results": eval_results,
        }

    print("All guardrails passed")
    return {"eval_results": eval_results}
