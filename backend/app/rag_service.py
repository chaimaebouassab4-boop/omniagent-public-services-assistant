"""RAG Service Module (OmniAgent RAG)

Wraps ChromaDB + LlamaIndex + BAAI/bge-m3 + a configurable LLM into a reusable service.
Provides query_rag(user_query, service_type) for FastAPI endpoints.
"""
import os
import re
from pathlib import Path
from typing import Any, Optional, List, Dict, Sequence
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Resolve project paths
THIS_FILE = Path(__file__).resolve()
# Root directory of the project (omniagent-public-services-assistant)
ROOT_DIR = THIS_FILE.parents[2]
CHROMA_DIR = ROOT_DIR / "chroma_db"
KNOWLEDGE_DIR = ROOT_DIR / "tests" / "knowledge_base"

# QA Prompt template in Moroccan Darija
QA_PROMPT_TMPL = (
    "المعلومات المتوفرة (sources):\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "أنت مساعد افتراضي مغربي. بناءً على المعلومات الفوق فقط، جاوب بالدارجة المغربية على السؤال التالي.\n"
    "مهم جداً: إذا كانت المعلومات لا تحتوي على الجواب أو كنت غير متأكد، قل حرفياً وبدون أي زيادة: \"ما متأكدش\" واطلب توضيح.\n"
    "لا تستخدم معلومات من خارج النص المتوفر.\n"
    "السؤال: {query_str}\n"
    "الجواب: "
)

ConversationMessage = Dict[str, str]


def _format_conversation_history(history: Optional[Sequence[ConversationMessage]]) -> str:
    """Render a small, untrusted conversation window for the generation prompt."""
    if not history:
        return "(no previous conversation)"
    labels = {"user": "User", "assistant": "Assistant"}
    lines = []
    for item in history[-10:]:
        role = labels.get(item.get("role", ""), "Message")
        content = item.get("content", "").strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines) or "(no previous conversation)"


def _prompt_with_history(history: Optional[Sequence[ConversationMessage]]) -> str:
    """Inject history into the prompt without changing the retrieval query."""
    history_text = _format_conversation_history(history)
    return (
        "Previous conversation (context only; factual answers must still come from sources):\n"
        f"{history_text}\n"
        "---------------------\n"
        + QA_PROMPT_TMPL
    )


def _is_rate_limit_error(error: BaseException) -> bool:
    """Recognize HTTP 429 across provider SDK exception wrappers."""
    current: Optional[BaseException] = error
    visited: set[int] = set()
    while current is not None and id(current) not in visited:
        visited.add(id(current))
        status = getattr(current, "status_code", None) or getattr(current, "code", None)
        text = str(current).lower()
        if status == 429 or "429" in text or "resource_exhausted" in text or "rate limit" in text:
            return True
        current = current.__cause__ or current.__context__
    return False

# ─── Service auto-detection from user query ──────────────────────────────────
# Maps keywords (Arabic/Darija/French) → canonical service_id
_SERVICE_KEYWORDS: Dict[str, List[str]] = {
    "criminal_record": [
        "السجل العدلي", "سجل عدلي", "casier judiciaire", "criminal record",
        "الكازي", "كازي جوديسيار",
    ],
    "birth_certificate": [
        "عقد الازدياد", "رسم الولادة", "شهادة الميلاد", "acte de naissance",
        "عقد ازدياد", "الازدياد",
    ],
    "residence_certificate": [
        "شهادة السكنى", "السكنى", "certificat de résidence", "شهادة سكنى",
    ],
    "marriage_contract": [
        "عقد الزواج", "عقد زواج", "الزواج", "acte de mariage", "زواج",
    ],
    "death_certificate": [
        "شهادة الوفاة", "رسم الوفاة", "الوفاة", "acte de décès",
    ],
    "life_certificate": [
        "شهادة الحياة", "الحياة", "certificat de vie",
    ],
    "single_status_certificate": [
        "شهادة العزوبة", "العزوبة", "célibat",
    ],
    "non_property_certificate": [
        "شهادة عدم الملكية", "عدم الملكية", "non propriété",
    ],
    "administrative_certificate": [
        "الشهادة الإدارية", "شهادة إدارية", "certificat administratif",
    ],
    "good_conduct_certificate": [
        "شهادة حسن السيرة", "حسن السيرة", "bonne conduite",
    ],
}


