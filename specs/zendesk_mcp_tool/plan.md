# Zendesk MCP Tool — Plan

## Technical Context

- Implementation: `tools/zendesk_mcp_tool.py` uses async `httpx` and `mcp` streamable client to invoke remote MCP tools.
- Supports optional configuration for URL, auth token, ticket status, and tool name.
- Falls back to a skipped result if no MCP URL is configured or to an error payload if dependencies are missing.

## Files in Scope

- `tools/zendesk_mcp_tool.py`

## Testing Strategy

- Mock async HTTP client and streamable MCP client to verify payload construction and error handling.
- Test skipped-path behavior when `ZENDESK_MCP_URL` is unset.

## Implementation Notes

- Build payloads in a reusable helper to separate transport concerns.
- Return informative diagnostics for skipped and error cases.
- Keep `httpx` and `mcp` dependency failures non-fatal.

## Risks and Contingencies

- Missing `mcp` or `httpx` dependencies should not crash the application.
- Asynchronous operations require careful test setup and event loop management.

## Follow-ups

- Add integration tests against a local MCP test server.
