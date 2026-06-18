# Action Agent — Plan

## Technical Context

- Implementation: `agents/action_agent.py` orchestrates side-effect operations using `tools.salesforce_tool`.
- It interprets `resolution` payloads and creates refund cases, credit cases, replacement tasks, or escalation logs.
- Side effects are only performed when the resolution demands them.

## Files in Scope

- `agents/action_agent.py`
- `tools/salesforce_tool.py`

## Testing Strategy

- Mock `process_refund`, `issue_credit`, and `create_replacement_order` to verify action selection and result composition.
- Test escalation logic to ensure no refund/credit is performed when `resolution_type == 'escalate'`.

## Implementation Notes

- Map each resolution type to the appropriate Salesforce helper while keeping action payloads consistent.
- Capture action results in a standardized `actions_taken` list for observability.
- Avoid side effects for unsupported or missing resolution types.

## Risks and Contingencies

- External Salesforce calls can fail; ensure callers interpret error payloads correctly.
- Missing or malformed customer history may still be passed into action helpers, so validate inputs early.

## Follow-ups

- Add retry and idempotency support for Salesforce side effects.
- Add audit logging for each `actions_taken` entry.
- Add audit logging for actions executed.
