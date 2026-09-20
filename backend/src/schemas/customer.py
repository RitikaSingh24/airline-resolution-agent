"""Customer Pydantic schemas."""

from pydantic import BaseModel, ConfigDict


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    tier: str
    email: str
    phone_masked: str
    flights_12m: int
    prior_complaints: int
    complaint_note: str | None = None
