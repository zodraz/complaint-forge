# Main FastAPI

status: migrated

## Summary

`main_fastapi.py` exposes HTTP endpoints for webhook ingestion, workflow execution, and resume/completion hooks. It orchestrates the complaint workflow and integrates with LangGraph, Zendesk MCP, and external specialist services.

## User Scenarios

- As a system, when a Zendesk webhook triggers, the main API starts the complaint workflow and returns a tracking result.
- As a system, when the workflow reaches a completion hook, the API resumes the process and updates the ticket via MCP.
- As a system, when external services are unavailable, the API surfaces appropriate error or skipped results.

## Requirements

- Provide endpoints for webhook ingestion and completion hooks.
- Wire the workflow nodes and agents in `graph.py`.
- Handle LangGraph interrupts and resume state.
- Integrate with `tools/zendesk_mcp_tool` for ticket updates.

## Success Criteria

- The API returns clear workflow status responses on successful ingestion and completion.
- Errors from external services do not crash the main process.
- Resume/completion hooks can be called with workflow state and return a valid summary.

## Assumptions

- Env vars and external services are configured during runtime.
- The workflow graph is defined correctly in `graph.py`.

## Known Gaps

- No direct integration tests are documented for webhook or completion hook flows.
