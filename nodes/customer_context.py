import newrelic.agent

from tools.salesforce_tool import get_customer_history


@newrelic.agent.function_trace()
def customer_context(state: dict) -> dict:
    email = state.get("customer_email")
    order_id = state.get("order_id")
    history = get_customer_history(email, order_id=order_id) if email else {}
    phone = history.get("phone") or state.get("customer_phone") or state.get("recipient_phone")

    customer_found = bool(history and not history.get("error"))
    has_prior_cases = bool(history.get("has_prior_cases"))
    has_prior_return_orders = bool(history.get("has_prior_return_orders"))
    repeat_customer = bool(history.get("repeat_customer"))
    total_recent_cases = history.get("total_recent_cases", 0)
    total_recent_opportunities = history.get("total_recent_opportunities", 0)
    lookup_error = bool(history.get("error"))

    newrelic.agent.add_custom_attribute("customer.found", customer_found)
    newrelic.agent.add_custom_attribute("customer.has_prior_cases", has_prior_cases)
    newrelic.agent.add_custom_attribute("customer.has_prior_return_orders", has_prior_return_orders)
    newrelic.agent.add_custom_attribute("customer.repeat_customer", repeat_customer)
    newrelic.agent.add_custom_attribute("customer.total_recent_cases", total_recent_cases)

    newrelic.agent.record_custom_metric("Custom/Customer/TotalRecentCases", total_recent_cases)

    newrelic.agent.record_custom_event("CustomerContextLookup", {
        "customer_found": customer_found,
        "has_prior_cases": has_prior_cases,
        "has_prior_return_orders": has_prior_return_orders,
        "repeat_customer": repeat_customer,
        "total_recent_cases": total_recent_cases,
        "total_recent_opportunities": total_recent_opportunities,
        "lookup_error": lookup_error,
    })

    if customer_found:
        newrelic.agent.record_log_event("Customer context loaded from Salesforce", level="INFO", attributes={"has_prior_cases": history.get("has_prior_cases", False), "repeat_customer": history.get("repeat_customer", False), "total_cases": history.get("total_recent_cases", 0)})
    elif history.get("error"):
        newrelic.agent.record_log_event("Salesforce customer lookup failed", level="ERROR", attributes={"error": str(history.get("error",""))[:255], "email": str(email or "")})
    else:
        newrelic.agent.record_log_event("Customer not found in Salesforce", level="WARNING", attributes={"email": str(email or "")})

    return {
        "customer_email": email,
        "customer_phone": phone,
        "order_id": order_id,
        "customer_history": history,
        "customer_context_result": {
            "source": "salesforce",
            "customer_found": customer_found,
        },
    }
