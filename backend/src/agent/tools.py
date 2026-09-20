"""LangChain tools wrapping service and repository layer functions."""

from typing import Any
from langchain_core.tools import tool
from sqlalchemy.orm import Session

from models.booking import Booking
import repositories.booking_repo as booking_repo
import services.action_service as action_service
import services.escalation_service as escalation_service
import services.rules_engine as rules_engine


def _get_db_from_context(kwargs: dict[str, Any]) -> Session | None:
    return kwargs.get("db")


@tool
def get_booking_status(customer_id: int, pnr: str, db: Any = None) -> dict[str, Any]:
    """Retrieves booking status for a given customer ID and PNR.

    Enforces customer ownership verification.
    """
    if not db:
        return {"error": "not available"}

    bookings = db.query(Booking).filter(Booking.pnr == pnr).all()
    if not bookings:
        return {"error": "not available"}

    # Verify ownership
    user_bookings = [b for b in bookings if b.customer_id == customer_id]
    if not user_bookings:
        return {"error": "not available"}

    result = []
    for b in user_bookings:
        result.append({
            "pnr": b.pnr,
            "segment_label": b.segment_label,
            "flight_no": b.flight_no if b.flight_no else "not available",
            "route": b.route,
            "flight_date": str(b.flight_date),
            "sched_dep": str(b.sched_dep),
            "status": b.status,
            "delay_minutes": b.delay_minutes if b.delay_minutes is not None else "not available",
            "new_dep": str(b.new_dep) if b.new_dep else "not available",
            "cause": b.cause if b.cause else "not available",
        })
    return {"bookings": result}


@tool
def evaluate_delay(delay_minutes: int) -> dict[str, Any]:
    """Evaluates disruption policy entitlements for flight delay minutes."""
    decision = rules_engine.evaluate_delay(delay_minutes)
    return {
        "status": decision.status,
        "entitlements": decision.entitlements,
        "reason_code": decision.reason_code,
        "customer_safe_explanation": decision.customer_safe_explanation,
    }


@tool
def evaluate_cancellation(customer_id: int, pnr: str, db: Any = None) -> dict[str, Any]:
    """Evaluates cancellation policy entitlements for a customer's PNR."""
    if not db:
        return {"status": "escalate", "reason_code": "NOT_AVAILABLE"}

    bookings = db.query(Booking).filter(Booking.pnr == pnr, Booking.customer_id == customer_id).all()
    if not bookings:
        return {"status": "escalate", "reason_code": "NOT_AVAILABLE"}

    # Evaluate outbound segment or first cancelled segment
    target_booking = next((b for b in bookings if str(b.status).lower() == "cancelled"), bookings[0])
    decision = rules_engine.evaluate_cancellation(target_booking)
    return {
        "status": decision.status,
        "entitlements": decision.entitlements,
        "reason_code": decision.reason_code,
        "customer_safe_explanation": decision.customer_safe_explanation,
    }


@tool
def rebook(
    customer_id: int,
    booking_id: int | None = None,
    customer_tier: str | None = None,
    db: Any = None,
) -> dict[str, Any]:
    """Logs a rebooking request for the next available flight within 24 hours."""
    if not db:
        return {"error": "not available"}

    action = action_service.request_rebooking(
        db, customer_id=customer_id, booking_id=booking_id, customer_tier=customer_tier
    )
    return {
        "action_type": action.action_type,
        "details_json": action.details_json,
        "status": "logged",
    }


@tool
def issue_voucher_lounge(
    customer_id: int,
    delay_minutes: int,
    booking_id: int | None = None,
    db: Any = None,
) -> dict[str, Any]:
    """Issues meal voucher and/or lounge access based on delay policy evaluation."""
    if not db:
        return {"error": "not available"}

    actions = []
    if delay_minutes >= 0:
        mv_action = action_service.issue_meal_voucher(
            db, delay_minutes=delay_minutes, customer_id=customer_id, booking_id=booking_id
        )
        actions.append(mv_action.action_type)

    if delay_minutes > 180:
        lounge_action = action_service.grant_lounge_access(
            db, delay_minutes=delay_minutes, customer_id=customer_id, booking_id=booking_id
        )
        actions.append(lounge_action.action_type)

    return {"issued_actions": actions, "status": "logged"}


