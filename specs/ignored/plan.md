# Ignored — Plan

## Technical Context

- Implementation: `nodes/ignored.py` returns an empty `final_response` and logs an `ignored_non_complaint` action.
- This node is used when triage determines the ticket is not a complaint.

## Files in Scope

- `nodes/ignored.py`

## Testing Strategy

- Unit tests should confirm `final_response` is empty and `actions_taken` includes the correct reason.

## Implementation Notes

- Keep the node implementation trivial to minimize risk.
- Preserve the original triage `reason` in the actions list.

## Risks and Contingencies

- Minimal risk; the node should not perform side effects.

## Follow-ups

- None required beyond coverage for the non-complaint path.
