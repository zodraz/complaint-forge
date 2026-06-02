from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from llm_factory import get_chat_llm
from prompts.system_prompts import TRIAGE_PROMPT


llm = get_chat_llm(temperature=0)


class TriageResult(BaseModel):
    is_complaint: bool = Field(description="Whether the ticket is a customer complaint.")
    confidence: float = Field(description="Classification confidence from 0.0 to 1.0.")
    reason: str = Field(description="Short reason for the triage decision.")
    customer_email: str | None = Field(default=None, description="Customer email if found.")
    order_id: str | None = Field(default=None, description="Order id if found.")


def triage(state: dict) -> dict:
    prompt = ChatPromptTemplate.from_template(TRIAGE_PROMPT)
    chain = prompt | llm.with_structured_output(TriageResult)
    result = chain.invoke({"input": state["complaint"]}).model_dump()

    return {
        "triage": result,
        "customer_email": result.get("customer_email"),
        "order_id": result.get("order_id"),
    }
