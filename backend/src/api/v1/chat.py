"""Chat, conversation, and action API endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from agent.agent import real_agent
from core.exceptions import NotFoundException
from db.session import get_db
import repositories.action_repo as action_repo
import repositories.conversation_repo as conversation_repo
import repositories.customer_repo as customer_repo
from schemas.action import ActionResponse
from schemas.chat import (
    ConversationResponse,
    CreateConversationRequest,
    CreateMessageRequest,
    MessageResponse,
)

router = APIRouter(tags=["Conversations & Chat"])


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Conversation",
    description="Initiates a new customer support conversation.",
)
def create_conversation(
    payload: CreateConversationRequest, db: Session = Depends(get_db)
) -> ConversationResponse:
    """Validates customer existence and creates a new conversation."""
    customer = customer_repo.get_by_id(db, payload.customer_id)
    if not customer:
        raise NotFoundException(message="Customer not found")

    return conversation_repo.create(db, customer_id=payload.customer_id)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    summary="Send Chat Message",
    description="Sends a customer message to the resolution agent.",
)
def send_message(
    conversation_id: int,
    payload: CreateMessageRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Processes customer chat message and returns assistant resolution response."""
    conversation = conversation_repo.get_by_id(db, conversation_id)
    if not conversation:
        raise NotFoundException(message="Conversation not found")

    return real_agent.respond(
        db, conversation_id=conversation_id, content=payload.content
    )


@router.get(
    "/conversations/{conversation_id}/actions",
    response_model=list[ActionResponse],
    summary="Get Conversation Actions",
    description="Retrieve all audited resolution actions taken in a conversation.",
)
def get_conversation_actions(
    conversation_id: int, db: Session = Depends(get_db)
) -> list[ActionResponse]:
    """Retrieves audit action records for the given conversation ID."""
    conversation = conversation_repo.get_by_id(db, conversation_id)
    if not conversation:
        raise NotFoundException(message="Conversation not found")

    return action_repo.list_by_conversation(db, conversation_id)
