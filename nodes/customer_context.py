from tools.salesforce_tool import get_customer_history


def customer_context(state: dict) -> dict:
    email = state.get("customer_email")
    order_id = state.get("order_id")
    history = get_customer_history(email, order_id=order_id) if email else {}
    phone = history.get("phone") or state.get("customer_phone") or state.get("recipient_phone")

    return {
        "customer_email": email,
        "customer_phone": phone,
        "order_id": order_id,
        "customer_history": history,
        "customer_context_result": {
            "source": "salesforce",
            "customer_found": bool(history and not history.get("error")),
        },
    }
