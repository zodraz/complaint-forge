# Refund Specialist A2A Service

Separate Python service that receives escalated ComplaintForge cases, runs a CrewAI specialist review, and returns a recommendation for the human reviewer.

Run locally with the shared project venv:

```powershell
cd ..
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn a2a_refund_specialist_service.app:app --host 0.0.0.0 --port 8010
```

CrewAI currently requires Python `>=3.10,<3.14`. If the shared project venv was
created with Python 3.14, CrewAI will not install and this service will return a
fallback recommendation with a `CrewAI import failed` reason instead of running
the CrewAI review. Recreate the shared `.venv` with Python 3.13 to run the real
CrewAI specialist.

Configure the main app:

```env
A2A_SPECIALIST_URL=http://localhost:8010
A2A_SPECIALIST_AUTH_TOKEN=optional-bearer-token
```

Useful endpoints:

- `GET /.well-known/agent-card.json`
- `POST /tasks/refund-specialist`
- `GET /health`
