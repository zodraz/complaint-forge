# quickstart.md — Outbound Communication Validation

## Prerequisites
- Python 3.10+ virtualenv activated
- `AZURE_OPENAI_*` env vars for LLM tests (if running end-to-end)
- `SENDGRID_API_KEY` and `TWILIO_*` test credentials (or use mocks)

## Run unit tests (fast)

```powershell
# from repo root
python -B -m unittest tests.test_communication_node -v
```

## Run integration test with mocks

```powershell
# example: run a single integration test file with mocked SendGrid/Twilio
python -B -m unittest tests.test_tools.SendGridTwilioIntegrationTest -v
```

## Manual end-to-end (local)
1. Start FastAPI server:

```powershell
uvicorn main_fastapi:app --reload --port 8000
```

2. POST a test payload to the communication endpoint (example using `http` file or curl):

```powershell
curl -X POST http://localhost:8000/communications -H "Content-Type: application/json" -d '{"correlation_id":"<uuid>","recipient_email":"test@example.com","subject":"Test","body_text":"Hello"}'
```

3. Observe workflow trace in logs; verify `DeliveryRecord` events and audit log entries.

## Expected outcomes
- On success: `delivered_email` final_status and a DeliveryAttempt with provider `sendgrid` and status `success`.
- On bounce: `delivered_sms` final_status with an SMS attempt recorded.
- On dual failure: final_status `failed` and human-review interrupt triggered.
