"""Deterministic policy rules engine.

Enforces strict airline disruption resolution rules. The LLM must NEVER
decide airline policy; this module is the authoritative decision layer.
"""
from dataclasses import dataclass, field
import re
from typing import Any, Literal

from services.decision_collector import record_decision_trace

DecisionStatus = Literal["allowed", "denied", "escalate"]


@dataclass
class Decision:
    """Typed decision returned by the rules engine."""
    status: DecisionStatus
    entitlements: list[str] = field(default_factory=list)
    reason_code: str | None = None
    customer_safe_explanation: str | None = None


LEGAL_PATTERNS = [
    r"\blegal\b",
    r"\blawyer\b",
    r"\battorney\b",
    r"\blawsuit\b",
    r"\bsue\b",
    r"\bsuing\b",
    r"\bcourt\b",
    r"\bformal complaint\b",
    r"\bconsumer court\b",
    r"\bconsumer forum\b",
]

COMPILED_LEGAL_REGEX = re.compile("|".join(LEGAL_PATTERNS), re.IGNORECASE)


def detect_legal_threat(text: str) -> bool:
    """Detects whether customer text contains a legal threat or formal complaint.

    Emotional expression (e.g., 'I'm furious') alone will NOT trigger detection.
    """
    if not text:
        return False
    is_legal = bool(COMPILED_LEGAL_REGEX.search(text))
    if is_legal:
        record_decision_trace(
            rule="legal_threat_detection",
            inputs={"text": text},
            outcome="escalate",
            reason_code="LEGAL_OR_FORMAL_COMPLAINT",
        )
    return is_legal


def evaluate_cancellation(booking: Any) -> Decision:
    """Evaluates cancellation policy for a given booking.

    For airline-caused cancellation:
      - Free rebooking on next available flight within 24h
      - Full refund to original payment method within 7 business days
    """
    if not booking:
        d = Decision(
            status="escalate",
            reason_code="NOT_AVAILABLE",
            customer_safe_explanation="Required booking information is not available."
        )
        return _record_cancellation(booking, d)

    # Support ORM model or dict access
    status = getattr(booking, "status", None) if not isinstance(booking, dict) else booking.get("status")
    cause = getattr(booking, "cause", None) if not isinstance(booking, dict) else booking.get("cause")

    if not status:
        d = Decision(
            status="escalate",
            reason_code="NOT_AVAILABLE",
            customer_safe_explanation="Booking status is not available."
        )
        return _record_cancellation(booking, d)

    status_str = str(status).lower()
    cause_str = str(cause).lower() if cause else ""

    # Known non-airline causes
    if "weather" in cause_str or "passenger" in cause_str or "customer" in cause_str or "ATC" in cause_str:
        d = Decision(
            status="escalate",
            reason_code="NON_AIRLINE_CAUSED",
            customer_safe_explanation="Disruption cause is not established as airline-caused."
        )
        return _record_cancellation(booking, d)

    if status_str == "cancelled" or "operational" in cause_str or cause_str != "":
        d = Decision(
            status="allowed",
            entitlements=[
                "free_rebooking_next_available_within_24h",
                "full_refund_original_payment_method"
            ],
            reason_code="AIRLINE_CAUSED_CANCELLATION",
            customer_safe_explanation=(
                "Your flight was cancelled due to operational reasons. You are eligible for "
                "free rebooking on the next available flight within 24 hours or a full refund "
                "to your original payment method within 7 business days."
            )
        )
        return _record_cancellation(booking, d)

    d = Decision(
        status="escalate",
        reason_code="NON_AIRLINE_CAUSED",
        customer_safe_explanation="Cancellation cause is undetermined and requires supervisor review."
    )
    return _record_cancellation(booking, d)


