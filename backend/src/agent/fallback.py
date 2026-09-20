"""Deterministic fallback response generator.

Generates safe, policy-compliant customer responses directly from database records,
rules_engine evaluations, actions, and escalations without using an LLM.
"""

from typing import Any
from sqlalchemy.orm import Session

from models.booking import Booking
from models.customer import Customer
import repositories.action_repo as action_repo
import repositories.booking_repo as booking_repo
import repositories.customer_repo as customer_repo
import repositories.escalation_repo as escalation_repo
import services.action_service as action_service
import services.escalation_service as escalation_service
from services.decision_collector import record_decision_trace
from services.rules_engine import (
    classify_request,
    detect_legal_threat,
    evaluate_cancellation,
    evaluate_delay,
    evaluate_fare_difference,
)


def generate_fallback_response(
    db: Session,
    customer_id: int,
    conversation_id: int,
    content: str,
) -> dict[str, Any]:
    """Generates a deterministic resolution response without calling an LLM."""
    customer = customer_repo.get_by_id(db, customer_id)
    if not customer:
        return {
            "reply": "I'm escalating this to our specialist support team right now, and they'll reach out to you directly.",
            "actions_taken": [],
            "escalation": True,
        }

    # 1. Pre-LLM Legal Threat Check
    if detect_legal_threat(content):
        esc = escalation_service.create_escalation(
            db,
            reason_code="LEGAL_OR_FORMAL_COMPLAINT",
            summary=f"Legal threat or formal complaint in customer message: '{content}'",
            customer_id=customer_id,
            conversation_id=conversation_id,
        )
        return {
            "reply": "I'm escalating this to our specialist support team right now, and they'll reach out to you directly.",
            "actions_taken": [],
            "escalation": True,
        }

    # Retrieve customer bookings
    bookings = booking_repo.list_by_customer(db, customer_id)
    if not bookings:
        return {
            "reply": "No booking records were found for your account. Please contact support.",
            "actions_taken": [],
            "escalation": False,
        }

    reply_parts: list[str] = []
    actions_taken: list[dict[str, Any]] = []
    escalated = False

    content_lower = content.lower()

    # Target relevant booking
    cancelled_booking = next((b for b in bookings if str(b.status).lower() == "cancelled"), None)
    delayed_booking = next((b for b in bookings if b.delay_minutes and b.delay_minutes > 0), None)

    # Process Cancellation Scenario
    if cancelled_booking and ("cancel" in content_lower or "refund" in content_lower or "rebook" in content_lower):
        canc_decision = evaluate_cancellation(cancelled_booking)
        if canc_decision.status == "allowed":
            reply_parts.append(canc_decision.customer_safe_explanation)

            if "refund" in content_lower:
                if "gpay" in content_lower or "paytm" in content_lower or "cash" in content_lower or "upi" in content_lower:
                    esc = escalation_service.create_escalation(
                        db,
                        reason_code="DIFFERENT_PAYMENT_METHOD",
                        summary="Customer requested refund to alternative payment method.",
                        customer_id=customer_id,
                        booking_id=cancelled_booking.id,
                        conversation_id=conversation_id,
                    )
                    escalated = True
                    reply_parts.append("Requests for refunds to alternative payment methods require human agent review.")
                else:
                    action = action_service.request_refund(
                        db, payment_method="original payment method", customer_id=customer_id, booking_id=cancelled_booking.id, conversation_id=conversation_id
                    )
                    if action:
                        actions_taken.append({"action_type": action.action_type, "details": action.details_json})

            if "rebook" in content_lower:
                action = action_service.request_rebooking(
                    db, customer_id=customer_id, booking_id=cancelled_booking.id, conversation_id=conversation_id, customer_tier=customer.tier
                )
                actions_taken.append({"action_type": action.action_type, "details": action.details_json})

    # Process Delay Scenario
    elif delayed_booking or "delay" in content_lower or "voucher" in content_lower or "hotel" in content_lower or "lounge" in content_lower:
        target_b = delayed_booking if delayed_booking else bookings[0]
        delay_mins = target_b.delay_minutes if target_b.delay_minutes is not None else 0

        delay_decision = evaluate_delay(delay_mins)
        if delay_decision.status == "allowed":
            reply_parts.append(delay_decision.customer_safe_explanation)

            # Issue meal voucher
            mv_act = action_service.issue_meal_voucher(
                db, delay_minutes=delay_mins, customer_id=customer_id, booking_id=target_b.id, conversation_id=conversation_id
            )
            actions_taken.append({"action_type": mv_act.action_type, "details": mv_act.details_json})

            # Issue lounge access if > 180 min
            if delay_mins > 180:
                lounge_act = action_service.grant_lounge_access(
                    db, delay_minutes=delay_mins, customer_id=customer_id, booking_id=target_b.id, conversation_id=conversation_id
                )
                actions_taken.append({"action_type": lounge_act.action_type, "details": lounge_act.details_json})

            # Issue hotel if > 300 min (5h)
            if delay_mins > 300:
                hotel_act = action_service.arrange_hotel_for_delayed_hours(
                    db, delay_minutes=delay_mins, customer_id=customer_id, booking_id=target_b.id, conversation_id=conversation_id
                )
                actions_taken.append({"action_type": hotel_act.action_type, "details": hotel_act.details_json})

    # Handle Beyond-Policy Requests (e.g. upgrades, full night hotel, fare waivers)
    if "upgrade" in content_lower or "business" in content_lower:
        upg_dec = classify_request("business_class_upgrade", customer.tier)
        esc = escalation_service.create_escalation(
            db,
            reason_code=upg_dec.reason_code,
            summary=f"Customer requested business-class upgrade.",
            customer_id=customer_id,
            conversation_id=conversation_id,
        )
        escalated = True
        reply_parts.append("Free business-class upgrades are beyond policy and have been escalated for supervisor review.")

    if "full night" in content_lower or "full-night" in content_lower or "whole night" in content_lower:
        fn_dec = classify_request("full_night_hotel", customer.tier)
        esc = escalation_service.create_escalation(
            db,
            reason_code=fn_dec.reason_code,
            summary="Customer requested full-night hotel accommodation.",
            customer_id=customer_id,
            conversation_id=conversation_id,
        )
        escalated = True
        reply_parts.append("Full-night hotel accommodation exceeds standard disruption policy and requires supervisor review.")

    if "hotel" in content_lower and delayed_booking and (delayed_booking.delay_minutes or 0) <= 300:
        record_decision_trace(
            rule="hotel_eligibility",
            inputs={"delay_minutes": delayed_booking.delay_minutes},
            outcome="Hotel accommodation is not authorized for delays of 5 hours or less.",
            reason_code="HOTEL_NOT_ELIGIBLE_UNDER_5H",
        )

    if "2000" in content_lower or "2,000" in content_lower or "waiver" in content_lower:
        fare_dec = evaluate_fare_difference(2000)
        if fare_dec.status == "escalate":
            esc = escalation_service.create_escalation(
                db,
                reason_code=fare_dec.reason_code,
                summary="Customer requested waiver for Rs 2,000 fare difference.",
                customer_id=customer_id,
                conversation_id=conversation_id,
            )
            escalated = True
            reply_parts.append("Waiving a fare difference above Rs 1,500 requires supervisor approval and has been escalated.")


    if escalated:
        reply_parts.append("I'm escalating this to our specialist support team right now, and they'll reach out to you directly.")

    if not reply_parts:
        reply_parts.append("Thank you for contacting customer support. Your inquiry has been processed.")

    return {
        "reply": " ".join(reply_parts),
        "actions_taken": actions_taken,
        "escalation": escalated,
    }
