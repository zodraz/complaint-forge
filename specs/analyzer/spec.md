# Analyzer Agent

status: migrated

## Summary

The Analyzer agent inspects a complaint and customer history to identify the issue category, customer sentiment, urgency, repeat complaint status, and key details. It is implemented in `agents/analyzer.py` and outputs a structured `AnalysisResult` using `pydantic`.

## User Scenarios

- As a system, when a complaint and customer history are available, the analyzer classifies the issue type and urgency so the resolver can choose an appropriate operational response.
- As a system, when customer history is missing or incomplete, the analyzer still returns a structured result with `repeat_complaint` false and a `key_details` summary of the available complaint.

## Requirements

- Accept `complaint` (string) and `history` (JSON-serializable dict) inputs.
- Return `issue_type`, `sentiment`, `urgency`, `repeat_complaint`, and `key_details`.
- Use normalized literal values for `issue_type` and `sentiment` as defined by `AnalysisResult`.
- Preserve text from the complaint in `key_details` to support downstream resolution and review.

## Success Criteria

- Analyzer returns all required fields for valid inputs.
- `issue_type` and `sentiment` must be one of the allowed literal values.
- A missing or empty `history` input does not prevent analyzer execution.
- `key_details` contains a concise summary of the main complaint facts.

## Assumptions

- LLM connectivity is available via `llm_factory.get_chat_llm`.
- Prompts are defined in `prompts/system_prompts.py`.
- Downstream components expect `analysis` to be serializable as JSON.

## Known Gaps

- `llm` is created at module import time, which complicates unit testing and injection.
- No direct unit tests yet mock structured LLM output for `analyzer()`.
