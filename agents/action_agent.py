import newrelic.agent
from tools.salesforce_tool import (
    create_replacement_order,
    issue_credit,
    process_refund,
)

@newrelic.agent.function_trace()
def action_agent(state: dict) -> dict:
    """
    Executes real-world actions (refunds, credits, etc.)
    """
    resolution = state.get("resolution", {})
    actions_taken = []

    resolution_type = resolution.get("resolution_type")
    refund_amount = resolution.get("refund_amount", 0)

    newrelic.agent.add_custom_attribute("action.resolution_type", resolution_type)

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

        newrelic.agent.record_custom_metric("Custom/Action/RefundAmount", refund_amount)
        newrelic.agent.record_custom_event("ActionTaken", {
            "action": "refund",
            "amount": refund_amount,
            "status": refund_result.get("status") if isinstance(refund_result, dict) else refund_result,
        })
        newrelic.agent.record_log_event("Refund case created in Salesforce", level="INFO", attributes={"amount": refund_amount, "status": refund_result.get("status",""), "case_id": refund_result.get("case_id","")})

    # Credit action (simulate)
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

        newrelic.agent.record_custom_metric("Custom/Action/CreditAmount", resolution["credit_amount"])
        newrelic.agent.record_custom_event("ActionTaken", {
            "action": "credit",
            "amount": resolution["credit_amount"],
            "status": credit_result.get("status") if isinstance(credit_result, dict) else credit_result,
        })
        newrelic.agent.record_log_event("Credit case created in Salesforce", level="INFO", attributes={"amount": resolution["credit_amount"], "status": credit_result.get("status","")})

    # Replacement action
    if resolution_type == "replacement":
        replacement_result = create_replacement_order(state.get("customer_history", {}))
        actions_taken.append({
            "action": "create_salesforce_replacement_case",
            "result": replacement_result
        })

        newrelic.agent.record_custom_event("ActionTaken", {
            "action": "replacement",
            "status": replacement_result.get("status") if isinstance(replacement_result, dict) else replacement_result,
        })
        newrelic.agent.record_log_event("Replacement order task created in Salesforce", level="INFO", attributes={"status": replacement_result.get("status","")})

    # Log escalation
    if resolution_type == "escalate":
        reason = resolution.get("action_needed")
        actions_taken.append({
            "action": "escalate_to_human",
            "reason": reason
        })

        newrelic.agent.record_custom_event("ActionTaken", {
            "action": "escalate_to_human",
            "reason": (reason[:255] if isinstance(reason, str) else reason),
        })
        newrelic.agent.record_log_event("Escalating to human review", level="WARNING", attributes={"reason": str(resolution.get("action_needed",""))[:255]})

    newrelic.agent.add_custom_attribute("action.actions_count", len(actions_taken))
    newrelic.agent.record_custom_metric("Custom/Action/ActionsPerComplaint", len(actions_taken))

    return {"actions_taken": actions_taken}
