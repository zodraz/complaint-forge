# A2A Refund Specialist Service — Plan

## Technical Context

- Implementation: `a2a_refund_specialist_service/app.py` is a FastAPI service with endpoints for agent card, task execution, and health.
- Uses CrewAI when available and falls back to a canned safe recommendation on import or runtime failure.
- Uses `llm_factory.get_chat_llm` to create the underlying LLM for CrewAI.

## Files in Scope

- `a2a_refund_specialist_service/app.py`
- `a2a_refund_specialist_service/requirements.txt`

## Testing Strategy

- Test endpoint auth enforcement when `A2A_SPECIALIST_AUTH_TOKEN` is configured.
- Simulate CrewAI import failure to ensure fallback recommendations are returned.
- Validate the generated recommendation payload structure.

## Implementation Notes

- Keep CrewAI invocation in a separate `run_crewai_review` helper for easier testing.
- Use `_fallback_recommendation` consistently for all failure paths.
- Validate JSON extraction carefully when CrewAI returns fenced code blocks.

## Risks and Contingencies

- CrewAI dependency may not be available in all environments; the service must still return safe output.
- Python version compatibility is noted; ensure runtime matches CrewAI requirements.

## Follow-ups

- Add deployment documentation and containerization notes.
- Add a dedicated health check for CrewAI availability.
