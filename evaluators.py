from langsmith.schemas import Example, Run
from typing import Dict, Any
import json
from llm_factory import get_chat_llm

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
    llm = get_chat_llm(temperature=0)
    
    result = llm.invoke(prompt).content
    try:
        return json.loads(result)
    except:
        return {"score": 7.0, "reasoning": "Could not parse evaluator output"}


def evaluate_resolution_appropriateness(run: Run, example: Example) -> Dict[str, Any]:
    """Evaluate if the chosen resolution matches the complaint severity"""
    analysis = run.outputs.get("analysis", {})
    resolution = run.outputs.get("resolution", {})
    
    prompt = f"""Rate how appropriate the resolution is for this complaint (1-10).

Complaint Analysis: {analysis}
Chosen Resolution: {resolution}

Return JSON:
{{"score": 9, "reasoning": "..."}}"""

    llm = get_chat_llm(temperature=0)
    result = llm.invoke(prompt).content
    try:
        return json.loads(result)
    except:
        return {"score": 7, "reasoning": "Parsing error"}


# ====================== EVALUATOR REGISTRATION ======================

CUSTOM_EVALUATORS = {
    "empathy_score": evaluate_response_empathy,
    "resolution_appropriateness": evaluate_resolution_appropriateness,
}


def apply_guardrails(eval_results: Dict[str, Dict[str, Any]]) -> tuple[bool, str, Dict[str, Any]]:
    empathy = eval_results.get("empathy_score", {})
    resolution = eval_results.get("resolution_appropriateness", {})

    failures = []

    if empathy.get("score", 0) < 6:
        failures.append("Response empathy score below threshold")

    if resolution.get("score", 0) < 6:
        failures.append("Resolution appropriateness score below threshold")

    if failures:
        return False, "; ".join(failures), eval_results

    return True, "All evaluator guardrails passed", eval_results
