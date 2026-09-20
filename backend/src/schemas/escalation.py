"""Escalation Pydantic schemas."""

import datetime
from pydantic import BaseModel, ConfigDict


class EscalationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reason_code: str
    summary: str
    status: str
    conversation_id: int | None = None
    customer_id: int | None = None
    booking_id: int | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