@tool
def arrange_hotel(
    customer_id: int,
    delay_minutes: int,
    booking_id: int | None = None,
    db: Any = None,
) -> dict[str, Any]:
    """Arranges hotel accommodation covering ONLY delayed hours for delays over 5 hours (>300 min)."""
    if not db:
        return {"error": "not available"}

    if delay_minutes <= 300:
        rules_engine.record_decision_trace(
            rule="hotel_eligibility",
            inputs={"delay_minutes": delay_minutes},
            outcome="Hotel accommodation is not authorized for delays of 5 hours or less.",
            reason_code="HOTEL_NOT_ELIGIBLE_UNDER_5H",
        )
        return {
            "status": "denied",
            "message": "Hotel accommodation is not authorized for delays of 5 hours or less.",
        }

    action = action_service.arrange_hotel_for_delayed_hours(
        db, delay_minutes=delay_minutes, customer_id=customer_id, booking_id=booking_id
    )
    return {
        "action_type": action.action_type,
        "details_json": action.details_json,
        "status": "logged",
    }


@tool
def request_refund(
    customer_id: int,
    payment_method: str = "original payment method",
    booking_id: int | None = None,
    db: Any = None,
) -> dict[str, Any]:
    """Processes a full refund request to original payment method."""
    if not db:
        return {"error": "not available"}

    action = action_service.request_refund(
        db, payment_method=payment_method, customer_id=customer_id, booking_id=booking_id
    )
    if not action:
        rules_engine.record_decision_trace(
            rule="request_refund",
            inputs={"payment_method": payment_method},
            outcome="escalate",
            reason_code="DIFFERENT_PAYMENT_METHOD",
        )
        return {
            "status": "escalated",
            "reason_code": "DIFFERENT_PAYMENT_METHOD",
            "message": "Refund to alternative payment method requires human escalation.",
        }

    return {
        "action_type": action.action_type,
        "details_json": action.details_json,
        "status": "logged",
    }


@tool
def check_fare_difference(amount: float) -> dict[str, Any]:
    """Evaluates policy for voluntary rebooking fare difference."""
    decision = rules_engine.evaluate_fare_difference(amount)
    return {
        "status": decision.status,
        "entitlements": decision.entitlements,
        "reason_code": decision.reason_code,
        "customer_safe_explanation": decision.customer_safe_explanation,
    }


@tool
def escalate_to_human(
    customer_id: int,
    reason_code: str,
    summary: str,
    booking_id: int | None = None,
    conversation_id: int | None = None,
    db: Any = None,
) -> dict[str, Any]:
    """Escalates a request to human agent review.

    Supported reason codes:
      - COMPENSATION_BEYOND_POLICY
      - FARE_WAIVER_ABOVE_1500
      - NON_AIRLINE_CAUSED
      - LEGAL_OR_FORMAL_COMPLAINT
      - DIFFERENT_PAYMENT_METHOD
    """
    rules_engine.record_decision_trace(
        rule="escalate_to_human",
        inputs={"reason_code": reason_code, "summary": summary},
        outcome="escalate",
        reason_code=reason_code,
    )
    if not db:
        return {
            "status": "escalated",
            "reason_code": reason_code,
            "message": "I'm escalating this to our specialist support team right now, and they'll reach out to you directly.",
        }

    esc = escalation_service.create_escalation(
        db,
        reason_code=reason_code,
        summary=summary,
        customer_id=customer_id,
        booking_id=booking_id,
        conversation_id=conversation_id,
    )
    return {
        "escalation_id": esc.id,
        "reason_code": esc.reason_code,
        "status": esc.status,
        "message": "I'm escalating this to our specialist support team right now, and they'll reach out to you directly.",
    }



AGENT_TOOLS = [
    get_booking_status,
    evaluate_delay,
    evaluate_cancellation,
    rebook,
    issue_voucher_lounge,
    arrange_hotel,
    request_refund,
    check_fare_difference,
    escalate_to_human,
]
