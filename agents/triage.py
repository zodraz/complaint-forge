import logging

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from llm_factory import get_chat_llm
from otel import add_event, function_trace, notice_error, record_metric, set_attribute
from prompts.system_prompts import TRIAGE_PROMPT

logger = logging.getLogger(__name__)
llm = get_chat_llm(temperature=0, request_timeout=20)


class TriageResult(BaseModel):
    is_complaint: bool = Field(description="Whether the ticket is a customer complaint.")
    confidence: float = Field(description="Classification confidence from 0.0 to 1.0.")
    reason: str = Field(description="Short reason for the triage decision.")
    customer_email: str | None = Field(default=None, description="Customer email if found.")
    order_id: str | None = Field(default=None, description="Order id if found.")


@function_trace()
def triage(state: dict) -> dict:
    prompt = ChatPromptTemplate.from_template(TRIAGE_PROMPT)
    chain = prompt | llm.with_structured_output(TriageResult)

    try:
        result = chain.invoke({"input": state["complaint"]}).model_dump()
    except Exception as exc:
        notice_error()
        logger.warning("Triage LLM unavailable, using fallback", extra={"error": str(exc)})
        result = {
            "is_complaint": False,
            "confidence": 0.0,
            "reason": f"LLM triage unavailable: {exc}",
            "customer_email": None,
            "order_id": None,
        }

    set_attribute("triage.is_complaint", result["is_complaint"])
    set_attribute("triage.confidence", result["confidence"])
    record_metric("triage.confidence", result["confidence"])
    record_metric("triage.is_complaint", 1 if result["is_complaint"] else 0)
    add_event("TriageResult", {
        "is_complaint": result["is_complaint"],
        "confidence": result["confidence"],
        "reason": result["reason"][:255],
        "has_email": result["customer_email"] is not None,
        "has_order_id": result["order_id"] is not None,
    })

    if result.get("is_complaint"):
        logger.info("Ticket classified as complaint", extra={"confidence": result.get("confidence", 0.0), "order_id": result.get("order_id")})
    else:
        logger.info("Ticket classified as non-complaint, will be ignored", extra={"confidence": result.get("confidence", 0.0), "reason": str(result.get("reason", ""))[:255]})

    return {
        "triage": result,
        "customer_email": result.get("customer_email"),
        "order_id": result.get("order_id"),
    }
