# Responder Agent

status: migrated

## Summary

The Responder agent drafts the customer-facing response using `RESPONDER_PROMPT` and the full complaint context. Implemented in `agents/responder.py`, it returns both `response_draft` and `final_response`.

## User Scenarios

- As a system, after a resolution has been selected, the responder writes an empathetic, policy-aligned message for the customer.
- As a system, when no customer history is available, the responder still produces a polite response based on complaint and resolution details.

## Requirements

- Accept inputs: `complaint`, `history`, `analysis`, and `resolution`.
- Produce `response_draft` and `final_response` strings.
- Use a calm, empathetic tone appropriate for customer support.
- Include the chosen resolution action in the response text.

## Success Criteria

- Output contains non-empty `response_draft` and `final_response`.
- Response text references the customer issue and the proposed resolution.
- Tone remains empathetic and customer-centered.

## Assumptions

- LLM prompt definitions are in `prompts/system_prompts.py`.
- Downstream caller may use `final_response` for Zendesk updates.

## Known Gaps

- Live LLM dependency makes unit tests harder without mocking.
- No explicit safety guardrails in `agents/responder.py`; response quality is validated later by `nodes/guardrails.py`.
