import stripe
from config import STRIPE_API_KEY

stripe.api_key = STRIPE_API_KEY

def process_refund(charge_id: str, amount: int = None) -> dict:
    """Process refund in Stripe"""
    try:
        refund = stripe.Refund.create(
            charge=charge_id,
            amount=amount  # in cents
        )
        return {"status": "success", "refund_id": refund.id, "amount": refund.amount}
    except Exception as e:
        return {"status": "error", "message": str(e)}