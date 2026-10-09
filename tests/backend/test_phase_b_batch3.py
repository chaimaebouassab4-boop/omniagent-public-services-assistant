"""Phase B / Batch 3 normalized knowledge-base regression coverage."""
from __future__ import annotations

from collections import Counter

import pytest

from app.rag_service import OmniAgentRAG
from scripts.build_bge_index import audit_chunks, load_chunks
from app.services.procedure_schema import (
    ConversationState,
    detect_explicit_procedure,
    generate_procedure_chunks,
    load_normalized_procedure,
    procedure_path,
    suggested_questions,
)


PROCEDURE_ID = "identity_card"
DIRECT_QUESTION = "بغيت نجدد البطاقة الوطنية"
ALIASES = (
    "البطاقة الوطنية للتعريف الإلكترونية",
    "carte nationale d'identité électronique",
    "bita9a wataniya",
)
NORMALIZED_FIELDS = {
    "procedure_id", "title_ar", "title_fr", "aliases", "description",
    "eligibility", "required_documents", "steps", "where_to_apply",
    "personal_presence", "fees", "processing_time", "validity",
    "special_cases", "rejection_reasons", "faq", "sources", "last_updated",
}
REQUIRED_METADATA = {
    "procedure_id", "section", "language", "source_type", "file_path",
    "service_type", "node_type",
}


def test_batch3_identity_card_uses_complete_normalized_schema():
    procedure = load_normalized_procedure(PROCEDURE_ID)

    assert set(procedure) == NORMALIZED_FIELDS | {"extra_sections"}
    assert procedure["procedure_id"] == PROCEDURE_ID
    assert procedure["title_ar"]
    assert procedure["title_fr"]
    assert procedure["aliases"]
    assert procedure["sources"] == [
        "https://adala.justice.gov.ma/api/uploads/2025/02/27/%D9%85%D8%B1%D8%B3%D9%88%D9%85%20%D8%B1%D9%82%D9%85%202.20.521%20%D9%84%D8%AA%D8%B7%D8%A8%D9%8A%D9%82%20%D8%A3%20%D8%A7%D9%84%D8%A5%D9%84%D9%83%D8%AA%D8%B1%D9%88%D9%86%D9%8A%D8%A9-1740673016703.pdf",
        "https://www.cnie.ma",
    ]
    assert procedure["extra_sections"] == {}


def test_batch3_explicit_followup_location_and_topic_switch():
    state = ConversationState(current_procedure_id="life_certificate")

    switched = state.resolve(DIRECT_QUESTION)
    documents = state.resolve("شنو الوثائق؟")
    location = state.resolve("فين نمشي؟")

    assert switched.procedure_id == PROCEDURE_ID
    assert switched.resolution == "explicit"
    assert documents.procedure_id == PROCEDURE_ID
    assert documents.resolution == "inherited"
    assert documents.section == "required_documents"
    assert location.procedure_id == PROCEDURE_ID
    assert location.resolution == "inherited"
    assert location.section == "where_to_apply"


@pytest.mark.parametrize("alias", ALIASES)
def test_batch3_aliases_cover_arabic_french_and_darija(alias):
    assert detect_explicit_procedure(f"عافاك {alias}") == PROCEDURE_ID


def test_batch3_chunks_are_section_level_and_metadata_complete():
    path = procedure_path(PROCEDURE_ID)
    procedure = load_normalized_procedure(PROCEDURE_ID)
    chunks = generate_procedure_chunks(procedure, path)
    counts = Counter(chunk.metadata["section"] for chunk in chunks)

    assert counts["description"] == 1
    assert counts["required_documents"] == 4
    assert counts["steps"] == 1
    assert counts["where_to_apply"] == 1
    assert counts["personal_presence"] == 1
    assert counts["faq"] == len(procedure["faq"])
    assert all(REQUIRED_METADATA <= set(chunk.metadata) for chunk in chunks)
    assert all(chunk.metadata["procedure_id"] == PROCEDURE_ID for chunk in chunks)
    assert all(chunk.metadata["source_type"] == "official" for chunk in chunks)
    assert all(chunk.text.strip() for chunk in chunks)


