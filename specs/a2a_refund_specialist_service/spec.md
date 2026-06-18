# A2A Refund Specialist Service

status: migrated

## Summary

A lightweight FastAPI service in `a2a_refund_specialist_service/app.py` that uses CrewAI to produce specialist recommendations for escalated refund and complaint cases. It exposes a `/tasks/refund-specialist` endpoint and includes fallback behavior if CrewAI cannot run.

## User Scenarios

- As a system, when the A2A specialist service receives an escalated case, it returns an advisory recommendation with decision, risk level, refund/credit amounts, reasoning, and draft response.
- As a system, when CrewAI is unavailable or import fails, the service returns a fallback safe recommendation indicating human review is required.
- As a system, when authorization is configured, requests without the correct bearer token are rejected.

## Requirements

- Expose `/tasks/refund-specialist` and `/health` endpoints.
- Authorize requests when `A2A_SPECIALIST_AUTH_TOKEN` is configured.
- Invoke CrewAI to generate a JSON recommendation when available.
- Return a safe fallback recommendation on CrewAI import or runtime failure.

## Success Criteria

- The service returns a valid JSON recommendation when the external agent is available.
- Authorization failure returns HTTP 401 when a token is configured.
- Fallback recommendations are returned safely without raising uncaught exceptions.

## Assumptions

- `AZURE_OPENAI_*` env vars are configured for the local `llm_factory` used by CrewAI.
- `A2A_SPECIALIST_URL` consumer expects the specific recommendation format.

## Known Gaps

- The service has no explicit integration tests covering CrewAI success/path or auth enforcement.
