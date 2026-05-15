from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated, Any
import operator
from dotenv import load_dotenv
import os

load_dotenv()

# ========================== LANGCHAIN / LANGSMITH SETUP ==========================
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "complaintforge-complaint-handler")

# Optional: Use persistent checkpointing (recommended for production)
checkpointer = MemorySaver()

# ========================== IMPORT AGENTS ==========================
from agents.coordinator import coordinator
from agents.analyzer import analyzer
from agents.resolver import resolver
from agents.responder import responder
from agents.action_agent import action_agent

class ComplaintState(TypedDict):
    complaint: str
    customer_email: str | None
    customer_history: dict
    analysis: dict
    resolution: dict
    response_draft: str
    actions_taken: list
    final_response: str
    messages: Annotated[list, operator.add]

# ========================== NODES ==========================
def coordinator_node(state: ComplaintState):
    return coordinator(state)

def analyzer_node(state: ComplaintState):
    return analyzer(state)

def resolver_node(state: ComplaintState):
    return resolver(state)

def responder_node(state: ComplaintState):
    return responder(state)

def action_node(state: ComplaintState):
    return action_agent(state)

# ========================== BUILD GRAPH ==========================
workflow = StateGraph(ComplaintState)

workflow.add_node("coordinator", coordinator_node)
workflow.add_node("analyzer", analyzer_node)
workflow.add_node("resolver", resolver_node)
workflow.add_node("responder", responder_node)
workflow.add_node("action", action_node)

workflow.set_entry_point("coordinator")

# Analysis must complete before resolution, because the resolver consumes the
# analyzer output when applying policy.
workflow.add_edge("coordinator", "analyzer")
workflow.add_edge("analyzer", "resolver")

workflow.add_edge("responder", END)
workflow.add_edge("action", END)
workflow.add_edge("resolver", "responder")
workflow.add_edge("resolver", "action")

# Compile with tracing + checkpointing
app = workflow.compile(checkpointer=checkpointer)

print("LangGraph compiled with LangSmith tracing enabled")
