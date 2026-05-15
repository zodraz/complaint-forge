from langsmith.schemas import Example, Run
from typing import Dict, Any
import json

# ====================== CUSTOM EVALUATORS ======================

def evaluate_response_empathy(run: Run, example: Example) -> Dict[str, Any]:
    """Evaluate how empathetic and professional the response is"""
    response = run.outputs.get("final_response", "")
    
    prompt = f"""Rate the following customer service response on a scale of 1-10 for EMPATHY and TONE.
    
Response:
{response}

Criteria:
- Shows genuine understanding and apology
- Uses warm, human language
- Avoids being defensive or robotic
- Builds trust

Return only a JSON:
{{"score": 8.5, "reasoning": "short explanation"}}"""

    # You can use the same LLM used in your agents
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    result = llm.invoke(prompt).content
    try:
        return json.loads(result)
    except:
        return {"score": 7.0, "reasoning": "Could not parse evaluator output"}


def evaluate_policy_compliance(run: Run, example: Example) -> Dict[str, Any]:
    """Check if resolution follows company policy"""
    resolution = run.outputs.get("resolution", {})
    resolution_type = resolution.get("resolution_type")
    refund_amount = resolution.get("refund_amount", 0)
    
    prompt = f"""Does this resolution follow the STRICT company policy?

Resolution: {resolution_type} | Refund: ${refund_amount}

Policy:
- First-time < $150 -> max 50% refund
- Repeat or >$150 -> full refund + credit allowed
- Never refund digital/custom orders

Return JSON:
{{"compliant": true, "reasoning": "explanation", "score": 10}}"""

    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    result = llm.invoke(prompt).content
    
    try:
        return json.loads(result)
    except:
        return {"compliant": False, "reasoning": "Evaluation failed", "score": 5}


def evaluate_resolution_appropriateness(run: Run, example: Example) -> Dict[str, Any]:
    """Evaluate if the chosen resolution matches the complaint severity"""
    analysis = run.outputs.get("analysis", {})
    resolution = run.outputs.get("resolution", {})
    
    prompt = f"""Rate how appropriate the resolution is for this complaint (1-10).

Complaint Analysis: {analysis}
Chosen Resolution: {resolution}

Return JSON:
{{"score": 9, "reasoning": "..."}}"""

    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    result = llm.invoke(prompt).content
    try:
        return json.loads(result)
    except:
        return {"score": 7, "reasoning": "Parsing error"}


# ====================== EVALUATOR REGISTRATION ======================

CUSTOM_EVALUATORS = {
    "empathy_score": evaluate_response_empathy,
    "policy_compliance": evaluate_policy_compliance,
    "resolution_appropriateness": evaluate_resolution_appropriateness,
}


def apply_guardrails(eval_results: Dict[str, Dict[str, Any]]) -> tuple[bool, str, Dict[str, Any]]:
    empathy = eval_results.get("empathy_score", {})
    policy = eval_results.get("policy_compliance", {})
    resolution = eval_results.get("resolution_appropriateness", {})

    failures = []

    if empathy.get("score", 0) < 6:
        failures.append("Response empathy score below threshold")

    if not policy.get("compliant", False) or policy.get("score", 0) < 7:
        failures.append("Resolution failed policy compliance")

    if resolution.get("score", 0) < 6:
        failures.append("Resolution appropriateness score below threshold")

    if failures:
        return False, "; ".join(failures), eval_results

    return True, "All evaluator guardrails passed", eval_results
