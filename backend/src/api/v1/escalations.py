"""Escalation API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.session import get_db
import repositories.escalation_repo as escalation_repo
from schemas.escalation import EscalationResponse

router = APIRouter(tags=["Escalations"])


@router.get(
    "/escalations",
    response_model=list[EscalationResponse],
    summary="List Escalations",
    description="Retrieve all support escalation records for human agent review.",
)
def list_escalations(db: Session = Depends(get_db)) -> list[EscalationResponse]:
    """Retrieves all escalation records."""
    return escalation_repo.list_all(db)
