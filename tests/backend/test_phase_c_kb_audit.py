"""Durable Phase C knowledge-base consistency and isolation checks."""
from __future__ import annotations

import json
from collections import defaultdict

import pytest

from app.rag_service import OmniAgentRAG
from app.services.procedure_schema import (
    PROCEDURE_DIRS,
    SUGGESTION_TEMPLATES,
    _searchable,
    load_normalized_procedure,
    procedure_path,
    suggested_questions,
)
from scripts.build_bge_index import REQUIRED_CHUNK_METADATA, audit_chunks, load_chunks


DEFERRED_ID = "administrative_certificate"
MIGRATED_IDS = tuple(pid for pid in PROCEDURE_DIRS if pid != DEFERRED_ID)
NORMALIZED_FIELDS = {
    "procedure_id", "title_ar", "title_fr", "aliases", "description",
    "eligibility", "required_documents", "steps", "where_to_apply",
    "personal_presence", "fees", "processing_time", "validity",
    "special_cases", "rejection_reasons", "faq", "sources", "last_updated",
}


def _supported(procedure: dict, section: str) -> bool:
    value = procedure.get(section)
    if section == "where_to_apply":
        return any(item not in (None, "") for item in value.values())
    if section == "personal_presence":
        return value.get("required") is not None or bool(value.get("exceptions"))
    if section == "fees":
        return value.get("amount") not in (None, "") or value.get("notes") not in (None, "")
    return value not in (None, "", [], {})


@pytest.mark.parametrize("procedure_id", MIGRATED_IDS)
def test_every_migrated_file_has_exact_normalized_schema(procedure_id):
    raw = json.loads(procedure_path(procedure_id).read_text(encoding="utf-8"))

    assert set(raw) == NORMALIZED_FIELDS
    assert raw["procedure_id"] == procedure_id
    assert isinstance(raw["title_ar"], str) and raw["title_ar"].strip()
    assert isinstance(raw["title_fr"], str) and raw["title_fr"].strip()
    assert isinstance(raw["aliases"], list) and raw["aliases"]
    assert isinstance(raw["description"], str) and raw["description"].strip()
    assert isinstance(raw["eligibility"], list)
    assert isinstance(raw["required_documents"], list)
    assert isinstance(raw["steps"], list)
    assert set(raw["where_to_apply"]) == {"type", "description"}
    assert set(raw["personal_presence"]) == {"required", "exceptions"}
    assert raw["personal_presence"]["required"] in (True, False, None)
    assert isinstance(raw["personal_presence"]["exceptions"], list)
    assert set(raw["fees"]) == {"amount", "notes"}
    assert raw["processing_time"] is None or isinstance(raw["processing_time"], str)
    assert raw["validity"] is None or isinstance(raw["validity"], str)
    assert isinstance(raw["special_cases"], list)
    assert isinstance(raw["rejection_reasons"], list)
    assert isinstance(raw["faq"], list)
    assert isinstance(raw["sources"], list) and raw["sources"]
    assert raw["last_updated"] is None or isinstance(raw["last_updated"], str)
    assert "todo" not in json.dumps(raw, ensure_ascii=False).casefold()
    assert "placeholder" not in json.dumps(raw, ensure_ascii=False).casefold()


def test_aliases_and_faqs_have_no_normalized_duplicates_or_exact_collisions():
    owners: dict[str, set[str]] = defaultdict(set)

    for procedure_id in PROCEDURE_DIRS:
        procedure = load_normalized_procedure(procedure_id)
        normalized_aliases = [_searchable(alias) for alias in procedure["aliases"]]
        assert len(normalized_aliases) == len(set(normalized_aliases)), procedure_id
        for alias in normalized_aliases:
            owners[alias].add(procedure_id)

        normalized_faqs = [_searchable(item["question"]) for item in procedure["faq"]]
        assert len(normalized_faqs) == len(set(normalized_faqs)), procedure_id

    assert {
        alias: procedure_ids
        for alias, procedure_ids in owners.items()
        if len(procedure_ids) > 1
    } == {}


@pytest.mark.parametrize("procedure_id", PROCEDURE_DIRS)
def test_suggestions_only_use_supported_sections_or_own_faq(procedure_id):
    procedure = load_normalized_procedure(procedure_id)
    suggestions = suggested_questions(procedure_id, "darija")
    supported_templates = {
        translations["darija"]
        for section, translations in SUGGESTION_TEMPLATES.items()
        if _supported(procedure, section)
    }
    own_faq = {item["question"] for item in procedure["faq"]}

    assert set(suggestions) <= supported_templates | own_faq
    for section, translations in SUGGESTION_TEMPLATES.items():
        if not _supported(procedure, section):
            assert translations["darija"] not in suggestions


def test_generated_index_payload_is_complete_unique_and_non_orphaned():
    chunks = load_chunks()
    chunk_ids = [chunk.chunk_id for chunk in chunks]
    procedure_ids = {chunk.metadata["procedure_id"] for chunk in chunks}

    assert audit_chunks(chunks) == (0, 0)
    assert len(chunk_ids) == len(set(chunk_ids))
    assert procedure_ids == set(PROCEDURE_DIRS)
    assert all(REQUIRED_CHUNK_METADATA <= set(chunk.metadata) for chunk in chunks)


@pytest.fixture(scope="module")
def actual_chroma_engine():
    pytest.importorskip("chromadb")
    pytest.importorskip("sentence_transformers")
    engine = OmniAgentRAG()
    if not engine.vector_retriever:
        pytest.skip("actual Chroma retriever is unavailable")
    engine._gemini = None
    return engine


@pytest.mark.parametrize("procedure_id", PROCEDURE_DIRS)
def test_actual_chroma_required_documents_is_isolated_and_preferred(
    procedure_id, actual_chroma_engine
):
    result = actual_chroma_engine.query(
        "شنو الوثائق المطلوبة؟",
        service_type=procedure_id,
    )
    chunks = result["retrieved_chunks"]

    assert result["backend"] == "chroma_bge_m3"
    assert chunks
    assert chunks[0]["section"] == "required_documents"
    assert chunks[0]["score"] is not None
    assert {chunk["procedure_id"] for chunk in chunks} == {procedure_id}
