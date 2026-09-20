"""Action service — coordinates resolution actions and logs audit events.

All actions taken by the service layer are audit-logged in the `actions` database table.
Strictly enforces missing data rules (e.g. flight inventory = 'not available').
"""
from typing import Any
from sqlalchemy.orm import Session

from models.action import Action
import repositories.action_repo as action_repo
import services.escalation_service as escalation_service


def request_rebooking(
    db: Session,
    *,
    customer_id: int | None = None,
    booking_id: int | None = None,
    conversation_id: int | None = None,
    customer_tier: str | None = None,
) -> Action:
    """Records a rebooking request.

    Note: Alternative-flight inventory is not available in current data.
    Does NOT invent a fake flight or flight number.
    """
    priority = customer_tier in ["Gold", "Platinum"]
    details: dict[str, Any] = {
        "flight_inventory": "not available",
        "next_available_within_24h": True,
        "priority_rebooking": priority,
    }

    return action_repo.create(
        db,
        action_type="REBOOK_REQUEST",
        details_json=details,
        conversation_id=conversation_id,
        customer_id=customer_id,
        booking_id=booking_id,
    )


def issue_meal_voucher(
    db: Session,
    *,
    delay_minutes: int,
    customer_id: int | None = None,
    booking_id: int | None = None,
    conversation_id: int | None = None,
) -> Action:
    """Records issuance of a meal voucher entitlement.

    Note: Meal voucher currency amount is not available in supplied policy.
    """
    details: dict[str, Any] = {
        "delay_minutes": delay_minutes,
        "amount": "not available",
    }

    return action_repo.create(
        db,
        action_type="MEAL_VOUCHER",
        details_json=details,
        conversation_id=conversation_id,
        customer_id=customer_id,
        booking_id=booking_id,
    )


def grant_lounge_access(
    db: Session,
    *,
    delay_minutes: int,
    customer_id: int | None = None,
    booking_id: int | None = None,
    conversation_id: int | None = None,
) -> Action:
    """Records granting of lounge access for delays > 3h."""
    details: dict[str, Any] = {
        "delay_minutes": delay_minutes,
        "lounge": "not available",
    }

    return action_repo.create(
        db,
        action_type="LOUNGE_ACCESS",
        details_json=details,
        conversation_id=conversation_id,
        customer_id=customer_id,
        booking_id=booking_id,
    )


def arrange_hotel_for_delayed_hours(
    db: Session,
    *,
    delay_minutes: int,
    customer_id: int | None = None,
    booking_id: int | None = None,
    conversation_id: int | None = None,
) -> Action:
    """Records hotel arrangement for delays > 5h.

    Coverage is strictly for delayed hours only (NOT a full night).
    """
    details: dict[str, Any] = {
        "delay_minutes": delay_minutes,
        "coverage": "delayed hours only",
        "hotel_name": "not available",
    }

    return action_repo.create(
        db,
        action_type="HOTEL_DELAYED_HOURS",
        details_json=details,
        conversation_id=conversation_id,
        customer_id=customer_id,
        booking_id=booking_id,
    )


def request_refund(
    db: Session,
    *,
    payment_method: str = "original payment method",
    customer_id: int | None = None,
    booking_id: int | None = None,
    conversation_id: int | None = None,
) -> Action | None:
    """Records a full refund request to the original payment method.

    If a different payment method is requested, creates a DIFFERENT_PAYMENT_METHOD escalation
    and rejects refund action processing.
    """
    normalized_method = payment_method.strip().lower()
    if normalized_method != "original payment method":
        escalation_service.create_escalation(
            db,
            reason_code="DIFFERENT_PAYMENT_METHOD",
            summary=f"Customer requested refund to alternative payment method '{payment_method}'.",
            conversation_id=conversation_id,
            customer_id=customer_id,
            booking_id=booking_id,
        )
        return None

    details: dict[str, Any] = {
        "payment_method": "original payment method",
        "timeline": "7 business days",
        "amount": "full refund",
    }

    return action_repo.create(
        db,
        action_type="REFUND_REQUEST",
        details_json=details,
        conversation_id=conversation_id,
        customer_id=customer_id,
        booking_id=booking_id,
    )
