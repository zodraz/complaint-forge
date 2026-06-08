# ComplaintForge

ComplaintForge is a FastAPI and LangGraph complaint handling workflow. It accepts Zendesk-style complaint requests, enriches them with Salesforce customer context, proposes a resolution, checks policy and response quality guardrails, and then either completes the action flow or pauses for human review.

The project also includes a separate A2A refund specialist service powered by CrewAI. That service is called before human review when policy or guardrails escalate a case.

## Workflow

```text
Zendesk webhook / test request
 -> triage agent
 -> if not complaint: ignored node -> end
 -> customer_context node: Salesforce lookup/history
 -> analyzer agent
 -> resolver agent
 -> policy node
    -> if policy escalates: specialist_review node -> human_review interrupt
 -> responder agent
 -> guardrails node
    -> if guardrails escalate: specialist_review node -> human_review interrupt
 -> action agent: Salesforce Case/Task actions
 -> FastAPI completion hook: Zendesk MCP ticket update
```

Escalations do not execute Salesforce actions directly. The escalation path is:

```text
policy/guardrail escalation
 -> A2A specialist recommendation
 -> human_review interrupt
 -> human resumes
 -> workflow completes
```

## Project Layout

- `main_fastapi.py` - FastAPI endpoints, LangGraph thread ids, human-review resume endpoints, and Zendesk completion hook.
- `graph.py` - LangGraph topology and routing.
- `agents/` - LLM-driven workflow steps.
- `nodes/` - deterministic graph nodes and workflow mechanics.
- `tools/` - external integration clients for Salesforce, Zendesk MCP, and A2A specialist calls.
- `a2a_refund_specialist_service/` - separate FastAPI service for CrewAI specialist review.
- `complaint_forge.http` - local HTTP request examples for health checks, test complaints, escalation, and human review resume.

## Requirements

Use Python 3.13 for the shared project virtual environment. CrewAI currently requires Python `>=3.10,<3.14`, so a Python 3.14 venv will install the main app dependencies but will skip or fail CrewAI.

The root `requirements.txt` includes both main app and A2A service dependencies. `mcp` is pinned to `>=1.26.0,<1.27.0` because CrewAI `1.14.x` depends on `mcp~=1.26.0`.

## Setup

Create and install the shared venv from the repo root:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in real values. Never commit real tokens.

Generate a local A2A specialist bearer token if needed:

```powershell
python -B -c "import secrets; print(secrets.token_urlsafe(48))"
```

Use the same `A2A_SPECIALIST_AUTH_TOKEN` value for the main app and A2A specialist service.

## Environment Variables

Root app expects:

- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_DEPLOYMENT_NAME`
- `SALESFORCE_LOGIN_URL`
- `SALESFORCE_CLIENT_ID`
- `SALESFORCE_CLIENT_SECRET`
- `SALESFORCE_API_VERSION`
- `SALESFORCE_RETURN_ORDER_OBJECT`
- `SALESFORCE_RETURN_ORDER_ACCOUNT_FIELD`
- `SALESFORCE_RETURN_ORDER_ORDER_FIELD`
- `ZENDESK_MCP_URL`
- `ZENDESK_MCP_AUTH_TOKEN`
- `ZENDESK_MCP_UPDATE_TICKET_TOOL`
- `A2A_SPECIALIST_URL`
- `A2A_SPECIALIST_AUTH_TOKEN`

For local LangSmith tracing:

```env
LANGSMITH_TRACING=true
LANGCHAIN_TRACING_V2=true
LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com
LANGSMITH_API_KEY=your-langsmith-api-key
LANGSMITH_PROJECT=complaint-forge
```

If you are behind a corporate TLS proxy and LangSmith upload fails with certificate verification errors, keep tracing enabled and point Python requests at your trusted CA bundle:

```env
REQUESTS_CA_BUNDLE=C:\path\to\corporate-ca-bundle.pem
SSL_CERT_FILE=C:\path\to\corporate-ca-bundle.pem
```

## Run Locally

Start the main API:

```powershell
.venv\Scripts\Activate.ps1
uvicorn main_fastapi:app --host 0.0.0.0 --port 8000 --reload
```

Start the A2A specialist service in another terminal:

```powershell
.venv\Scripts\Activate.ps1
uvicorn a2a_refund_specialist_service.app:app --host 0.0.0.0 --port 8010 --reload
```

Configure the main app to call it:

```env
A2A_SPECIALIST_URL=http://localhost:8010
A2A_SPECIALIST_AUTH_TOKEN=your-a2a-specialist-token
```

Useful endpoints:

- `GET /health`
- `POST /webhook/zendesk/complaint`
- `POST /test/complaint`
- `GET /review`
- `GET /review/{thread_id}`
- `POST /review/{thread_id}/resume`
- `GET http://localhost:8010/.well-known/agent-card.json`
- `POST http://localhost:8010/tasks/refund-specialist`

Use `complaint_forge.http` for ready-made request examples, including a high-value refund that should escalate to human review.

## Tests

Tests use standard-library `unittest`.

```powershell
python -B -m unittest discover -s tests -v
```

Use `-B` to avoid generating bytecode.

## Troubleshooting

Salesforce OAuth returns `400 Bad Request`:

- Check `SALESFORCE_CLIENT_ID` and `SALESFORCE_CLIENT_SECRET`.
- Use `https://test.salesforce.com` for sandbox orgs and `https://login.salesforce.com` for production orgs.
- Make sure the Salesforce Connected App supports the client credentials flow and has a run-as user configured.

CrewAI fallback says `No module named 'crewai'`:

- Confirm the service is running from the shared `.venv`.
- Confirm the shared `.venv` was created with Python 3.13.
- Reinstall dependencies with `pip install -r requirements.txt`.

Pip reports an MCP conflict:

- Keep `mcp>=1.26.0,<1.27.0` while using CrewAI `1.14.x`.
- CrewAI `1.14.x` depends on `mcp~=1.26.0`.

LangSmith emits SSL upload warnings:

- The workflow can still pass tests and process requests.
- Add `REQUESTS_CA_BUNDLE` and `SSL_CERT_FILE` if you want tracing enabled behind a corporate TLS proxy.

Pending human reviews disappear after restart:

- `MemorySaver` and `review_runs` are in-memory only. This is expected for local development.
