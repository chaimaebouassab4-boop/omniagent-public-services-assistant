"""Phase B / Batch 1 normalized knowledge-base regression coverage."""
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


BATCH1 = {
    "residence_certificate": {
        "direct": "بغيت شهادة السكنى",
        "aliases": ("شهادة الإقامة", "certificat de domicile", "chahadat sokna"),
    },
    "birth_certificate": {
        "direct": "بغيت عقد الازدياد",
        "aliases": ("رسم الولادة", "extrait d'acte de naissance", "3a9d l'izdiad"),
    },
    "criminal_record": {
        "direct": "بغيت السجل العدلي",
        "aliases": ("سجل عدلي", "extrait du casier judiciaire", "sijil 3adli"),
    },
    "death_certificate": {
        "direct": "بغيت مستخرج شهادة الوفاة",
        "aliases": ("رسم الوفاة", "extrait d'acte de décès", "mostakhraj chahadat lwafat"),
    },
}

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


@pytest.mark.parametrize("procedure_id", BATCH1)
def test_batch1_files_use_complete_normalized_schema(procedure_id):
    procedure = load_normalized_procedure(procedure_id)

    assert set(procedure) == NORMALIZED_FIELDS | {"extra_sections"}
    assert procedure["procedure_id"] == procedure_id
    assert procedure["title_ar"]
    assert procedure["title_fr"]
    assert procedure["aliases"]
    assert procedure["sources"]
    assert procedure["extra_sections"] == {}


@pytest.mark.parametrize("procedure_id", BATCH1)
def test_batch1_explicit_followup_location_and_topic_switch(procedure_id):
    direct = BATCH1[procedure_id]["direct"]
    state = ConversationState(current_procedure_id="life_certificate")

    switched = state.resolve(direct)
    documents = state.resolve("شنو الوثائق؟")
    location = state.resolve("فين نمشي؟")

    assert switched.procedure_id == procedure_id
    assert switched.resolution == "explicit"
    assert documents.procedure_id == procedure_id
    assert documents.resolution == "inherited"
    assert documents.section == "required_documents"
    assert location.procedure_id == procedure_id
    assert location.resolution == "inherited"
    assert location.section == "where_to_apply"


@pytest.mark.parametrize("procedure_id", BATCH1)
def test_batch1_aliases_cover_arabic_french_and_common_wording(procedure_id):
    for alias in BATCH1[procedure_id]["aliases"]:
        assert detect_explicit_procedure(f"عافاك {alias}") == procedure_id


@pytest.mark.parametrize("procedure_id", BATCH1)
def test_batch1_chunks_are_section_level_and_metadata_complete(procedure_id):
    path = procedure_path(procedure_id)
    procedure = load_normalized_procedure(procedure_id)
    chunks = generate_procedure_chunks(procedure, path)
    counts = Counter(chunk.metadata["section"] for chunk in chunks)

    assert counts["description"] == 1
    assert counts["required_documents"] >= 1
    assert counts["steps"] >= 1
    assert counts["where_to_apply"] == 1
    assert counts["faq"] == len(procedure["faq"])
    assert all(REQUIRED_METADATA <= set(chunk.metadata) for chunk in chunks)
    assert all(chunk.metadata["procedure_id"] == procedure_id for chunk in chunks)
    assert all(chunk.metadata["source_type"] == "official" for chunk in chunks)
    assert all(chunk.text.strip() for chunk in chunks)


def test_batch1_index_payload_passes_chunk_audit():
    chunks = load_chunks(set(BATCH1))

    assert audit_chunks(chunks) == (0, 0)


@pytest.mark.parametrize("procedure_id", BATCH1)
def test_batch1_suggested_questions_are_procedure_contextual(procedure_id):
    suggestions = suggested_questions(procedure_id, "darija")
    unrelated = {
        "residence_certificate": ("الازدياد", "السجل العدلي", "الوفاة"),
        "birth_certificate": ("السكنى", "السجل العدلي", "الوفاة"),
        "criminal_record": ("السكنى", "الازدياد", "الوفاة"),
        "death_certificate": ("السكنى", "الازدياد", "السجل العدلي"),
    }[procedure_id]

    assert "شنو الوثائق المطلوبة؟" in suggestions
    assert "فين نقدر نقدّم الطلب؟" in suggestions
    assert all(term not in " ".join(suggestions) for term in unrelated)


@pytest.fixture(scope="module")
def batch1_rag_engine():
    engine = OmniAgentRAG()
    engine._gemini = None
    return engine


@pytest.mark.parametrize("procedure_id", BATCH1)
def test_batch1_retrieval_is_strictly_procedure_isolated(
    procedure_id, batch1_rag_engine
):
    result = batch1_rag_engine.query(
        "شنو الوثائق المطلوبة؟",
        service_type=procedure_id,
    )

    expected_backend = (
        "chroma_bge_m3" if batch1_rag_engine.vector_retriever
        else "bm25_fallback"
    )
    assert result["backend"] == expected_backend
    assert result["retrieved_chunks"]
    assert {
        chunk["procedure_id"] for chunk in result["retrieved_chunks"]
    } == {procedure_id}


def _headers(client) -> dict[str, str]:
    response = client.post(
        "/api/auth/signup",
        json={
            "fullName": "Batch One API User",
            "email": "batch-one-api@demo.ma",
            "password": "secret123",
        },
    )
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_batch1_real_api_acceptance_scenarios(
    client, monkeypatch, batch1_rag_engine
):
    monkeypatch.setattr("app.rag_service._rag_instance", batch1_rag_engine)
    headers = _headers(client)
    scenarios = (
        (
            "batch1-residence",
            ("بغيت شهادة السكنى", "شنو الوثائق؟", "فين نقدر نديرها؟"),
            ("residence_certificate",) * 3,
        ),
        (
            "batch1-birth",
            ("بغيت عقد الازدياد", "شنو الوثائق؟", "شحال كتشد؟"),
            ("birth_certificate",) * 3,
        ),
        (
            "batch1-criminal",
            ("بغيت السجل العدلي", "شنو الوثائق المطلوبة؟", "فين نقدر نطلبو؟"),
            ("criminal_record",) * 3,
        ),
        (
            "batch1-death",
            ("بغيت مستخرج شهادة الوفاة", "شنو الوثائق؟"),
            ("death_certificate",) * 2,
        ),
        (
            "batch1-switch",
            (
                "بغيت شهادة السكنى",
                "شنو الوثائق؟",
                "دابا بغيت السجل العدلي",
                "شنو الوثائق المطلوبة؟",
            ),
            (
                "residence_certificate",
                "residence_certificate",
                "criminal_record",
                "criminal_record",
            ),
        ),
    )

    for session_id, questions, expected_procedures in scenarios:
        responses = [
            client.post(
                "/api/chat/messages",
                headers=headers,
                json={"sessionId": session_id, "content": question},
            )
            for question in questions
        ]
        assert all(response.status_code == 201 for response in responses)
        assert [
            response.json()["procedureId"] for response in responses
        ] == list(expected_procedures)
        assert all(response.json()["content"] for response in responses)
