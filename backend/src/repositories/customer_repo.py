"""Customer repository — pure CRUD, no business logic."""
from sqlalchemy.orm import Session

from models.customer import Customer


def create(db: Session, *, name: str, tier: str, email: str,
           phone_masked: str, flights_12m: int, prior_complaints: int,
           complaint_note: str | None = None) -> Customer:
    customer = Customer(
        name=name,
        tier=tier,
        email=email,
        phone_masked=phone_masked,
        flights_12m=flights_12m,
        prior_complaints=prior_complaints,
        complaint_note=complaint_note,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def get_by_id(db: Session, customer_id: int) -> Customer | None:
    return db.query(Customer).filter(Customer.id == customer_id).first()


def get_by_email(db: Session, email: str) -> Customer | None:
    return db.query(Customer).filter(Customer.email == email).first()


def list_all(db: Session, skip: int = 0, limit: int = 100) -> list[Customer]:
    return db.query(Customer).offset(skip).limit(limit).all()


def update(db: Session, customer_id: int, **kwargs) -> Customer | None:
    customer = get_by_id(db, customer_id)
    if customer is None:
        return None
    for key, value in kwargs.items():
        if hasattr(customer, key):
            setattr(customer, key, value)
    db.commit()
    db.refresh(customer)
    return customer


def delete(db: Session, customer_id: int) -> bool:
    customer = get_by_id(db, customer_id)
    if customer is None:
        return False
    db.delete(customer)
    db.commit()
    return True
