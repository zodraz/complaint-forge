# data-model.md — Outbound Communication

## Entities

### CommunicationPayload
- `correlation_id`: `str` (UUID) — primary id for dedup and idempotence
- `subject`: `str` — email subject
- `body_text`: `str` — plain text body
- `body_html`: `str?` — optional HTML body
- `recipient_email`: `str?` — RFC-validated email
- `recipient_phone`: `str?` — E.164-formatted phone number
- `metadata`: `dict[str, Any]?` — optional additional context (order id, email template id)

Validation rules:
- At least one of `recipient_email` or `recipient_phone` must be present
- `correlation_id` must be a UUID
- `body_text` required

### DeliveryAttempt
- `timestamp`: `datetime` (UTC)
- `channel`: `"email" | "sms"`
- `provider`: `str` (e.g., "sendgrid", "twilio")
- `provider_response`: `dict` — raw provider response for auditing
- `status`: `"success" | "permanent_failure" | "transient_failure" | "timeout"`
- `attempt_number`: `int`

### DeliveryRecord
- `correlation_id`: `str` (UUID)
- `final_status`: `"delivered_email" | "delivered_sms" | "failed"`
- `attempts`: `list[DeliveryAttempt]`
- `last_updated`: `datetime`

## State transitions
- Initial -> EmailAttempted -> (EmailSucceeded -> DeliveredEmail)
- EmailAttempted -> (PermanentFailure -> SmsAttempted -> DeliveredSms)
- EmailAttempted -> (TransientFailure -> Retry per policy -> SmsAttempted if exhausted)
- SmsAttempted -> (Success -> DeliveredSms) or (Failure -> Failed)

## Storage
- Short-term in-memory store during workflow execution (MemorySaver)
- Persist DeliveryRecord in workflow trace and observational logs
- For production, write DeliveryRecord to PostgreSQL Case/Task for auditability
