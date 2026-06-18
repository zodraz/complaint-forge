# Triage Agent — Tasks

All tasks below reflect the current repository state and are marked complete where implemented.

- [x] Implement `agents/triage.py` using `ChatPromptTemplate` and `pydantic.TriageResult`.
- [x] Add prompt template `TRIAGE_PROMPT` in `prompts/system_prompts.py`.
- [x] Wire `triage_node` in `graph.py` to call `triage(state)` and route based on `is_complaint`.
- [x] Add prompt template tests in `tests/test_prompts.py` (verifies input variables).

Gaps / Recommended follow-ups:

- [x] Add unit tests for `triage()` that mock the LLM.
- [ ] Refactor to allow LLM injection for easier testing (module top-level `llm` is instantiated at import).
- [x] Add error handling and timeouts around LLM invocation.
