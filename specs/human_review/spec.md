# Human Review Node

status: migrated

## Summary

`nodes/human_review.py` invokes `langgraph.types.interrupt` to pause the workflow for manual human review. It returns the review payload, audit actions, and a `final_response` fallback if the interrupt result is not a dict.

## User Scenarios

- As a system, when a case needs human approval, the workflow interrupts and sends a review payload that includes complaint, customer history, analysis, and escalation details.
- As a system, when the human review returns a modified `final_response`, the node propagates it.
- As a system, when the interrupt returns a non-dict response, the node still provides a fallback `final_response`.

## Requirements

- Invoke `interrupt()` with a payload containing `reason`, `complaint`, `customer_email`, `order_id`, `customer_history`, `analysis`, `resolution`, and `specialist_review`.
- Return `human_review` with the interrupt result.
- Include `actions_taken` with an `escalate_to_human` action entry.
- Provide `final_response` from the review if available, otherwise use a fallback message.

## Success Criteria

- The node always returns `human_review` and `actions_taken`.
- If interrupt returns a dict with `final_response`, that response is used.
- If interrupt returns another type, fallback response text is returned.

## Assumptions

- LangGraph `interrupt` behaves as expected in this workflow environment.
- Human review payloads may be persisted outside the local workflow state.

## Known Gaps

- No direct tests simulate `langgraph.types.interrupt` behavior.
