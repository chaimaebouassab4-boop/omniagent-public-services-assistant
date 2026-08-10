"""RAG Service Module (OmniAgent RAG)

Wraps ChromaDB + LlamaIndex + BAAI/bge-m3 + Ollama into a clean, reusable service.
Provides query_rag(user_query, service_type) for FastAPI endpoints.
"""
import os
from pathlib import Path
from typing import Any, Optional, List, Dict

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


class OmniAgentRAG:
    """Reusable RAG Engine wrapping ChromaDB + LlamaIndex + BAAI/bge-m3 + Ollama."""

    def __init__(
        self,
        chroma_dir: Optional[Path] = None,
        collection_name: str = "public_services_kb",
        ollama_model: str = "llama3.1:8b"
    ):
        self.chroma_dir = chroma_dir or CHROMA_DIR
        self.collection_name = collection_name
        self.ollama_model = ollama_model
        self.initialized = False
        self.index = None
        self.qa_prompt = None
        self._init_rag()

    def _init_rag(self) -> None:
        """Initialize LlamaIndex Settings, ChromaDB store, and VectorStoreIndex."""
        try:
            os.environ["ANONYMIZED_TELEMETRY"] = "False"

            import chromadb
            from llama_index.core import VectorStoreIndex, Settings, PromptTemplate
            from llama_index.vector_stores.chroma import ChromaVectorStore
            from llama_index.llms.ollama import Ollama
            from llama_index.embeddings.huggingface import HuggingFaceEmbedding

            # Configure Ollama LLM
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            Settings.llm = Ollama(
                model=self.ollama_model,
                request_timeout=180.0,
                base_url=base_url,
                temperature=0.1
            )

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
            print(f"[WARN] OmniAgentRAG initialization notice: {e}")
            self.initialized = False

    def query(self, user_query: str, service_type: Optional[str] = None) -> Dict[str, Any]:
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

            query_engine = self.index.as_query_engine(
                similarity_top_k=3,
                text_qa_template=self.qa_prompt,
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
            print(f"[ERROR] Error during RAG query execution: {e}")
            return self._fallback_query(user_query, service_type, reason=str(e))

    def _fallback_query(self, user_query: str, service_type: Optional[str], reason: str) -> Dict[str, Any]:
        """Fallback to local structured Knowledge Base if RAG index is unavailable."""
        try:
            from app.services.knowledge_base import answer_with_metadata
            kb_ans = answer_with_metadata(service_type or "residence_certificate", user_query)
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


def query_rag(user_query: str, service_type: Optional[str] = None) -> Dict[str, Any]:
    """Public functional interface for querying the RAG pipeline.

    Args:
        user_query: User question in Darija/Arabic/French.
        service_type: Optional category filter (e.g. 'birth', 'residence', 'marriage').

    Returns:
        Dict: {"answer": "...", "sources": [...], "confidence": 0.92, "language": "darija"}
    """
    engine = get_rag_engine()
    return engine.query(user_query=user_query, service_type=service_type)
