from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from prompts.system_prompts import RESOLVER_PROMPT
import json

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def resolver(state: dict) -> dict:
    """
    Decides the best resolution based on policy + customer history + analysis
    """
    prompt = ChatPromptTemplate.from_template(RESOLVER_PROMPT)
    
    chain = prompt | llm.with_structured_output(
        schema={
            "type": "object",
            "properties": {
                "resolution_type": {"type": "string", "enum": ["full_refund", "partial_refund", "credit", "replacement", "apology", "escalate"]},
                "refund_amount": {"type": "number"},
                "credit_amount": {"type": "number"},
                "action_needed": {"type": "string"},
                "confidence": {"type": "number"}
            },
            "required": ["resolution_type", "refund_amount", "credit_amount", "action_needed", "confidence"]
        }
    )
    
    result = chain.invoke({
        "history": json.dumps(state.get("customer_history", {}), indent=2),
        "analysis": json.dumps(state.get("analysis", {}), indent=2)
    })
    
    # Safety guardrail
    if result.get("confidence", 0) < 0.85 or result.get("refund_amount", 0) > 500:
        result["resolution_type"] = "escalate"
        result["action_needed"] = "High value or low confidence - escalate to human team"
    
    return {"resolution": result}