"""Regression coverage for procedure-aware multi-turn chat and retrieval."""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from google.genai import errors

from app.rag_service import (
    KBNode,
    OmniAgentRAG,
    ScoredNode,
    _llm_generate,
    _load_kb_nodes,
)
from app.services.gemini_client import GeminiRequestError, generate_text
from app.services.procedure_schema import (
    ConversationState,
    generate_procedure_chunks,
    load_normalized_procedure,
    procedure_path,
    suggested_questions,
)


def _headers(client, suffix: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/signup",
        json={
            "fullName": f"Procedure Test {suffix}",
            "email": f"procedure-{suffix}@demo.ma",
            "password": "secret123",
        },
    )
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}


def _fake_rag(calls):
    def query_rag(user_query, service_type=None, conversation_history=None):
        calls.append({
            "query": user_query,
            "procedure_id": service_type,
            "history": conversation_history,
        })
        return {
            "answer": f"answer for {service_type}",
            "confidence": 0.9,
            "sources": ["test"],
            "language": "darija",
        }
    return query_rag


def test_same_procedure_followups_remain_life_certificate(client, monkeypatch):
    calls = []
    monkeypatch.setattr("app.rag_service.query_rag", _fake_rag(calls))
    headers = _headers(client, "same-procedure")
    session_id = "life-followups"

    responses = [
        client.post("/api/chat/messages", headers=headers, json={"sessionId": session_id, "content": question})
        for question in ("كيفاش نخرج شهادة الحياة؟", "شنو الوثائق؟", "فين نقدر نصاوبها؟")
    ]

    assert all(response.status_code == 201 for response in responses)
    assert [call["procedure_id"] for call in calls] == ["life_certificate"] * 3
    assert [response.json()["procedureId"] for response in responses] == ["life_certificate"] * 3


def test_explicit_topic_switch_overrides_then_followup_inherits(client, monkeypatch):
    calls = []
    monkeypatch.setattr("app.rag_service.query_rag", _fake_rag(calls))
    headers = _headers(client, "topic-switch")
    session_id = "switch-procedure"

    for question in ("كيفاش نجدد CNIE؟", "دابا بغيت شهادة الحياة", "فين نقدر نصاوبها؟"):
        response = client.post(
            "/api/chat/messages",
            headers=headers,
            json={"sessionId": session_id, "content": question},
        )
        assert response.status_code == 201, response.text

    assert [call["procedure_id"] for call in calls] == [
        "identity_card",
        "life_certificate",
        "life_certificate",
    ]


def test_sessions_keep_procedure_state_isolated(client, monkeypatch):
    calls = []
    monkeypatch.setattr("app.rag_service.query_rag", _fake_rag(calls))
    headers = _headers(client, "isolated-sessions")

    for session_id, question in (
        ("identity-session", "بغيت CNIE"),
        ("life-session", "بغيت شهادة الحياة"),
        ("identity-session", "شنو الوثائق؟"),
        ("life-session", "فين نقدر نصاوبها؟"),
    ):
        response = client.post(
            "/api/chat/messages",
            headers=headers,
            json={"sessionId": session_id, "content": question},
        )
        assert response.status_code == 201, response.text

    assert [call["procedure_id"] for call in calls] == [
        "identity_card",
        "life_certificate",
        "identity_card",
        "life_certificate",
    ]


def test_retrieval_is_strictly_isolated_to_resolved_procedure():
    engine = OmniAgentRAG()
    engine._gemini = None
    engine.vector_retriever = False  # deterministic local fallback in unit tests
    result = engine.query("شنو الوثائق؟", service_type="life_certificate")

    assert result["retrieved_chunks"]
    assert {chunk["procedure_id"] for chunk in result["retrieved_chunks"]} == {"life_certificate"}


