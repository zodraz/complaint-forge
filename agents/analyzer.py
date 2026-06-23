import json
import logging
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from llm_factory import get_chat_llm
from otel import add_event, function_trace, record_metric, set_attribute
from prompts.system_prompts import ANALYZER_PROMPT

logger = logging.getLogger(__name__)
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


SENTIMENT_LEVELS = {"positive": 1, "neutral": 2, "negative": 3, "very_negative": 4}
URGENCY_LEVELS = {"low": 1, "medium": 2, "high": 3}


@function_trace()
def analyzer(state: dict) -> dict:
    prompt = ChatPromptTemplate.from_template(ANALYZER_PROMPT)
    chain = prompt | llm.with_structured_output(AnalysisResult)
    result = chain.invoke({
        "complaint": state["complaint"],
        "history": json.dumps(state.get("customer_history", {}))
    }).model_dump()

    set_attribute("analysis.issue_type", result["issue_type"])
    set_attribute("analysis.sentiment", result["sentiment"])
    set_attribute("analysis.urgency", result["urgency"])
    set_attribute("analysis.repeat_complaint", result["repeat_complaint"])

    record_metric("analysis.sentiment_level", SENTIMENT_LEVELS.get(result["sentiment"], 0))
    record_metric("analysis.urgency_level", URGENCY_LEVELS.get(result["urgency"], 0))

    add_event("AnalysisResult", {
        "issue_type": result["issue_type"],
        "sentiment": result["sentiment"],
        "urgency": result["urgency"],
        "repeat_complaint": result["repeat_complaint"],
    })

    logger.info("Analysis completed", extra={"issue_type": result.get("issue_type", ""), "sentiment": result.get("sentiment", ""), "urgency": result.get("urgency", ""), "repeat_complaint": result.get("repeat_complaint", False)})

    if result.get("urgency") == "high":
        logger.warning("High urgency complaint detected", extra={"issue_type": result.get("issue_type", ""), "sentiment": result.get("sentiment", "")})

    if result.get("sentiment") == "very_negative":
        logger.warning("Very negative customer sentiment detected", extra={"issue_type": result.get("issue_type", ""), "urgency": result.get("urgency", "")})

    return {"analysis": result}
