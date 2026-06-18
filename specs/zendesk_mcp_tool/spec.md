# Zendesk MCP Tool

status: migrated

## Summary

`tools/zendesk_mcp_tool.py` sends workflow summaries to a remote MCP Streamable HTTP server to update Zendesk ticket status and comments. It supports local skipping when `ZENDESK_MCP_URL` is not configured and handles missing MCP dependencies gracefully.

## User Scenarios

- As a system, when the workflow completes, the tool updates the Zendesk ticket status to `solved` and adds a summary comment.
- As a system, when MCP config is missing, the tool skips updates and returns a `skipped` payload.
- As a system, when the `mcp` client or `httpx` is not installed, the tool returns a helpful error message.

## Requirements

- Accept `ticket_id`, optional `status`, optional `comment`, and optional `workflow_result`.
- Construct a payload with ticket details and workflow summary.
- Use async HTTP calls through the `mcp` streamable client.
- Return structured status information whether the call succeeds, is skipped, or fails.

## Success Criteria

- When configured, the tool sends the payload successfully and returns tool metadata.
- When not configured, it returns a skipped result rather than raising.
- When dependencies are missing, it returns a clear error message and install hint.

## Assumptions

- `ZENDESK_MCP_URL` and `ZENDESK_MCP_AUTH_TOKEN` are optional configuration values.
- Downstream callers can consume the returned structure for logging.

## Known Gaps

- No direct tests covering async MCP client operation.
- Dependency failure path is covered only by code inspection.
