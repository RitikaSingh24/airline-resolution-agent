#!/usr/bin/env python3
"""E2E Verification Script for Scenarios S1, S2, and S3.

Exercises the backend API using the deterministic policy engine and asserts
that decision traces, audited actions, and escalations match PRD expectations.
"""

import os
import sys

# Add backend and backend/src to python path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(root_dir, "backend")
backend_src_dir = os.path.join(backend_dir, "src")

for path in [backend_dir, backend_src_dir]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Disable LLM API key for deterministic test execution
from core.config import settings
settings.LLM_API_KEY = None

from fastapi.testclient import TestClient
from main import app
from db.base import Base
from db.session import engine, SessionLocal
from db.seed import seed_data

# Ensure tables are initialized and seeded
Base.metadata.create_all(bind=engine)
db = SessionLocal()
seed_data(db)
db.close()

client = TestClient(app)


def test_s1_priya():
    """S1 - Priya Nair: Cancelled flight, refund + upgrade request."""
    # 1. Create conversation for Priya (Customer ID 1)
    conv_res = client.post("/api/v1/conversations", json={"customer_id": 1})
    assert conv_res.status_code == 201, f"Failed to create conversation: {conv_res.text}"
    conv_id = conv_res.json()["id"]

    # 2. Send message
    msg_res = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={
            "content": "My flight was cancelled and I am furious! I want a full refund and a free business class upgrade on my return flight."
        },
    )
    assert msg_res.status_code == 200, f"Chat request failed: {msg_res.text}"
    data = msg_res.json()

    # 3. Inspect response & trace
    trace_reasons = [item.get("reason_code") for item in data.get("decision_trace", [])]
    assert "COMPENSATION_BEYOND_POLICY" in trace_reasons, (
        f"Expected COMPENSATION_BEYOND_POLICY in trace, got {trace_reasons}"
    )
    assert "LEGAL_OR_FORMAL_COMPLAINT" not in trace_reasons, (
        "Anger alone must NOT trigger legal threat escalation"
    )

    # 4. Check escalations
    esc_res = client.get("/api/v1/escalations?customer_id=1")
    assert esc_res.status_code == 200
    esc_reasons = [e["reason_code"] for e in esc_res.json()]
    assert "COMPENSATION_BEYOND_POLICY" in esc_reasons

    # 5. Check actions
    act_res = client.get(f"/api/v1/conversations/{conv_id}/actions")
    assert act_res.status_code == 200
    act_types = [a["action_type"] for a in act_res.json()]
    assert "REFUND_REQUEST" in act_types

    print("S1: PASS")


def test_s2_arvind():
    """S2 - Arvind Kulkarni: 4h delay, hotel request."""
    # 1. Create conversation for Arvind (Customer ID 2)
    conv_res = client.post("/api/v1/conversations", json={"customer_id": 2})
    assert conv_res.status_code == 201
    conv_id = conv_res.json()["id"]

    # 2. Send message
    msg_res = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={
            "content": "My flight SK-118 is delayed by 4 hours. Can you arrange a hotel for me?"
        },
    )
    assert msg_res.status_code == 200
    data = msg_res.json()

    # 3. Inspect decision_trace
    trace_items = data.get("decision_trace", [])
    delay_item = next((item for item in trace_items if item.get("rule") == "delay_compensation"), None)
    assert delay_item is not None, "Expected delay_compensation rule in decision_trace"
    assert delay_item.get("inputs", {}).get("delay_minutes") == 240
    assert delay_item.get("reason_code") == "DELAY_3H_TO_5H"

    # 4. Check actions (MEAL_VOUCHER + LOUNGE_ACCESS, no HOTEL)
    act_res = client.get(f"/api/v1/conversations/{conv_id}/actions")
    assert act_res.status_code == 200
    act_types = [a["action_type"] for a in act_res.json()]
    assert "MEAL_VOUCHER" in act_types
    assert "LOUNGE_ACCESS" in act_types
    assert "HOTEL_DELAYED_HOURS" not in act_types

    print("S2: PASS")


def test_s3_meher():
    """S3 - Meher Kaur: 6h delay, full-night hotel & fare waiver request."""
    # 1. Create conversation for Meher (Customer ID 3)
    conv_res = client.post("/api/v1/conversations", json={"customer_id": 3})
    assert conv_res.status_code == 201
    conv_id = conv_res.json()["id"]

    # 2. Send message
    msg_res = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={
            "content": "My flight SK-305 is delayed by 6 hours. I want a full night hotel and I want a higher-fare flight without paying the Rs 2,000 extra amount."
        },
    )
    assert msg_res.status_code == 200
    data = msg_res.json()

    # 3. Inspect decision_trace
    trace_reasons = [item.get("reason_code") for item in data.get("decision_trace", [])]
    assert "DELAY_OVER_5H" in trace_reasons
    assert "COMPENSATION_BEYOND_POLICY" in trace_reasons
    assert "FARE_WAIVER_ABOVE_1500" in trace_reasons

    # 4. Check escalations
    esc_res = client.get("/api/v1/escalations?customer_id=3")
    assert esc_res.status_code == 200
    esc_reasons = [e["reason_code"] for e in esc_res.json()]
    assert "COMPENSATION_BEYOND_POLICY" in esc_reasons
    assert "FARE_WAIVER_ABOVE_1500" in esc_reasons

    # 5. Check actions
    act_res = client.get(f"/api/v1/conversations/{conv_id}/actions")
    assert act_res.status_code == 200
    act_types = [a["action_type"] for a in act_res.json()]
    assert "HOTEL_DELAYED_HOURS" in act_types

    print("S3: PASS")


def main():
    print("=== Running AIONOS Assignment 3 E2E Scenario Verification ===")
    try:
        test_s1_priya()
        test_s2_arvind()
        test_s3_meher()
        print("=== ALL E2E SCENARIOS PASSED SUCCESSFULLY ===")
        sys.exit(0)
    except Exception as exc:
        print(f"E2E Verification FAILED: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
