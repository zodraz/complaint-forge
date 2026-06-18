# Policy — Plan

## Technical Context

- Implementation: `nodes/policy.py` applies deterministic business rules before drafting and side effects.
- Evaluates confidence, refund limits, order matching, excluded products, and Salesforce lookup success.
- On failure, it escalates the resolution and returns policy metadata.

## Files in Scope

- `nodes/policy.py`

## Testing Strategy

- Unit tests should cover each rule independently:
  - low confidence
  - refund amount over limit
  - missing matched order
  - excluded product matches
  - history lookup failure
- Verify both approval and escalation outputs.

## Implementation Notes

- Collect escalation reasons incrementally and join them into a single `action_needed` string.
- Preserve `credit_amount` for excluded products if the rule allows credit but not refund.
- Avoid mutating the original `resolution` object beyond what is needed for escalation.

## Risks and Contingencies

- The current escalation logic sets `confidence` to `min(confidence, 0.0)`, which may not be the intended behavior.
- Overlapping escalation conditions should be aggregated into a single actionable reason.

## Follow-ups

- Clarify and fix confidence handling on escalation.
- Document policy thresholds and make them configurable if needed.
