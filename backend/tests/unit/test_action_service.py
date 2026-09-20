"""Unit tests for action service auditing (services/action_service.py)."""

import repositories.action_repo as action_repo
import repositories.escalation_repo as escalation_repo
import services.action_service as action_service


def test_request_rebooking_logging(db):
    action = action_service.request_rebooking(
        db, customer_id=1, booking_id=10, customer_tier="Gold"
    )

    assert action is not None
    assert action.action_type == "REBOOK_REQUEST"
    assert action.details_json["flight_inventory"] == "not available"
    assert action.details_json["priority_rebooking"] is True

    # Verify persisted in database
    db_action = action_repo.get_by_id(db, action.id)
    assert db_action is not None
    assert db_action.action_type == "REBOOK_REQUEST"


def test_issue_meal_voucher_logging(db):
    action = action_service.issue_meal_voucher(
        db, delay_minutes=240, customer_id=2, booking_id=20
    )

    assert action is not None
    assert action.action_type == "MEAL_VOUCHER"
    assert action.details_json["delay_minutes"] == 240
    assert action.details_json["amount"] == "not available"


def test_grant_lounge_access_logging(db):
    action = action_service.grant_lounge_access(
        db, delay_minutes=240, customer_id=2, booking_id=20
    )

    assert action is not None
    assert action.action_type == "LOUNGE_ACCESS"
    assert action.details_json["delay_minutes"] == 240
    assert action.details_json["lounge"] == "not available"


def test_arrange_hotel_for_delayed_hours_logging(db):
    action = action_service.arrange_hotel_for_delayed_hours(
        db, delay_minutes=360, customer_id=3, booking_id=30
    )

    assert action is not None
    assert action.action_type == "HOTEL_DELAYED_HOURS"
    assert action.details_json["delay_minutes"] == 360
    assert action.details_json["coverage"] == "delayed hours only"


def test_request_refund_original_payment_method(db):
    action = action_service.request_refund(
        db, payment_method="original payment method", customer_id=1, booking_id=10
    )

    assert action is not None
    assert action.action_type == "REFUND_REQUEST"
    assert action.details_json["payment_method"] == "original payment method"
    assert action.details_json["timeline"] == "7 business days"


def test_request_refund_different_payment_method_escalates(db):
    action = action_service.request_refund(
        db, payment_method="UPI / Paytm", customer_id=1, booking_id=10
    )

    # Refund action must NOT be created
    assert action is None

    # Escalation must be logged
    escalations = escalation_repo.list_all(db)
    assert len(escalations) == 1
    assert escalations[0].reason_code == "DIFFERENT_PAYMENT_METHOD"
