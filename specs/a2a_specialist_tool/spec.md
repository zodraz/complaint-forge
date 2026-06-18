# A2A Specialist Tool

status: migrated

## Summary

`tools/a2a_specialist_tool.py` posts escalation payloads to the A2A specialist service and returns the JSON response, with fallback error handling for network or auth failures.

## User Scenarios

- As a system, when a case is escalated, the tool sends the current workflow state to the specialist service and returns its recommendation.
- As a system, when the service is unavailable, the tool returns an error payload that can still be reviewed by downstream workflow logic.

## Requirements

- Read `A2A_SPECIALIST_URL` and optional auth token.
- POST escalation payload to `/tasks/refund-specialist`.
- Return the parsed JSON response or a structured error payload.

## Success Criteria

- A valid service response is returned as JSON.
- Network failures and bad status codes are reported clearly.
- Missing service URL results in a skipped response.

## Assumptions

- The external service follows the expected REST contract.
- Downstream logic handles both success and error payloads.

## Known Gaps

- No direct tests for auth header handling and request failure modes.
