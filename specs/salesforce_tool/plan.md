# Salesforce Tool — Plan

## Technical Context

- Implementation: `tools/salesforce_tool.py` handles Salesforce OAuth, SOQL queries, record lookup, and create operations for cases and tasks.
- Uses environment configuration for credentials and login URL.
- Exposes utility functions for customer history lookup and refund/credit/replacement actions.

## Files in Scope

- `tools/salesforce_tool.py`

## Testing Strategy

- Mock HTTP responses to verify token exchange, SOQL queries, and record creation.
- Validate error message wrapping and exception handling.

## Implementation Notes

- Use helper functions to separate auth, query, and create operations.
- Sanitize SOQL identifiers to avoid invalid query construction.
- Return structured error payloads instead of raising where callers expect data.

## Risks and Contingencies

- External HTTP failures can occur; use structured error payloads and do not crash the caller.
- Input sanitization is critical for SOQL queries to avoid invalid identifiers.

## Follow-ups

- Add retry/backoff and idempotency for create operations.
- Improve security around SOQL identifier building.
