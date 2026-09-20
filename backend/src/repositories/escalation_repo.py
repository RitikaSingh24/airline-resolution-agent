"""Escalation repository — CRUD with status-update support.

Escalation decision logic belongs in the future services layer.
This repository only stores and retrieves escalation records.
"""
import datetime

from sqlalchemy.orm import Session

from models.escalation import Escalation


def create(db: Session, *, reason_code: str, summary: str,
           status: str = "open",
           conversation_id: int | None = None,
           customer_id: int | None = None,
           booking_id: int | None = None) -> Escalation:
    now = datetime.datetime.utcnow()
    escalation = Escalation(
        reason_code=reason_code,
        summary=summary,
        status=status,
        conversation_id=conversation_id,
        customer_id=customer_id,
        booking_id=booking_id,
        created_at=now,
        updated_at=now,
    )
    db.add(escalation)
    db.commit()
    db.refresh(escalation)
    return escalation


def get_by_id(db: Session, escalation_id: int) -> Escalation | None:
    return db.query(Escalation).filter(Escalation.id == escalation_id).first()


def list_all(db: Session, skip: int = 0, limit: int = 100) -> list[Escalation]:
    return (
        db.query(Escalation)
        .order_by(Escalation.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def list_by_conversation(db: Session, conversation_id: int) -> list[Escalation]:
    return (
        db.query(Escalation)
        .filter(Escalation.conversation_id == conversation_id)
        .order_by(Escalation.created_at.asc())
        .all()
    )


def update(db: Session, escalation_id: int, **kwargs) -> Escalation | None:
    escalation = get_by_id(db, escalation_id)
    if escalation is None:
        return None
    for key, value in kwargs.items():
        if hasattr(escalation, key):
            setattr(escalation, key, value)
    escalation.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(escalation)
    return escalation
