"""Offline retrieval-quality tests for the knowledge base answer engine.

These cover the keyword retrieval layer used by /api/chat. The full
LLM RAG pipeline (Ollama + BGE-M3) lives in tests/llama_rag and needs a
running Ollama server, so it is exercised separately.

Run from the repo root:
    backend/.venv/Scripts/python.exe -m pytest tests/ai -v
"""
import json
from pathlib import Path

import pytest

from app.services.knowledge_base import (
    LOW_CONFIDENCE_THRESHOLD,
    SERVICE_DIRS,
    answer_with_metadata,
    load_service_knowledge,
    normalize_service_id,
    _tokenize,
)

KB_ROOT = Path(__file__).resolve().parents[1] / "knowledge_base"
DATASET_PATH = KB_ROOT / "test_cases.json" / "all_test_cases.json"


def test_aliases_normalize_to_canonical_ids():
    assert normalize_service_id("residence") == "residence_certificate"
    assert normalize_service_id("Marriage") == "marriage_contract"
    assert normalize_service_id("death") == "death_certificate"
    assert normalize_service_id(None) is None


@pytest.mark.parametrize("service_id", sorted(SERVICE_DIRS))
def test_every_service_has_knowledge(service_id):
    knowledge = load_service_knowledge(service_id)
    assert knowledge, f"no knowledge loaded for {service_id}"
    assert knowledge.get("faq"), f"no FAQ entries for {service_id}"


@pytest.mark.parametrize("service_id", sorted(SERVICE_DIRS))
def test_faq_questions_retrieve_their_own_answers(service_id):
    """Asking an exact FAQ question must return that FAQ answer."""
    knowledge = load_service_knowledge(service_id)
    hits = 0
    faq = knowledge["faq"]
    for entry in faq:
        result = answer_with_metadata(service_id, entry["question"])
        if result.answer.strip() == str(entry["answer"]).strip():
            hits += 1
    assert hits / len(faq) >= 0.8, f"{service_id}: only {hits}/{len(faq)} FAQ self-retrievals"


def test_answer_includes_confidence_and_sources():
    result = answer_with_metadata("residence", "شنو الوثائق المطلوبة لشهادة السكنى؟")
    assert 0.0 < result.confidence <= 1.0
    assert result.sources
    assert result.sources[0].startswith("residence/")


def test_off_topic_question_gets_low_confidence():
    result = answer_with_metadata("residence", "شروط السفر إلى القمر بالمكوك الفضائي")
    assert result.confidence <= 0.55, "off-topic question should not be answered confidently"


def test_unknown_service_falls_back_gracefully():
    result = answer_with_metadata("passport_renewal", "شنو الوثائق؟")
    assert result.answer


def test_evaluation_dataset_keyword_recall():
    """The /api/chat engine should cover most expected keywords of the eval set."""
    with DATASET_PATH.open(encoding="utf-8") as handle:
        cases = json.load(handle)
    assert len(cases) >= 15

    passing = 0
    for case in cases:
        result = answer_with_metadata(case["service_type"], case["query"])
        expected_tokens = _tokenize(case["expected_answer"])
        answer_tokens = _tokenize(result.answer)
        recall = len(expected_tokens & answer_tokens) / max(1, len(expected_tokens))
        if recall >= 0.30:
            passing += 1
    assert passing / len(cases) >= 0.60, f"only {passing}/{len(cases)} eval cases passed"
