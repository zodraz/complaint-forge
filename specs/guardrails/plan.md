# Guardrails — Plan

## Technical Context

- Implementation: `nodes/guardrails.py` runs response quality evaluators from `response_evaluators.RESPONSE_QUALITY_EVALUATORS`.
- Evaluators receive the workflow outputs and complaint as inputs.
- Failing scores or evaluator exceptions trigger a safe escalation and fallback response.

## Files in Scope

- `nodes/guardrails.py`
- `response_evaluators.py`

## Testing Strategy

- Unit tests should replace evaluator functions with stubs that return passing and failing scores.
- Add tests for evaluator exceptions to ensure they are caught and treated as failures.

## Implementation Notes

- Use `SimpleNamespace` wrappers to adapt outputs into evaluator-friendly objects.
- Keep the evaluator loop resilient and continue after individual failures.
- Return a clear fallback response and escalation action when any guardrail fails.

## Risks and Contingencies

- Hardcoded score thresholds may need tuning for real-world response quality.
- Evaluator exceptions should never crash the workflow.

## Follow-ups

- Make thresholds configurable.
- Add logging or tracing for evaluator performance and failure reasons.
