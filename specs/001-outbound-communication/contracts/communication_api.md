# contracts/communication_api.md

## POST /communications
Creates a delivery request and enqueues the outbound communication workflow.

Request JSON schema (Pydantic model `CommunicationRequest`):

```python
class CommunicationRequest(BaseModel):
    correlation_id: UUID
    subject: str
    body_text: str
    body_html: Optional[str] = None
    recipient_email: Optional[EmailStr] = None
    recipient_phone: Optional[str] = None  # E.164
    metadata: Optional[dict] = None

    @root_validator
    def at_least_one_recipient(cls, values):
        if not (values.get('recipient_email') or values.get('recipient_phone')):
            raise ValueError('At least one recipient (email or phone) is required')
        return values
```

Responses:
- `202 Accepted` — Payload accepted; header `Location` points to workflow status URL
- `400 Bad Request` — Validation error
- `500 Internal Server Error` — Unexpected processing error

Workflow state contract:
- Response includes `thread_id` and `status_url` for polling

Example request:
```json
{
  "correlation_id": "11111111-2222-3333-4444-555555555555",
  "subject": "Order update",
  "body_text": "Your refund is processed",
  "recipient_email": "customer@example.com"
}
```
