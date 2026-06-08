from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated, Any
import operator
from dotenv import load_dotenv
import os

load_dotenv()

# ========================== LANGCHAIN / LANGSMITH SETUP ==========================
_tracing_enabled = (
    os.getenv("LANGSMITH_TRACING")
    or os.getenv("LANGCHAIN_TRACING_V2")
    or "false"
).lower() in {"1", "true", "yes", "on"}
os.environ["LANGCHAIN_TRACING_V2"] = "true" if _tracing_enabled else "false"
os.environ["LANGSMITH_TRACING"] = "true" if _tracing_enabled else "false"
os.environ["LANGCHAIN_PROJECT"] = (
    os.getenv("LANGCHAIN_PROJECT")
    or os.getenv("LANGSMITH_PROJECT")
    or "complaintforge-complaint-handler"
)

# Optional: Use persistent checkpointing (recommended for production)
checkpointer = MemorySaver()

# ========================== IMPORT AGENTS ==========================
from agents.triage import triage
from nodes.customer_context import customer_context
from nodes.policy import policy
from nodes.guardrails import guardrails
from nodes.specialist_review import specialist_review
from nodes.human_review import human_review
from nodes.ignored import ignored
from agents.analyzer import analyzer
from agents.resolver import resolver
from agents.responder import responder
from agents.action_agent import action_agent

class ComplaintState(TypedDict):
    complaint: str
    triage: dict
    customer_email: str | None
    order_id: str | None
    customer_history: dict
    customer_context_result: dict
    analysis: dict
    resolution: dict
    policy_result: dict
    response_draft: str
    actions_taken: Annotated[list, operator.add]
    eval_results: dict
    specialist_review: dict
    human_review: dict
    final_response: str
    messages: Annotated[list, operator.add]

# ========================== NODES ==========================
def triage_node(state: ComplaintState):
    return triage(state)

def customer_context_node(state: ComplaintState):
    return customer_context(state)

def analyzer_node(state: ComplaintState):
    return analyzer(state)

def resolver_node(state: ComplaintState):
    return resolver(state)

def policy_node(state: ComplaintState):
    return policy(dict(state))

def responder_node(state: ComplaintState):
    return responder(state)

async def guardrails_node(state: ComplaintState):
    return await guardrails(dict(state))

def action_node(state: ComplaintState):
    return action_agent(state)

def specialist_review_node(state: ComplaintState):
    return specialist_review(dict(state))

def human_review_node(state: ComplaintState):
    return human_review(state)

def route_after_resolver(state: ComplaintState):
    if state.get("resolution", {}).get("resolution_type") == "escalate":
        return "specialist_review"
    return "responder"

def route_after_guardrails(state: ComplaintState):
    if state.get("resolution", {}).get("resolution_type") == "escalate":
        return "specialist_review"
    return "action"

def route_after_triage(state: ComplaintState):
    triage_result = state.get("triage", {})
    if triage_result.get("is_complaint") is True:
        return "customer_context"
    return "ignored"

def ignored_node(state: ComplaintState):
    return ignored(state)

# ========================== BUILD GRAPH ==========================
workflow = StateGraph(ComplaintState)

workflow.add_node("triage", triage_node)
workflow.add_node("customer_context", customer_context_node)
workflow.add_node("analyzer", analyzer_node)
workflow.add_node("resolver", resolver_node)
workflow.add_node("policy", policy_node)
workflow.add_node("responder", responder_node)
workflow.add_node("guardrails", guardrails_node)
workflow.add_node("action", action_node)
workflow.add_node("specialist_review", specialist_review_node)
workflow.add_node("human_review", human_review_node)
workflow.add_node("ignored", ignored_node)

workflow.set_entry_point("triage")

workflow.add_conditional_edges(
    "triage",
    route_after_triage,
    {
        "customer_context": "customer_context",
        "ignored": "ignored",
    },
)
workflow.add_edge("customer_context", "analyzer")
workflow.add_edge("analyzer", "resolver")
workflow.add_edge("resolver", "policy")

workflow.add_conditional_edges(
    "policy",
    route_after_resolver,
    {
        "specialist_review": "specialist_review",
        "responder": "responder",
    },
)

workflow.add_edge("responder", "guardrails")
workflow.add_conditional_edges(
    "guardrails",
    route_after_guardrails,
    {
        "specialist_review": "specialist_review",
        "action": "action",
    },
)

workflow.add_edge("action", END)
workflow.add_edge("specialist_review", "human_review")
workflow.add_edge("human_review", END)
workflow.add_edge("ignored", END)

# Compile with tracing + checkpointing
app = workflow.compile(checkpointer=checkpointer)

print(f"LangGraph compiled with LangSmith tracing {'enabled' if _tracing_enabled else 'disabled'}")
