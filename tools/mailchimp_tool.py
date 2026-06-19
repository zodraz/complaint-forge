import os
from typing import Any

try:
    import mailchimp_transactional as MailchimpTransactional
except ImportError:
    MailchimpTransactional = None

MAILCHIMP_API_KEY = os.getenv("MAILCHIMP_API_KEY")
MAILCHIMP_FROM_EMAIL = os.getenv("MAILCHIMP_FROM_EMAIL")
MAILCHIMP_TIMEOUT = float(os.getenv("MAILCHIMP_TIMEOUT", "30"))


def _missing_config(channel: str) -> list[str]:
    required = {
        "MAILCHIMP_API_KEY": MAILCHIMP_API_KEY,
        "MAILCHIMP_FROM_EMAIL": MAILCHIMP_FROM_EMAIL if channel == "email" else None,
    }
    return [name for name, value in required.items() if value is None]


def _classify_mailchimp_error(error_code: int | str) -> str:
    """Classify Mailchimp error codes as success, permanent_failure, or transient_failure."""
    error_code_int = int(error_code) if isinstance(error_code, str) else error_code
    
    # 4xx errors (except 429) are permanent failures
    if 400 <= error_code_int < 500 and error_code_int != 429:
        return "permanent_failure"
    # 5xx errors and 429 (rate limit) are transient failures
    if error_code_int >= 500 or error_code_int == 429:
        return "transient_failure"
    # 2xx are success (handled separately)
    if 200 <= error_code_int < 300:
        return "success"
    return "transient_failure"


def send_email(
    *,
    subject: str,
    body_text: str,
    body_html: str | None,
    to_email: str,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Send an email through Mailchimp Transactional API using the official SDK."""
    missing = _missing_config("email")
    if missing:
        return {
            "status": "error",
            "provider": "mailchimp",
            "provider_response": {
                "error": "Missing Mailchimp configuration",
                "missing_config": missing,
            },
        }

    if not MailchimpTransactional:
        return {
            "status": "error",
            "provider": "mailchimp",
            "provider_response": {
                "error": "mailchimp_transactional SDK not installed. Install with: pip install mailchimp-transactional",
            },
        }

    try:
        client = MailchimpTransactional.Client()
        client.set_default_client(MAILCHIMP_API_KEY)

        message = {
            "from_email": MAILCHIMP_FROM_EMAIL,
            "subject": subject,
            "text": body_text,
            "to": [{"email": to_email, "type": "to"}],
        }

        if body_html:
            message["html"] = body_html

        if correlation_id:
            message["metadata"] = {"correlation_id": correlation_id}

        # Send the email using the SDK
        response = client.messages.send({"message": message})

        # Extract status from response
        if response and len(response) > 0:
            result = response[0]
            status_value = result.get("status", "")

            if status_value == "sent" or status_value == "queued":
                return {
                    "status": "success",
                    "provider": "mailchimp",
                    "provider_response": {
                        "id": result.get("_id"),
                        "status": status_value,
                    },
                }
            elif status_value == "rejected":
                return {
                    "status": "permanent_failure",
                    "provider": "mailchimp",
                    "provider_response": {
                        "id": result.get("_id"),
                        "status": status_value,
                        "reason": result.get("reject_reason"),
                    },
                }
            else:
                return {
                    "status": "transient_failure",
                    "provider": "mailchimp",
                    "provider_response": result,
                }

        return {
            "status": "error",
            "provider": "mailchimp",
            "provider_response": {"error": "Empty response from Mailchimp"},
        }

    except Exception as exc:
        error_str = str(exc)
        # Check if this is a known error type from the SDK
        if hasattr(exc, "status") or hasattr(exc, "error_code"):
            error_code = getattr(exc, "error_code", getattr(exc, "status", None))
            status = _classify_mailchimp_error(error_code) if error_code else "transient_failure"
        else:
            status = "transient_failure"

        return {
            "status": status,
            "provider": "mailchimp",
            "provider_response": {"error": error_str},
        }


def send_sms(*, to: str, message: str) -> dict[str, Any]:
    """Send an SMS through Mailchimp Transactional SMS API using the official SDK."""
    missing = _missing_config("sms")
    if missing:
        return {
            "status": "error",
            "provider": "mailchimp",
            "provider_response": {
                "error": "Missing Mailchimp configuration",
                "missing_config": missing,
            },
        }

    if not MailchimpTransactional:
        return {
            "status": "error",
            "provider": "mailchimp",
            "provider_response": {
                "error": "mailchimp_transactional SDK not installed. Install with: pip install mailchimp-transactional",
            },
        }

    try:
        client = MailchimpTransactional.Client()
        client.set_default_client(MAILCHIMP_API_KEY)

        sms_message = {
            "from_name": "System",
            "to": to,
            "text": message,
        }

        # Send the SMS using the SDK
        response = client.messages_sms.send({"message": sms_message})

        # Extract status from response
        if response and len(response) > 0:
            result = response[0]
            status_value = result.get("state", "")

            if status_value == "sent" or status_value == "queued":
                return {
                    "status": "success",
                    "provider": "mailchimp",
                    "provider_response": {
                        "id": result.get("_id"),
                        "state": status_value,
                    },
                }
            elif status_value == "rejected" or status_value == "failed":
                return {
                    "status": "permanent_failure",
                    "provider": "mailchimp",
                    "provider_response": {
                        "id": result.get("_id"),
                        "state": status_value,
                        "reason": result.get("reason"),
                    },
                }
            else:
                return {
                    "status": "transient_failure",
                    "provider": "mailchimp",
                    "provider_response": result,
                }

        return {
            "status": "error",
            "provider": "mailchimp",
            "provider_response": {"error": "Empty response from Mailchimp"},
        }

    except Exception as exc:
        error_str = str(exc)
        # Check if this is a known error type from the SDK
        if hasattr(exc, "status") or hasattr(exc, "error_code"):
            error_code = getattr(exc, "error_code", getattr(exc, "status", None))
            status = _classify_mailchimp_error(error_code) if error_code else "transient_failure"
        else:
            status = "transient_failure"

        return {
            "status": status,
            "provider": "mailchimp",
            "provider_response": {"error": error_str},
        }
