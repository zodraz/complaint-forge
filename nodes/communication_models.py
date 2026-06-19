from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator


class CommunicationPayload(BaseModel):
    correlation_id: str
    subject: str
    body_text: str
    body_html: str | None = None
    recipient_email: str | None = None
    recipient_phone: str | None = None
    metadata: dict[str, Any] | None = None


class DeliveryAttempt(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    channel: str
    provider: str
    provider_response: dict[str, Any]
    status: str
    attempt_number: int


class DeliveryRecord(BaseModel):
    correlation_id: str
    final_status: str
    attempts: list[DeliveryAttempt] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
