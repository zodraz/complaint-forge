import json
import logging
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from llm_factory import get_chat_llm
from otel import add_event, function_trace, record_metric, set_attribute
from prompts.system_prompts import RESOLVER_PROMPT

logger = logging.getLogger(__name__)
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


@function_trace()
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

    resolution_type = result.get("resolution_type", "")
    refund_amount = result.get("refund_amount", 0.0)
    credit_amount = result.get("credit_amount", 0.0)
    confidence = result.get("confidence", 0.0)
    action_needed = result.get("action_needed", "")

    set_attribute("resolution.type", resolution_type)
    set_attribute("resolution.refund_amount", refund_amount)
    set_attribute("resolution.credit_amount", credit_amount)
    set_attribute("resolution.confidence", confidence)

    record_metric("resolution.refund_amount", refund_amount)
    record_metric("resolution.credit_amount", credit_amount)
    record_metric("resolution.confidence", confidence)

    add_event("ResolutionResult", {
        "resolution_type": resolution_type,
        "refund_amount": refund_amount,
        "credit_amount": credit_amount,
        "confidence": confidence,
        "action_needed": action_needed[:255],
    })

    logger.info("Resolution determined", extra={"resolution_type": result.get("resolution_type", ""), "refund_amount": result.get("refund_amount", 0.0), "credit_amount": result.get("credit_amount", 0.0), "confidence": result.get("confidence", 0.0)})

    if result.get("confidence", 1.0) < 0.85:
        logger.warning("Low confidence resolution, may escalate", extra={"confidence": result.get("confidence", 0.0), "resolution_type": result.get("resolution_type", "")})

    if result.get("resolution_type") == "escalate":
        logger.warning("Resolver recommends escalation", extra={"action_needed": str(result.get("action_needed", ""))[:255]})

    return {"resolution": result}
