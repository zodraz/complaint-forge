# Refund Specialist A2A Service

Separate Python service that receives escalated ComplaintForge cases, runs a CrewAI specialist review, and returns a recommendation for the human reviewer.

Run locally:

```powershell
cd a2a_refund_specialist_service
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8010
```

Configure the main app:

```env
A2A_SPECIALIST_URL=http://localhost:8010
A2A_SPECIALIST_AUTH_TOKEN=optional-bearer-token
```

Useful endpoints:

- `GET /.well-known/agent-card.json`
- `POST /tasks/refund-specialist`
- `GET /health`
