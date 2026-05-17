from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uuid
import os
from dotenv import load_dotenv
from langsmith import traceable
from langgraph.types import Command

load_dotenv()

# ========================== IMPORTS ==========================
from graph import app as complaint_graph

review_runs: dict[str, dict] = {}

app = FastAPI(
    title="ComplaintForge - Autonomous Complaint Handler",
    description="LangGraph + LangSmith powered autonomous customer complaint system",
    version="1.0.0"
)


class HumanReviewResume(BaseModel):
    final_response: str | None = None
    approved: bool | None = None
    notes: str | None = None
    resolution: dict | None = None


def _graph_config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def _serialize_interrupt(interrupt_obj) -> dict:
    return {
        "id": getattr(interrupt_obj, "id", None),
        "value": getattr(interrupt_obj, "value", interrupt_obj),
    }


def _serialize_interrupts(result: dict) -> list[dict]:
    return [
        _serialize_interrupt(interrupt_obj)
        for interrupt_obj in result.get("__interrupt__", [])
    ]


def _pending_review_state(thread_id: str) -> dict:
    snapshot = complaint_graph.get_state(_graph_config(thread_id))
    interrupts = [
        _serialize_interrupt(interrupt_obj)
        for interrupt_obj in getattr(snapshot, "interrupts", ())
    ]
    return {
        "thread_id": thread_id,
        "status": "pending_review" if interrupts else review_runs.get(thread_id, {}).get("status", "unknown"),
        "interrupts": interrupts,
        "state": getattr(snapshot, "values", {}),
        "next": list(getattr(snapshot, "next", ())),
    }


def _record_run(thread_id: str, **updates) -> None:
    current = review_runs.setdefault(thread_id, {"thread_id": thread_id})
    current.update(updates)


# ========================== BACKGROUND PROCESSOR ==========================
@traceable(run_type="chain", name="Autonomous Complaint Handler")
async def process_complaint_async(
    complaint_text: str,
    ticket_id: int,
    email: str,
    thread_id: str | None = None,
):
    """Clean version: Graph execution + Post-processing separated"""
    print(f"Processing Zendesk Ticket #{ticket_id} from {email}")
    
    thread_id = thread_id or str(uuid.uuid4())
    config = _graph_config(thread_id)
    _record_run(
        thread_id,
        status="running",
        ticket_id=ticket_id,
        requester_email=email,
    )
    
    initial_state = {
        "complaint": f"Ticket #{ticket_id}\n\n{complaint_text}",
        "messages": []
    }
    
    try:
        # 1. Run the main LangGraph workflow
        result = await complaint_graph.ainvoke(initial_state, config=config)
        if result.get("__interrupt__"):
            interrupts = _serialize_interrupts(result)
            _record_run(
                thread_id,
                status="pending_review",
                interrupts=interrupts,
            )
            print(f"Ticket #{ticket_id} paused for human review")
            return {
                "status": "pending_review",
                "thread_id": thread_id,
                "interrupts": interrupts,
            }
        
        _record_run(thread_id, status="completed", result=result)
        
        print(f"Ticket #{ticket_id} processed successfully")
        return {"status": "completed", "thread_id": thread_id, "result": result}

    except Exception as e:
        _record_run(thread_id, status="error", error=str(e))
        print(f"Error processing ticket #{ticket_id}: {e}")
        raise


# ========================== ZENDESK WEBHOOK ==========================
@app.post("/webhook/zendesk/complaint")
async def zendesk_complaint_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    try:
        payload = await request.json()
        ticket = payload.get("ticket", payload)

        ticket_id = ticket.get("id")
        subject = ticket.get("subject", "")
        description = ticket.get("description") or ticket.get("comment", {}).get("body", "")
        requester_email = (
            ticket.get("requester", {}).get("email") or
            ticket.get("via", {}).get("source", {}).get("from", {}).get("address")
        )

        if not description or not requester_email:
            raise HTTPException(status_code=400, detail="Missing description or email")

        complaint_text = f"Subject: {subject}\n\n{description}"
        thread_id = str(uuid.uuid4())

        background_tasks.add_task(
            process_complaint_async,
            complaint_text=complaint_text,
            ticket_id=ticket_id or 0,
            email=requester_email,
            thread_id=thread_id,
        )

        return {
            "status": "accepted",
            "ticket_id": ticket_id,
            "thread_id": thread_id,
            "message": "Complaint received and being processed autonomously"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================== TEST ENDPOINT ==========================
@app.post("/test/complaint")
async def test_complaint(payload: dict):
    complaint_text = payload.get("complaint", "")
    email = payload.get("email", "test@example.com")
    
    if not complaint_text:
        raise HTTPException(status_code=400, detail="complaint text is required")
    
    result = await process_complaint_async(
        complaint_text=complaint_text,
        ticket_id=9999,
        email=email
    )
    
    return result


# ========================== HUMAN REVIEW ==========================
@app.get("/review")
async def list_reviews():
    return {
        "reviews": [
            run for run in review_runs.values()
            if run.get("status") == "pending_review"
        ]
    }


@app.get("/review/{thread_id}")
async def get_review(thread_id: str):
    if thread_id not in review_runs:
        raise HTTPException(status_code=404, detail="Unknown thread_id")
    return _pending_review_state(thread_id)


@app.post("/review/{thread_id}/resume")
async def resume_review(thread_id: str, review: HumanReviewResume):
    if thread_id not in review_runs:
        raise HTTPException(status_code=404, detail="Unknown thread_id")

    payload = review.model_dump(exclude_none=True)
    if not payload:
        raise HTTPException(status_code=400, detail="Resume payload cannot be empty")

    try:
        result = await complaint_graph.ainvoke(
            Command(resume=payload),
            config=_graph_config(thread_id),
        )
    except Exception as e:
        _record_run(thread_id, status="error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

    if result.get("__interrupt__"):
        interrupts = _serialize_interrupts(result)
        _record_run(thread_id, status="pending_review", interrupts=interrupts)
        return {
            "status": "pending_review",
            "thread_id": thread_id,
            "interrupts": interrupts,
        }

    _record_run(thread_id, status="completed", result=result)
    return {
        "status": "completed",
        "thread_id": thread_id,
        "result": result,
    }


# ========================== HEALTH CHECK ==========================
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "ComplaintForge Complaint Handler"
    }


@app.on_event("startup")
async def startup_event():
    print("ComplaintForge Autonomous Complaint Handler started")
    print("Webhook: /webhook/zendesk/complaint")
    print("Test: /test/complaint")
