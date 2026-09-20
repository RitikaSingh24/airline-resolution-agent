"""Conversation repository — pure CRUD, no business logic."""
import datetime

from sqlalchemy.orm import Session

from models.conversation import Conversation


def create(db: Session, *, customer_id: int) -> Conversation:
    now = datetime.datetime.utcnow()
    conversation = Conversation(
        customer_id=customer_id,
        created_at=now,
        updated_at=now,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_by_id(db: Session, conversation_id: int) -> Conversation | None:
    return db.query(Conversation).filter(Conversation.id == conversation_id).first()


def list_by_customer(db: Session, customer_id: int) -> list[Conversation]:
    return (
        db.query(Conversation)
        .filter(Conversation.customer_id == customer_id)
        .order_by(Conversation.created_at.desc())
        .all()
    )


def update(db: Session, conversation_id: int, **kwargs) -> Conversation | None:
    conversation = get_by_id(db, conversation_id)
    if conversation is None:
        return None
    for key, value in kwargs.items():
        if hasattr(conversation, key):
            setattr(conversation, key, value)
    conversation.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(conversation)
    return conversation


def delete(db: Session, conversation_id: int) -> bool:
    conversation = get_by_id(db, conversation_id)
    if conversation is None:
        return False
    db.delete(conversation)
    db.commit()
    return True