def evaluate_delay(delay_minutes: int | float | None) -> Decision:
    """Evaluates entitlements based on flight delay duration (in minutes).

    PRD policy bands:
      < 180 min  -> Rs500 meal voucher
      > 180 min  -> meal voucher + lounge access
      > 300 min  -> meal voucher + lounge access + hotel for delayed hours only

    Boundary assumption (documented, not explicit in PRD):
      Exactly 180 min and exactly 300 min are treated as the LOWER band.
      179 -> meal_voucher   |  180 -> meal_voucher
      181 -> meal + lounge  |  300 -> meal + lounge
      301 -> meal + lounge + hotel
    """
    if delay_minutes is None or delay_minutes < 0:
        d = Decision(
            status="escalate",
            reason_code="NOT_AVAILABLE",
            customer_safe_explanation="Delay information is invalid or not available."
        )
        return _record_delay(delay_minutes, d)

    if delay_minutes <= 180:
        d = Decision(
            status="allowed",
            entitlements=["meal_voucher"],
            reason_code="DELAY_UNDER_3H",
            customer_safe_explanation=(
                "Your flight delay entitles you to a Rs 500 meal voucher."
            )
        )
        return _record_delay(delay_minutes, d)

    if delay_minutes <= 300:
        d = Decision(
            status="allowed",
            entitlements=["meal_voucher", "lounge_access"],
            reason_code="DELAY_3H_TO_5H",
            customer_safe_explanation=(
                "Your flight delay entitles you to a meal voucher and lounge access."
            )
        )
        return _record_delay(delay_minutes, d)

    # delay_minutes > 300 (301+)
    d = Decision(
        status="allowed",
        entitlements=["meal_voucher", "lounge_access", "hotel_for_delayed_hours"],
        reason_code="DELAY_OVER_5H",
        customer_safe_explanation=(
            "Your flight delay entitles you to a meal voucher, lounge access, "
            "and hotel accommodation covering the delayed hours only "
            "(not a full-night stay)."
        )
    )
    return _record_delay(delay_minutes, d)


def evaluate_fare_difference(amount: float | int | None) -> Decision:
    """Evaluates voluntary rebooking fare difference policy.

    Rules:
      amount < 0          -> invalid/not available
      amount == 0         -> no fare difference
      0 < amount <= 1500  -> customer pays fare difference (normal)
      amount > 1500       -> waiver requires supervisor approval
    """
    if amount is None or amount < 0:
        d = Decision(
            status="escalate",
            reason_code="NOT_AVAILABLE",
            customer_safe_explanation="Fare difference amount is invalid or not available."
        )
        return _record_fare_diff(amount, d)

    if amount == 0:
        d = Decision(
            status="allowed",
            entitlements=["no_fare_difference"],
            reason_code="NO_FARE_DIFFERENCE",
            customer_safe_explanation="No fare difference applies for this rebooking."
        )
        return _record_fare_diff(amount, d)

    if amount <= 1500:
        d = Decision(
            status="allowed",
            entitlements=["customer_pays_fare_difference"],
            reason_code="NORMAL_FARE_DIFFERENCE",
            customer_safe_explanation=f"Rebooking fare difference is Rs {amount:,.0f}, payable by the customer."
        )
        return _record_fare_diff(amount, d)

    d = Decision(
        status="escalate",
        reason_code="FARE_WAIVER_ABOVE_1500",
        customer_safe_explanation=(
            f"Fare difference is Rs {amount:,.0f}. Customer must pay the fare difference; "
            "waiving a fare difference above Rs 1,500 requires supervisor approval."
        )
    )
    return _record_fare_diff(amount, d)


