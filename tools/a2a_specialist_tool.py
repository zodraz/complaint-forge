import logging
import os
import time
from typing import Any

import requests
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout

from otel import add_event, function_trace, record_metric, set_attribute

logger = logging.getLogger(__name__)

A2A_SPECIALIST_URL = os.getenv("A2A_SPECIALIST_URL")
A2A_SPECIALIST_AUTH_TOKEN = os.getenv("A2A_SPECIALIST_AUTH_TOKEN")


@function_trace()
def request_specialist_review(state: dict[str, Any]) -> dict[str, Any]:
    """Call the external A2A specialist service for an escalation recommendation."""
    if not A2A_SPECIALIST_URL:
        add_event("A2ASpecialistCall", {"status": "skipped", "reason": "not_configured"})
        logger.warning("A2A specialist URL not configured, skipping")
        return {
            "status": "skipped",
            "reason": "A2A_SPECIALIST_URL is not configured",
        }

    headers = {"Accept": "application/json"}
    if A2A_SPECIALIST_AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {A2A_SPECIALIST_AUTH_TOKEN}"

    payload = {
        "complaint": state.get("complaint"),
        "triage": state.get("triage", {}),
        "customer_email": state.get("customer_email"),
        "customer_phone": state.get("customer_phone"),
        "order_id": state.get("order_id"),
        "customer_history": state.get("customer_history", {}),
        "analysis": state.get("analysis", {}),
        "resolution": state.get("resolution", {}),
        "policy_result": state.get("policy_result", {}),
        "eval_results": state.get("eval_results", {}),
        "actions_taken": state.get("actions_taken", []),
    }

    url = A2A_SPECIALIST_URL.rstrip("/") + "/tasks/refund-specialist"
    max_retries = 3
    backoff_factor = 1

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=60,
            )
            response.raise_for_status()
            result = response.json()
            set_attribute("a2a.attempt_count", attempt)
            set_attribute("a2a.status", "success")
            record_metric("a2a.retry_count", attempt)
            add_event("A2ASpecialistCall", {"status": "success", "attempt": attempt})
            logger.info("A2A specialist call succeeded", extra={"attempt": attempt, "url": str(A2A_SPECIALIST_URL or "")})
            return result
        except (Timeout, ConnectionError) as e:
            if attempt == max_retries:
                logger.error("A2A specialist call timed out after all retries", extra={"attempt": attempt, "url": str(A2A_SPECIALIST_URL or ""), "error": str(e)[:255]})
                return {
                    "status": "error",
                    "message": f"Temporary A2A outage after {attempt} retries: {e}",
                    "service_url": A2A_SPECIALIST_URL,
                    "retry_attempts": attempt,
                    "fallback": "retry_exhausted",
                }
        except HTTPError as e:
            response = getattr(e, "response", None)
            if response is not None and 500 <= response.status_code < 600 and attempt < max_retries:
                pass
            else:
                logger.error("A2A specialist call HTTP error", extra={"attempt": attempt, "error": str(e)[:255]})
                return {
                    "status": "error",
                    "message": f"A2A service error: {e}",
                    "service_url": A2A_SPECIALIST_URL,
                    "retry_attempts": attempt,
                }
        except RequestException as e:
            return {
                "status": "error",
                "message": str(e),
                "service_url": A2A_SPECIALIST_URL,
                "retry_attempts": attempt,
            }

        sleep_seconds = backoff_factor * attempt
        time.sleep(sleep_seconds)

    set_attribute("a2a.status", "exhausted")
    record_metric("a2a.retry_count", max_retries)
    add_event("A2ASpecialistCall", {"status": "error", "attempt": max_retries, "reason": "retry_exhausted"})
    logger.error("A2A specialist unavailable after all retries", extra={"max_retries": max_retries, "url": str(A2A_SPECIALIST_URL or "")})
    return {
        "status": "error",
        "message": "A2A specialist service unavailable after retries",
        "service_url": A2A_SPECIALIST_URL,
        "retry_attempts": max_retries,
        "fallback": "retry_exhausted",
    }
