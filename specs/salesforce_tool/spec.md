# Salesforce Tool

status: migrated

## Summary

`tools/salesforce_tool.py` encapsulates Salesforce REST interactions: OAuth auth token exchange, SOQL queries, and case/task creation helpers used by `nodes/customer_context` and `agents/action_agent`.

## User Scenarios

- As a system, when a customer email is available, Salesforce tool finds the contact and returns account, cases, opportunities, and order history.
- As a system, when an order ID is provided, Salesforce tool attempts to match the order and surface return order history.
- As a system, when a refund is required, Salesforce tool creates a refund case with a descriptive subject and description.

## Requirements

- Support auth token retrieval via client credentials.
- Support SOQL query execution and record parsing.
- Return structured data for contact, cases, opportunities, and order matching.
- Provide helper functions `process_refund`, `issue_credit`, and `create_replacement_order` that create Salesforce cases or tasks.

## Success Criteria

- Salesforce lookups return `contact_id`, `account_id`, and related record lists when successful.
- Create functions return successful action payloads or standardized error payloads.
- Errors from HTTP failures are wrapped with readable diagnostic details.

## Assumptions

- Salesforce config environment variables are present when the tool is used.
- Calling code can handle `error` payloads returned by the tool.

## Known Gaps

- No retries or backoff for HTTP failures.
- Tool does not currently support bulk or idempotent create operations.
