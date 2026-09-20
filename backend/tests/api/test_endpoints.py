"""Integration tests for FastAPI API endpoints."""

import services.action_service as action_service
import services.escalation_service as escalation_service


def test_health_endpoint(client):
    """Test GET /health returns status OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}


def test_api_v1_health_endpoint(client):
    """Test GET /api/v1/health returns status OK."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}


def test_get_customers(client):
    """Test GET /api/v1/customers returns the 3 seeded customers."""
    response = client.get("/api/v1/customers")
    assert response.status_code == 200
    customers = response.json()
    assert len(customers) == 3

    emails = [c["email"] for c in customers]
    assert "priya.nair@example.com" in emails
    assert "arvind.kulkarni@example.com" in emails
    assert "meher.kaur@example.com" in emails


def test_get_customer_bookings(client):
    """Test GET /api/v1/customers/{id}/bookings for all seeded customers."""
    # Priya Nair (ID 1) -> 2 bookings
    res_priya = client.get("/api/v1/customers/1/bookings")
    assert res_priya.status_code == 200
    priya_bookings = res_priya.json()
    assert len(priya_bookings) == 2

    # Verify return flight_no is null
    return_booking = next(b for b in priya_bookings if b["segment_label"] == "return")
    assert return_booking["flight_no"] is None

    # Arvind Kulkarni (ID 2) -> 1 booking (delayed 240 mins)
    res_arvind = client.get("/api/v1/customers/2/bookings")
    assert res_arvind.status_code == 200
    arvind_bookings = res_arvind.json()
    assert len(arvind_bookings) == 1
    assert arvind_bookings[0]["delay_minutes"] == 240

    # Meher Kaur (ID 3) -> 1 booking (delayed 360 mins)
    res_meher = client.get("/api/v1/customers/3/bookings")
    assert res_meher.status_code == 200
    meher_bookings = res_meher.json()
    assert len(meher_bookings) == 1
    assert meher_bookings[0]["delay_minutes"] == 360


def test_get_customer_bookings_not_found(client):
    """Test GET /api/v1/customers/999/bookings returns 404 structured error."""
    response = client.get("/api/v1/customers/999/bookings")
    assert response.status_code == 404
    data = response.json()
    assert data["error"] == "NotFound"
    assert data["message"] == "Customer not found"


def test_create_conversation(client):
    """Test POST /api/v1/conversations creates a conversation (HTTP 201)."""
    response = client.post("/api/v1/conversations", json={"customer_id": 1})
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["customer_id"] == 1


def test_create_conversation_invalid_customer(client):
    """Test POST /api/v1/conversations returns 404 if customer is missing."""
    response = client.post("/api/v1/conversations", json={"customer_id": 999})
    assert response.status_code == 404
    assert response.json()["error"] == "NotFound"


def test_send_chat_message(client):
    """Test POST /api/v1/conversations/{id}/messages with stub agent."""
    # Create conversation first
    conv_res = client.post("/api/v1/conversations", json={"customer_id": 1})
    conv_id = conv_res.json()["id"]

    # Send chat message
    msg_res = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "My flight was cancelled. What are my options?"},
    )
    assert msg_res.status_code == 200
    data = msg_res.json()
    assert "reply" in data
    assert data["actions_taken"] == []
    assert data["escalation"] is False
    assert data["conversation_id"] == conv_id


def test_send_chat_message_conversation_not_found(client):
    """Test POST /api/v1/conversations/999/messages returns 404."""
    response = client.post(
        "/api/v1/conversations/999/messages",
        json={"content": "Hello?"},
    )
    assert response.status_code == 404
    assert response.json()["error"] == "NotFound"


def test_get_conversation_actions(client, db):
    """Test GET /api/v1/conversations/{id}/actions returns conversation actions."""
    # Create conversation
    conv_res = client.post("/api/v1/conversations", json={"customer_id": 1})
    conv_id = conv_res.json()["id"]

    # Log action using action_service
    action_service.request_rebooking(
        db, customer_id=1, conversation_id=conv_id, customer_tier="Gold"
    )

    actions_res = client.get(f"/api/v1/conversations/{conv_id}/actions")
    assert actions_res.status_code == 200
    actions = actions_res.json()
    assert len(actions) == 1
    assert actions[0]["action_type"] == "REBOOK_REQUEST"
    assert actions[0]["conversation_id"] == conv_id


def test_get_conversation_actions_not_found(client):
    """Test GET /api/v1/conversations/999/actions returns 404."""
    response = client.get("/api/v1/conversations/999/actions")
    assert response.status_code == 404
    assert response.json()["error"] == "NotFound"


def test_get_escalations(client, db):
    """Test GET /api/v1/escalations returns escalation records."""
    # Log an escalation
    escalation_service.create_escalation(
        db,
        reason_code="COMPENSATION_BEYOND_POLICY",
        summary="Customer requested free business class upgrade.",
        customer_id=1,
    )

    esc_res = client.get("/api/v1/escalations")
    assert esc_res.status_code == 200
    escalations = esc_res.json()
    assert len(escalations) == 1
    assert escalations[0]["reason_code"] == "COMPENSATION_BEYOND_POLICY"


def test_startup_without_llm_key(monkeypatch, client):
    """Verify application boots and /health works when LLM_API_KEY is not set."""
    from core.config import settings

    monkeypatch.setattr(settings, "LLM_API_KEY", None)

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}
