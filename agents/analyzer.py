from langchain_core.prompts import ChatPromptTemplate
from prompts.system_prompts import ANALYZER_PROMPT
from llm_factory import get_chat_llm
from pydantic import BaseModel, Field
from typing import Literal
import json

llm = get_chat_llm(temperature=0)


class AnalysisResult(BaseModel):
    issue_type: Literal["shipping", "billing", "product", "service", "other"] = Field(
        description="Primary complaint category."
    )
    sentiment: Literal["positive", "neutral", "negative", "very_negative"] = Field(
        description="Customer sentiment."
    )
    urgency: Literal["low", "medium", "high"] = Field(description="Urgency level.")
    repeat_complaint: bool = Field(description="Whether history indicates a repeat complaint.")
    key_details: str = Field(description="Short summary of the key complaint facts.")


def analyzer(state: dict) -> dict:
    prompt = ChatPromptTemplate.from_template(ANALYZER_PROMPT)
    chain = prompt | llm.with_structured_output(AnalysisResult)
    result = chain.invoke({
        "complaint": state["complaint"],
        "history": json.dumps(state.get("customer_history", {}))
    }).model_dump()
    return {"analysis": result}
