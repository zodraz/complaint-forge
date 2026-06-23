from __future__ import annotations

import logging
from typing import Any

from langgraph.types import interrupt
from nodes.communication_models import CommunicationPayload, DeliveryAttempt, DeliveryRecord
from otel import add_event, function_trace, record_metric, set_attribute
from tools.mailchimp_tool import send_email, send_sms
from config import OUTBOUND_COMMUNICATION_ENABLED

logger = logging.getLogger(__name__)


def _build_sms_message(payload: CommunicationPayload) -> str:
    return (
        f"{payload.subject}\n\n{payload.body_text[:300]}"
        + ("\n\nReply for more details." if len(payload.body_text) > 300 else "")
    )


def _record_attempt(
    record: DeliveryRecord,
    channel: str,
    provider: str,
    provider_response: dict[str, Any],
    status: str,
) -> None:
    record.attempts.append(
        DeliveryAttempt(
            channel=channel,
            provider=provider,
            provider_response=provider_response,
            status=status,
            attempt_number=len(record.attempts) + 1,
        )
    )
    record.last_updated = record.attempts[-1].timestamp


@function_trace()
def communication_node(state: dict[str, Any]) -> dict[str, Any]:
    """Send a final communication via email then SMS fallback on permanent failure."""
    if not OUTBOUND_COMMUNICATION_ENABLED:
        set_attribute("delivery.final_status", "skipped")
        add_event("CommunicationDelivery", {"final_status": "skipped", "channel": "none", "outbound_enabled": False})
        logger.info("Outbound communication skipped (feature flag disabled)", extra={"correlation_id": state.get("correlation_id", "")})
        return {
            "delivery_record": DeliveryRecord(
                correlation_id=state.get("correlation_id", ""),
                final_status="skipped",
            )
        }

    payload = CommunicationPayload(
        correlation_id=state.get("correlation_id", ""),
        subject=state.get("subject", "Customer update"),
        body_text=state.get("response_draft") or state.get("final_response", ""),
        body_html=state.get("response_html"),
        recipient_email=state.get("customer_email"),
        recipient_phone=state.get("recipient_phone") or state.get("customer_phone"),
        metadata=state.get("metadata"),
    )

    existing_record = state.get("delivery_record")
    if existing_record and existing_record.get("correlation_id") == payload.correlation_id:
        return {"delivery_record": existing_record}

    record = DeliveryRecord(correlation_id=payload.correlation_id, final_status="pending")

    if payload.recipient_email:
        email_result = send_email(
            subject=payload.subject,
            body_text=payload.body_text,
            body_html=payload.body_html,
            to_email=str(payload.recipient_email),
            correlation_id=payload.correlation_id,
        )
        _record_attempt(
            record,
            channel="email",
            provider=email_result.get("provider", "mailchimp"),
            provider_response=email_result.get("provider_response", {}),
            status=email_result.get("status", "error"),
        )

        if email_result.get("status") == "success":
            record.final_status = "delivered_email"
            set_attribute("delivery.final_status", "delivered_email")
            set_attribute("delivery.channel", "email")
            record_metric("communication.delivered_email", 1)
            add_event("CommunicationDelivery", {"final_status": "delivered_email", "channel": "email"})
            logger.info("Email delivered successfully", extra={"correlation_id": payload.correlation_id, "to_email": str(payload.recipient_email)})
            return {"delivery_record": record}

        if email_result.get("status") == "permanent_failure" and payload.recipient_phone:
            sms_message = _build_sms_message(payload)
            sms_result = send_sms(to=str(payload.recipient_phone), message=sms_message)
            _record_attempt(
                record,
                channel="sms",
                provider=sms_result.get("provider", "mailchimp"),
                provider_response=sms_result.get("provider_response", {}),
                status=sms_result.get("status", "error"),
            )

            if sms_result.get("status") == "success":
                record.final_status = "delivered_sms"
                set_attribute("delivery.final_status", "delivered_sms")
                set_attribute("delivery.channel", "sms")
                record_metric("communication.delivered_sms", 1)
                add_event("CommunicationDelivery", {"final_status": "delivered_sms", "channel": "sms"})
                logger.info("SMS delivered successfully", extra={"correlation_id": payload.correlation_id})
                return {"delivery_record": record}

        if email_result.get("status") == "permanent_failure":
            record.final_status = "failed"
            set_attribute("delivery.final_status", "failed")
            record_metric("communication.delivery_failed", 1)
            logger.error("Communication delivery failed", extra={"correlation_id": payload.correlation_id, "reason": "permanent_failure or no recipient"})
            review = interrupt({
                "reason": "Communication failed after email bounce",
                "delivery_record": record.model_dump(),
            })
            return {
                "delivery_record": record,
                "human_review": review,
            }

    if payload.recipient_phone and not payload.recipient_email:
        sms_message = _build_sms_message(payload)
        sms_result = send_sms(to=str(payload.recipient_phone), message=sms_message)
        _record_attempt(
            record,
            channel="sms",
            provider=sms_result.get("provider", "mailchimp"),
            provider_response=sms_result.get("provider_response", {}),
            status=sms_result.get("status", "error"),
        )

        if sms_result.get("status") == "success":
            record.final_status = "delivered_sms"
            set_attribute("delivery.final_status", "delivered_sms")
            set_attribute("delivery.channel", "sms")
            record_metric("communication.delivered_sms", 1)
            add_event("CommunicationDelivery", {"final_status": "delivered_sms", "channel": "sms"})
            logger.info("SMS delivered successfully", extra={"correlation_id": payload.correlation_id})
            return {"delivery_record": record}

        record.final_status = "failed"
        set_attribute("delivery.final_status", "failed")
        record_metric("communication.delivery_failed", 1)
        logger.error("Communication delivery failed", extra={"correlation_id": payload.correlation_id, "reason": "permanent_failure or no recipient"})
        review = interrupt({
            "reason": "SMS communication failed",
            "delivery_record": record.model_dump(),
        })
        return {
            "delivery_record": record,
            "human_review": review,
        }

    record.final_status = "failed"
    set_attribute("delivery.final_status", "failed")
    record_metric("communication.delivery_failed", 1)
    logger.error("Communication delivery failed", extra={"correlation_id": payload.correlation_id, "reason": "permanent_failure or no recipient"})
    review = interrupt({
        "reason": "No valid recipient available for communication",
        "delivery_record": record.model_dump(),
    })
    return {
        "delivery_record": record,
        "human_review": review,
    }
