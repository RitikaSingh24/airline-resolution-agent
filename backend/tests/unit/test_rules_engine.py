"""Unit tests for deterministic rules engine (services/rules_engine.py)."""

from services.rules_engine import (
    Decision,
    classify_request,
    detect_legal_threat,
    evaluate_cancellation,
    evaluate_delay,
    evaluate_fare_difference,
)


class TestLegalThreatDetection:
    def test_emotional_text_is_not_legal_threat(self):
        assert detect_legal_threat("I'm furious about this delay!") is False
        assert detect_legal_threat("This service is terrible and I am very angry.") is False

    def test_legal_action_wording_triggers_detection(self):
        assert detect_legal_threat("I will take legal action against your airline.") is True
        assert detect_legal_threat("My lawyer will contact your legal department.") is True
        assert detect_legal_threat("I am planning to file a lawsuit.") is True
        assert detect_legal_threat("I will file a formal complaint with the consumer court.") is True


class TestCancellationEvaluation:
    def test_airline_caused_cancellation(self):
        booking = {"status": "Cancelled", "cause": "operational reasons"}
        decision = evaluate_cancellation(booking)
        assert decision.status == "allowed"
        assert decision.reason_code == "AIRLINE_CAUSED_CANCELLATION"
        assert "free_rebooking_next_available_within_24h" in decision.entitlements
        assert "full_refund_original_payment_method" in decision.entitlements

    def test_non_airline_caused_cancellation(self):
        booking = {"status": "Cancelled", "cause": "severe weather"}
        decision = evaluate_cancellation(booking)
        assert decision.status == "escalate"
        assert decision.reason_code == "NON_AIRLINE_CAUSED"

    def test_missing_booking_information(self):
        decision = evaluate_cancellation(None)
        assert decision.status == "escalate"
        assert decision.reason_code == "NOT_AVAILABLE"


class TestDelayEvaluationBoundaries:
    """PRD boundary assumption: exactly 180 and 300 min are treated as the lower band."""

    def test_delay_179_minutes(self):
        """179 min -> lower band: meal voucher only."""
        decision = evaluate_delay(179)
        assert decision.status == "allowed"
        assert decision.reason_code == "DELAY_UNDER_3H"
        assert decision.entitlements == ["meal_voucher"]

    def test_delay_180_minutes_is_lower_band(self):
        """180 min is treated as lower band (meal voucher only) per documented assumption."""
        decision = evaluate_delay(180)
        assert decision.status == "allowed"
        assert decision.reason_code == "DELAY_UNDER_3H"
        assert decision.entitlements == ["meal_voucher"]

    def test_delay_181_minutes(self):
        """181 min -> upper band: meal voucher + lounge."""
        decision = evaluate_delay(181)
        assert decision.status == "allowed"
        assert decision.reason_code == "DELAY_3H_TO_5H"
        assert "meal_voucher" in decision.entitlements
        assert "lounge_access" in decision.entitlements
        assert "hotel_for_delayed_hours" not in decision.entitlements

    def test_delay_300_minutes_is_lower_band(self):
        """300 min is treated as lower band (meal + lounge, no hotel) per documented assumption."""
        decision = evaluate_delay(300)
        assert decision.status == "allowed"
        assert decision.reason_code == "DELAY_3H_TO_5H"
        assert "meal_voucher" in decision.entitlements
        assert "lounge_access" in decision.entitlements
        assert "hotel_for_delayed_hours" not in decision.entitlements

    def test_delay_301_minutes(self):
        """301 min -> meal voucher + lounge + hotel for delayed hours only."""
        decision = evaluate_delay(301)
        assert decision.status == "allowed"
        assert decision.reason_code == "DELAY_OVER_5H"
        assert "meal_voucher" in decision.entitlements
        assert "lounge_access" in decision.entitlements
        assert "hotel_for_delayed_hours" in decision.entitlements

    def test_negative_or_missing_delay(self):
        assert evaluate_delay(-10).status == "escalate"
        assert evaluate_delay(None).status == "escalate"


class TestFareDifferenceEvaluation:
    def test_zero_fare_difference(self):
        decision = evaluate_fare_difference(0)
        assert decision.status == "allowed"
        assert decision.reason_code == "NO_FARE_DIFFERENCE"

    def test_fare_difference_1500_no_escalation(self):
        """Rs 1,500 is within threshold — customer pays, no supervisor required."""
        decision = evaluate_fare_difference(1500)
        assert decision.status == "allowed"
        assert decision.reason_code == "NORMAL_FARE_DIFFERENCE"

    def test_fare_difference_1501_requires_supervisor_waiver(self):
        """Rs 1,501 exceeds threshold — waiver requires supervisor approval."""
        decision = evaluate_fare_difference(1501)
        assert decision.status == "escalate"
        assert decision.reason_code == "FARE_WAIVER_ABOVE_1500"

    def test_fare_difference_2000_requires_supervisor_waiver(self):
        decision = evaluate_fare_difference(2000)
        assert decision.status == "escalate"
        assert decision.reason_code == "FARE_WAIVER_ABOVE_1500"

    def test_invalid_fare_difference(self):
        assert evaluate_fare_difference(-500).status == "escalate"
        assert evaluate_fare_difference(None).status == "escalate"


class TestClassifyRequest:
    def test_gold_platinum_priority_rebooking(self):
        gold_decision = classify_request("rebooking", "Gold")
        assert gold_decision.status == "allowed"
        assert "priority_rebooking" in gold_decision.entitlements

        platinum_decision = classify_request("rebooking", "Platinum")
        assert platinum_decision.status == "allowed"
        assert "priority_rebooking" in platinum_decision.entitlements

    def test_silver_no_priority_rebooking(self):
        silver_decision = classify_request("rebooking", "Silver")
        assert silver_decision.status == "allowed"
        assert "priority_rebooking" not in silver_decision.entitlements

    def test_beyond_policy_compensation_request(self):
        upgrade_decision = classify_request("upgrade", "Platinum")
        assert upgrade_decision.status == "escalate"
        assert upgrade_decision.reason_code == "COMPENSATION_BEYOND_POLICY"

        hotel_decision = classify_request("full_night_hotel", "Gold")
        assert hotel_decision.status == "escalate"
        assert hotel_decision.reason_code == "COMPENSATION_BEYOND_POLICY"
