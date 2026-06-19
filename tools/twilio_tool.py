import os
from typing import Any

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")
TWILIO_TIMEOUT = float(os.getenv("TWILIO_TIMEOUT", "30"))


def _missing_config() -> list[str]:
    return [
        name
        for name, value in {
            "TWILIO_ACCOUNT_SID": TWILIO_ACCOUNT_SID,
            "TWILIO_AUTH_TOKEN": TWILIO_AUTH_TOKEN,
            "TWILIO_FROM_NUMBER": TWILIO_FROM_NUMBER,
        }.items()
        if not value
    ]


def send_sms(*, to: str, message: str) -> dict[str, Any]:
    """Send an SMS through Twilio."""
    missing = _missing_config()
    if missing:
        return {
            "status": "error",
            "provider": "twilio",
            "provider_response": {
                "error": "Missing Twilio configuration",
                "missing_config": missing,
            },
        }

    try:
        from twilio.base.exceptions import TwilioRestException
        from twilio.rest import Client
    except ImportError as exc:
        return {
            "status": "error",
            "provider": "twilio",
            "provider_response": {
                "error": f"Twilio dependency is not installed: {exc}",
            },
        }

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, timeout=TWILIO_TIMEOUT)

    try:
        message_result = client.messages.create(
            body=message,
            from_=TWILIO_FROM_NUMBER,
            to=to,
        )
        return {
            "status": "success",
            "provider": "twilio",
            "provider_response": {
                "sid": getattr(message_result, "sid", None),
                "status": getattr(message_result, "status", None),
            },
        }
    except TwilioRestException as exc:
        return {
            "status": "error",
            "provider": "twilio",
            "provider_response": {"error": str(exc)},
        }
    except Exception as exc:
        return {
            "status": "error",
            "provider": "twilio",
            "provider_response": {"error": str(exc)},
        }
