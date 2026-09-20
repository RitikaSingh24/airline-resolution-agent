"""Action audit Pydantic schemas."""

import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict


class ActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action_type: str
    details_json: dict[str, Any] | None = None
    conversation_id: int | None = None
    customer_id: int | None = None
    booking_id: int | None = None
    created_at: datetime.datetime
