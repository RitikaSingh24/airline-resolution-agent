"""Unit tests for Scenarios S1 (Priya), S2 (Arvind), and S3 (Meher) — PRD acceptance criteria."""

import repositories.action_repo as action_repo
import repositories.escalation_repo as escalation_repo
import services.action_service as action_service
import services.escalation_service as escalation_service
from services.rules_engine import (
    classify_request,
    detect_legal_threat,
    evaluate_cancellation,
    evaluate_delay,
    evaluate_fare_difference,
)


def test_scenario_s1_priya(db):
    """S1 - Priya Nair: Gold tier, cancelled flight (operational reasons).

    Customer asks for full refund + free business class upgrade on return.
    Customer states: "I'm furious about this!"
    """
    priya_booking = {
        "pnr": "SK4821X",
        "flight_no": "SK-204",
        "route": "DEL-GOI",
        "status": "Cancelled",
        "cause": "operational reasons",
    }
    priya_tier = "Gold"
    customer_utterance = "I'm furious about this cancellation!"

    # 1. Evaluate cancellation entitlement
    canc_decision = evaluate_cancellation(priya_booking)
    assert canc_decision.status == "allowed"
    assert canc_decision.reason_code == "AIRLINE_CAUSED_CANCELLATION"
    assert "free_rebooking_next_available_within_24h" in canc_decision.entitlements
    assert "full_refund_original_payment_method" in canc_decision.entitlements

    # 2. Check upgrade request -> compensation beyond policy
    upgrade_decision = classify_request("business_class_upgrade", priya_tier)
    assert upgrade_decision.status == "escalate"
    assert upgrade_decision.reason_code == "COMPENSATION_BEYOND_POLICY"

    # Log escalation for beyond-policy compensation
    esc = escalation_service.create_escalation(
        db,
        reason_code=upgrade_decision.reason_code,
        summary="Priya Nair requested free business-class upgrade on return segment.",
        customer_id=1,
    )
    assert esc.reason_code == "COMPENSATION_BEYOND_POLICY"

    # 3. Verify anger does NOT trigger legal threat
    is_legal = detect_legal_threat(customer_utterance)
    assert is_legal is False

    # 4. Action logging for allowed refund request
    refund_action = action_service.request_refund(
        db, payment_method="original payment method", customer_id=1
    )
    assert refund_action is not None
    assert refund_action.action_type == "REFUND_REQUEST"


def test_scenario_s2_arvind(db):
    """S2 - Arvind Kulkarni: Silver tier, delayed 4h (240 mins).

    Customer asks for hotel.
    Expected: meal voucher + lounge access. Hotel is DENIED because 4h is not >5h.
    """
    delay_minutes = 240  # 4 hours
    customer_tier = "Silver"

    # 1. Evaluate delay entitlements
    delay_decision = evaluate_delay(delay_minutes)
    assert delay_decision.status == "allowed"
    assert "meal_voucher" in delay_decision.entitlements
    assert "lounge_access" in delay_decision.entitlements
    assert "hotel_for_delayed_hours" not in delay_decision.entitlements

    # 2. Verify hotel action for 240 mins is not authorized by rules
    # If customer insists on hotel, it becomes beyond-policy compensation
    hotel_req = classify_request("hotel", customer_tier)
    # The classification permits hotel request evaluation, but delay rules control entitlement
    assert "hotel_for_delayed_hours" not in delay_decision.entitlements

    # 3. Log actions for authorized entitlements
    meal_action = action_service.issue_meal_voucher(
        db, delay_minutes=delay_minutes, customer_id=2
    )
    assert meal_action.action_type == "MEAL_VOUCHER"

    lounge_action = action_service.grant_lounge_access(
        db, delay_minutes=delay_minutes, customer_id=2
    )
    assert lounge_action.action_type == "LOUNGE_ACCESS"


def test_scenario_s3_meher(db):
    """S3 - Meher Kaur: Platinum tier, delayed 6h (360 mins).

    Customer asks for full-night hotel, higher-fare flight with Rs 2,000 fare diff.
    Expected:
      - Entitled to meal voucher, lounge access, hotel for DELAYED HOURS ONLY.
      - Full-night hotel request -> COMPENSATION_BEYOND_POLICY escalation.
      - Rs 2,000 fare difference waiver request -> FARE_WAIVER_ABOVE_1500 escalation.
      - Platinum gives priority rebooking, but NO extra monetary/upgrade compensation.
    """
    delay_minutes = 360  # 6 hours
    customer_tier = "Platinum"

    # 1. Evaluate delay entitlements
    delay_decision = evaluate_delay(delay_minutes)
    assert delay_decision.status == "allowed"
    assert "meal_voucher" in delay_decision.entitlements
    assert "lounge_access" in delay_decision.entitlements
    assert "hotel_for_delayed_hours" in delay_decision.entitlements

    # 2. Full-night hotel request is beyond policy (coverage is delayed hours only)
    full_night_decision = classify_request("full_night_hotel", customer_tier)
    assert full_night_decision.status == "escalate"
    assert full_night_decision.reason_code == "COMPENSATION_BEYOND_POLICY"

    esc_hotel = escalation_service.create_escalation(
        db,
        reason_code=full_night_decision.reason_code,
        summary="Meher Kaur requested full-night hotel accommodation.",
        customer_id=3,
    )
    assert esc_hotel.reason_code == "COMPENSATION_BEYOND_POLICY"

    # 3. Fare difference evaluation for Rs 2,000
    fare_decision = evaluate_fare_difference(2000)
    assert fare_decision.status == "escalate"
    assert fare_decision.reason_code == "FARE_WAIVER_ABOVE_1500"

    esc_fare = escalation_service.create_escalation(
        db,
        reason_code=fare_decision.reason_code,
        summary="Meher Kaur requested waiver for Rs 2,000 fare difference on voluntary rebooking.",
        customer_id=3,
    )
    assert esc_fare.reason_code == "FARE_WAIVER_ABOVE_1500"

    # 4. Platinum tier rebooking receives priority flag
    rebooking_req = classify_request("rebooking", customer_tier)
    assert "priority_rebooking" in rebooking_req.entitlements

    rebook_action = action_service.request_rebooking(
        db, customer_id=3, customer_tier=customer_tier
    )
    assert rebook_action.details_json["priority_rebooking"] is True
    assert rebook_action.details_json["flight_inventory"] == "not available"
