"""Escalation service — manages creation and tracking of support escalations.

Supported standard reason codes:
  - COMPENSATION_BEYOND_POLICY
  - FARE_WAIVER_ABOVE_1500
  - NON_AIRLINE_CAUSED
  - LEGAL_OR_FORMAL_COMPLAINT
  - DIFFERENT_PAYMENT_METHOD
"""
from sqlalchemy.orm import Session

from models.escalation import Escalation
import repositories.escalation_repo as escalation_repo

REQUIRED_REASON_CODES = {
    "COMPENSATION_BEYOND_POLICY",
    "FARE_WAIVER_ABOVE_1500",
    "NON_AIRLINE_CAUSED",
    "LEGAL_OR_FORMAL_COMPLAINT",
    "DIFFERENT_PAYMENT_METHOD",
}


def create_escalation(
    db: Session,
    *,
    reason_code: str,
    summary: str,
    status: str = "OPEN",
    conversation_id: int | None = None,
    customer_id: int | None = None,
    booking_id: int | None = None,
) -> Escalation:
    """Creates a new escalation record for human agent review."""
    return escalation_repo.create(
        db,
        reason_code=reason_code,
        summary=summary,
        status=status,
        conversation_id=conversation_id,
        customer_id=customer_id,
        booking_id=booking_id,
    )
