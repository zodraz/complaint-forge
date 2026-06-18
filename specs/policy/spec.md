# Policy Node

status: migrated

## Summary

`nodes/policy.py` applies deterministic business rules before responder drafting and external actions. It evaluates confidence, refund limits, matched Salesforce orders, excluded products, and lookup failures, then approves the resolution or escalates by updating `resolution` and returning `policy_result`.

## User Scenarios

- As a system, when the resolution confidence is below 0.85, the policy node escalates the case for human review.
- As a system, when a refund is requested above $500 or no matched order is found, the policy node prevents automation and escalates.
- As a system, when the complaint mentions excluded product types, refund resolutions are blocked and escalated.

## Requirements

- Accept workflow state containing `resolution`, `customer_history`, `analysis`, and `complaint`.
- Evaluate deterministic rules and collect escalation reasons.
- If any rule fails, set `resolution_type` to `escalate`, zero automated refund amounts where appropriate, and return `policy_result.approved = False`.
- If all checks pass, return `policy_result.approved = True`.

## Success Criteria

- Policy sets `approved` false for all failed deterministic checks.
- Escalation reasons are clear and included in `action_needed` and `policy_result.reasons`.
- No policy escalation occurs when all business rules pass.

## Assumptions

- `customer_history` may contain an `error` key if Salesforce lookup failed.
- `analysis` may contain issue classification used for excluded-product detection.

## Known Gaps

- Confidence is reset to `min(confidence, 0.0)` on escalation, which always yields 0.0; this may be unintended.
- There are no explicit unit tests verifying all escalation branches.