def test_batch3_unsupported_timing_remains_null_and_unchunked():
    procedure = load_normalized_procedure(PROCEDURE_ID)
    chunks = generate_procedure_chunks(procedure, procedure_path(PROCEDURE_ID))

    assert procedure["processing_time"] is None
    assert "processing_time" not in {chunk.metadata["section"] for chunk in chunks}


def test_batch3_index_payload_passes_chunk_audit():
    chunks = load_chunks({PROCEDURE_ID})

    assert audit_chunks(chunks) == (0, 0)


def test_batch3_suggested_questions_are_contextual_and_source_backed():
    suggestions = suggested_questions(PROCEDURE_ID, "darija")

    assert "شنو الوثائق المطلوبة؟" in suggestions
    assert "واش الحضور الشخصي ضروري؟" in suggestions
    assert "فين نقدر نقدّم الطلب؟" in suggestions
    assert "شحال كتبقى صالحة؟" in suggestions
    assert "شحال كتحتاج من الوقت؟" not in suggestions
    assert all(term not in " ".join(suggestions) for term in ("السكنى", "السجل العدلي", "الزواج"))


@pytest.fixture(scope="module")
def batch3_rag_engine():
    engine = OmniAgentRAG()
    engine._gemini = None
    return engine


def test_batch3_retrieval_is_strictly_procedure_isolated(batch3_rag_engine):
    result = batch3_rag_engine.query(
        "شنو الوثائق المطلوبة؟",
        service_type=PROCEDURE_ID,
    )

    expected_backend = (
        "chroma_bge_m3" if batch3_rag_engine.vector_retriever
        else "bm25_fallback"
    )
    assert result["backend"] == expected_backend
    assert result["retrieved_chunks"]
    assert {
        chunk["procedure_id"] for chunk in result["retrieved_chunks"]
    } == {PROCEDURE_ID}


def _headers(client, email: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/signup",
        json={
            "fullName": "Batch Three API User",
            "email": email,
            "password": "secret123",
        },
    )
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}


def _chat(client, headers, session_id: str, question: str):
    response = client.post(
        "/api/chat/messages",
        headers=headers,
        json={"sessionId": session_id, "content": question},
    )
    assert response.status_code == 201, response.text
    assert response.json()["content"]
    return response.json()["procedureId"]


def test_batch3_api_cross_procedure_switch_sequence(
    client, monkeypatch, batch3_rag_engine
):
    monkeypatch.setattr("app.rag_service._rag_instance", batch3_rag_engine)
    headers = _headers(client, "batch-three-switch@demo.ma")
    session_id = "batch3-switch"

    procedure_ids = [
        _chat(client, headers, session_id, "بغيت نجدد البطاقة الوطنية"),
        _chat(client, headers, session_id, "شنو الوثائق؟"),
        _chat(client, headers, session_id, "دابا بغيت شهادة السكنى"),
        _chat(client, headers, session_id, "فين نمشي؟"),
    ]

    assert procedure_ids == [
        "identity_card",
        "identity_card",
        "residence_certificate",
        "residence_certificate",
    ]


def test_batch3_api_new_sessions_do_not_leak_state(
    client, monkeypatch, batch3_rag_engine
):
    monkeypatch.setattr("app.rag_service._rag_instance", batch3_rag_engine)
    headers = _headers(client, "batch-three-isolation@demo.ma")

    identity_ids = [
        _chat(client, headers, "batch3-isolation-identity", "بغيت نجدد CNIE"),
        _chat(client, headers, "batch3-isolation-identity", "شنو الوثائق؟"),
    ]
    criminal_ids = [
        _chat(client, headers, "batch3-isolation-criminal", "بغيت السجل العدلي"),
        _chat(client, headers, "batch3-isolation-criminal", "فين نمشي؟"),
    ]

    assert identity_ids == ["identity_card", "identity_card"]
    assert criminal_ids == ["criminal_record", "criminal_record"]
