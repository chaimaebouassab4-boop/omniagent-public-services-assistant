"""BGE-M3 dense retrieval. Scores are cosine similarities, not probabilities."""
import math
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

MODEL = "BAAI/bge-m3"
COLLECTION = "public_services_bge_m3_cosine"


class RetrievedChunk(BaseModel):
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    similarity_score: float = Field(ge=-1, le=1)


class RetrievalResult(BaseModel):
    chunks: list[RetrievedChunk] = Field(default_factory=list)
    confidence: float = Field(default=0, ge=0, le=1)
    threshold: float = 0
    candidate_count: int = 0
    backend: str = "chroma_bge_m3"


def select_chunks(chunks: list[RetrievedChunk], floor: float = 0.45,
                  relative_margin: float = 0.12) -> RetrievalResult:
    """Keep the strong cluster near the best hit; reject uniformly weak hits.

    Parameters are calibration defaults, not universal BGE decision boundaries.
    Confidence combines best relevance and support, not a correctness probability.
    """
    ranked = sorted(chunks, key=lambda c: c.similarity_score, reverse=True)
    if not ranked:
        return RetrievalResult()
    threshold = max(floor, ranked[0].similarity_score - relative_margin)
    seen = set()
    kept = []
    for chunk in ranked:
        key = " ".join(chunk.content.split())
        if key and key not in seen and chunk.similarity_score >= threshold:
            kept.append(chunk)
            seen.add(key)
    confidence = 0.0
    if kept:
        scores = [c.similarity_score for c in kept]
        confidence = max(0.0, min(1.0, 0.6 * scores[0] + 0.4 * sum(scores) / len(scores)))
        if len(kept) == 1:
            confidence *= 0.85
    return RetrievalResult(chunks=kept, confidence=round(confidence, 4),
                           threshold=threshold, candidate_count=len(ranked))


class VectorRetriever:
    def __init__(self, collection, encoder):
        self.collection = collection
        self.encoder = encoder
        meta = collection.metadata or {}
        if meta.get("embedding_model") != MODEL or meta.get("hnsw:space") != "cosine":
            raise ValueError("Collection incompatible: rebuild with BGE-M3 and cosine; do not reuse E5/L2 vectors")
        if meta.get("build_complete") is not True:
            raise ValueError("Collection build is incomplete")

    @classmethod
    def from_environment(cls):
        import chromadb
        from sentence_transformers import SentenceTransformer
        root = Path(__file__).resolve().parents[3]
        client = chromadb.PersistentClient(path=os.getenv("CHROMA_PATH", str(root / "chroma_db")))
        collection = client.get_collection(os.getenv("CHROMA_COLLECTION", COLLECTION), embedding_function=None)
        # Validate collection before loading a large model.
        instance = cls(collection, None)
        instance.encoder = SentenceTransformer(MODEL)
        return instance

    def retrieve(self, query: str, service: str | None = None, top_k: int = 20) -> RetrievalResult:
        if not 15 <= top_k <= 20:
            raise ValueError("top_k must be between 15 and 20")
        count = self.collection.count()
        if not count:
            return RetrievalResult()
        vector = self.encoder.encode([query], normalize_embeddings=True)[0].tolist()
        if len(vector) != 1024:
            raise ValueError("BGE-M3 must produce 1024-dimensional embeddings")
        kwargs = {"where": {"service_type": service}} if service else {}
        result = self.collection.query(query_embeddings=[vector], n_results=min(top_k, count),
                                       include=["documents", "metadatas", "distances"], **kwargs)
        chunks = []
        for content, metadata, distance in zip(result["documents"][0], result["metadatas"][0], result["distances"][0]):
            if content and distance is not None and math.isfinite(distance):
                chunks.append(RetrievedChunk(content=content, metadata=metadata or {},
                    similarity_score=max(-1.0, min(1.0, 1.0 - distance))))
        return select_chunks(chunks)
