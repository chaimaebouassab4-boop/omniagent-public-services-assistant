"""Regression tests for complete CNIE retrieval in the production RAG path."""

from app.rag_service import OmniAgentRAG, _detect_service_from_query, _load_kb_nodes
from app.services.knowledge_base import answer_with_metadata, normalize_service_id


def test_identity_card_aliases_and_multilingual_detection():
    assert normalize_service_id("CIN") == "identity_card"
    assert normalize_service_id("cnie") == "identity_card"
    assert _detect_service_from_query("Comment renouveler ma carte d'identité (CIN) ?") == "identity_card"
    assert _detect_service_from_query("كيفاش نجدد بطاقة التعريف الوطنية؟") == "identity_card"


def test_loader_indexes_all_structured_identity_fields():
    identity_nodes = [
        node for node in _load_kb_nodes()
        if node.metadata.get("service_type") == "identity_card"
    ]
    node_types = {node.metadata.get("node_type") for node in identity_nodes}
    assert "procedure_types" in node_types
    assert "legal_basis" in node_types
    assert "conditions" in node_types
    assert "issuing_authorities" in node_types


def test_cin_question_uses_identity_card_knowledge_without_llm():
    engine = OmniAgentRAG()
    engine._gemini = None
    result = engine.query("Comment renouveler ma carte d'identité (CIN) ?")

    assert result["sources"] == ["identity_card/identity_card.json"]
    assert "renouvel" in result["answer"].lower()
    assert "watiqa" not in result["answer"].lower()


def test_structured_fallback_answers_exact_cin_faq():
    result = answer_with_metadata(
        "identity_card",
        "Comment renouveler ma carte d'identité (CIN) ?",
        use_rag=False,
    )
    assert result.confidence >= 0.30
    assert result.sources == ["identity_card/identity_card.json"]
    assert "ancienne carte" in result.answer
