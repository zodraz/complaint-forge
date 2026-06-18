# Resolver Agent — Plan

## Technical Context

- Implementation: `agents/resolver.py` using `ChatPromptTemplate` and `ResolutionResult` pydantic model.
- Inputs: serialized `history` and `analysis` JSON strings.
- Uses module-level Azure OpenAI LLM from `llm_factory.get_chat_llm`.
- Output drives `nodes/policy.py`, `nodes/guardrails.py`, and `agents/action_agent.py`.

## Files in Scope

- `agents/resolver.py`
- `prompts/system_prompts.py`
- `llm_factory.py`

## Testing Strategy

- Mock the LLM response to verify output parsing into `ResolutionResult`.
- Include tests for edge cases: escalation, zero refund/credit amounts, and confidence boundaries.

## Implementation Notes

- Serialize `history` and `analysis` using JSON with indentation for readability.
- Normalize numeric fields before returning to avoid string or null values.
- Ensure `confidence` is bounded between 0.0 and 1.0 for downstream policy checks.

## Risks and Contingencies

- Monetary fields should be validated to avoid negative or nonsensical values.
- Unexpected LLM output can break downstream policy checks; add schema validation and fallback defaults.

## Follow-ups

- Consider adding currency-awareness or unit normalization.
- Extract LLM initialization for easier test injection and environment validation.
