"""Integration test for persisted multi-turn RAG context."""
from app.services.knowledge_base import KnowledgeAnswer


def test_second_chat_turn_receives_previous_exchange(client, monkeypatch):
    signup = client.post(
        "/api/auth/signup",
        json={
            "fullName": "Memory User",
            "email": "memory-user@demo.ma",
            "password": "secret123",
        },
    )
    token = signup.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    captured_histories = []

    def fake_answer(**kwargs):
        captured_histories.append(kwargs.get("conversation_history"))
        return KnowledgeAnswer(answer="remembered answer", confidence=1.0, sources=["test"])

    monkeypatch.setattr("app.api.omni.answer_with_metadata", fake_answer)

    first = client.post(
        "/api/chat/messages",
        headers=headers,
        json={"content": "First question", "sessionId": "memory-session"},
    )
    second = client.post(
        "/api/chat/messages",
        headers=headers,
        json={"content": "And what about that?", "sessionId": "memory-session"},
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert captured_histories[0] == []
    assert captured_histories[1] == [
        {"role": "user", "content": "First question"},
        {"role": "assistant", "content": "remembered answer"},
    ]


def test_real_visit_analytics_are_admin_only(client, admin_headers):
    recorded = client.post(
        "/api/analytics/visits",
        json={
            "sessionId": "browser-session",
            "page": "/services",
            "pageLabel": "Services",
            "language": "fr",
            "device": "Desktop",
        },
    )
    assert recorded.status_code == 201

    unauthorized = client.get("/api/admin/analytics/visits")
    assert unauthorized.status_code == 403

    response = client.get("/api/admin/analytics/visits", headers=admin_headers)
    assert response.status_code == 200
    assert any(event["sessionId"] == "browser-session" for event in response.json())


def test_single_chat_session_can_be_deleted(client, monkeypatch):
    signup = client.post(
        "/api/auth/signup",
        json={
            "fullName": "Delete Session User",
            "email": "delete-session@demo.ma",
            "password": "secret123",
        },
    )
    headers = {"Authorization": f"Bearer {signup.json()['token']}"}
    monkeypatch.setattr(
        "app.api.omni.answer_with_metadata",
        lambda **kwargs: KnowledgeAnswer(answer="answer", confidence=1.0, sources=["test"]),
    )
    client.post(
        "/api/chat/messages",
        headers=headers,
        json={"content": "hello", "sessionId": "delete-me"},
    )
    response = client.delete("/api/chat/sessions/delete-me", headers=headers)
    assert response.status_code == 200
    assert response.json()["deleted"] == 2


def test_admin_can_update_case_through_frontend_contract(client, admin_headers):
    signup = client.post(
        "/api/auth/signup",
        json={"fullName": "Case Owner", "email": "case-owner@demo.ma", "password": "secret123"},
    )
    citizen_headers = {"Authorization": f"Bearer {signup.json()['token']}"}
    created = client.post(
        "/api/cases",
        headers=citizen_headers,
        json={"serviceId": 1, "applicantName": "Case Owner", "applicantEmail": "case-owner@demo.ma"},
    )
    case_id = created.json()["id"]

    updated = client.patch(
        f"/api/admin/cases/{case_id}",
        headers=admin_headers,
        json={"status": "UNDER_REVIEW"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "UNDER_REVIEW"
