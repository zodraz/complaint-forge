import os
from typing import Any

import requests

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL")
SENDGRID_TIMEOUT = float(os.getenv("SENDGRID_TIMEOUT", "30"))


def _missing_config() -> list[str]:
    return [
        name
        for name, value in {
            "SENDGRID_API_KEY": SENDGRID_API_KEY,
            "SENDGRID_FROM_EMAIL": SENDGRID_FROM_EMAIL,
        }.items()
        if not value
    ]


def _classify_response(response: requests.Response) -> str:
    if 200 <= response.status_code < 300:
        return "success"
    if 400 <= response.status_code < 500:
        return "permanent_failure"
    return "transient_failure"


def send_email(
    *,
    subject: str,
    body_text: str,
    body_html: str | None,
    to_email: str,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Send an email through SendGrid and classify the response."""
    missing = _missing_config()
    if missing:
        return {
            "status": "error",
            "provider": "sendgrid",
            "provider_response": {
                "error": "Missing SendGrid configuration",
                "missing_config": missing,
            },
        }

    payload = {
        "personalizations": [
            {
                "to": [{"email": to_email}],
                "subject": subject,
            }
        ],
        "from": {"email": SENDGRID_FROM_EMAIL},
        "content": [{"type": "text/plain", "value": body_text}],
    }

    if body_html:
        payload["content"].append({"type": "text/html", "value": body_html})

    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json",
    }

    if correlation_id:
        headers["X-Message-ID"] = correlation_id

    try:
        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            json=payload,
            headers=headers,
            timeout=SENDGRID_TIMEOUT,
        )
        status = _classify_response(response)
        provider_response = {
            "status_code": response.status_code,
            "body": response.text,
        }

        if status == "success":
            return {
                "status": "success",
                "provider": "sendgrid",
                "provider_response": provider_response,
            }

        return {
            "status": status,
            "provider": "sendgrid",
            "provider_response": provider_response,
        }
    except requests.RequestException as exc:
        return {
            "status": "transient_failure",
            "provider": "sendgrid",
            "provider_response": {"error": str(exc)},
        }
