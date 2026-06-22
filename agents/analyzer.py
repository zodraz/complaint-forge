import newrelic.agent
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


SENTIMENT_LEVELS = {"positive": 1, "neutral": 2, "negative": 3, "very_negative": 4}
URGENCY_LEVELS = {"low": 1, "medium": 2, "high": 3}


@newrelic.agent.function_trace()
def analyzer(state: dict) -> dict:
    prompt = ChatPromptTemplate.from_template(ANALYZER_PROMPT)
    chain = prompt | llm.with_structured_output(AnalysisResult)
    result = chain.invoke({
        "complaint": state["complaint"],
        "history": json.dumps(state.get("customer_history", {}))
    }).model_dump()

    newrelic.agent.add_custom_attribute("analysis.issue_type", result["issue_type"])
    newrelic.agent.add_custom_attribute("analysis.sentiment", result["sentiment"])
    newrelic.agent.add_custom_attribute("analysis.urgency", result["urgency"])
    newrelic.agent.add_custom_attribute("analysis.repeat_complaint", result["repeat_complaint"])

    newrelic.agent.record_custom_metric(
        "Custom/Analysis/SentimentLevel",
        SENTIMENT_LEVELS.get(result["sentiment"], 0)
    )
    newrelic.agent.record_custom_metric(
        "Custom/Analysis/UrgencyLevel",
        URGENCY_LEVELS.get(result["urgency"], 0)
    )

    newrelic.agent.record_custom_event("AnalysisResult", {
        "issue_type": result["issue_type"],
        "sentiment": result["sentiment"],
        "urgency": result["urgency"],
        "repeat_complaint": result["repeat_complaint"],
    })

    newrelic.agent.record_log_event("Analysis completed", level="INFO", attributes={"issue_type": result.get("issue_type",""), "sentiment": result.get("sentiment",""), "urgency": result.get("urgency",""), "repeat_complaint": result.get("repeat_complaint", False)})

    if result.get("urgency") == "high":
        newrelic.agent.record_log_event("High urgency complaint detected", level="WARNING", attributes={"issue_type": result.get("issue_type",""), "sentiment": result.get("sentiment","")})

    if result.get("sentiment") == "very_negative":
        newrelic.agent.record_log_event("Very negative customer sentiment detected", level="WARNING", attributes={"issue_type": result.get("issue_type",""), "urgency": result.get("urgency","")})

    return {"analysis": result}
