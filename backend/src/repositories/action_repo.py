"""Action repository — audit-record creation and retrieval only.

Actions are immutable audit records; no update/delete operations are exposed.
"""
import datetime
from typing import Any

from sqlalchemy.orm import Session

from models.action import Action


def create(db: Session, *, action_type: str,
           details_json: dict[str, Any] | None = None,
           conversation_id: int | None = None,
           customer_id: int | None = None,
           booking_id: int | None = None) -> Action:
    action = Action(
        action_type=action_type,
        details_json=details_json,
        conversation_id=conversation_id,
        customer_id=customer_id,
        booking_id=booking_id,
        created_at=datetime.datetime.utcnow(),
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    return action


def get_by_id(db: Session, action_id: int) -> Action | None:
    return db.query(Action).filter(Action.id == action_id).first()


def list_all(db: Session, skip: int = 0, limit: int = 100) -> list[Action]:
    return (
        db.query(Action)
        .order_by(Action.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def list_by_conversation(db: Session, conversation_id: int) -> list[Action]:
    return (
        db.query(Action)
        .filter(Action.conversation_id == conversation_id)
        .order_by(Action.created_at.asc())
        .all()
    )
