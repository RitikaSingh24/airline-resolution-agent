"""Scenario and guardrail integration tests for the LangChain Tool-Calling Agent."""

from unittest.mock import MagicMock, patch
import pytest

from agent.agent import real_agent
from agent.guardrails import validate_post_llm
from core.config import settings
import repositories.action_repo as action_repo
import repositories.conversation_repo as conversation_repo
import repositories.escalation_repo as escalation_repo
from db.seed import seed_data


def test_scenario_s1_priya_agent(client, db):
    """S1 - Priya Nair (Gold): Cancelled flight.

    Customer asks: Full refund + free business-class upgrade on return.
    Expected:
      - Full refund allowed to original payment method.
      - Business-class upgrade escalated (COMPENSATION_BEYOND_POLICY).
      - Return flight_no is NOT invented.
      - Anger does NOT trigger legal escalation.
      - decision_trace includes cancellation entitlement & upgrade escalation.
    """
    seed_data(db)
    conv = conversation_repo.create(db, customer_id=1)

    res = real_agent.respond(
        db,
        conversation_id=conv.id,
        content="My flight was cancelled and I am furious! I want a full refund and a free business class upgrade on my return flight.",
    )

    reply = res.reply.lower()
    assert "refund" in reply or "rebook" in reply
    assert "sk-999" not in reply
    assert "business-class upgrade confirmed" not in reply

    # Verify escalation logged
    escalations = escalation_repo.list_by_conversation(db, conv.id)
    assert len(escalations) == 1
    assert escalations[0].reason_code == "COMPENSATION_BEYOND_POLICY"

    # Verify decision_trace
    trace_rules = [t.rule for t in res.decision_trace]
    trace_reasons = [t.reason_code for t in res.decision_trace]

    assert "evaluate_cancellation" in trace_rules or "classify_request" in trace_rules
    assert "COMPENSATION_BEYOND_POLICY" in trace_reasons
    # Anger must NOT trigger legal threat trace
    assert "LEGAL_OR_FORMAL_COMPLAINT" not in trace_reasons


def test_scenario_s2_arvind_agent(client, db):
    """S2 - Arvind Kulkarni (Silver): 4h delay.

    Customer asks: Can you arrange a hotel for me?
    Expected:
      - Meal voucher & lounge access provided.
      - Hotel NOT arranged (4h is not >5h).
      - decision_trace includes delay_compensation (delay_minutes: 240) and hotel eligibility.
    """
    seed_data(db)
    conv = conversation_repo.create(db, customer_id=2)

    res = real_agent.respond(
        db,
        conversation_id=conv.id,
        content="My flight SK-118 is delayed by 4 hours. Can you arrange a hotel for me?",
    )

    actions = action_repo.list_by_conversation(db, conv.id)
    action_types = [a.action_type for a in actions]

    assert "MEAL_VOUCHER" in action_types
    assert "LOUNGE_ACCESS" in action_types
    assert "HOTEL_DELAYED_HOURS" not in action_types
    assert "full-night hotel" not in res.reply.lower()

    # Verify decision_trace
    trace_rules = [t.rule for t in res.decision_trace]
    assert "delay_compensation" in trace_rules

    delay_item = next(t for t in res.decision_trace if t.rule == "delay_compensation")
    assert delay_item.inputs.get("delay_minutes") == 240
    assert delay_item.reason_code == "DELAY_3H_TO_5H"


def test_scenario_s3_meher_agent(client, db):
    """S3 - Meher Kaur (Platinum): 6h delay.

    Customer asks: Full-night hotel + higher-fare flight without paying extra.
    Expected:
      - Hotel for delayed hours ONLY provided.
      - Full-night hotel escalated (COMPENSATION_BEYOND_POLICY).
      - Rs 2,000 fare difference waiver escalated (FARE_WAIVER_ABOVE_1500).
      - decision_trace contains expected deterministic reason codes.
    """
    seed_data(db)
    conv = conversation_repo.create(db, customer_id=3)

    res = real_agent.respond(
        db,
        conversation_id=conv.id,
        content="My flight SK-305 is delayed by 6 hours. I want a full night hotel and I want a higher-fare flight without paying the Rs 2,000 extra amount.",
    )

    actions = action_repo.list_by_conversation(db, conv.id)
    action_types = [a.action_type for a in actions]
    assert "HOTEL_DELAYED_HOURS" in action_types

    escalations = escalation_repo.list_by_conversation(db, conv.id)
    reason_codes = [e.reason_code for e in escalations]

    assert "COMPENSATION_BEYOND_POLICY" in reason_codes
    assert "FARE_WAIVER_ABOVE_1500" in reason_codes
    assert "waived the rs 2,000" not in res.reply.lower()

    # Verify decision_trace
    trace_reasons = [t.reason_code for t in res.decision_trace]
    assert "DELAY_OVER_5H" in trace_reasons
    assert "COMPENSATION_BEYOND_POLICY" in trace_reasons
    assert "FARE_WAIVER_ABOVE_1500" in trace_reasons


def test_missing_llm_key_fallback(client, db, monkeypatch):
    """Verify system uses deterministic fallback engine when LLM_API_KEY is missing."""
    seed_data(db)
    monkeypatch.setattr(settings, "LLM_API_KEY", None)

    conv = conversation_repo.create(db, customer_id=1)
    res = real_agent.respond(
        db,
        conversation_id=conv.id,
        content="My flight SK-204 was cancelled. What are my options?",
    )

    assert res.reply is not None
    assert "cancelled" in res.reply.lower() or "refund" in res.reply.lower() or "rebooking" in res.reply.lower()
    assert isinstance(res.decision_trace, list)
    assert len(res.decision_trace) > 0


