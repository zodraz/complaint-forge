import newrelic.agent
from langchain_core.prompts import ChatPromptTemplate
from prompts.system_prompts import RESPONDER_PROMPT
from llm_factory import get_chat_llm

llm = get_chat_llm(temperature=0.3)  # slight creativity for tone

@newrelic.agent.function_trace()
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

    newrelic.agent.add_custom_attribute("responder.response_length", len(response_text))
    newrelic.agent.record_custom_metric("Custom/Responder/ResponseLength", len(response_text))
    newrelic.agent.record_log_event("Customer response drafted", level="INFO", attributes={"response_length": len(response_text)})

    return {
        "response_draft": response_text,
        "final_response": response_text
    }
