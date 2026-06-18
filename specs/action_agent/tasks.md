# Action Agent — Tasks

- [x] Implement `agents/action_agent.py` to call `tools.salesforce_tool`.
- [ ] Add unit tests that mock `salesforce_tool` functions.
- [ ] Implement retries/idempotency and audit logging for side effects.

Gaps / Recommended follow-ups:

- [ ] Add unit tests verifying each resolution type maps to the correct Salesforce action.
- [ ] Add retry and idempotency support for side-effect calls.
- [ ] Add structured error handling for service failures.
