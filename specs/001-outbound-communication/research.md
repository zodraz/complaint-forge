# research.md — Outbound Communication

## Decisions

- SMS provider: Twilio (chosen).
- Email failure definition: SendGrid permanent bounce events trigger immediate SMS fallback.
- Retry policy: No automatic retries for other transient HTTP errors by default; behavior must be configurable via environment variables.

## Rationale

- Twilio is a widely used, reliable SMS provider with clear APIs and good Python SDK support.
- Permanent bounces represent a definitive delivery failure; immediate SMS fallback reduces time-to-notification for customers.
- Making retry behavior configurable allows operators to tune conservatism vs. speed.

## Alternatives Considered

- AWS SNS: lower cost in some regions but different feature set; chosen alternative if organization prefers AWS.
- Immediate fallback on 4xx/5xx: rejected by default to avoid unnecessary SMS for transient issues; can be enabled via configuration.

## Action Items

- Implement `tools/sendgrid_tool.py` and `tools/twilio_tool.py` or adapt existing tools following `tools/*` patterns.
- Add configuration entries in `config.py` for `SENDGRID_API_KEY`, `TWILIO_*`, `COMM_AGENT_RETRY_POLICY`.
- Add unit and integration tests covering success, bounce, transient failures, and idempotence.