def test_life_suggestions_and_chunks_are_procedure_contextual():
    suggestions = suggested_questions("life_certificate", "darija")
    assert "شنو الوثائق المطلوبة؟" in suggestions
    assert "واش الحضور الشخصي ضروري؟" in suggestions
    unrelated = ("CNIE", "السكنى", "الوفاة", "السجل العدلي")
    assert all(term not in " ".join(suggestions) for term in unrelated)

    procedure = load_normalized_procedure("life_certificate")
    chunks = generate_procedure_chunks(procedure, procedure_path("life_certificate"))
    sections = {chunk.metadata["section"] for chunk in chunks}
    assert {"required_documents", "steps", "where_to_apply", "personal_presence", "fees", "faq"} <= sections
    assert all(chunk.metadata["procedure_id"] == "life_certificate" for chunk in chunks)
    assert all(chunk.metadata["source_type"] == "official" for chunk in chunks)


def test_aliases_and_conversation_state_support_three_initial_procedures():
    assert ConversationState().resolve("chahadat lhayat").procedure_id == "life_certificate"
    assert ConversationState().resolve("bita9a wataniya").procedure_id == "identity_card"
    assert ConversationState().resolve("chahadat l3ozoba").procedure_id == "single_status_certificate"

    nodes = _load_kb_nodes()
    assert any(node.metadata.get("procedure_id") == "identity_card" for node in nodes)
    assert any(node.metadata.get("procedure_id") == "single_status_certificate" for node in nodes)


def test_chat_request_emits_complete_safe_development_trace(client, monkeypatch):
    events = []

    def capture(section, **fields):
        events.append((section, fields))

    monkeypatch.setattr("app.api.omni.development_trace", capture)
    monkeypatch.setattr(
        "app.rag_service.query_rag",
        lambda **kwargs: {
            "answer": "local answer",
            "backend": "chroma_bge_m3",
            "procedure_id": kwargs["service_type"],
            "section": "required_documents",
            "retrieved_chunks": [{
                "procedure_id": "life_certificate",
                "section": "required_documents",
                "score": 0.88,
            }],
            "llm_status": "fallback",
            "llm_fallback_reason": "gemini_rate_limited_http_429",
        },
    )
    headers = _headers(client, "development-trace")

    response = client.post(
        "/api/chat/messages",
        headers=headers,
        json={"sessionId": "trace-session", "content": "شنو وثائق شهادة الحياة؟"},
    )

    assert response.status_code == 201
    assert [event[0] for event in events] == [
        "CHAT", "STATE BEFORE", "ROUTER", "RAG", "LLM", "STATE AFTER",
    ]
    assert events[0][1] == {"session_id": "trace-session"}
    assert events[2][1]["resolution"] == "explicit"
    assert events[3][1]["procedure_filter"] == "life_certificate"
    assert events[3][1]["top_chunks"] == [{
        "procedure_id": "life_certificate",
        "section": "required_documents",
        "similarity": 0.88,
    }]
    assert events[4][1] == {
        "provider": "gemini",
        "status": "fallback",
        "fallback_reason": "gemini_rate_limited_http_429",
    }
    assert "content" not in str(events)


def test_gemini_failure_diagnostic_is_categorical_and_redacted(monkeypatch, capsys):
    monkeypatch.setattr(
        "app.rag_service.generate_text",
        lambda **kwargs: (_ for _ in ()).throw(
            GeminiRequestError("HTTP 429 request failed with secret-token")
        ),
    )
    diagnostics = {}

    result = _llm_generate(("not-a-real-key", "test-model"), "private prompt", diagnostics)

    assert result == ""
    assert diagnostics == {
        "status": "fallback",
        "fallback_reason": "gemini_rate_limited_http_429",
    }
    output = capsys.readouterr().out
    assert "secret-token" not in output
    assert "private prompt" not in output


def _chroma_ready_engine() -> OmniAgentRAG:
    engine = OmniAgentRAG.__new__(OmniAgentRAG)
    engine.initialized = True
    engine.vector_retriever = True
    engine.bm25_retriever = False
    engine._bm25_index = None
    engine._bm25_nodes = []
    engine._rewrite_cache = {}
    engine._gemini = ("not-a-real-key", "test-model")
    engine._retrieve_chroma = lambda **kwargs: [
        ScoredNode(
            KBNode(
                "الوثائق المطلوبة لشهادة الحياة: بطاقة التعريف.",
                {
                    "procedure_id": "life_certificate",
                    "section": "required_documents",
                },
            ),
            0.91,
        )
    ]
    return engine


