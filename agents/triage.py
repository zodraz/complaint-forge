from langchain_core.prompts import ChatPromptTemplate

from llm_factory import get_chat_llm
from prompts.system_prompts import TRIAGE_PROMPT


llm = get_chat_llm(temperature=0)


def triage(state: dict) -> dict:
    prompt = ChatPromptTemplate.from_template(TRIAGE_PROMPT)
    chain = prompt | llm.with_structured_output(
        schema={
            "type": "object",
            "properties": {
                "is_complaint": {"type": "boolean"},
                "confidence": {"type": "number"},
                "reason": {"type": "string"},
                "customer_email": {"type": ["string", "null"]},
                "order_id": {"type": ["string", "null"]},
            },
            "required": [
                "is_complaint",
                "confidence",
                "reason",
                "customer_email",
                "order_id",
            ],
        }
    )
    result = chain.invoke({"input": state["complaint"]})

    return {
        "triage": result,
        "customer_email": result.get("customer_email"),
        "order_id": result.get("order_id"),
    }
