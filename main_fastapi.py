from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uuid
import os
from dotenv import load_dotenv
from langsmith import traceable

load_dotenv()

# ========================== IMPORTS ==========================
from graph import app as complaint_graph
from guardrails import run_evaluators_and_guardrails

app = FastAPI(
    title="ComplaintForge - Autonomous Complaint Handler",
    description="LangGraph + LangSmith powered autonomous customer complaint system",
    version="1.0.0"
)

# ========================== BACKGROUND PROCESSOR ==========================
@traceable(run_type="chain", name="Autonomous Complaint Handler")
async def process_complaint_async(complaint_text: str, ticket_id: int, email: str):
    """Clean version: Graph execution + Post-processing separated"""
    print(f"Processing Zendesk Ticket #{ticket_id} from {email}")
    
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    initial_state = {
        "complaint": f"Ticket #{ticket_id}\n\n{complaint_text}",
        "messages": []
    }
    
    try:
        # 1. Run the main LangGraph workflow
        result = await complaint_graph.ainvoke(initial_state, config=config)
        
        # 2. Run evaluators + guardrails (clean separation)
        result = await run_evaluators_and_guardrails(result, complaint_text)
        
        print(f"Ticket #{ticket_id} processed successfully")
        return result

    except Exception as e:
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

        complaint_keywords = ["complaint", "issue", "problem", "not working", "late", "refund", "angry", "disappointed", "terrible"]
        text_to_check = (subject + " " + description).lower()
        is_complaint = any(kw in text_to_check for kw in complaint_keywords)

        if not is_complaint:
            return {"status": "ignored", "reason": "not detected as complaint"}

        complaint_text = f"Subject: {subject}\n\n{description}"

        background_tasks.add_task(
            process_complaint_async,
            complaint_text=complaint_text,
            ticket_id=ticket_id or 0,
            email=requester_email
        )

        return {
            "status": "accepted",
            "ticket_id": ticket_id,
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
    
    await process_complaint_async(
        complaint_text=complaint_text,
        ticket_id=9999,
        email=email
    )
    
    return {"status": "test_started", "message": "Complaint processing triggered"}


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