def test_chroma_chat_uses_one_gemini_call_for_answer_only(monkeypatch):
    calls = []

    def fake_generate(**kwargs):
        calls.append(kwargs)
        return "generated answer"

    monkeypatch.setattr("app.rag_service.generate_text", fake_generate)
    result = _chroma_ready_engine().query(
        "عافاك شنو الوراق المطلوبة دابا؟",
        service_type="life_certificate",
    )

    assert result["answer"] == "generated answer"
    assert result["llm_status"] == "success"
    assert len(calls) == 1
    assert "المعلومات المتوفرة" in calls[0]["contents"]
    assert "أنت مترجم متخصص" not in calls[0]["contents"]


def test_chroma_429_uses_local_answer_without_second_gemini_call(monkeypatch):
    calls = []

    def rate_limited(**kwargs):
        calls.append(kwargs)
        raise GeminiRequestError(
            "Gemini is temporarily unavailable.",
            reason="gemini_rate_limited_http_429",
            status_code=429,
        )

    monkeypatch.setattr("app.rag_service.generate_text", rate_limited)
    result = _chroma_ready_engine().query(
        "عافاك شنو الوراق المطلوبة دابا؟",
        service_type="life_certificate",
    )

    assert len(calls) == 1
    assert result["answer"].startswith("الوثائق المطلوبة")
    assert result["llm_status"] == "fallback"
    assert result["llm_fallback_reason"] == "gemini_rate_limited_http_429"


def test_bm25_rewrite_429_skips_answer_generation_retry(monkeypatch):
    calls = []

    def rate_limited(**kwargs):
        calls.append(kwargs)
        raise GeminiRequestError(
            "Gemini is temporarily unavailable.",
            reason="gemini_rate_limited_http_429",
            status_code=429,
        )

    class FakeBm25:
        def get_scores(self, tokens):
            return [1.0]

    engine = _chroma_ready_engine()
    engine.vector_retriever = False
    engine.bm25_retriever = True
    engine._retrieve_chroma = lambda **kwargs: []
    engine._bm25_index = FakeBm25()
    engine._bm25_nodes = [
        KBNode(
            "عافاك شنو الوراق المطلوبة دابا شهادة الحياة",
            {
                "procedure_id": "life_certificate",
                "section": "required_documents",
            },
        )
    ]
    monkeypatch.setattr("app.rag_service.generate_text", rate_limited)

    result = engine.query(
        "عافاك شنو الوراق المطلوبة دابا؟",
        service_type="life_certificate",
    )

    assert len(calls) == 1
    assert "أنت مترجم متخصص" in calls[0]["contents"]
    assert result["backend"] == "bm25_fallback"
    assert result["llm_status"] == "fallback"
    assert result["llm_fallback_reason"] == "gemini_rate_limited_http_429"


@pytest.mark.parametrize(
    ("status_code", "expected_reason"),
    [
        (429, "gemini_rate_limited_http_429"),
        (503, "gemini_service_unavailable_http_503"),
    ],
)
def test_gemini_client_redacts_expected_provider_failures(
    monkeypatch, caplog, status_code, expected_reason
):
    captured_configs = []

    class FakeModels:
        def generate_content(self, **kwargs):
            captured_configs.append(kwargs["config"])
            raise errors.APIError(
                status_code,
                {"error": {"status": "RESOURCE_EXHAUSTED", "secret": "payload"}},
            )

    class FakeClient:
        models = FakeModels()

        def close(self):
            pass

    monkeypatch.setattr(
        "app.services.gemini_client.genai.Client",
        lambda **kwargs: FakeClient(),
    )

    with pytest.raises(GeminiRequestError) as caught:
        generate_text(
            api_key="not-a-real-key",
            model="test-model",
            contents="private citizen message",
        )

    assert caught.value.reason == expected_reason
    assert caught.value.status_code == status_code
    assert captured_configs[0].automatic_function_calling.disable is True
    assert "payload" not in caplog.text
    assert "private citizen message" not in caplog.text
