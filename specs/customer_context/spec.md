# Customer Context Node

status: migrated

## Summary

The `customer_context` node enriches the workflow with customer and order history by calling `tools.salesforce_tool.get_customer_history`. It returns `customer_history`, `customer_email`, `order_id`, and a `customer_context_result` metadata object.

## User Scenarios

- As a system, when triage identifies a customer email and order ID, the node fetches customer history from Salesforce and marks whether a customer record was found.
- As a system, when no email is available, the node returns empty history and marks `customer_found` as false.

## Requirements

- Accept `customer_email` and optional `order_id` from the workflow state.
- Use `tools.salesforce_tool.get_customer_history` to fetch relevant records.
- Return `customer_history`, `customer_email`, `order_id`, and `customer_context_result` with `source` and `customer_found`.

## Success Criteria

- When a contact is found, `customer_history` contains Salesforce fields and `customer_context_result.customer_found` is true.
- When no contact is found, `customer_history` contains an `error` and `customer_context_result.customer_found` is false.
- The node does not throw exceptions for missing `customer_email`.

## Assumptions

- Salesforce tool environment variables are configured for lookups.
- Downstream components consume `customer_history` and context metadata.

## Known Gaps

- No direct unit tests currently validate happy-path and missing-email behavior.
- No retry/backoff is implemented for Salesforce lookup failures.
