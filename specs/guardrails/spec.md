# Guardrails Node

status: migrated

## Summary

`nodes/guardrails.py` validates response quality after drafting and before external actions. It executes evaluators from `response_evaluators.RESPONSE_QUALITY_EVALUATORS` and escalates the workflow if empathy or resolution appropriateness scores fall below thresholds.

## User Scenarios

- As a system, when the drafted response has insufficient empathy, guardrails escalate the case and return a safer fallback response.
- As a system, when the resolution is judged inappropriate, guardrails trigger escalation with a clear failure reason.
- As a system, when evaluators raise exceptions, guardrails treat those evaluators as failed and continue safely.

## Requirements

- Accept workflow state containing `complaint`, `response_draft`, `analysis`, `resolution`, and `actions_taken`.
- Execute each registered evaluator and record their scores in `eval_results`.
- Fail safely when any evaluator score is below threshold or when an evaluator throws an exception.
- On failure, return an escalated `resolution`, a fallback `final_response`, `actions_taken`, and `eval_results`.

## Success Criteria

- Guardrails pass only when all evaluator scores meet thresholds.
- Failed evaluations result in a clearly documented escalation reason.
- The node never raises uncaught exceptions from evaluator failures.

## Assumptions

- Evaluators return dicts containing `score` and `reasoning`.
- Score thresholds are currently fixed at 6 for empathy and resolution appropriateness.

## Known Gaps

- Threshold values are hardcoded rather than configurable.
- No direct unit tests verify evaluator exception handling or escalation output.
