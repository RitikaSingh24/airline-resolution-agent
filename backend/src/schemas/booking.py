"""Booking Pydantic schemas."""

import datetime
from pydantic import BaseModel, ConfigDict


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pnr: str
    customer_id: int
    segment_label: str
    flight_no: str | None = None
    route: str
    flight_date: datetime.date
    sched_dep: datetime.time
    status: str
    delay_minutes: int | None = None
    new_dep: datetime.time | None = None
    cause: str | None = None
