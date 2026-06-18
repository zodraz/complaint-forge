# Main FastAPI — Plan

## Technical Context

- Implementation: `main_fastapi.py` exposes HTTP endpoints for workflow ingestion, completion, and resume.
- Orchestrates the complaint workflow defined in `graph.py`.
- Integrates with external services via MCP, Salesforce tools, and A2A specialist tooling.

## Files in Scope

- `main_fastapi.py`
- `graph.py`
- `tools/zendesk_mcp_tool.py`

## Testing Strategy

- Add integration tests for webhook ingestion and completion hooks.
- Mock external services (Zendesk MCP, Salesforce, A2A specialist) and LangGraph interrupts.

## Implementation Notes

- Keep endpoint handlers focused on orchestration and external integration.
- Avoid embedding business logic in HTTP request handling.
- Ensure workflow errors are captured and returned as structured responses.

## Risks and Contingencies

- External dependencies can fail or timeout; the API should surface errors with safe defaults.
- Workflow entry and resume paths must remain consistent across calls.

## Follow-ups

- Add end-to-end tests covering a full complaint workflow from webhook to ticket update.
- Document environment variable requirements for deployment.