def classify_request(request_type: str, customer_tier: str | None = None) -> Decision:
    """Classifies a customer request type and incorporates loyalty entitlements."""
    if not request_type:
        d = Decision(
            status="escalate",
            reason_code="NOT_AVAILABLE",
            customer_safe_explanation="Request type is missing or not available."
        )
        return _record_classify(request_type, customer_tier, d)

    req = request_type.strip().lower()

    # Beyond-policy compensation requests
    if req in ["upgrade", "business_class_upgrade", "full_night_hotel", "cash_compensation", "extra_compensation"]:
        d = Decision(
            status="escalate",
            reason_code="COMPENSATION_BEYOND_POLICY",
            customer_safe_explanation="Requested benefit is beyond standard policy and requires supervisor approval."
        )
        return _record_classify(request_type, customer_tier, d)

    if req == "rebooking":
        entitlements = ["rebooking_request"]
        if customer_tier in ["Gold", "Platinum"]:
            entitlements.append("priority_rebooking")
        d = Decision(
            status="allowed",
            entitlements=entitlements,
            reason_code="REBOOKING_REQUEST",
            customer_safe_explanation="Rebooking request classified."
        )
        return _record_classify(request_type, customer_tier, d)

    if req == "refund":
        d = Decision(
            status="allowed",
            entitlements=["full_refund_original_payment_method"],
            reason_code="REFUND_REQUEST",
            customer_safe_explanation="Refund request classified."
        )
        return _record_classify(request_type, customer_tier, d)

    if req in ["meal_voucher", "meal"]:
        d = Decision(
            status="allowed",
            entitlements=["meal_voucher"],
            reason_code="MEAL_VOUCHER_REQUEST",
            customer_safe_explanation="Meal voucher request classified."
        )
        return _record_classify(request_type, customer_tier, d)

    if req == "lounge":
        d = Decision(
            status="allowed",
            entitlements=["lounge_access"],
            reason_code="LOUNGE_REQUEST",
            customer_safe_explanation="Lounge access request classified."
        )
        return _record_classify(request_type, customer_tier, d)

    if req in ["hotel", "hotel_delayed_hours"]:
        d = Decision(
            status="allowed",
            entitlements=["hotel_for_delayed_hours"],
            reason_code="HOTEL_REQUEST",
            customer_safe_explanation="Hotel request classified."
        )
        return _record_classify(request_type, customer_tier, d)

    if req == "fare_difference":
        d = Decision(
            status="allowed",
            entitlements=["fare_difference_eval"],
            reason_code="FARE_DIFFERENCE_REQUEST",
            customer_safe_explanation="Fare difference request classified."
        )
        return _record_classify(request_type, customer_tier, d)

    d = Decision(
        status="escalate",
        reason_code="NOT_AVAILABLE",
        customer_safe_explanation=f"Request type '{request_type}' is not recognized or available."
    )
    return _record_classify(request_type, customer_tier, d)


# Helper functions to record trace and return decision
def _record_cancellation(booking: Any, d: Decision) -> Decision:
    pnr = getattr(booking, "pnr", None) if not isinstance(booking, dict) else booking.get("pnr")
    status_val = getattr(booking, "status", None) if not isinstance(booking, dict) else booking.get("status")
    cause_val = getattr(booking, "cause", None) if not isinstance(booking, dict) else booking.get("cause")
    inputs_dict = {
        "pnr": pnr or "not available",
        "status": status_val or "not available",
        "cause": cause_val or "not available",
    }
    record_decision_trace(
        rule="evaluate_cancellation",
        inputs=inputs_dict,
        outcome=d.entitlements if d.entitlements else d.status,
        reason_code=d.reason_code,
    )
    return d


def _record_delay(delay_minutes: int | float | None, d: Decision) -> Decision:
    if d.entitlements:
        if d.entitlements == ["meal_voucher"]:
            outcome_val = "meal voucher"
        elif d.entitlements == ["meal_voucher", "lounge_access"]:
            outcome_val = "meal voucher + lounge"
        elif "hotel_for_delayed_hours" in d.entitlements:
            outcome_val = "meal voucher + hotel for delayed hours only"
        else:
            outcome_val = d.entitlements
    else:
        outcome_val = d.status

    record_decision_trace(
        rule="delay_compensation",
        inputs={"delay_minutes": delay_minutes if delay_minutes is not None else 0},
        outcome=outcome_val,
        reason_code=d.reason_code,
    )
    return d


def _record_fare_diff(amount: float | int | None, d: Decision) -> Decision:
    record_decision_trace(
        rule="fare_difference",
        inputs={"amount": amount if amount is not None else 0},
        outcome=d.customer_safe_explanation or d.status,
        reason_code=d.reason_code,
    )
    return d


def _record_classify(request_type: str, customer_tier: str | None, d: Decision) -> Decision:
    record_decision_trace(
        rule="classify_request",
        inputs={"request_type": request_type, "customer_tier": customer_tier},
        outcome=d.entitlements if d.entitlements else d.status,
        reason_code=d.reason_code,
    )
    return d
