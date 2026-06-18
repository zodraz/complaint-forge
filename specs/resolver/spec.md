# Resolver Agent

status: migrated

## Summary

The Resolver agent proposes an operational resolution (refund, credit, replacement, escalate) based on customer complaint context, analysis, and history. It is implemented in `agents/resolver.py` and emits a structured `ResolutionResult`.

## User Scenarios

- As a system, when a complaint has been analyzed and customer history is available, the resolver chooses the best resolution type and amounts.
- As a system, when analysis indicates a complex or high-risk complaint, the resolver may return `resolution_type: escalate` with an appropriate `action_needed` reason.

## Requirements

- Accept `history` and `analysis` inputs.
- Return `resolution_type`, `refund_amount`, `credit_amount`, `action_needed`, and `confidence`.
- Use the allowed literal values defined by `ResolutionResult`.
- Provide numeric refund and credit amounts even when zero.

## Success Criteria

- Resolver returns all required fields for valid inputs.
- `resolution_type` is one of the allowed categories.
- `confidence` is a float between 0.0 and 1.0.
- The returned resolution can be interpreted by downstream policy and action components.

## Assumptions

- Prompt templates are defined in `prompts/system_prompts.py` and represent the desired business logic.
- Downstream components may enforce policy and guardrail checks before actions.

## Known Gaps

- No direct unit tests currently mock `resolver()` LLM behavior.
- Module-level `llm` initialization makes test injection more difficult.
