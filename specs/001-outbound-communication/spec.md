# Outbound Communication

**Short name**: outbound-communication

## Summary

Add outbound communication that delivers the final customer-facing response via email and falls back to SMS if the email delivery fails. The workflow should use SendGrid for sending email messages, and SMS should use a configurable provider.

## Background

Resolver/responder produce the final response text and a resolution. This feature centralizes outbound delivery: first attempt email, on durable email failure send SMS, and log outcomes for auditing and retries.

## Actors

- System: complaint handling workflow
- Outbound Communication: the new workflow component
- External providers: SendGrid (email), configurable SMS provider
- Human reviewer (for escalations)

## User Scenarios

1. Successful email
   - Input: Responder produces final message and customer's email address
   - Flow: Outbound communication sends email via SendGrid; provider returns success; update workflow with delivered status; no SMS sent.
   - Acceptance: Customer receives email; system records delivery timestamp.

2. Email fails, SMS fallback
   - Input: Responder produces final message, customer's email and phone
   - Flow: SendGrid returns a permanent failure (or other failure condition); the node attempts SMS via configured provider; SMS succeeds; update workflow with delivered-via-SMS status and reason for email failure.
   - Acceptance: Customer receives SMS; system records both attempts and final status.

3. Both channels fail
   - Flow: Email fails and SMS also fails; the node marks communication as failed and triggers retry policy or human review per policy/guardrails.

## Functional Requirements (testable)

1. The node accepts a message payload containing: subject, body (plain/text + optional HTML), recipient email, recipient phone, and correlation id.
   - Test: Unit test constructing payload and verifying validation errors for missing required fields.

2. Email sending via SendGrid
   - The node must call SendGrid with provided subject/body and recipient email and handle synchronous success/failure responses.
   - Test: Integration test stub/mock SendGrid and assert correct API call parameters and handling of success and error responses.

3. Failure detection and classification
   - The node must distinguish between transient and permanent email failures (configurable thresholds) and treat permanent failures as immediate triggers for SMS fallback.
   - Test: Simulate SendGrid error responses and assert fallback behavior.

4. SMS fallback
   - On classified permanent email failure, the node must call the configured SMS provider with an SMS-friendly message and recipient phone.
   - Test: Mock SMS provider and assert call made only when email fallback condition met.

5. Idempotence and deduplication
   - The node must be idempotent for repeated delivery attempts for the same correlation id.
   - Test: Re-run with same correlation id and verify no duplicate sends recorded.

6. Audit logging
   - Record each outbound attempt with timestamp, provider response, and final status in the workflow trace.
   - Test: Verify persisted log entries after send attempts.

7. Configurability
   - Email sender address, SMS provider, retry counts, and classification rules must be configurable via environment or config file.
   - Test: Load configuration overrides and verify behavior.

## Assumptions

- When customer's phone is missing, and email fails, the node marks communication as failed and triggers human-review interrupt.
- Default SMS provider will be Twilio unless the customer requests an alternative.
- Sender email will use a company-managed address; templates are provided by the responder.

## Success Criteria (measurable)

- 99% of successful deliveries are completed on first attempt (email or SMS) in normal conditions.
- When email fails permanently, SMS fallback completes within 30 seconds of failure detection 95% of the time.
- Audit logs show delivery status for 100% of messages processed by this node.
- No duplicate messages are delivered for the same correlation id.

## Key Entities

- CommunicationPayload: {correlation_id, subject, body_text, body_html?, recipient_email?, recipient_phone?, metadata}
- DeliveryAttempt: {timestamp, channel, provider, provider_response, status, attempt_number}
- DeliveryRecord: {correlation_id, final_status, attempts[]}

## Acceptance Criteria

- Specified functional requirements 1–7 are implemented and covered by unit and integration tests.
- Spec does not include implementation technology choices beyond provider names.

## Decisions

- **SMS provider**: Twilio (chosen). The node will use Twilio as the default SMS provider for fallback delivery unless overridden in configuration.

- **Email failure definition & retry policy**: A permanent bounce event from SendGrid (bounce) will be treated as a definitive email failure and will trigger immediate SMS fallback. No additional retries are attempted for other transient HTTP errors by default. These behaviors must be configurable.

## Notes

- SendGrid will be used for email; the node must use the existing `tools/` integration pattern and a new `tools/sendgrid_tool.py` client if one doesn't already exist.
 - SendGrid will be used for email; the node must integrate with SendGrid through a configurable provider client (implementation details such as file paths are out of scope for this spec).
