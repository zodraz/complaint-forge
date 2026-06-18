# A2A Specialist Tool — Plan

## Technical Context

- Implementation: `tools/a2a_specialist_tool.py` sends a POST request to `A2A_SPECIALIST_URL/tasks/refund-specialist`.
- Supports optional bearer token authentication.
- Returns JSON response or structured error payload for failures.

## Files in Scope

- `tools/a2a_specialist_tool.py`

## Testing Strategy

- Mock `requests.post` to simulate successful responses, HTTP errors, and network timeouts.
- Validate auth header inclusion when the token is configured.

## Implementation Notes

- Keep the request payload structure aligned with the specialist service contract.
- Handle missing URL configuration by returning a skipped response.
- Wrap all request failures in structured error payloads.

## Risks and Contingencies

- Service unavailability should be handled gracefully and returned as an error payload.
- Timeout and network failures should not crash the workflow.

## Follow-ups

- Add retry or circuit-breaker logic if this service becomes critical.
