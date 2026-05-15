from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from prompts.system_prompts import ANALYZER_PROMPT
import json

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def analyzer(state: dict) -> dict:
    prompt = ChatPromptTemplate.from_template(ANALYZER_PROMPT)
    chain = prompt | llm.with_structured_output(dict)
    result = chain.invoke({
        "complaint": state["complaint"],
        "history": json.dumps(state.get("customer_history", {}))
    })
    return {"analysis": result}
