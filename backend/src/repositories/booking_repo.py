"""Booking repository — pure CRUD, no business logic."""
import datetime

from sqlalchemy.orm import Session

from models.booking import Booking


def create(db: Session, *, pnr: str, customer_id: int, segment_label: str,
           route: str, flight_date: datetime.date, sched_dep: datetime.time,
           status: str, cause: str | None = None, flight_no: str | None = None,
           delay_minutes: int | None = None,
           new_dep: datetime.time | None = None) -> Booking:
    booking = Booking(
        pnr=pnr,
        customer_id=customer_id,
        segment_label=segment_label,
        flight_no=flight_no,
        route=route,
        flight_date=flight_date,
        sched_dep=sched_dep,
        status=status,
        delay_minutes=delay_minutes,
        new_dep=new_dep,
        cause=cause,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def get_by_id(db: Session, booking_id: int) -> Booking | None:
    return db.query(Booking).filter(Booking.id == booking_id).first()


def get_by_pnr(db: Session, pnr: str) -> list[Booking]:
    return db.query(Booking).filter(Booking.pnr == pnr).all()


def list_by_customer(db: Session, customer_id: int) -> list[Booking]:
    return db.query(Booking).filter(Booking.customer_id == customer_id).all()


def update(db: Session, booking_id: int, **kwargs) -> Booking | None:
    booking = get_by_id(db, booking_id)
    if booking is None:
        return None
    for key, value in kwargs.items():
        if hasattr(booking, key):
            setattr(booking, key, value)
    db.commit()
    db.refresh(booking)
    return booking


def delete(db: Session, booking_id: int) -> bool:
    booking = get_by_id(db, booking_id)
    if booking is None:
        return False
    db.delete(booking)
    db.commit()
    return True
