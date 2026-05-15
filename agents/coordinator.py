from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from tools.hubspot_tool import get_customer_history
from prompts.system_prompts import COORDINATOR_PROMPT
import json

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def coordinator(state: dict) -> dict:
    prompt = ChatPromptTemplate.from_template(COORDINATOR_PROMPT)
    chain = prompt | llm.with_structured_output(schema=dict)  # or use JSON mode
    result = chain.invoke({"input": state["complaint"]})
    
    email = result.get("customer_email")
    history = get_customer_history(email) if email else {}
    
    return {
        "customer_email": email,
        "customer_history": history,
        "coordinator_decision": result
    }