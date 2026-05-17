from langchain_core.prompts import ChatPromptTemplate
from prompts.system_prompts import ANALYZER_PROMPT
from llm_factory import get_chat_llm
import json

llm = get_chat_llm(temperature=0)

def analyzer(state: dict) -> dict:
    prompt = ChatPromptTemplate.from_template(ANALYZER_PROMPT)
    chain = prompt | llm.with_structured_output(dict)
    result = chain.invoke({
        "complaint": state["complaint"],
        "history": json.dumps(state.get("customer_history", {}))
    })
    return {"analysis": result}
