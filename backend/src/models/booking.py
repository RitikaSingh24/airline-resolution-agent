"""Booking model — stores flight booking/segment data."""
import datetime

from sqlalchemy import Date, ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        # Prevents duplicate seeded booking segments.
        UniqueConstraint("pnr", "segment_label", name="uq_booking_pnr_segment"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pnr: Mapped[str] = mapped_column(String, nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=False
    )
    segment_label: Mapped[str] = mapped_column(String, nullable=False)
    flight_no: Mapped[str | None] = mapped_column(String, nullable=True)
    route: Mapped[str] = mapped_column(String, nullable=False)
    flight_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    sched_dep: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    delay_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    new_dep: Mapped[datetime.time | None] = mapped_column(Time, nullable=True)
    cause: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationships
    customer: Mapped["Customer"] = relationship(  # noqa: F821
        "Customer", back_populates="bookings"
    )

    def __repr__(self) -> str:
        return (
            f"<Booking id={self.id} pnr={self.pnr!r} "
            f"segment={self.segment_label!r} status={self.status!r}>"
        )
