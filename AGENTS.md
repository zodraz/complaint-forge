# ComplaintForge Agent Guide

This repo contains a FastAPI + LangGraph complaint handling workflow. Keep changes aligned with the current architecture and naming.

## Architecture

Main app:

- `main_fastapi.py` owns HTTP endpoints, LangGraph thread ids, human-review resume endpoints, and completion hooks.
- `graph.py` owns workflow topology only. Keep node routing explicit and readable.
- `agents/` contains LLM-driven steps.
- `nodes/` contains deterministic graph nodes and workflow mechanics.
- `tools/` contains external integration clients.
- `a2a_refund_specialist_service/` is a separate Python service that provides an external A2A/CrewAI specialist recommendation before human review.

Current workflow:

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

## Naming Rules

- Use `triage_agent` / `agents/triage.py` for complaint classification and extraction.
- Use `nodes/customer_context.py` for Salesforce enrichment. Do not reintroduce a `coordinator` agent unless it truly coordinates the whole workflow.
- Use `nodes/policy.py` for deterministic business rules.
- Use `nodes/guardrails.py` for evaluator-based quality checks after the response draft and before external actions.
- Use `nodes/specialist_review.py` for external A2A specialist calls.
- Use `nodes/human_review.py` for LangGraph `interrupt(...)`.

## Provider Integrations

- OpenAI access is Azure OpenAI via `llm_factory.get_chat_llm`.
- `get_chat_llm` intentionally uses `ChatOpenAI` with Azure OpenAI v1-style `base_url`.
- Salesforce is the CRM system. Do not add HubSpot or Stripe back.
- Zendesk ticket updates should go through the remote MCP client in `tools/zendesk_mcp_tool.py`.
- A2A specialist calls go through `tools/a2a_specialist_tool.py`.

## Human In The Loop

Escalations must not execute Salesforce actions directly.

Escalation flow:

```text
policy/guardrail escalation
 -> A2A specialist recommendation
 -> human_review interrupt
 -> human resumes
 -> workflow completes
```

The human interrupt payload should include:

- complaint
- customer email
- order id
- Salesforce customer history
- analysis
- resolution
- specialist review

## Guardrails And Policy

Keep these separate:

- Resolver proposes a resolution.
- Policy applies hard deterministic rules before drafting or external action.
- Responder drafts customer-facing text.
- Guardrails evaluate response quality and resolution appropriateness.
- Action agent runs only after policy and guardrails pass.

Do not move side-effecting Salesforce/Zendesk calls before policy and guardrails.

## Tests

Tests are standard-library `unittest`, not pytest.

Run:

```powershell
python -B -m unittest discover -s tests -v
```

Use `-B` to avoid generating bytecode. This repo previously had tracked `__pycache__` files, so avoid adding new `.pyc` changes.

## Local Running

Main API:

```powershell
uvicorn main_fastapi:app --host 0.0.0.0 --port 8000 --reload
```

A2A specialist service:

```powershell
cd a2a_refund_specialist_service
uvicorn app:app --host 0.0.0.0 --port 8010 --reload
```

VS Code launch configs are in `.vscode/launch.json`.

## Env Vars

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

Never commit real tokens. `.env.example` must contain placeholders only.

## Common Pitfalls

- `.gitignore` does not stop Git from tracking files that were already committed. Use `git rm --cached` for tracked `__pycache__` files.
- `MemorySaver` and `review_runs` are in-memory only. Pending reviews are lost on process restart.
- LangSmith tracing can emit 403 warnings if no valid key is configured. That does not necessarily mean tests failed.
- Zendesk status should usually be set to `solved`, not `closed`.
