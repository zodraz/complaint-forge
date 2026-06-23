import logging

from langchain_core.prompts import ChatPromptTemplate

from llm_factory import get_chat_llm
from otel import function_trace, record_metric, set_attribute
from prompts.system_prompts import RESPONDER_PROMPT

logger = logging.getLogger(__name__)
llm = get_chat_llm(temperature=0.3)  # slight creativity for tone


@function_trace()
def responder(state: dict) -> dict:
    """
    Writes the final empathetic response to the customer
    """
    prompt = ChatPromptTemplate.from_template(RESPONDER_PROMPT)

    chain = prompt | llm

    response_text = chain.invoke({
        "complaint": state["complaint"],
        "history": state.get("customer_history", {}),
        "resolution": state.get("resolution", {}),
        "analysis": state.get("analysis", {})
    }).content

    set_attribute("responder.response_length", len(response_text))
    record_metric("responder.response_length", len(response_text))
    logger.info("Customer response drafted", extra={"response_length": len(response_text)})

    return {
        "response_draft": response_text,
        "final_response": response_text
    }