def test_fallback_decision_trace_s2(client, db, monkeypatch):
    """S2 fallback test: without LLM key, S2 still returns expected delay trace."""
    seed_data(db)
    monkeypatch.setattr(settings, "LLM_API_KEY", None)

    conv = conversation_repo.create(db, customer_id=2)
    res = real_agent.respond(
        db,
        conversation_id=conv.id,
        content="My flight SK-118 is delayed by 4 hours. Can you arrange a hotel for me?",
    )

    trace_rules = [t.rule for t in res.decision_trace]
    assert "delay_compensation" in trace_rules

    delay_item = next(t for t in res.decision_trace if t.rule == "delay_compensation")
    assert delay_item.inputs.get("delay_minutes") == 240
    assert delay_item.reason_code == "DELAY_3H_TO_5H"


def test_no_rule_empty_decision_trace(client, db):
    """Verify 'what is my flight status' returns an empty decision_trace."""
    seed_data(db)
    conv = conversation_repo.create(db, customer_id=1)

    res = real_agent.respond(
        db,
        conversation_id=conv.id,
        content="what is my flight status",
    )

    assert res.decision_trace == []


def test_empty_llm_key_boot_and_chat(client, db, monkeypatch):
    """Verify system boots and answers chat when LLM_API_KEY is empty string ('')."""
    seed_data(db)
    monkeypatch.setattr(settings, "LLM_API_KEY", "")

    conv = conversation_repo.create(db, customer_id=2)
    res = real_agent.respond(
        db,
        conversation_id=conv.id,
        content="My flight SK-118 is delayed by 4 hours.",
    )

    assert res.reply is not None
    assert "meal voucher" in res.reply.lower() or "lounge" in res.reply.lower() or "delay" in res.reply.lower()
    assert len(res.decision_trace) > 0


def test_pre_llm_legal_threat_bypass(client, db, monkeypatch):
    """Verify legal threat triggers pre-LLM guardrail, returning LEGAL_OR_FORMAL_COMPLAINT trace."""
    seed_data(db)
    monkeypatch.setattr(settings, "LLM_API_KEY", "mock-key")

    mock_llm = MagicMock()
    monkeypatch.setattr("langchain_openai.ChatOpenAI.invoke", mock_llm)

    conv = conversation_repo.create(db, customer_id=1)
    res = real_agent.respond(
        db,
        conversation_id=conv.id,
        content="If you don't refund me immediately, my lawyer will file a lawsuit in consumer court.",
    )

    # LLM must NOT be called
    assert mock_llm.call_count == 0
    assert res.escalation is True
    assert "escalating this to our specialist support team" in res.reply

    escalations = escalation_repo.list_by_conversation(db, conv.id)
    assert len(escalations) == 1
    assert escalations[0].reason_code == "LEGAL_OR_FORMAL_COMPLAINT"

    # Verify decision_trace contains LEGAL_OR_FORMAL_COMPLAINT
    trace_reasons = [t.reason_code for t in res.decision_trace]
    assert "LEGAL_OR_FORMAL_COMPLAINT" in trace_reasons


def test_post_llm_hallucination_rejection(client, db, monkeypatch):
    """Verify post-LLM guardrail rejects hallucinated flight numbers (SK-999) or unauthorized upgrades."""
    seed_data(db)
    monkeypatch.setattr(settings, "LLM_API_KEY", "mock-key")

    # Mock ChatOpenAI response containing hallucinated flight SK-999
    mock_ai_msg = MagicMock()
    mock_ai_msg.content = "Your business-class upgrade is confirmed on flight SK-999."

    with patch("langchain_openai.ChatOpenAI.bind_tools") as mock_bind:
        mock_bound_llm = MagicMock()
        mock_bound_llm.invoke.return_value = mock_ai_msg
        mock_bind.return_value = mock_bound_llm

        conv = conversation_repo.create(db, customer_id=1)
        res = real_agent.respond(
            db,
            conversation_id=conv.id,
            content="Can I get an upgrade?",
        )

        # Hallucinated response must be rejected by post-LLM guardrail
        assert "SK-999" not in res.reply
        assert "business-class upgrade confirmed" not in res.reply.lower()


def test_customer_ownership_boundary(client, db):
    """Verify customer A (Priya) cannot query or access customer B's PNR (TR1190B)."""
    seed_data(db)
    from models.booking import Booking

    bookings = db.query(Booking).filter(Booking.pnr == "TR1190B").all()
    user_bookings = [b for b in bookings if b.customer_id == 1]
    assert user_bookings == [], "Customer 1 must not have access to PNR TR1190B"


def test_multi_intent_independent_evaluation(client, db):
    """Verify multi-intent message (refund + upgrade) allows valid refund while escalating upgrade."""
    seed_data(db)
    conv = conversation_repo.create(db, customer_id=1)

    res = real_agent.respond(
        db,
        conversation_id=conv.id,
        content="Please issue a full refund for my cancelled flight and upgrade me to business class.",
    )

    actions = action_repo.list_by_conversation(db, conv.id)
    action_types = [a.action_type for a in actions]
    assert "REFUND_REQUEST" in action_types

    escalations = escalation_repo.list_by_conversation(db, conv.id)
    assert len(escalations) == 1
    assert escalations[0].reason_code == "COMPENSATION_BEYOND_POLICY"
