# Specialist Review — Plan

## Technical Context

- Implementation: `nodes/specialist_review.py` calls `tools.a2a_specialist_tool.request_specialist_review`.
- Returns the specialist recommendation and logs the action.

## Files in Scope

- `nodes/specialist_review.py`
- `tools/a2a_specialist_tool.py`

## Testing Strategy

- Unit tests should mock `request_specialist_review` for successful and failed service calls.
- Validate `actions_taken` includes the A2A review entry.

## Implementation Notes

- Keep the node logic small: request recommendation, return payload, and record the action.
- Propagate error payloads unmodified so downstream review can handle them.

## Risks and Contingencies

- The external A2A service may be unavailable; the node must preserve failure payloads for human review.

## Follow-ups

- Add retries or fallback mechanisms for temporary service outages.
