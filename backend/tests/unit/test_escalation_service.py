"""Unit tests for escalation service (services/escalation_service.py)."""

import repositories.escalation_repo as escalation_repo
import services.escalation_service as escalation_service


def test_create_escalations_all_required_reason_codes(db):
    reason_codes = [
        "COMPENSATION_BEYOND_POLICY",
        "FARE_WAIVER_ABOVE_1500",
        "NON_AIRLINE_CAUSED",
        "LEGAL_OR_FORMAL_COMPLAINT",
        "DIFFERENT_PAYMENT_METHOD",
    ]

    for code in reason_codes:
        esc = escalation_service.create_escalation(
            db,
            reason_code=code,
            summary=f"Test summary for {code}",
            status="OPEN",
            customer_id=1,
        )
        assert esc is not None
        assert esc.reason_code == code
        assert esc.status == "OPEN"

    all_esc = escalation_repo.list_all(db)
    assert len(all_esc) == len(reason_codes)
