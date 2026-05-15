# guardrails.py
from evaluators import CUSTOM_EVALUATORS, apply_guardrails
from typing import Dict, Any
from types import SimpleNamespace

async def run_evaluators_and_guardrails(result: Dict, complaint_text: str) -> Dict:
    """
    Runs all LangSmith evaluators and applies guardrails.
    Returns the (possibly modified) result.
    """
    print("Running LangSmith evaluators...")
    eval_results = {}

    for eval_name, evaluator_func in CUSTOM_EVALUATORS.items():
        try:
            eval_output = evaluator_func(
                SimpleNamespace(outputs=result),
                SimpleNamespace(inputs={"complaint": complaint_text}, outputs=result)
            )
            eval_results[eval_name] = eval_output
            print(f"   {eval_name}: {eval_output.get('score', 'N/A')}")
        except Exception as e:
            print(f"   {eval_name} failed: {e}")
            eval_results[eval_name] = {"score": 0, "reasoning": str(e)}

    # === APPLY GUARDRAILS ===
    is_safe, guardrail_reason, guardrail_details = apply_guardrails(eval_results)

    if not is_safe:
        print(f"GUARDRAIL TRIGGERED: {guardrail_reason}")
        
        result["resolution"] = {
            "resolution_type": "escalate",
            "refund_amount": 0,
            "credit_amount": 0,
            "action_needed": guardrail_reason,
            "confidence": 0.0
        }
        result["final_response"] = (
            "Thank you for reaching out. Your issue has been flagged for immediate "
            "review by our senior support team. We will contact you within the next 2 hours."
        )
        result.setdefault("actions_taken", []).append({
            "action": "guardrail_escalation",
            "reason": guardrail_reason,
            "details": guardrail_details
        })
    else:
        print("All guardrails passed")

    return result
