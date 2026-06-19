# research.md — Outbound Communication

## Decisions

- SMS provider: Mailchimp Transactional SMS API via official SDK (chosen).
- Email provider: Mailchimp Transactional Email API via official SDK (chosen).
- Email failure definition: Mailchimp rejected status or permanent errors trigger immediate SMS fallback.
- Retry policy: No automatic retries for transient HTTP errors by default; behavior configurable via environment variables.
- Integration approach: Use official `mailchimp_transactional` Python SDK instead of REST API calls.

## Rationale

- Using the official `mailchimp_transactional` SDK provides better type safety, error handling, and future compatibility compared to direct REST API calls.
- Mailchimp Transactional API provides both email and SMS through a unified platform, reducing operational complexity.
- Permanent rejections represent a definitive delivery failure; immediate SMS fallback reduces time-to-notification for customers.
- Making retry behavior configurable allows operators to tune conservatism vs. speed.

## Alternatives Considered

- AWS SNS: lower cost in some regions but different feature set; chosen alternative if organization prefers AWS.
- Immediate fallback on 4xx/5xx: rejected by default to avoid unnecessary SMS for transient issues; can be enabled via configuration.

## Action Items

- Implement `tools/mailchimp_tool.py` with `send_email()` and `send_sms()` functions using the `mailchimp_transactional` SDK.
- Add configuration entries in `config.py` for `MAILCHIMP_API_KEY`, `MAILCHIMP_FROM_EMAIL`, `MAILCHIMP_TIMEOUT`.
- Add `mailchimp-transactional` to `requirements.txt` for SDK dependency.
- Add unit and integration tests covering success, rejection, transient failures, and idempotence.
