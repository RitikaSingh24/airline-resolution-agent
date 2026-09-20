"""Chat and conversation Pydantic schemas."""

import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict


class CreateConversationRequest(BaseModel):
    customer_id: int


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime


from services.decision_collector import DecisionTraceItem


class CreateMessageRequest(BaseModel):
    content: str


class MessageResponse(BaseModel):
    reply: str
    actions_taken: list[dict[str, Any]] = []
    escalation: bool = False
    conversation_id: int | None = None
    decision_trace: list[DecisionTraceItem] = []