def _detect_service_from_query(user_query: str) -> Optional[str]:
    """Auto-detect the service type from keywords in the user's question."""
    query_lower = user_query.lower()
    for service_id, keywords in _SERVICE_KEYWORDS.items():
        for kw in keywords:
            if kw in user_query or kw.lower() in query_lower:
                return service_id
    return None


class OmniAgentRAG:
    """Reusable RAG engine with one retrieval pipeline and a configurable LLM."""

    def __init__(
        self,
        chroma_dir: Optional[Path] = None,
        collection_name: str = "public_services_kb",
        ollama_model: Optional[str] = None,
        gemini_model: Optional[str] = None,
    ):
        self.chroma_dir = chroma_dir or CHROMA_DIR
        self.collection_name = collection_name
        self.initialized = False
        self.index = None
        self.qa_prompt = None
        self._model_overrides = {
            key: value
            for key, value in {
                "ollama_model": ollama_model,
                "gemini_model": gemini_model,
            }.items()
            if value is not None
        }
        self._init_rag()

    def _init_rag(self) -> None:
        """Initialize LlamaIndex Settings, ChromaDB store, and VectorStoreIndex."""
        try:
            os.environ["ANONYMIZED_TELEMETRY"] = "False"

            import chromadb
            from llama_index.core import VectorStoreIndex, Settings, PromptTemplate
            from llama_index.vector_stores.chroma import ChromaVectorStore
            from llama_index.embeddings.huggingface import HuggingFaceEmbedding
            from app.core.config import settings as app_settings
            from app.llm_factory import create_llm

            # Only generation varies; retrieval and embeddings remain shared.
            llm_settings = app_settings.model_copy(update=self._model_overrides)
            Settings.llm = create_llm(llm_settings)

            # Embeddings using BAAI/bge-m3 (State-of-the-art for Arabic/Multilingual/Darija)
            Settings.embed_model = HuggingFaceEmbedding(
                model_name="BAAI/bge-m3"
            )

            # Connect to ChromaDB
            if self.chroma_dir.exists():
                client = chromadb.PersistentClient(path=str(self.chroma_dir))
                collection = client.get_or_create_collection(self.collection_name)
                vector_store = ChromaVectorStore(chroma_collection=collection)
                self.index = VectorStoreIndex.from_vector_store(vector_store)
                self.qa_prompt = PromptTemplate(QA_PROMPT_TMPL)
                self.initialized = True
                print(f"[OK] OmniAgentRAG initialized successfully with collection '{collection.name}' ({collection.count()} vectors).")
            else:
                print(f"[WARN] ChromaDB directory not found at {self.chroma_dir}. RAG running in fallback mode.")
                self.initialized = False
        except Exception as e:
            provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
            print(f"[WARN] LLM provider '{provider}' unavailable during RAG initialization: {e}")
            self.initialized = False

    def query(
        self,
        user_query: str,
        service_type: Optional[str] = None,
        conversation_history: Optional[Sequence[ConversationMessage]] = None,
    ) -> Dict[str, Any]:
        """Query RAG pipeline with optional service_type metadata filter.

        Args:
            user_query: The question in Arabic, Darija, or French.
            service_type: Optional service category filter (e.g., 'residence', 'birth', 'marriage').

        Returns:
            Dict containing 'answer', 'sources', 'confidence', and 'language'.
        """
        if not self.initialized or self.index is None:
            return self._fallback_query(user_query, service_type, reason="RAG Vector Index offline")

        try:
            from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

            filters = None
            if service_type:
                # Normalize service_type name
                clean_service = (
                    service_type.lower()
                    .replace("_certificate", "")
                    .replace("_contract", "")
                    .strip()
                )
                filters = MetadataFilters(
                    filters=[ExactMatchFilter(key="service_type", value=clean_service)]
                )

            from llama_index.core import PromptTemplate

            query_engine = self.index.as_query_engine(
                similarity_top_k=3,
                text_qa_template=PromptTemplate(_prompt_with_history(conversation_history)),
                filters=filters
            )

            response = query_engine.query(user_query)
            answer_text = str(response.response).strip()

            # Extract source node metadata
            sources: List[str] = []
            max_score = 0.0

            if hasattr(response, "source_nodes") and response.source_nodes:
                for node_with_score in response.source_nodes:
                    meta = getattr(node_with_score.node, "metadata", {}) or {}
                    score = getattr(node_with_score, "score", 0.0) or 0.0
                    if score > max_score:
                        max_score = float(score)

                    fp = meta.get("file_path", "")
                    st = meta.get("service_type", "")
                    if fp:
                        rel_path = Path(fp).name
                        if rel_path not in sources:
                            sources.append(rel_path)
                    elif st and st not in sources:
                        sources.append(f"{st}_service")

            # Calculate confidence score
            confidence = round(float(max_score), 2) if max_score > 0 else 0.85
            if "ما متأكدش" in answer_text or "ما متأكدش" in answer_text.replace(" ", ""):
                confidence = 0.30

            return {
                "answer": answer_text,
                "sources": sources if sources else [service_type or "knowledge_base"],
                "confidence": confidence,
                "language": "darija"
            }
        except Exception as e:
            provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
            if _is_rate_limit_error(e):
                print(f"[WARN] LLM provider '{provider}' rate limited (HTTP 429); using local KB fallback")
                return self._fallback_query(
                    user_query, service_type, reason=f"LLM provider '{provider}' rate limited (HTTP 429)"
                )
            print(f"[WARN] LLM provider '{provider}' unavailable during RAG query: {e}")
            return self._fallback_query(user_query, service_type, reason=str(e))

    def _fallback_query(self, user_query: str, service_type: Optional[str], reason: str) -> Dict[str, Any]:
        """Fallback to local structured Knowledge Base if RAG index is unavailable."""
        try:
            from app.services.knowledge_base import answer_with_metadata

            # Auto-detect service type from the question if not provided
            resolved_service = service_type or _detect_service_from_query(user_query) or "residence_certificate"

            kb_ans = answer_with_metadata(resolved_service, user_query, use_rag=False)
            return {
                "answer": kb_ans.answer,
                "sources": kb_ans.sources,
                "confidence": kb_ans.confidence,
                "language": "darija",
                "fallback_reason": reason
            }
        except Exception as fallback_err:
            return {
                "answer": "المعلومات غير متوفرة حاليا، يرجى المحاولة لاحقا.",
                "sources": [],
                "confidence": 0.0,
                "language": "darija",
                "fallback_reason": f"{reason}; Fallback error: {fallback_err}"
            }


# Global Singleton Instance
_rag_instance: Optional[OmniAgentRAG] = None


def get_rag_engine() -> OmniAgentRAG:
    """Get or create singleton instance of OmniAgentRAG."""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = OmniAgentRAG()
    return _rag_instance


def query_rag(
    user_query: str,
    service_type: Optional[str] = None,
    conversation_history: Optional[Sequence[ConversationMessage]] = None,
) -> Dict[str, Any]:
    """Public functional interface for querying the RAG pipeline.

    Args:
        user_query: User question in Darija/Arabic/French.
        service_type: Optional category filter (e.g. 'birth', 'residence', 'marriage').

    Returns:
        Dict: {"answer": "...", "sources": [...], "confidence": 0.92, "language": "darija"}
    """
    engine = get_rag_engine()
    return engine.query(
        user_query=user_query,
        service_type=service_type,
        conversation_history=conversation_history,
    )
