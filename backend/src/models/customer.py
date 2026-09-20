"""Customer model — stores airline customer profile data."""
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    tier: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    phone_masked: Mapped[str] = mapped_column(String, nullable=False)
    flights_12m: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    prior_complaints: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    complaint_note: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationships (populated by the future service/API layer)
    bookings: Mapped[list["Booking"]] = relationship(  # noqa: F821
        "Booking", back_populates="customer", lazy="select"
    )
    conversations: Mapped[list["Conversation"]] = relationship(  # noqa: F821
        "Conversation", back_populates="customer", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Customer id={self.id} email={self.email!r} tier={self.tier!r}>"
