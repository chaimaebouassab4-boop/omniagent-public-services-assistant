import math
from types import SimpleNamespace

import pytest

from app.services.vector_retrieval import MODEL, RetrievedChunk, VectorRetriever, select_chunks


def chunk(score, text=None):
    return RetrievedChunk(content=text or str(score), similarity_score=score)


def test_relative_selection_does_not_require_point_eight():
    result = select_chunks([chunk(.72), chunk(.67), chunk(.62), chunk(.49)])
    assert [c.similarity_score for c in result.chunks] == [.72, .67, .62]
    assert .6 < result.confidence < .8
    assert result.candidate_count == 4


def test_weak_empty_and_duplicate_results():
    assert not select_chunks([chunk(.24), chunk(.20)]).chunks
    assert select_chunks([]).confidence == 0
    assert len(select_chunks([chunk(.9, "same"), chunk(.89, "same")]).chunks) == 1


def test_rejects_wrong_embedding_space():
    with pytest.raises(ValueError, match="incompatible"):
        VectorRetriever(SimpleNamespace(metadata={"embedding_model": "intfloat/multilingual-e5-small"}), None)


def test_vector_pipeline_exposes_evidence_and_rejects_weak_hits(monkeypatch):
    from app.rag_service import OmniAgentRAG
    from app.services.vector_retrieval import RetrievalResult
    engine = OmniAgentRAG.__new__(OmniAgentRAG)
    engine.backend = "chroma"
    engine._gemini = None
    engine._vector = SimpleNamespace(retrieve=lambda *args: select_chunks([chunk(.74, "Relevant procedure")]))
    result = engine.query("Question")
    assert result["chunks"][0]["similarity_score"] == .74
    assert result["backend"] == "chroma_bge_m3"
    assert result["fallback_reason"] == "generation_unavailable_source_extracts"
    engine._vector = SimpleNamespace(retrieve=lambda *args: RetrievalResult())
    assert engine.query("Question")["confidence"] == 0
    assert engine.query("Question")["chunks"] == []


def test_real_chroma_cosine_distances(tmp_path):
    chromadb = pytest.importorskip("chromadb")
    import numpy as np
    collection = chromadb.PersistentClient(path=str(tmp_path / "chroma")).create_collection(
        "test_bge_cosine", embedding_function=None,
        metadata={"embedding_model": MODEL, "hnsw:space": "cosine", "build_complete": True})
    first = [1.0] + [0.0] * 1023
    close = [.7, math.sqrt(1-.7**2)] + [0.0] * 1022
    far = [0.0, 1.0] + [0.0] * 1022
    collection.add(ids=["1", "2", "3"], documents=["exact", "near", "unrelated"],
                   metadatas=[{"service_type": "residence"}] * 3, embeddings=[first, close, far])
    class Encoder:
        def encode(self, texts, normalize_embeddings):
            assert normalize_embeddings
            return np.array([first])
    result = VectorRetriever(collection, Encoder()).retrieve("question", "residence")
    assert result.candidate_count == 3
    assert result.chunks[0].content == "exact"
    assert result.chunks[0].similarity_score == pytest.approx(1)
    assert not VectorRetriever(collection, Encoder()).retrieve("question", "identity_card").chunks
