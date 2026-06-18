# Triage Agent — Plan

## Technical Context

- Implementation: `agents/triage.py` — uses `langchain_core.prompts.ChatPromptTemplate` and `pydantic` for structured output (`TriageResult`).
- Prompts: `prompts/system_prompts.py` (TRIAGE_PROMPT).
- LLM factory: `llm_factory.get_chat_llm` (Azure OpenAI, env var driven).
- Workflow: `graph.py` defines `triage_node` as the entry point.

## Files In Scope

- `agents/triage.py`
- `prompts/system_prompts.py`
- `llm_factory.py`
- `graph.py` (workflow wiring)
- Tests referencing prompt template: `tests/test_prompts.py`

## Complexity

- Small, bounded feature: ~30–80 lines of core logic.
- Main complexity: external LLM dependency and structured-output mapping.

## Testing Strategy

- Unit tests should mock `llm_factory.get_chat_llm` or construct `agents.triage` with an injected mock LLM.
- Add tests to validate routing when `is_complaint` true/false and to assert `customer_email`/`order_id` extraction.

## Implementation Notes

- Consider moving LLM initialization out of module top-level to allow injection for tests (e.g., factory function or `get_llm()` accessor).
- Add exception handling around `chain.invoke(...)` to convert LLM errors into deterministic workflow failures.

## Follow-ups

- Add unit tests that mock LLM responses.
- Add a small helper to create a test-friendly `triage` (dependency injection).
