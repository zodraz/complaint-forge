import logging

from otel import add_event, function_trace, record_metric, set_attribute
from tools.salesforce_tool import (
    create_replacement_order,
    issue_credit,
    process_refund,
)

logger = logging.getLogger(__name__)


@function_trace()
def action_agent(state: dict) -> dict:
    """
    Executes real-world actions (refunds, credits, etc.)
    """
    resolution = state.get("resolution", {})
    actions_taken = []

    resolution_type = resolution.get("resolution_type")
    refund_amount = resolution.get("refund_amount", 0)

    set_attribute("action.resolution_type", resolution_type)

    # Execute refund if needed
    if resolution_type in ["full_refund", "partial_refund"] and refund_amount > 0:
        refund_result = process_refund(
            customer_history=state.get("customer_history", {}),
            amount=refund_amount,
            reason=resolution.get("action_needed"),
        )

        actions_taken.append({
            "action": "create_salesforce_refund_case",
            "amount": refund_amount,
            "result": refund_result
        })

        record_metric("action.refund_amount", refund_amount)
        add_event("ActionTaken", {
            "action": "refund",
            "amount": refund_amount,
            "status": refund_result.get("status") if isinstance(refund_result, dict) else refund_result,
        })
        logger.info("Refund case created in Salesforce", extra={"amount": refund_amount, "status": refund_result.get("status", ""), "case_id": refund_result.get("case_id", "")})

    # Credit action
    if resolution.get("credit_amount", 0) > 0:
        credit_result = issue_credit(
            customer_history=state.get("customer_history", {}),
            amount=resolution["credit_amount"],
            reason=resolution.get("action_needed"),
        )
        actions_taken.append({
            "action": "create_salesforce_credit_case",
            "amount": resolution["credit_amount"],
            "result": credit_result
        })

        record_metric("action.credit_amount", resolution["credit_amount"])
        add_event("ActionTaken", {
            "action": "credit",
            "amount": resolution["credit_amount"],
            "status": credit_result.get("status") if isinstance(credit_result, dict) else credit_result,
        })
        logger.info("Credit case created in Salesforce", extra={"amount": resolution["credit_amount"], "status": credit_result.get("status", "")})

    # Replacement action
    if resolution_type == "replacement":
        replacement_result = create_replacement_order(state.get("customer_history", {}))
        actions_taken.append({
            "action": "create_salesforce_replacement_case",
            "result": replacement_result
        })

        add_event("ActionTaken", {
            "action": "replacement",
            "status": replacement_result.get("status") if isinstance(replacement_result, dict) else replacement_result,
        })
        logger.info("Replacement order task created in Salesforce", extra={"status": replacement_result.get("status", "")})

    # Log escalation
    if resolution_type == "escalate":
        reason = resolution.get("action_needed")
        actions_taken.append({
            "action": "escalate_to_human",
            "reason": reason
        })

        add_event("ActionTaken", {
            "action": "escalate_to_human",
            "reason": (reason[:255] if isinstance(reason, str) else reason),
        })
        logger.warning("Escalating to human review", extra={"reason": str(resolution.get("action_needed", ""))[:255]})

    set_attribute("action.actions_count", len(actions_taken))
    record_metric("action.actions_per_complaint", len(actions_taken))

    return {"actions_taken": actions_taken}
