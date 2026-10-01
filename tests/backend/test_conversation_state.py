import pytest
from pydantic import ValidationError

from app.services.conversation_state import ConversationState, advance


def test_followup_switch_and_document_mention():
    state = advance(ConversationState(session_id="s"), "Certificat de résidence", "fr")
    assert state.current_procedure_id == "residence_certificate"
    state = advance(state, "Et le prix ?", "fr")
    assert state.current_procedure_id == "residence_certificate"
    assert state.last_user_intent == "fees"
    state = advance(state, "J'ai une CIN", "fr")
    assert state.current_procedure_id == "residence_certificate"
    assert "identity_card" in state.mentioned_documents
    state = advance(state, "Comment renouveler ma carte d'identité ?", "fr")
    assert state.current_procedure_id == "identity_card"
    assert state.turn_count == 4
    assert state.last_updated.tzinfo is not None
    state = advance(state, "Nouveau sujet", "fr")
    assert state.current_procedure_id is None
    assert state.stage == "exploring"
    assert state.mentioned_documents == []


def test_validation_and_profiles():
    with pytest.raises(ValidationError):
        ConversationState(session_id="s", stage="ready")
    a = ConversationState(session_id="a")
    b = ConversationState(session_id="b")
    a.mentioned_documents.append("cin")
    assert b.mentioned_documents == []
    assert advance(b, "Quels documents pour un mineur ?", "fr").user_type is None
    assert advance(b, "Je suis étudiant", "fr").user_type == "student"
    assert advance(b, "Je suis médecin", "fr").current_procedure_id is None


def test_replay_ignores_corrupt_snapshot(client, monkeypatch):
    from app.models import ChatMessage
    from app.db.database import SessionLocal
    monkeypatch.setattr("app.rag_service.query_rag", lambda **kwargs: {"answer": "test"})
    client.post("/api/chat/messages", json={"content": "Certificat de résidence", "sessionId": "corrupt-test", "language": "fr"})
    with SessionLocal() as db:
        row = db.query(ChatMessage).filter_by(session_id="corrupt-test", sender="user").one()
        row.conversation_state = {"stage": "invalid", "turn_count": -10}
        db.commit()
    state = client.get("/api/chat/sessions/corrupt-test/state").json()
    assert state["current_procedure_id"] == "residence_certificate"
    assert state["turn_count"] == 1


def test_legacy_session_can_be_continued_and_deleted(client, monkeypatch):
    monkeypatch.setattr("app.rag_service.query_rag", lambda **kwargs: {"answer": "test"})
    response = client.post("/api/chat/messages", json={"content": "Certificat de résidence", "sessionId": "legacy"})
    assert response.status_code == 201
    assert response.json()["conversationState"]["session_id"] == "legacy"
    state = client.get("/api/chat/sessions/legacy/state")
    assert state.status_code == 200
    assert state.json()["current_procedure_id"] == "residence_certificate"
    client.delete("/api/chat/sessions/legacy")
    assert client.get("/api/chat/sessions/legacy/state").status_code == 404


def test_state_persists_and_is_scoped_to_owner(client, monkeypatch):
    captured = []
    def fake_query(**kwargs):
        captured.append(kwargs)
        return {"answer": "Test", "confidence": .7, "sources": []}
    monkeypatch.setattr("app.rag_service.query_rag", fake_query)
    for text in ["Certificat de résidence", "Et le prix ?"]:
        response = client.post("/api/chat/messages", json={"content": text, "language": "fr", "sessionId": "state-test"})
        assert response.status_code == 201
    state = client.get("/api/chat/sessions/state-test/state").json()
    assert state["turn_count"] == 2
    assert state["last_user_intent"] == "fees"
    assert captured[-1]["service_type"] == "residence_certificate"
    assert captured[-1]["conversation_state"]["turn_count"] == 2
    other = client.post("/api/auth/signup", json={"fullName": "State Other", "email": "state-other@example.test", "password": "secret123"}).json()
    denied = client.get("/api/chat/sessions/state-test/state", headers={"Authorization": f"Bearer {other['token']}"})
    assert denied.status_code == 404
    client.delete("/api/chat/sessions/state-test")
    assert client.get("/api/chat/sessions/state-test/state").status_code == 404
