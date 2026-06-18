# Analyzer Agent — Plan

## Technical Context

- Implementation: `agents/analyzer.py` using `ChatPromptTemplate` and `AnalysisResult` pydantic model.
- Inputs: `complaint`, `history` (serialized JSON string).
- The agent uses Azure OpenAI via `llm_factory.get_chat_llm` with a module-level LLM instance.
- Output is downstream consumption by `agents/resolver.py` and `nodes/policy.py`.

## Files in Scope

- `agents/analyzer.py`
- `prompts/system_prompts.py`
- `llm_factory.py`

## Testing Strategy

- Unit tests should mock `get_chat_llm` or the module-level `llm` to return deterministic `AnalysisResult` values.
- Validate field mapping for `issue_type`, `sentiment`, `urgency`, `repeat_complaint`, and `key_details`.

## Implementation Notes

- Keep prompt generation and structured-output definitions localized to the agent function.
- Prefer explicit JSON serialization of `history` to avoid malformed input.
- Add validation for unexpected literal values from the LLM and fail fast with clear error messages.

## Risks and Contingencies

- Structured output may break if the LLM returns unexpected literals; add strict validation and fallback behavior.
- The module-level `llm` means environment misconfiguration raises at import time, complicating test isolation.

## Follow-ups

- Refactor LLM initialization for dependency injection.
- Add resilience to malformed `customer_history` input.
