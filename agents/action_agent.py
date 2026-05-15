from tools.stripe_tool import process_refund

def _find_charge_id(history: dict) -> str | None:
    if not isinstance(history, dict):
        return None

    for key in ("charge_id", "stripe_charge_id"):
        if history.get(key):
            return history[key]

    for deal in history.get("deals", []):
        properties = deal.get("properties", {}) if isinstance(deal, dict) else {}
        for key in ("charge_id", "stripe_charge_id"):
            if properties.get(key):
                return properties[key]

    return None

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
        charge_id = _find_charge_id(state.get("customer_history", {}))
        if charge_id:
            refund_result = process_refund(
                charge_id=charge_id,
                amount=int(refund_amount * 100)  # convert to cents
            )
        else:
            refund_result = {
                "status": "skipped",
                "message": "No Stripe charge ID found in customer history"
            }

        actions_taken.append({
            "action": "refund",
            "amount": refund_amount,
            "result": refund_result
        })
    
    # Credit action (simulate)
    if resolution.get("credit_amount", 0) > 0:
        actions_taken.append({
            "action": "issue_credit",
            "amount": resolution["credit_amount"],
            "status": "success"
        })
    
    # Replacement action
    if resolution_type == "replacement":
        actions_taken.append({
            "action": "create_replacement_order",
            "status": "success"
        })
    
    # Log escalation
    if resolution_type == "escalate":
        actions_taken.append({
            "action": "escalate_to_human",
            "reason": resolution.get("action_needed")
        })
    
    return {"actions_taken": actions_taken}
