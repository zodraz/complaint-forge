# Customer Context — Plan

## Technical Context

- Implementation: `nodes/customer_context.py` calls `tools.salesforce_tool.get_customer_history(email, order_id)`.
- Returns enriched customer history and context metadata for downstream nodes.

## Files in Scope

- `nodes/customer_context.py`
- `tools/salesforce_tool.py`

## Testing Strategy

- Mock `get_customer_history` for contact found, contact not found, and Salesforce error cases.
- Validate output structure includes `customer_history`, `customer_context_result`, and preserved input keys.

## Implementation Notes

- Return empty history gracefully when `customer_email` is missing.
- Preserve the input `customer_email` and `order_id` fields in the output state.
- Treat Salesforce lookup errors as payload data rather than exceptions.

## Risks and Contingencies

- Salesforce lookups may be slow or fail; the node currently returns errors in payloads rather than raising.
- Missing email input should result in empty history rather than a crash.

## Follow-ups

- Add retry/backoff and metrics for external lookup latency.
- Consider caching or query de-duplication for repeated requests.
