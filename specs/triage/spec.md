# Triage Agent

status: migrated

## Summary

The Triage agent classifies incoming customer tickets as complaints or non-complaints and extracts basic fields (customer email, order id). It is implemented in agents/triage.py and uses a LangChain prompt (prompts/system_prompts.py) with Azure OpenAI via llm_factory.get_chat_llm.

## User Scenarios

- As a system, when a Zendesk webhook provides a ticket body containing a clear complaint, the triage agent marks it as a complaint and returns extracted metadata (email, order id).
- As a system, when the ticket is not a complaint (e.g., a product question), the triage agent marks it as not a complaint so the workflow can terminate early.

## Requirements

- Classify whether a ticket is a complaint (`is_complaint: bool`).
- Provide a confidence score in range 0.0–1.0.
- Return a short `reason` for the decision.
- Extract optional `customer_email` and `order_id` when present.
- Be callable as `triage(state: dict) -> dict` and used as the workflow entry node.

## Success Criteria

- Triage outputs must include `is_complaint`, `confidence`, and `reason` for each input.
- The prompt template accepts `input` and does not require additional context (covered by tests).
- The workflow routes correctly when `is_complaint` is true or false.

## Assumptions

- LLM connectivity and credentials are provided via Azure OpenAI env vars used by `llm_factory`.
- Structured output is validated using `pydantic.BaseModel` (`TriageResult`).

## Known Gaps

- No unit tests directly exercise `triage()` or mock the LLM; only prompt template tests exist.
- `llm` is created at module import time in `agents/triage.py`, coupling the module to environment configuration and making tests harder.
- There is no explicit error handling for LLM failures or timeouts.
