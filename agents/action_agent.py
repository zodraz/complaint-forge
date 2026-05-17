from tools.salesforce_tool import (
    create_replacement_order,
    issue_credit,
    process_refund,
)

def action_agent(state: dict) -> dict:
    """
    Executes real-world actions (refunds, credits, etc.)
    """
    resolution = state.get("resolution", {})
    actions_taken = []
    
    resolution_type = resolution.get("resolution_type")
    refund_amount = resolution.get("refund_amount", 0)
    
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
    
    # Credit action (simulate)
    if resolution.get("credit_amount", 0) > 0:
        actions_taken.append({
            "action": "create_salesforce_credit_case",
            "amount": resolution["credit_amount"],
            "result": issue_credit(
                customer_history=state.get("customer_history", {}),
                amount=resolution["credit_amount"],
                reason=resolution.get("action_needed"),
            )
        })
    
    # Replacement action
    if resolution_type == "replacement":
        actions_taken.append({
            "action": "create_salesforce_replacement_case",
            "result": create_replacement_order(state.get("customer_history", {}))
        })
    
    # Log escalation
    if resolution_type == "escalate":
        actions_taken.append({
            "action": "escalate_to_human",
            "reason": resolution.get("action_needed")
        })
    
    return {"actions_taken": actions_taken}
