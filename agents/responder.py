from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from prompts.system_prompts import RESPONDER_PROMPT

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)  # slight creativity for tone

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
    
    return {
        "response_draft": response_text,
        "final_response": response_text
    }