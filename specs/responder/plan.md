# Responder Agent — Plan

## Technical Context

- Implementation: `agents/responder.py` using `ChatPromptTemplate` and a slightly creative LLM temperature.
- Inputs: `complaint`, `history`, `resolution`, and `analysis`.
- Returns `response_draft` and `final_response` strings.
- Uses `llm_factory.get_chat_llm` at module import time.

## Files in Scope

- `agents/responder.py`
- `prompts/system_prompts.py`
- `llm_factory.py`

## Testing Strategy

- Mock the LLM invocation and assert that the prompt receives the expected context.
- Verify `response_draft` and `final_response` are both populated and identical in current implementation.

## Implementation Notes

- Keep the response generation logic simple; the current agent returns the same text for draft and final response.
- Use the prompt to enforce empathetic tone and customer-centric language.
- Consider separating response text generation from formatting to support future variants.

## Risks and Contingencies

- The LLM could generate tone or content that requires additional guardrails; rely on `nodes/guardrails.py` for quality checks.
- Response generation depends on live LLM connectivity, so consider offline substitution for tests.

## Follow-ups

- Add an injection-friendly wrapper around LLM calls.
- Add response safety guardrails earlier in the pipeline if needed.
