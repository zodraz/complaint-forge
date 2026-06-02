from langchain_core.prompts import ChatPromptTemplate
from prompts.system_prompts import RESOLVER_PROMPT
from llm_factory import get_chat_llm
from pydantic import BaseModel, Field
from typing import Literal
import json

llm = get_chat_llm(temperature=0)


class ResolutionResult(BaseModel):
    resolution_type: Literal[
        "full_refund",
        "partial_refund",
        "credit",
        "replacement",
        "apology",
        "escalate",
    ] = Field(description="The selected resolution category.")
    refund_amount: float = Field(description="Refund amount in account currency.")
    credit_amount: float = Field(description="Customer credit amount in account currency.")
    action_needed: str = Field(description="Operational action or escalation reason.")
    confidence: float = Field(description="Resolution confidence from 0.0 to 1.0.")


def resolver(state: dict) -> dict:
    """
    Decides the best resolution based on policy + customer history + analysis
    """
    prompt = ChatPromptTemplate.from_template(RESOLVER_PROMPT)
    
    chain = prompt | llm.with_structured_output(ResolutionResult)
    
    result = chain.invoke({
        "history": json.dumps(state.get("customer_history", {}), indent=2),
        "analysis": json.dumps(state.get("analysis", {}), indent=2)
    }).model_dump()
    
    return {"resolution": result}
