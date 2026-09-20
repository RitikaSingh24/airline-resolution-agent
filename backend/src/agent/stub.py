"""Agent abstraction interface and stub implementation."""

import datetime
from sqlalchemy.orm import Session

from models.message import Message
from schemas.chat import MessageResponse


class AgentInterface:
    """Abstract interface for agent implementations."""

    def respond(
        self, db: Session, conversation_id: int, content: str
    ) -> MessageResponse:
        raise NotImplementedError


class StubAgent(AgentInterface):
    """Stub agent providing a deterministic fallback response.

    Does NOT determine airline policy or replace future LLM agent logic.
    """

    def respond(
        self, db: Session, conversation_id: int, content: str
    ) -> MessageResponse:
        # Save user message
        user_msg = Message(
            conversation_id=conversation_id,
            role="user",
            content=content,
            created_at=datetime.datetime.utcnow(),
        )
        db.add(user_msg)

        placeholder_reply = (
            "Thank you for contacting airline customer support. "
            "Our automated resolution agent is processing your request."
        )

        # Save assistant reply
        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=placeholder_reply,
            created_at=datetime.datetime.utcnow(),
        )
        db.add(assistant_msg)
        db.commit()

        return MessageResponse(
            reply=placeholder_reply,
            actions_taken=[],
            escalation=False,
            conversation_id=conversation_id,
        )


stub_agent = StubAgent()
