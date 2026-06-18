# Action Agent

status: migrated

## Summary

The Action Agent executes side-effect operations based on the selected resolution. Implemented in `agents/action_agent.py`, it invokes `tools.salesforce_tool` helpers to create refund cases, credit cases, replacement orders, or log escalations.

## User Scenarios

- As a system, when a customer is approved for a full or partial refund, the action agent creates a Salesforce refund case and records the result.
- As a system, when a customer is approved for credit, the action agent creates a Salesforce credit case and records the result.
- As a system, when the resolution is `replacement`, the action agent creates a Salesforce task to coordinate fulfillment.
- As a system, when the resolution is `escalate`, the action agent logs an escalation action without creating automated financial transactions.

## Requirements

- Inspect `resolution_type`, `refund_amount`, `credit_amount`, and `action_needed`.
- Call `process_refund` for refunds, `issue_credit` for credits, and `create_replacement_order` for replacements.
- Return `actions_taken` as a list of action entries.
- Avoid side effects for unsupported or missing resolution types.

## Success Criteria

- `actions_taken` captures one or more actions when a valid resolution is supplied.
- Refund/credit actions include the executed amount and result payload.
- Escalation actions are logged with a clear `reason`.
- No action is taken for unsupported resolution types.

## Assumptions

- Salesforce helpers are configured correctly and can handle missing or malformed customer history.
- Upstream policy and guardrails have already validated the resolution.

## Known Gaps

- No retry or idempotency support for Salesforce side effects.
- Error handling is limited to the underlying helper response rather than the action agent itself.
