# Specialist Review Node

status: migrated

## Summary

`nodes/specialist_review.py` requests an A2A specialist recommendation via `tools.a2a_specialist_tool.request_specialist_review` and returns the recommendation along with audit actions.

## User Scenarios

- As a system, when policy or guardrails escalate a case, the specialist review node requests a recommendation from the external A2A service.
- As a system, when the A2A specialist service is unavailable, the node returns an error status that can still be reviewed by a human.

## Requirements

- Accept workflow state containing complaint, triage, customer history, analysis, resolution, policy result, and actions taken.
- Call `request_specialist_review` and include its response in `specialist_review`.
- Record an `a2a_specialist_review` action entry.

## Success Criteria

- `specialist_review` contains the external service response.
- `actions_taken` includes the `a2a_specialist_review` action and result.
- Service failures are returned as structured error dictionaries rather than uncaught exceptions.

## Assumptions

- `A2A_SPECIALIST_URL` and auth token configuration are optional but enable service usage.
- Downstream human review can handle skipped or error responses.

## Known Gaps

- No direct tests cover successful and failed A2A specialist calls.
